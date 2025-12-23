"""
Vision-Language Model interface for scene understanding.

This module provides a unified interface to VLMs (primarily OpenAI GPT-4 Vision)
with fallback to mock mode for testing without API keys.

Key Design Decisions:
- Structured prompting for consistent, parseable outputs
- Explicit focus on safety-relevant features
- Graceful degradation with mock mode
- Retry logic for transient failures
- Response validation and error handling
"""

import base64
import io
import json
import logging
import time
from typing import Optional, Dict, Any
from datetime import datetime
import numpy as np
from PIL import Image

from models import Frame, VisionAnalysis
from config import VLMConfig

logger = logging.getLogger(__name__)


class VisionModelInterface:
    """
    Abstract interface for Vision-Language Models.
    
    This abstraction allows easy swapping of model providers
    while maintaining consistent behavior.
    """
    
    def analyze_frame(self, frame: Frame) -> VisionAnalysis:
        """
        Analyze a frame and return structured vision analysis.
        
        Args:
            frame: Frame to analyze
            
        Returns:
            VisionAnalysis with scene understanding
        """
        raise NotImplementedError


class OpenAIVisionModel(VisionModelInterface):
    """
    OpenAI GPT-4 Vision implementation.
    
    Uses GPT-4o or GPT-4-turbo with vision capabilities for
    comprehensive scene understanding.
    """
    
    SYSTEM_PROMPT = """You are an expert factory safety monitoring AI. 
Your role is to analyze images from factory floors and identify safety concerns.

Focus on:
1. Personal Protective Equipment (PPE) - hard hats, safety vests, gloves, safety glasses, steel-toed boots
2. Unsafe behaviors - improper lifting, reaching into machinery, standing in hazardous areas
3. Environmental hazards - spills, obstructions, poor lighting, damaged equipment
4. Machinery safety - guards in place, proper operation, proximity of workers
5. Zone violations - unauthorized access to restricted areas
6. Ergonomic risks - poor posture, repetitive motions, awkward positions

Provide structured, factual observations. Be specific about locations and conditions."""

    ANALYSIS_PROMPT = """Analyze this factory floor image and provide a structured safety assessment.

Return your analysis in this JSON format:
{
  "scene_description": "Brief overall description of the scene",
  "environment_type": "Type of facility (warehouse, assembly line, loading dock, etc.)",
  "lighting_conditions": "well-lit | dim | mixed | poor",
  "visibility": "clear | partially obscured | poor",
  "detected_people": [
    {
      "id": 1,
      "location": "description of where person is",
      "activity": "what they're doing",
      "ppe_visible": ["list", "of", "visible", "ppe"],
      "ppe_missing": ["list", "of", "missing", "ppe"],
      "posture": "standing | sitting | crouching | climbing | etc."
    }
  ],
  "detected_objects": [
    {
      "object": "object name",
      "location": "where it is",
      "condition": "good | damaged | unclear",
      "safety_relevant": true/false
    }
  ],
  "activities": ["list", "of", "observed", "activities"],
  "hazards_visible": ["list", "of", "any", "visible", "hazards"],
  "safety_equipment": ["list", "of", "safety", "equipment", "present"],
  "immediate_concerns": ["list", "of", "immediate", "safety", "concerns"]
}

Be thorough but concise. If you cannot see certain details clearly, note this in your response."""

    def __init__(self, config: VLMConfig):
        """
        Initialize OpenAI Vision Model.
        
        Args:
            config: VLM configuration
        """
        self.config = config
        self.client = None
        
        # Initialize OpenAI client
        if config.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=config.api_key)
                logger.info(f"Initialized OpenAI client with model: {config.model_name}")
            except ImportError:
                logger.error("OpenAI library not installed. Install with: pip install openai")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
        else:
            logger.warning("No OpenAI API key provided")
    
    def _encode_image(self, image: np.ndarray) -> str:
        """
        Encode numpy image array to base64 string.
        
        Args:
            image: RGB image array
            
        Returns:
            Base64 encoded image string
        """
        # Convert numpy array to PIL Image
        pil_image = Image.fromarray(image)
        
        # Resize if too large (to reduce token usage and latency)
        max_size = 1024
        if max(pil_image.size) > max_size:
            pil_image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Encode to base64
        buffer = io.BytesIO()
        pil_image.save(buffer, format="JPEG", quality=85)
        image_bytes = buffer.getvalue()
        
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from model, with fallback handling.
        
        Args:
            response_text: Raw response text
            
        Returns:
            Parsed dictionary
        """
        try:
            # Try to find JSON in the response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # No JSON found, create structured response from text
                logger.warning("No JSON in response, parsing as text")
                return {
                    "scene_description": response_text[:500],
                    "environment_type": "unknown",
                    "lighting_conditions": "unclear",
                    "visibility": "unclear",
                    "detected_people": [],
                    "detected_objects": [],
                    "activities": [],
                    "hazards_visible": [],
                    "safety_equipment": [],
                    "immediate_concerns": []
                }
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            # Return minimal valid structure
            return {
                "scene_description": response_text[:500] if response_text else "Parse error",
                "environment_type": "unknown",
                "lighting_conditions": "unclear",
                "visibility": "unclear",
                "detected_people": [],
                "detected_objects": [],
                "activities": [],
                "hazards_visible": [],
                "safety_equipment": [],
                "immediate_concerns": []
            }
    
    def analyze_frame(self, frame: Frame) -> VisionAnalysis:
        """
        Analyze frame using OpenAI Vision API.
        
        Args:
            frame: Frame to analyze
            
        Returns:
            VisionAnalysis with structured results
        """
        if not self.client:
            raise RuntimeError("OpenAI client not initialized")
        
        start_time = time.time()
        
        try:
            # Encode image
            image_b64 = self._encode_image(frame.image)
            
            # Create API request
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": self.ANALYSIS_PROMPT
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}",
                                    "detail": self.config.detail
                                }
                            }
                        ]
                    }
                ],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=self.config.timeout
            )
            
            # Extract response
            response_text = response.choices[0].message.content
            processing_time = time.time() - start_time
            
            # Parse response
            parsed = self._parse_response(response_text)
            
            # Create VisionAnalysis object
            analysis = VisionAnalysis(
                frame_id=frame.frame_id,
                timestamp=datetime.now(),
                scene_description=parsed.get("scene_description", ""),
                detected_people=parsed.get("detected_people", []),
                detected_objects=parsed.get("detected_objects", []),
                activities=parsed.get("activities", []),
                environment_type=parsed.get("environment_type", ""),
                lighting_conditions=parsed.get("lighting_conditions", ""),
                visibility=parsed.get("visibility", ""),
                ppe_status={
                    "people_count": len(parsed.get("detected_people", [])),
                    "ppe_compliant": sum(1 for p in parsed.get("detected_people", []) 
                                        if not p.get("ppe_missing", [])),
                },
                hazards_visible=parsed.get("hazards_visible", []) + 
                              parsed.get("immediate_concerns", []),
                safety_equipment=parsed.get("safety_equipment", []),
                model_name=self.config.model_name,
                processing_time=processing_time,
                raw_response=response_text
            )
            
            logger.info(f"Vision analysis completed in {processing_time:.2f}s")
            logger.debug(f"Detected: {len(analysis.detected_people)} people, "
                        f"{len(analysis.hazards_visible)} hazards")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Vision analysis failed: {e}", exc_info=True)
            raise


class MockVisionModel(VisionModelInterface):
    """
    Mock vision model for testing without API access.
    
    Uses basic computer vision to actually analyze frames,
    only generating alerts when it detects something.
    """
    
    def __init__(self, config: VLMConfig):
        """Initialize mock model."""
        self.config = config
        self.frame_count = 0
        logger.info("Initialized MOCK vision model (for testing without API key)")
        logger.warning("⚠️  MOCK MODE: Using basic CV analysis. For real analysis, add OpenAI API key.")
    
    def _analyze_frame_cv(self, frame: Frame) -> Dict[str, Any]:
        """
        Actually analyze frame using basic computer vision.
        Only reports issues if detected.
        """
        import cv2
        
        image = frame.image
        height, width = image.shape[:2]
        
        # Convert to different color spaces for analysis
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        
        # Basic analysis
        detected_people = []
        hazards_visible = []
        safety_equipment = []
        
        # Detect bright colors (safety vests, hard hats)
        # Yellow/Orange range for safety vests
        yellow_lower = np.array([20, 100, 100])
        yellow_upper = np.array([30, 255, 255])
        yellow_mask = cv2.inRange(hsv, yellow_lower, yellow_upper)
        yellow_pixels = np.sum(yellow_mask > 0)
        
        # Bright yellow (hard hats)
        bright_yellow_lower = np.array([20, 200, 200])
        bright_yellow_upper = np.array([30, 255, 255])
        bright_yellow_mask = cv2.inRange(hsv, bright_yellow_lower, bright_yellow_upper)
        bright_yellow_pixels = np.sum(bright_yellow_mask > 0)
        
        # Detect skin tones (people)
        skin_lower = np.array([0, 20, 70])
        skin_upper = np.array([20, 255, 255])
        skin_mask = cv2.inRange(hsv, skin_lower, skin_upper)
        skin_pixels = np.sum(skin_mask > 0)
        
        # Detect red (fire extinguishers, warnings)
        red_lower1 = np.array([0, 100, 100])
        red_upper1 = np.array([10, 255, 255])
        red_lower2 = np.array([170, 100, 100])
        red_upper2 = np.array([180, 255, 255])
        red_mask1 = cv2.inRange(hsv, red_lower1, red_upper1)
        red_mask2 = cv2.inRange(hsv, red_lower2, red_upper2)
        red_pixels = np.sum((red_mask1 + red_mask2) > 0)
        
        # Estimate if people are present (based on skin tone detection)
        # More sensitive detection - lower threshold
        has_people = skin_pixels > (width * height * 0.005)  # At least 0.5% of frame (more sensitive)
        
        # Also check for human-like shapes (rectangular patterns that might be people)
        # Simple heuristic: look for vertical structures (people are taller than wide)
        gray = cv2.cvtColor(frame.image, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Check for person-like contours (tall rectangles)
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            if h > 0 and w > 0:
                aspect_ratio = h / w
                area = w * h
                # Person-like: tall (aspect > 1.5) and reasonable size
                if aspect_ratio > 1.5 and area > (width * height * 0.01):
                    has_people = True
                    break
        
        # Estimate if safety equipment is visible (more sensitive)
        has_safety_vest = yellow_pixels > (width * height * 0.003)  # Lower threshold
        has_hard_hat = bright_yellow_pixels > (width * height * 0.001)  # Lower threshold
        has_safety_equipment = red_pixels > (width * height * 0.002)  # Lower threshold
        
        # Build analysis - be more generous with detection
        if has_people:
            # Estimate number of people (rough heuristic)
            num_people = min(5, max(1, int(skin_pixels / (width * height * 0.03))))
            if num_people > 0:
                for i in range(num_people):
                    ppe_missing = []
                    ppe_visible = []
                    
                    # Check for hard hat (bright yellow detection)
                    if has_hard_hat:
                        ppe_visible.append("hard hat")
                    else:
                        ppe_missing.append("hard hat")
                    
                    # Check for safety vest (orange/yellow detection)
                    if has_safety_vest:
                        ppe_visible.append("safety vest")
                    else:
                        ppe_missing.append("safety vest")
                    
                    detected_people.append({
                        "id": i + 1,
                        "location": "factory floor",
                        "activity": "working",
                        "ppe_visible": ppe_visible,
                        "ppe_missing": ppe_missing,
                        "posture": "standing"
                    })
        else:
            # Even if we don't detect people clearly, if there's movement/activity, report it
            # Check for any significant color variation (might be people)
            color_variance = np.std(frame.image)
            if color_variance > 30:  # Significant variation suggests activity
                # Conservative: assume 1 person but with low confidence
                detected_people.append({
                    "id": 1,
                    "location": "factory floor",
                    "activity": "activity detected",
                    "ppe_visible": (["hard hat"] if has_hard_hat else []) + 
                                 (["safety vest"] if has_safety_vest else []),
                    "ppe_missing": (["hard hat"] if not has_hard_hat else []) + 
                                 (["safety vest"] if not has_safety_vest else []),
                    "posture": "unknown"
                })
        
        # Report hazards if we detect people without proper PPE
        if detected_people:
            for person in detected_people:
                if person.get("ppe_missing"):
                    missing = ", ".join(person["ppe_missing"])
                    hazards_visible.append(f"Worker visible without {missing}")
        
        if has_safety_equipment:
            safety_equipment.append("Fire safety equipment visible")
        
        # Scene description based on what we see
        scene_parts = []
        if detected_people:
            scene_parts.append(f"{len(detected_people)} worker(s) visible")
        else:
            scene_parts.append("Factory floor visible")
        
        if has_safety_vest or has_hard_hat:
            scene_parts.append("Some safety equipment visible")
        
        if has_safety_equipment:
            scene_parts.append("Safety equipment present")
        
        # Also check overall scene for general safety observations
        gray_mean = np.mean(cv2.cvtColor(frame.image, cv2.COLOR_RGB2GRAY))
        if gray_mean < 100:  # Darker scene
            scene_parts.append("dim lighting")
        
        if not has_safety_equipment and detected_people:
            # People present but no visible safety equipment
            scene_parts.append("limited safety equipment visible")
        
        scene_description = "Factory floor. " + ". ".join(scene_parts) + "."
        
        return {
            "scene_description": scene_description,
            "environment_type": "factory floor",
            "lighting_conditions": "adequate" if np.mean(gray) > 100 else "dim",
            "visibility": "clear",
            "detected_people": detected_people,
            "detected_objects": [],
            "activities": ["work activity"] if has_people else [],
            "hazards_visible": hazards_visible,
            "safety_equipment": safety_equipment,
            "immediate_concerns": hazards_visible.copy()
        }
    
    def _generate_mock_analysis(self, frame: Frame) -> Dict[str, Any]:
        """
        Generate analysis by actually looking at the frame.
        Only reports issues if detected.
        """
        self.frame_count += 1
        
        # Actually analyze the frame using CV
        return self._analyze_frame_cv(frame)
        
        if scenario == 0:
            # Compliant scenario
            return {
                "scene_description": "Factory floor with workers performing assembly tasks. "
                                   "Good lighting and clear visibility. Workers wearing proper PPE.",
                "environment_type": "assembly line",
                "lighting_conditions": "well-lit",
                "visibility": "clear",
                "detected_people": [
                    {
                        "id": 1,
                        "location": "near assembly station",
                        "activity": "assembling components",
                        "ppe_visible": ["hard hat", "safety vest", "safety glasses"],
                        "ppe_missing": [],
                        "posture": "standing"
                    },
                    {
                        "id": 2,
                        "location": "quality inspection area",
                        "activity": "inspecting parts",
                        "ppe_visible": ["hard hat", "safety vest", "gloves"],
                        "ppe_missing": [],
                        "posture": "standing"
                    }
                ],
                "detected_objects": [
                    {"object": "conveyor belt", "location": "center", "condition": "good", "safety_relevant": True},
                    {"object": "tool cart", "location": "left side", "condition": "good", "safety_relevant": False}
                ],
                "activities": ["assembly work", "quality inspection"],
                "hazards_visible": [],
                "safety_equipment": ["fire extinguisher", "first aid station", "emergency stop button"],
                "immediate_concerns": []
            }
        
        elif scenario == 1:
            # Minor PPE violation
            return {
                "scene_description": "Warehouse area with forklift operation. "
                                   "One worker not wearing complete PPE.",
                "environment_type": "warehouse",
                "lighting_conditions": "well-lit",
                "visibility": "clear",
                "detected_people": [
                    {
                        "id": 1,
                        "location": "near forklift",
                        "activity": "directing forklift",
                        "ppe_visible": ["safety vest"],
                        "ppe_missing": ["hard hat", "safety glasses"],
                        "posture": "standing"
                    }
                ],
                "detected_objects": [
                    {"object": "forklift", "location": "center", "condition": "good", "safety_relevant": True},
                    {"object": "pallet stack", "location": "background", "condition": "good", "safety_relevant": True}
                ],
                "activities": ["forklift operation", "material handling"],
                "hazards_visible": ["incomplete PPE on worker"],
                "safety_equipment": ["fire extinguisher", "spill kit"],
                "immediate_concerns": ["Worker near forklift without hard hat"]
            }
        
        elif scenario == 2:
            # Environmental hazard
            return {
                "scene_description": "Loading dock area with potential slip hazard. "
                                   "Wet floor visible near worker pathway.",
                "environment_type": "loading dock",
                "lighting_conditions": "mixed",
                "visibility": "clear",
                "detected_people": [
                    {
                        "id": 1,
                        "location": "near loading bay",
                        "activity": "loading packages",
                        "ppe_visible": ["hard hat", "safety vest", "gloves"],
                        "ppe_missing": [],
                        "posture": "bending"
                    }
                ],
                "detected_objects": [
                    {"object": "wet floor", "location": "walkway", "condition": "damaged", "safety_relevant": True},
                    {"object": "loading dock", "location": "background", "condition": "good", "safety_relevant": True},
                    {"object": "packages", "location": "stacked near dock", "condition": "good", "safety_relevant": False}
                ],
                "activities": ["loading operations", "material handling"],
                "hazards_visible": ["wet floor without warning sign", "worker bending with potential strain risk"],
                "safety_equipment": ["loading dock barriers"],
                "immediate_concerns": ["Slip hazard on walkway"]
            }
        
        else:
            # Machinery proximity concern
            return {
                "scene_description": "Machine shop with active equipment. "
                                   "Worker in close proximity to operating machinery.",
                "environment_type": "machine shop",
                "lighting_conditions": "well-lit",
                "visibility": "clear",
                "detected_people": [
                    {
                        "id": 1,
                        "location": "next to CNC machine",
                        "activity": "monitoring machine operation",
                        "ppe_visible": ["hard hat", "safety vest", "safety glasses", "hearing protection"],
                        "ppe_missing": [],
                        "posture": "standing"
                    }
                ],
                "detected_objects": [
                    {"object": "CNC machine", "location": "center", "condition": "good", "safety_relevant": True},
                    {"object": "safety guard", "location": "on machine", "condition": "good", "safety_relevant": True},
                    {"object": "coolant tank", "location": "near machine", "condition": "good", "safety_relevant": True}
                ],
                "activities": ["machine operation", "equipment monitoring"],
                "hazards_visible": ["worker very close to operating machinery"],
                "safety_equipment": ["machine guards", "emergency stop", "fire extinguisher"],
                "immediate_concerns": ["Monitor safe distance from active machinery"]
            }
    
    def analyze_frame(self, frame: Frame) -> VisionAnalysis:
        """
        Generate mock vision analysis.
        
        Args:
            frame: Frame to "analyze"
            
        Returns:
            VisionAnalysis with mock data
        """
        # Simulate processing time
        time.sleep(0.5)
        
        start_time = time.time()
        parsed = self._generate_mock_analysis(frame)
        processing_time = time.time() - start_time
        
        analysis = VisionAnalysis(
            frame_id=frame.frame_id,
            timestamp=datetime.now(),
            scene_description=parsed["scene_description"],
            detected_people=parsed["detected_people"],
            detected_objects=parsed["detected_objects"],
            activities=parsed["activities"],
            environment_type=parsed["environment_type"],
            lighting_conditions=parsed["lighting_conditions"],
            visibility=parsed["visibility"],
            ppe_status={
                "people_count": len(parsed["detected_people"]),
                "ppe_compliant": sum(1 for p in parsed["detected_people"] 
                                    if not p.get("ppe_missing", [])),
            },
            hazards_visible=parsed["hazards_visible"] + parsed["immediate_concerns"],
            safety_equipment=parsed["safety_equipment"],
            model_name="MOCK",
            processing_time=processing_time,
            raw_response=json.dumps(parsed, indent=2)
        )
        
        logger.info(f"[MOCK] Vision analysis completed in {processing_time:.2f}s")
        
        return analysis


class VisionModelFactory:
    """
    Factory for creating appropriate vision model instance.
    
    Automatically selects between real API and mock based on configuration.
    """
    
    @staticmethod
    def create(config: VLMConfig) -> VisionModelInterface:
        """
        Create vision model instance.
        
        Args:
            config: VLM configuration
            
        Returns:
            VisionModelInterface instance
        """
        # Use mock if no API key and mock is enabled
        if not config.api_key and config.enable_mock:
            logger.warning("No API key provided, using MOCK vision model")
            return MockVisionModel(config)
        
        # Use configured provider
        if config.provider == "openai":
            return OpenAIVisionModel(config)
        else:
            raise ValueError(f"Unsupported VLM provider: {config.provider}")


def test_vision_model():
    """Test function for vision model."""
    from config import Config
    import cv2
    
    config = Config()
    
    # Create vision model
    model = VisionModelFactory.create(config.vlm)
    
    # Create a test frame (solid color for testing)
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    test_image[:] = (100, 150, 200)  # Blue-ish color
    
    frame = Frame(
        image=test_image,
        frame_number=1,
        source="test",
        width=640,
        height=480
    )
    
    print("Testing vision model...")
    analysis = model.analyze_frame(frame)
    
    print(f"\nAnalysis Results:")
    print(f"Scene: {analysis.scene_description}")
    print(f"Environment: {analysis.environment_type}")
    print(f"People detected: {len(analysis.detected_people)}")
    print(f"Hazards: {analysis.hazards_visible}")
    print(f"Processing time: {analysis.processing_time:.2f}s")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_vision_model()

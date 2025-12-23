"""
Chatbot module using Google Gemini for video Q&A.

Allows users to ask questions about:
- Current video frame
- Analysis results
- Safety events
- General safety questions
"""

import logging
import base64
import io
from typing import Optional, Dict, Any
from datetime import datetime
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class ChatbotInterface:
    """Abstract interface for chatbot."""
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process chat message with optional context.
        
        Args:
            message: User's question
            context: Optional context (current frame, analysis, events, etc.)
            
        Returns:
            Bot's response
        """
        raise NotImplementedError


class GeminiChatbot(ChatbotInterface):
    """
    Google Gemini chatbot for video Q&A.
    
    Uses Gemini Pro Vision for free, high-quality responses.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Gemini chatbot."""
        self.api_key = api_key
        self.client = None
        
        if api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel('gemini-pro-vision')
                logger.info("✅ Gemini chatbot initialized")
            except ImportError:
                logger.warning("⚠️  google-generativeai not installed. Install with: pip install google-generativeai")
                self.client = None
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.client = None
        else:
            logger.warning("⚠️  No Gemini API key provided. Chatbot will use mock mode.")
    
    def _encode_image(self, image: np.ndarray) -> bytes:
        """Convert numpy array to JPEG bytes."""
        pil_image = Image.fromarray(image.astype('uint8'), 'RGB')
        buffer = io.BytesIO()
        pil_image.save(buffer, format='JPEG', quality=85)
        return buffer.getvalue()
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Process chat message with context.
        
        Args:
            message: User's question
            context: Dict with keys like:
                - 'current_frame': numpy array of current video frame
                - 'latest_analysis': VisionAnalysis object
                - 'recent_events': List of SafetyEvent objects
                - 'video_info': Dict with video metadata
                
        Returns:
            Bot's response
        """
        if not self.client:
            return self._mock_response(message, context)
        
        try:
            # Build context-aware prompt
            prompt = self._build_prompt(message, context)
            
            # Prepare content
            content = [prompt]
            
            # Add image if available
            if context and 'current_frame' in context and context['current_frame'] is not None:
                image_bytes = self._encode_image(context['current_frame'])
                content.append({
                    'mime_type': 'image/jpeg',
                    'data': image_bytes
                })
            
            # Call Gemini
            response = self.client.generate_content(content)
            
            return response.text
            
        except Exception as e:
            logger.error(f"Chatbot error: {e}", exc_info=True)
            return f"Sorry, I encountered an error: {str(e)}. Please try again."
    
    def _build_prompt(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build context-aware prompt."""
        base_prompt = """You are a helpful factory safety monitoring assistant. 
You help users understand safety analysis results and answer questions about factory safety.

"""
        
        if context:
            context_parts = []
            
            if 'latest_analysis' in context and context['latest_analysis']:
                analysis = context['latest_analysis']
                context_parts.append(f"""
CURRENT ANALYSIS:
- Scene: {analysis.scene_description}
- People detected: {len(analysis.detected_people)}
- Hazards: {', '.join(analysis.hazards_visible[:3]) if analysis.hazards_visible else 'None'}
- Environment: {analysis.environment_type}
""")
            
            if 'recent_events' in context and context['recent_events']:
                events = context['recent_events'][:5]  # Last 5 events
                events_text = "\n".join([f"- {e.title} ({e.risk_level.value})" for e in events])
                context_parts.append(f"""
RECENT SAFETY EVENTS:
{events_text}
""")
            
            if 'video_info' in context:
                video_info = context['video_info']
                context_parts.append(f"""
VIDEO INFO:
- Duration: {video_info.get('duration', 'Unknown')} seconds
- FPS: {video_info.get('fps', 'Unknown')}
""")
            
            if context_parts:
                base_prompt += "\n".join(context_parts) + "\n"
        
        base_prompt += f"""
USER QUESTION: {message}

Please provide a helpful, accurate response. If you see an image, describe what you see and answer the question based on both the image and the context provided.
"""
        
        return base_prompt
    
    def _mock_response(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Mock response when Gemini is not available."""
        message_lower = message.lower()
        
        # Greetings
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'greetings']):
            return "Hello! I'm your factory safety assistant. I can help you understand safety analysis results. Ask me about the video, safety events, or general safety questions!"
        
        # Safety questions
        if any(word in message_lower for word in ['safety', 'hazard', 'risk', 'danger', 'unsafe']):
            if context and 'latest_analysis' in context and context['latest_analysis']:
                analysis = context['latest_analysis']
                if hasattr(analysis, 'hazards_visible') and analysis.hazards_visible:
                    hazards = ', '.join(analysis.hazards_visible[:3])
                    return f"I detected {len(analysis.hazards_visible)} safety concern(s): {hazards}. For more detailed analysis with image understanding, add a Gemini API key (free at https://makersuite.google.com/app/apikey)."
                else:
                    return "The current scene appears safe. No immediate hazards detected in the latest analysis. For detailed image analysis, add a Gemini API key."
            return "I can analyze safety concerns! Upload a video and start analysis, then ask me about what I see. For advanced AI-powered responses with image understanding, add a Gemini API key (free)."
        
        # People questions
        if any(word in message_lower for word in ['people', 'worker', 'person', 'how many']):
            if context and 'latest_analysis' in context and context['latest_analysis']:
                analysis = context['latest_analysis']
                if hasattr(analysis, 'detected_people'):
                    count = len(analysis.detected_people) if analysis.detected_people else 0
                    return f"I detected {count} person(s) in the current frame. For detailed person analysis and descriptions, add a Gemini API key."
            return "I can detect people in the video. Upload a video and start analysis, then ask me about people. For detailed analysis, add a Gemini API key."
        
        # Event questions
        if any(word in message_lower for word in ['event', 'alert', 'violation', 'ppe']):
            if context and 'recent_events' in context and context['recent_events']:
                events = context['recent_events']
                if events:
                    event_list = []
                    for e in events[:3]:
                        if hasattr(e, 'title'):
                            event_list.append(e.title)
                        elif isinstance(e, dict):
                            event_list.append(e.get('title', 'Unknown event'))
                    if event_list:
                        return f"Recent safety events: {', '.join(event_list)}. For detailed explanations, add a Gemini API key."
            return "No recent safety events detected. For detailed event analysis, add a Gemini API key."
        
        # Video questions
        if any(word in message_lower for word in ['video', 'frame', 'what do you see', 'describe']):
            if context and 'video_info' in context:
                info = context['video_info']
                return f"I'm analyzing a video ({info.get('filename', 'unknown')}, {info.get('duration', 0):.1f}s). For detailed frame-by-frame descriptions, add a Gemini API key to enable image understanding."
            return "Upload a video and start analysis, then I can tell you what I see. For detailed image descriptions, add a Gemini API key."
        
        # General responses
        if '?' in message:
            return "I'm here to help with factory safety questions! Ask me about safety events, people in the video, hazards, or general safety topics. For advanced AI responses with image understanding, add a Gemini API key (free at https://makersuite.google.com/app/apikey)."
        
        return "I'm a factory safety chatbot! I can answer questions about video analysis, safety events, and general safety topics. For detailed AI-powered responses, add a Gemini API key (free). Try asking: 'What safety issues do you see?' or 'How many people are in the video?'"


class MockChatbot(ChatbotInterface):
    """Simple mock chatbot for testing."""
    
    def chat(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Mock chat response."""
        return GeminiChatbot()._mock_response(message, context)


def create_chatbot(api_key: Optional[str] = None) -> ChatbotInterface:
    """
    Factory function to create appropriate chatbot.
    
    Args:
        api_key: Gemini API key (optional)
        
    Returns:
        ChatbotInterface instance
    """
    if api_key:
        return GeminiChatbot(api_key)
    else:
        return MockChatbot()

"""
Risk reasoning and assessment module.

This module takes vision analysis results and performs deeper reasoning
about safety risks, providing structured risk assessments with actionable recommendations.

Key Design Decisions:
- LLM-based reasoning for contextual understanding
- Structured prompting for consistent risk assessment
- Confidence scoring to handle uncertainty
- Prioritization of immediate vs. potential risks
- Actionable recommendations tied to specific regulations/best practices
"""

import json
import logging
import time
from typing import List, Optional
from datetime import datetime

from models import VisionAnalysis, SafetyEvent, RiskLevel, EventType
from config import ReasoningConfig

logger = logging.getLogger(__name__)


class RiskReasonerInterface:
    """Abstract interface for risk reasoning."""
    
    def assess_risks(self, analysis: VisionAnalysis) -> List[SafetyEvent]:
        """
        Assess safety risks from vision analysis.
        
        Args:
            analysis: Vision analysis results
            
        Returns:
            List of detected safety events
        """
        raise NotImplementedError


class LLMRiskReasoner(RiskReasonerInterface):
    """
    LLM-based risk reasoner using GPT-4 or similar.
    
    Performs contextual risk assessment by reasoning over vision analysis,
    considering:
    - Severity and immediacy of risks
    - Context-dependent hazards
    - Compound risks (multiple factors combining)
    - Regulatory compliance
    - Best practices and industry standards
    """
    
    SYSTEM_PROMPT = """You are an expert occupational safety analyst with deep knowledge of:
- OSHA regulations and standards
- Industrial safety best practices
- Risk assessment methodologies
- Factory and warehouse safety protocols
- Ergonomics and human factors
- Machinery and equipment safety

Your role is to analyze safety observations and provide structured risk assessments.
Be precise, practical, and focused on preventing incidents.
Consider both immediate dangers and developing risk situations.
"""

    REASONING_PROMPT = """Based on the following factory safety observations, identify and assess all safety risks.

OBSERVATIONS:
{observations}

For each identified risk, provide your assessment in this JSON format:
{
  "risks": [
    {
      "event_type": "ppe_violation | unsafe_behavior | zone_violation | machinery_hazard | environmental_hazard | ergonomic_risk | near_miss | general_safety",
      "risk_level": "LOW | MEDIUM | HIGH | CRITICAL",
      "title": "Brief descriptive title",
      "description": "Detailed description of the risk",
      "location": "Specific location if mentioned",
      "people_involved": 0,
      "equipment_involved": ["list", "of", "equipment"],
      "confidence": 0.0-1.0,
      "severity_score": 0.0-10.0,
      "urgency": "low | normal | high | immediate",
      "recommended_actions": ["specific", "actionable", "recommendations"],
      "contributing_factors": ["factors", "contributing", "to", "risk"],
      "related_regulations": ["relevant", "OSHA", "or", "standards"],
      "reasoning": "Why this is a concern and what could happen",
      "false_positive_likelihood": "low | medium | high"
    }
  ]
}

ASSESSMENT GUIDELINES:
- CRITICAL: Immediate danger of serious injury/death (e.g., no fall protection at height, exposed to moving machinery)
- HIGH: Significant injury likely if not addressed (e.g., missing hard hat near overhead hazards, unsafe lifting)
- MEDIUM: Potential for injury exists (e.g., incomplete PPE in moderate risk area, minor ergonomic issues)
- LOW: Best practice violation with low injury potential (e.g., housekeeping issues, minor procedural non-compliance)

- Be conservative but not alarmist
- Consider context (same action may be safe in one environment, unsafe in another)
- Prioritize immediate physical hazards over procedural issues
- Note when visibility or information is insufficient for confident assessment
- Provide specific, actionable recommendations

Return ONLY valid JSON. If no significant risks are identified, return {"risks": []}."""

    def __init__(self, config: ReasoningConfig):
        """
        Initialize LLM risk reasoner.
        
        Args:
            config: Reasoning configuration
        """
        self.config = config
        self.client = None
        
        # Initialize OpenAI client (or other LLM provider)
        if config.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=config.api_key)
                logger.info(f"Initialized reasoning client with model: {config.model_name}")
            except ImportError:
                logger.error("OpenAI library not installed")
            except Exception as e:
                logger.error(f"Failed to initialize reasoning client: {e}")
        else:
            logger.warning("No API key provided for risk reasoner")
    
    def _format_observations(self, analysis: VisionAnalysis) -> str:
        """
        Format vision analysis into structured observations for reasoning.
        
        Args:
            analysis: Vision analysis results
            
        Returns:
            Formatted observation string
        """
        observations = []
        
        # Scene overview
        observations.append(f"Scene: {analysis.scene_description}")
        observations.append(f"Environment: {analysis.environment_type}")
        observations.append(f"Lighting: {analysis.lighting_conditions}")
        observations.append(f"Visibility: {analysis.visibility}")
        
        # People and PPE
        if analysis.detected_people:
            observations.append(f"\nPeople detected: {len(analysis.detected_people)}")
            for person in analysis.detected_people:
                person_info = [
                    f"  Person {person.get('id', '?')}:",
                    f"    Location: {person.get('location', 'unknown')}",
                    f"    Activity: {person.get('activity', 'unknown')}",
                    f"    Posture: {person.get('posture', 'unknown')}",
                    f"    PPE visible: {', '.join(person.get('ppe_visible', [])) or 'none'}",
                    f"    PPE missing: {', '.join(person.get('ppe_missing', [])) or 'none'}"
                ]
                observations.append('\n'.join(person_info))
        
        # Objects and equipment
        if analysis.detected_objects:
            observations.append(f"\nObjects/Equipment detected:")
            for obj in analysis.detected_objects:
                obj_info = f"  - {obj.get('object', 'unknown')}: {obj.get('location', 'unknown')} (condition: {obj.get('condition', 'unknown')})"
                observations.append(obj_info)
        
        # Activities
        if analysis.activities:
            observations.append(f"\nActivities: {', '.join(analysis.activities)}")
        
        # Visible hazards
        if analysis.hazards_visible:
            observations.append(f"\nVisible hazards/concerns:")
            for hazard in analysis.hazards_visible:
                observations.append(f"  - {hazard}")
        
        # Safety equipment present
        if analysis.safety_equipment:
            observations.append(f"\nSafety equipment present: {', '.join(analysis.safety_equipment)}")
        
        return '\n'.join(observations)
    
    def _parse_risk_response(self, response_text: str) -> List[dict]:
        """
        Parse JSON response containing risk assessments.
        
        Args:
            response_text: Raw LLM response
            
        Returns:
            List of risk dictionaries
        """
        try:
            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                parsed = json.loads(json_str)
                return parsed.get('risks', [])
            else:
                logger.warning("No JSON found in risk assessment response")
                return []
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse risk response: {e}")
            return []
    
    def _create_safety_event(self, risk_dict: dict, analysis: VisionAnalysis) -> Optional[SafetyEvent]:
        """
        Create SafetyEvent from parsed risk dictionary.
        
        Args:
            risk_dict: Risk assessment dictionary
            analysis: Source vision analysis
            
        Returns:
            SafetyEvent or None if invalid
        """
        try:
            # Parse event type
            event_type_str = risk_dict.get('event_type', 'general_safety')
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                event_type = EventType.GENERAL_SAFETY
            
            # Parse risk level
            risk_level_str = risk_dict.get('risk_level', 'LOW')
            try:
                risk_level = RiskLevel(risk_level_str)
            except ValueError:
                risk_level = RiskLevel.LOW
            
            # Create event
            event = SafetyEvent(
                timestamp=datetime.now(),
                frame_id=analysis.frame_id,
                analysis_id=analysis.analysis_id,
                event_type=event_type,
                risk_level=risk_level,
                title=risk_dict.get('title', 'Safety concern'),
                description=risk_dict.get('description', ''),
                location=risk_dict.get('location'),
                people_involved=risk_dict.get('people_involved', 0),
                equipment_involved=risk_dict.get('equipment_involved', []),
                confidence=float(risk_dict.get('confidence', 0.5)),
                severity_score=float(risk_dict.get('severity_score', 5.0)),
                urgency=risk_dict.get('urgency', 'normal'),
                recommended_actions=risk_dict.get('recommended_actions', []),
                contributing_factors=risk_dict.get('contributing_factors', []),
                related_regulations=risk_dict.get('related_regulations', []),
                reasoning=risk_dict.get('reasoning'),
                false_positive_likelihood=risk_dict.get('false_positive_likelihood')
            )
            
            return event
            
        except Exception as e:
            logger.error(f"Error creating safety event: {e}")
            return None
    
    def assess_risks(self, analysis: VisionAnalysis) -> List[SafetyEvent]:
        """
        Assess risks from vision analysis using LLM reasoning.
        
        Args:
            analysis: Vision analysis results
            
        Returns:
            List of detected safety events
        """
        if not self.client:
            raise RuntimeError("Reasoning client not initialized")
        
        start_time = time.time()
        
        try:
            # Format observations
            observations = self._format_observations(analysis)
            
            # Create reasoning prompt
            prompt = self.REASONING_PROMPT.format(observations=observations)
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                timeout=self.config.timeout
            )
            
            response_text = response.choices[0].message.content
            processing_time = time.time() - start_time
            
            # Parse response
            risk_dicts = self._parse_risk_response(response_text)
            
            # Create SafetyEvent objects
            events = []
            for risk_dict in risk_dicts:
                event = self._create_safety_event(risk_dict, analysis)
                if event and event.confidence >= self.config.min_confidence:
                    events.append(event)
            
            logger.info(f"Risk assessment completed in {processing_time:.2f}s: "
                       f"{len(events)} events identified")
            
            return events
            
        except Exception as e:
            logger.error(f"Risk assessment failed: {e}", exc_info=True)
            return []


class MockRiskReasoner(RiskReasonerInterface):
    """
    Mock risk reasoner for testing without API access.
    
    Only generates events when actual issues are detected in the analysis.
    """
    
    def __init__(self, config: ReasoningConfig):
        """Initialize mock reasoner."""
        self.config = config
        logger.info("Initialized MOCK risk reasoner (for testing without API key)")
        logger.warning("⚠️  MOCK MODE: Using heuristic analysis. For real analysis, add OpenAI API key.")
    
    def assess_risks(self, analysis: VisionAnalysis) -> List[SafetyEvent]:
        """
        Assess risks based on actual analysis data.
        Only generates events when real issues are detected.
        
        Args:
            analysis: Vision analysis results
            
        Returns:
            List of safety events (only if issues detected)
        """
        # Simulate processing time
        time.sleep(0.3)
        
        events = []
        
        # Only generate events if we actually detected something concerning
        # Check for PPE violations (only if people detected AND PPE missing)
        if analysis.detected_people:
            for person in analysis.detected_people:
                ppe_missing = person.get('ppe_missing', [])
                if ppe_missing:  # Only alert if PPE is actually missing
                    risk_level = RiskLevel.HIGH if 'hard hat' in ppe_missing else RiskLevel.MEDIUM
                    
                    event = SafetyEvent(
                        frame_id=analysis.frame_id,
                        analysis_id=analysis.analysis_id,
                        event_type=EventType.PPE_VIOLATION,
                        risk_level=risk_level,
                        title=f"PPE Violation: Missing {', '.join(ppe_missing)}",
                        description=f"Worker at {person.get('location', 'unknown location')} "
                                  f"is missing required PPE: {', '.join(ppe_missing)}",
                        location=person.get('location'),
                        people_involved=1,
                        confidence=0.75,  # Lower confidence in mock mode
                        severity_score=7.0 if 'hard hat' in ppe_missing else 5.0,
                        urgency="high" if 'hard hat' in ppe_missing else "normal",
                        recommended_actions=[
                            f"Ensure worker dons {', '.join(ppe_missing)}",
                            "Verify PPE compliance before allowing work to continue"
                        ],
                        contributing_factors=["PPE not worn"],
                        related_regulations=["OSHA 1910.135 (Head Protection)", "OSHA 1910.132 (General PPE)"],
                        reasoning="Missing critical PPE exposes worker to injury risk",
                        false_positive_likelihood="medium"  # Higher in mock mode
                    )
                    events.append(event)
        
        # Only report hazards if they were actually detected
        if analysis.hazards_visible:
            for hazard in analysis.hazards_visible[:2]:  # Limit to top 2
                # Determine severity based on keywords
                hazard_lower = hazard.lower()
                
                if any(word in hazard_lower for word in ['hard hat', 'safety vest', 'ppe']):
                    event_type = EventType.PPE_VIOLATION
                    risk_level = RiskLevel.HIGH if 'hard hat' in hazard_lower else RiskLevel.MEDIUM
                    severity = 7.0
                elif any(word in hazard_lower for word in ['slip', 'wet', 'spill']):
                    event_type = EventType.ENVIRONMENTAL_HAZARD
                    risk_level = RiskLevel.MEDIUM
                    severity = 6.0
                elif any(word in hazard_lower for word in ['machinery', 'equipment', 'moving']):
                    event_type = EventType.MACHINERY_HAZARD
                    risk_level = RiskLevel.HIGH
                    severity = 8.0
                else:
                    event_type = EventType.GENERAL_SAFETY
                    risk_level = RiskLevel.LOW
                    severity = 4.0
                
                event = SafetyEvent(
                    frame_id=analysis.frame_id,
                    analysis_id=analysis.analysis_id,
                    event_type=event_type,
                    risk_level=risk_level,
                    title=f"Hazard Detected: {hazard[:50]}",
                    description=hazard,
                    location=analysis.environment_type,
                    people_involved=len(analysis.detected_people),
                    confidence=0.70,  # Lower confidence in mock mode
                    severity_score=severity,
                    urgency="high" if risk_level == RiskLevel.HIGH else "normal",
                    recommended_actions=[
                        "Address hazard immediately",
                        "Restrict access to affected area if necessary"
                    ],
                    contributing_factors=["Detected in video analysis"],
                    related_regulations=["OSHA General Duty Clause"],
                    reasoning=f"Visible hazard detected: {hazard}",
                    false_positive_likelihood="medium"  # Higher in mock mode
                )
                events.append(event)
        
        # If no events but we detected people, create a general observation
        # This helps users see that the system is working
        if not events and len(analysis.detected_people) > 0:
            # Create a low-priority observation to show system is working
            event = SafetyEvent(
                frame_id=analysis.frame_id,
                analysis_id=analysis.analysis_id,
                event_type=EventType.GENERAL_SAFETY,
                risk_level=RiskLevel.LOW,
                title="Factory Floor Monitoring",
                description=f"Monitoring factory floor with {len(analysis.detected_people)} worker(s) visible. Scene appears generally safe.",
                location=analysis.environment_type,
                people_involved=len(analysis.detected_people),
                confidence=0.50,  # Lower confidence for general observation
                severity_score=1.0,
                urgency="low",
                recommended_actions=["Continue monitoring", "Maintain situational awareness"],
                contributing_factors=[],
                related_regulations=[],
                reasoning="Routine safety monitoring - no immediate concerns detected",
                false_positive_likelihood="low"
            )
            events.append(event)
            logger.info(f"[MOCK] Created general observation to show system is working")
        
        if events:
            logger.info(f"[MOCK] Risk assessment: {len(events)} events detected")
        else:
            logger.debug(f"[MOCK] Risk assessment: No people or activity detected in frame")
        
        return events


class RiskReasonerFactory:
    """Factory for creating risk reasoner instances."""
    
    @staticmethod
    def create(config: ReasoningConfig) -> RiskReasonerInterface:
        """
        Create risk reasoner instance.
        
        Args:
            config: Reasoning configuration
            
        Returns:
            RiskReasonerInterface instance
        """
        # Use mock if no API key
        if not config.api_key:
            logger.warning("No API key provided, using MOCK risk reasoner")
            return MockRiskReasoner(config)
        
        # Use configured provider
        if config.provider == "openai":
            return LLMRiskReasoner(config)
        else:
            raise ValueError(f"Unsupported reasoning provider: {config.provider}")


def test_risk_reasoner():
    """Test function for risk reasoner."""
    from config import Config
    
    config = Config()
    
    # Create reasoner
    reasoner = RiskReasonerFactory.create(config.reasoning)
    
    # Create mock vision analysis
    analysis = VisionAnalysis(
        frame_id="test-frame-1",
        scene_description="Factory floor with workers",
        detected_people=[
            {
                "id": 1,
                "location": "near conveyor",
                "activity": "assembly work",
                "ppe_visible": ["safety vest"],
                "ppe_missing": ["hard hat", "safety glasses"],
                "posture": "standing"
            }
        ],
        detected_objects=[],
        activities=["assembly work"],
        environment_type="assembly line",
        lighting_conditions="well-lit",
        visibility="clear",
        hazards_visible=["Worker missing critical PPE"],
        safety_equipment=["fire extinguisher"],
        model_name="test"
    )
    
    print("Testing risk reasoner...")
    events = reasoner.assess_risks(analysis)
    
    print(f"\nIdentified {len(events)} safety events:")
    for event in events:
        print(f"\n- {event.title}")
        print(f"  Risk Level: {event.risk_level.value}")
        print(f"  Confidence: {event.confidence:.2f}")
        print(f"  Description: {event.description}")
        print(f"  Actions: {', '.join(event.recommended_actions[:2])}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_risk_reasoner()

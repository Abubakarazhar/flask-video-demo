"""
Data models for Factory Safety Monitoring System.

This module defines the core data structures used throughout the system,
ensuring type safety and clear data contracts between components.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
import uuid
import numpy as np


class RiskLevel(Enum):
    """Risk severity levels."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    
    def __lt__(self, other):
        order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        return order[self.value] < order[other.value]
    
    def __gt__(self, other):
        order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
        return order[self.value] > order[other.value]


class EventType(Enum):
    """Types of safety events."""
    PPE_VIOLATION = "ppe_violation"
    UNSAFE_BEHAVIOR = "unsafe_behavior"
    ZONE_VIOLATION = "zone_violation"
    MACHINERY_HAZARD = "machinery_hazard"
    ENVIRONMENTAL_HAZARD = "environmental_hazard"
    ERGONOMIC_RISK = "ergonomic_risk"
    NEAR_MISS = "near_miss"
    GENERAL_SAFETY = "general_safety"


@dataclass
class Frame:
    """
    Represents a captured video frame with metadata.
    
    This class encapsulates both the raw image data and associated
    metadata needed for processing and traceability.
    """
    
    frame_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    image: np.ndarray = None  # RGB image array
    frame_number: int = 0
    source: str = ""
    
    # Image metadata
    width: int = 0
    height: int = 0
    channels: int = 3
    
    # Processing metadata
    scene_change_score: Optional[float] = None
    processing_started: Optional[datetime] = None
    processing_completed: Optional[datetime] = None
    
    def get_processing_time(self) -> Optional[float]:
        """Get processing time in seconds."""
        if self.processing_started and self.processing_completed:
            return (self.processing_completed - self.processing_started).total_seconds()
        return None
    
    def to_dict(self) -> dict:
        """Convert to dictionary (excluding image data)."""
        return {
            "frame_id": self.frame_id,
            "timestamp": self.timestamp.isoformat(),
            "frame_number": self.frame_number,
            "source": self.source,
            "dimensions": f"{self.width}x{self.height}",
            "scene_change_score": self.scene_change_score,
            "processing_time": self.get_processing_time()
        }


@dataclass
class VisionAnalysis:
    """
    Results from Vision-Language Model analysis.
    
    This captures the VLM's understanding of the scene, including
    detected objects, people, activities, and environmental context.
    """
    
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    frame_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Scene understanding
    scene_description: str = ""
    detected_people: List[Dict[str, Any]] = field(default_factory=list)
    detected_objects: List[Dict[str, Any]] = field(default_factory=list)
    activities: List[str] = field(default_factory=list)
    
    # Environmental context
    environment_type: str = ""  # e.g., "warehouse", "assembly line", "loading dock"
    lighting_conditions: str = ""  # e.g., "well-lit", "dim", "mixed"
    visibility: str = ""  # e.g., "clear", "partially obscured", "poor"
    
    # Safety-relevant observations
    ppe_status: Dict[str, Any] = field(default_factory=dict)
    hazards_visible: List[str] = field(default_factory=list)
    safety_equipment: List[str] = field(default_factory=list)
    
    # Model metadata
    model_name: str = ""
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    processing_time: float = 0.0
    
    # Raw model output for debugging
    raw_response: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "analysis_id": self.analysis_id,
            "frame_id": self.frame_id,
            "timestamp": self.timestamp.isoformat(),
            "scene_description": self.scene_description,
            "detected_people": len(self.detected_people),
            "detected_objects": len(self.detected_objects),
            "activities": self.activities,
            "environment_type": self.environment_type,
            "ppe_status": self.ppe_status,
            "hazards_visible": self.hazards_visible,
            "processing_time": self.processing_time
        }


@dataclass
class SafetyEvent:
    """
    Represents a detected safety event or violation.
    
    This is the primary unit of safety concern, containing both
    the factual observation and the assessed risk level.
    """
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    frame_id: str = ""
    analysis_id: str = ""
    
    # Event classification
    event_type: EventType = EventType.GENERAL_SAFETY
    risk_level: RiskLevel = RiskLevel.LOW
    
    # Event details
    title: str = ""
    description: str = ""
    location: Optional[str] = None  # Area/zone in the facility
    
    # Involved entities
    people_involved: int = 0
    equipment_involved: List[str] = field(default_factory=list)
    
    # Risk assessment
    confidence: float = 0.0  # 0-1
    severity_score: float = 0.0  # 0-10
    urgency: str = "normal"  # "low", "normal", "high", "immediate"
    
    # Recommendations
    recommended_actions: List[str] = field(default_factory=list)
    
    # Contextual information
    contributing_factors: List[str] = field(default_factory=list)
    related_regulations: List[str] = field(default_factory=list)
    
    # Processing metadata
    reasoning: Optional[str] = None  # Why this was flagged
    false_positive_likelihood: Optional[str] = None  # "low", "medium", "high"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type.value,
            "risk_level": self.risk_level.value,
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "confidence": self.confidence,
            "severity_score": self.severity_score,
            "urgency": self.urgency,
            "people_involved": self.people_involved,
            "recommended_actions": self.recommended_actions,
            "reasoning": self.reasoning
        }
    
    def should_alert(self, min_confidence: float = 0.6) -> bool:
        """Determine if this event should trigger an alert."""
        if self.confidence < min_confidence:
            return False
        
        if self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            return True
        
        if self.risk_level == RiskLevel.MEDIUM and self.urgency in ["high", "immediate"]:
            return True
        
        return False


@dataclass
class AggregatedRisk:
    """
    Aggregated risk assessment over a time window.
    
    This represents patterns and trends detected across multiple
    frames and events, providing higher-level situational awareness.
    """
    
    aggregation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    window_start: datetime = field(default_factory=datetime.now)
    window_end: datetime = field(default_factory=datetime.now)
    
    # Events in this window
    events: List[SafetyEvent] = field(default_factory=list)
    event_count: int = 0
    
    # Risk statistics
    max_risk_level: RiskLevel = RiskLevel.LOW
    avg_confidence: float = 0.0
    event_types_distribution: Dict[str, int] = field(default_factory=dict)
    
    # Patterns detected
    recurring_issues: List[str] = field(default_factory=list)
    escalating_risks: bool = False
    spatial_clusters: List[str] = field(default_factory=list)  # Areas with multiple events
    
    # Overall assessment
    overall_risk_score: float = 0.0  # 0-10
    requires_intervention: bool = False
    summary: str = ""
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "aggregation_id": self.aggregation_id,
            "timestamp": self.timestamp.isoformat(),
            "window_duration": (self.window_end - self.window_start).total_seconds(),
            "event_count": self.event_count,
            "max_risk_level": self.max_risk_level.value,
            "avg_confidence": self.avg_confidence,
            "event_types": self.event_types_distribution,
            "recurring_issues": self.recurring_issues,
            "escalating_risks": self.escalating_risks,
            "overall_risk_score": self.overall_risk_score,
            "requires_intervention": self.requires_intervention,
            "summary": self.summary
        }


@dataclass
class Alert:
    """
    An alert to be sent to operators/management.
    
    Alerts are the final output of the system, representing
    actionable information that requires human attention.
    """
    
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Alert classification
    priority: str = "normal"  # "low", "normal", "high", "critical"
    category: str = "safety"
    
    # Alert content
    title: str = ""
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Source information
    source_events: List[str] = field(default_factory=list)  # Event IDs
    source_frames: List[str] = field(default_factory=list)  # Frame IDs
    
    # Alert status
    status: str = "active"  # "active", "acknowledged", "resolved"
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Deduplication
    similar_alerts: List[str] = field(default_factory=list)  # Similar alert IDs
    occurrence_count: int = 1
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "alert_id": self.alert_id,
            "timestamp": self.timestamp.isoformat(),
            "priority": self.priority,
            "category": self.category,
            "title": self.title,
            "message": self.message,
            "details": self.details,
            "status": self.status,
            "occurrence_count": self.occurrence_count
        }


@dataclass
class PerformanceMetrics:
    """
    Performance metrics for system monitoring.
    
    Tracks latency, throughput, and resource utilization
    to ensure the system meets real-time requirements.
    """
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Throughput metrics
    frames_processed: int = 0
    frames_per_second: float = 0.0
    events_detected: int = 0
    alerts_generated: int = 0
    
    # Latency metrics (all in seconds)
    avg_frame_capture_time: float = 0.0
    avg_vision_inference_time: float = 0.0
    avg_reasoning_time: float = 0.0
    avg_end_to_end_latency: float = 0.0
    
    # Resource utilization
    cpu_usage_percent: float = 0.0
    memory_usage_mb: float = 0.0
    
    # Error tracking
    api_errors: int = 0
    processing_errors: int = 0
    
    # Queue depths (if using async processing)
    frame_queue_depth: int = 0
    event_queue_depth: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "frames_processed": self.frames_processed,
            "fps": round(self.frames_per_second, 2),
            "events_detected": self.events_detected,
            "alerts_generated": self.alerts_generated,
            "avg_latency": {
                "capture": round(self.avg_frame_capture_time, 3),
                "vision": round(self.avg_vision_inference_time, 3),
                "reasoning": round(self.avg_reasoning_time, 3),
                "end_to_end": round(self.avg_end_to_end_latency, 3)
            },
            "resources": {
                "cpu_percent": round(self.cpu_usage_percent, 1),
                "memory_mb": round(self.memory_usage_mb, 1)
            },
            "errors": {
                "api": self.api_errors,
                "processing": self.processing_errors
            }
        }

"""
Alert management and prioritization module.

This module handles:
- Alert generation from safety events and aggregations
- Alert deduplication to prevent spam
- Priority-based alert queuing
- Cooldown periods for similar alerts
- Multi-channel output (console, file, webhook, etc.)

Key Design Decisions:
- Deduplicate similar alerts using semantic similarity
- Enforce cooldown periods to prevent alert fatigue
- Priority-based handling for critical vs. routine alerts
- Maintain alert history for audit trail
- Support multiple output channels for flexibility
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set
from pathlib import Path
from collections import defaultdict, deque
from difflib import SequenceMatcher

from models import Alert, SafetyEvent, AggregatedRisk, RiskLevel
from config import AlertConfig

logger = logging.getLogger(__name__)


class AlertDeduplicator:
    """
    Handles alert deduplication using text similarity.
    
    Prevents generating multiple alerts for essentially the same issue,
    which causes alert fatigue and reduces operator effectiveness.
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize deduplicator.
        
        Args:
            similarity_threshold: Similarity threshold (0-1) for deduplication
        """
        self.similarity_threshold = similarity_threshold
        self.recent_alerts: deque[Alert] = deque(maxlen=50)  # Keep recent for comparison (reduced for short videos)
    
    def _calculate_similarity(self, alert1: Alert, alert2: Alert) -> float:
        """
        Calculate similarity between two alerts.
        
        Uses a combination of:
        - Title similarity (normalized)
        - Message similarity
        - Category match
        - Priority match (bonus)
        
        Args:
            alert1: First alert
            alert2: Second alert
            
        Returns:
            Similarity score (0-1)
        """
        # Category must match for deduplication
        if alert1.category != alert2.category:
            return 0.0
        
        # Normalize titles (remove frame/worker numbers, lowercase)
        title1 = alert1.title.lower().replace("worker #", "worker").replace("worker ", "worker")
        title2 = alert2.title.lower().replace("worker #", "worker").replace("worker ", "worker")
        
        # Title similarity (weighted heavily)
        title_sim = SequenceMatcher(None, title1, title2).ratio()
        
        # Message similarity (first 100 chars to focus on core issue)
        msg1 = alert1.message[:100].lower()
        msg2 = alert2.message[:100].lower()
        message_sim = SequenceMatcher(None, msg1, msg2).ratio()
        
        # Priority match bonus
        priority_bonus = 0.1 if alert1.priority == alert2.priority else 0.0
        
        # Weighted combination (title matters most)
        overall_sim = (title_sim * 0.7) + (message_sim * 0.3) + priority_bonus
        
        return min(1.0, overall_sim)  # Cap at 1.0
    
    def find_similar_alert(self, alert: Alert) -> Optional[Alert]:
        """
        Find similar alert in recent history.
        
        Args:
            alert: Alert to check
            
        Returns:
            Similar alert if found, None otherwise
        """
        for recent_alert in self.recent_alerts:
            similarity = self._calculate_similarity(alert, recent_alert)
            if similarity >= self.similarity_threshold:
                logger.debug(f"Found similar alert (similarity: {similarity:.2f})")
                return recent_alert
        
        return None
    
    def add_alert(self, alert: Alert):
        """Add alert to recent history."""
        self.recent_alerts.append(alert)


class AlertCooldownManager:
    """
    Manages cooldown periods for alerts.
    
    Prevents re-alerting for the same issue too frequently,
    while still allowing periodic reminders for ongoing issues.
    """
    
    def __init__(self, cooldown_seconds: float = 60.0):
        """
        Initialize cooldown manager.
        
        Args:
            cooldown_seconds: Cooldown period in seconds
        """
        self.cooldown_seconds = cooldown_seconds
        # Map: alert category/type -> last alert time
        self.last_alert_times: Dict[str, datetime] = {}
    
    def _get_alert_key(self, alert: Alert) -> str:
        """
        Generate key for alert cooldown tracking.
        
        Groups alerts by category and priority for cooldown purposes.
        Uses normalized title (first 30 chars) to catch similar issues.
        """
        # Normalize title - remove frame-specific info, keep core issue
        title_normalized = alert.title[:30].lower().strip()
        # Remove common variations
        title_normalized = title_normalized.replace("worker #", "worker")
        title_normalized = title_normalized.replace("worker ", "worker")
        return f"{alert.category}:{alert.priority}:{title_normalized}"
    
    def is_in_cooldown(self, alert: Alert) -> bool:
        """
        Check if alert is in cooldown period.
        
        Args:
            alert: Alert to check
            
        Returns:
            True if in cooldown, False otherwise
        """
        # Critical alerts bypass cooldown (but still deduplicated)
        # For short videos, even critical alerts should respect cooldown if very similar
        key = self._get_alert_key(alert)
        
        if key in self.last_alert_times:
            time_since_last = (datetime.now() - self.last_alert_times[key]).total_seconds()
            # Critical alerts have shorter cooldown (5 seconds)
            cooldown = 5.0 if alert.priority == "critical" else self.cooldown_seconds
            return time_since_last < cooldown
        
        return False
    
    def record_alert(self, alert: Alert):
        """Record that an alert was sent."""
        key = self._get_alert_key(alert)
        self.last_alert_times[key] = datetime.now()
    
    def cleanup(self):
        """Remove old cooldown entries."""
        cutoff = datetime.now() - timedelta(seconds=self.cooldown_seconds * 2)
        keys_to_remove = [
            key for key, timestamp in self.last_alert_times.items()
            if timestamp < cutoff
        ]
        for key in keys_to_remove:
            del self.last_alert_times[key]


class AlertManager:
    """
    Manages alert lifecycle from generation to delivery.
    
    Responsibilities:
    - Generate alerts from safety events and aggregations
    - Deduplicate similar alerts
    - Enforce cooldown periods
    - Prioritize and queue alerts
    - Output alerts to configured channels
    - Maintain alert history
    """
    
    def __init__(self, config: AlertConfig, output_dir: Path):
        """
        Initialize alert manager.
        
        Args:
            config: Alert configuration
            output_dir: Directory for alert outputs
        """
        self.config = config
        self.output_dir = output_dir
        
        # Alert components
        self.deduplicator = AlertDeduplicator(config.dedup_similarity_threshold) \
                           if config.enable_deduplication else None
        self.cooldown_manager = AlertCooldownManager(config.alert_cooldown)
        
        # Alert storage
        self.active_alerts: List[Alert] = []
        self.alert_history: deque[Alert] = deque(maxlen=1000)
        
        # Alert queues by priority
        self.alert_queues: Dict[str, deque[Alert]] = {
            "critical": deque(),
            "high": deque(),
            "normal": deque(),
            "low": deque()
        }
        
        # Statistics
        self.total_alerts_generated = 0
        self.total_alerts_deduplicated = 0
        self.total_alerts_in_cooldown = 0
        self.total_alerts_sent = 0
        
        # Setup output
        self._setup_outputs()
    
    def _setup_outputs(self):
        """Setup output channels."""
        # Create alerts directory
        self.alerts_dir = self.output_dir / "alerts"
        self.alerts_dir.mkdir(parents=True, exist_ok=True)
        
        # Alert log file
        self.alert_log_file = self.alerts_dir / "alert_log.jsonl"
    
    def _generate_alert_from_event(self, event: SafetyEvent) -> Alert:
        """
        Generate alert from safety event.
        
        Args:
            event: Safety event
            
        Returns:
            Alert object
        """
        # Map risk level to priority
        priority_map = {
            RiskLevel.LOW: "low",
            RiskLevel.MEDIUM: "normal",
            RiskLevel.HIGH: "high",
            RiskLevel.CRITICAL: "critical"
        }
        priority = priority_map.get(event.risk_level, "normal")
        
        # Create alert
        alert = Alert(
            timestamp=datetime.now(),
            priority=priority,
            category="safety",
            title=event.title,
            message=event.description,
            details={
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "risk_level": event.risk_level.value,
                "location": event.location,
                "people_involved": event.people_involved,
                "equipment_involved": event.equipment_involved,
                "confidence": event.confidence,
                "severity_score": event.severity_score,
                "urgency": event.urgency,
                "recommended_actions": event.recommended_actions,
                "reasoning": event.reasoning
            },
            source_events=[event.event_id],
            source_frames=[event.frame_id]
        )
        
        return alert
    
    def _generate_alert_from_aggregation(self, aggregation: AggregatedRisk) -> Optional[Alert]:
        """
        Generate alert from aggregated risk assessment.
        
        Args:
            aggregation: Aggregated risk assessment
            
        Returns:
            Alert or None if no alert needed
        """
        # Only generate alert if intervention required or risk is high
        if not aggregation.requires_intervention and aggregation.overall_risk_score < 5.0:
            return None
        
        # Determine priority
        if aggregation.overall_risk_score >= 8.0 or aggregation.max_risk_level == RiskLevel.CRITICAL:
            priority = "critical"
        elif aggregation.overall_risk_score >= 6.0 or aggregation.max_risk_level == RiskLevel.HIGH:
            priority = "high"
        elif aggregation.overall_risk_score >= 4.0:
            priority = "normal"
        else:
            priority = "low"
        
        # Create title
        title = f"Safety Alert: {aggregation.event_count} incidents in time window"
        if aggregation.escalating_risks:
            title = "⚠ ESCALATING RISKS: " + title
        
        # Create alert
        alert = Alert(
            timestamp=datetime.now(),
            priority=priority,
            category="safety",
            title=title,
            message=aggregation.summary,
            details={
                "aggregation_id": aggregation.aggregation_id,
                "window_duration": (aggregation.window_end - aggregation.window_start).total_seconds(),
                "event_count": aggregation.event_count,
                "max_risk_level": aggregation.max_risk_level.value,
                "overall_risk_score": aggregation.overall_risk_score,
                "event_types": aggregation.event_types_distribution,
                "recurring_issues": aggregation.recurring_issues,
                "escalating_risks": aggregation.escalating_risks,
                "spatial_clusters": aggregation.spatial_clusters
            },
            source_events=[e.event_id for e in aggregation.events],
            source_frames=list(set(e.frame_id for e in aggregation.events))
        )
        
        return alert
    
    def process_event(self, event: SafetyEvent) -> Optional[Alert]:
        """
        Process a safety event and potentially generate an alert.
        
        Args:
            event: Safety event to process
            
        Returns:
            Generated alert if one was created and sent, None otherwise
        """
        # Check if event should trigger alert
        if not event.should_alert(self.config.critical_requires_immediate):
            logger.debug(f"Event does not meet alert criteria: {event.title}")
            return None
        
        # Generate alert
        alert = self._generate_alert_from_event(event)
        self.total_alerts_generated += 1
        
        # Check for deduplication FIRST (before cooldown)
        if self.deduplicator:
            similar_alert = self.deduplicator.find_similar_alert(alert)
            if similar_alert:
                logger.info(f"Alert deduplicated: {alert.title} (similar to: {similar_alert.title})")
                similar_alert.occurrence_count += 1
                similar_alert.similar_alerts.append(alert.alert_id)
                self.total_alerts_deduplicated += 1
                # Update timestamp to show it's still active
                similar_alert.timestamp = datetime.now()
                return None
        
        # Check cooldown (shorter cooldown for better deduplication)
        if self.cooldown_manager.is_in_cooldown(alert):
            logger.debug(f"Alert in cooldown: {alert.title}")
            self.total_alerts_in_cooldown += 1
            return None
        
        # Send alert
        self._send_alert(alert)
        
        return alert
    
    def process_aggregation(self, aggregation: AggregatedRisk) -> Optional[Alert]:
        """
        Process an aggregated risk assessment and potentially generate an alert.
        
        Args:
            aggregation: Aggregated risk assessment
            
        Returns:
            Generated alert if one was created and sent, None otherwise
        """
        # Generate alert if needed
        alert = self._generate_alert_from_aggregation(aggregation)
        
        if not alert:
            logger.debug("Aggregation does not require alert")
            return None
        
        self.total_alerts_generated += 1
        
        # Check for deduplication
        if self.deduplicator:
            similar_alert = self.deduplicator.find_similar_alert(alert)
            if similar_alert:
                logger.info(f"Aggregation alert deduplicated: {alert.title}")
                similar_alert.occurrence_count += 1
                self.total_alerts_deduplicated += 1
                return None
        
        # Check cooldown (aggregation alerts have longer cooldown)
        if self.cooldown_manager.is_in_cooldown(alert):
            logger.info(f"Aggregation alert in cooldown: {alert.title}")
            self.total_alerts_in_cooldown += 1
            return None
        
        # Send alert
        self._send_alert(alert)
        
        return alert
    
    def _send_alert(self, alert: Alert):
        """
        Send alert through configured output channels.
        
        Args:
            alert: Alert to send
        """
        # Add to active alerts
        self.active_alerts.append(alert)
        self.alert_history.append(alert)
        
        # Record for deduplication and cooldown
        if self.deduplicator:
            self.deduplicator.add_alert(alert)
        self.cooldown_manager.record_alert(alert)
        
        # Output to configured channels
        for output_mode in self.config.output_modes:
            try:
                if output_mode == "console":
                    self._output_console(alert)
                elif output_mode == "file":
                    self._output_file(alert)
                # Additional modes (webhook, email, etc.) would go here
            except Exception as e:
                logger.error(f"Failed to output alert via {output_mode}: {e}")
        
        self.total_alerts_sent += 1
        logger.info(f"Alert sent: {alert.title} (priority: {alert.priority})")
    
    def _output_console(self, alert: Alert):
        """Output alert to console."""
        # Color coding by priority
        colors = {
            "critical": "\033[91m",  # Red
            "high": "\033[93m",      # Yellow
            "normal": "\033[94m",    # Blue
            "low": "\033[92m"        # Green
        }
        reset = "\033[0m"
        
        color = colors.get(alert.priority, "")
        
        print(f"\n{'=' * 80}")
        print(f"{color}[{alert.priority.upper()} ALERT] {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}{reset}")
        print(f"{color}{alert.title}{reset}")
        print(f"\n{alert.message}")
        
        if alert.details.get("recommended_actions"):
            print(f"\nRecommended Actions:")
            for action in alert.details["recommended_actions"][:3]:
                print(f"  • {action}")
        
        print(f"{'=' * 80}\n")
    
    def _output_file(self, alert: Alert):
        """Output alert to log file."""
        with open(self.alert_log_file, 'a') as f:
            alert_data = alert.to_dict()
            f.write(json.dumps(alert_data) + '\n')
    
    def get_active_alerts(self, priority: Optional[str] = None) -> List[Alert]:
        """
        Get active alerts, optionally filtered by priority.
        
        Args:
            priority: Priority filter (optional)
            
        Returns:
            List of active alerts
        """
        if priority:
            return [a for a in self.active_alerts if a.priority == priority]
        return self.active_alerts.copy()
    
    def acknowledge_alert(self, alert_id: str):
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert ID to acknowledge
        """
        for alert in self.active_alerts:
            if alert.alert_id == alert_id:
                alert.status = "acknowledged"
                alert.acknowledged_at = datetime.now()
                logger.info(f"Alert acknowledged: {alert_id}")
                break
    
    def get_statistics(self) -> Dict:
        """Get alert statistics."""
        return {
            "total_generated": self.total_alerts_generated,
            "total_sent": self.total_alerts_sent,
            "total_deduplicated": self.total_alerts_deduplicated,
            "total_in_cooldown": self.total_alerts_in_cooldown,
            "active_alerts": len(self.active_alerts),
            "alert_history_size": len(self.alert_history)
        }


def test_alert_manager():
    """Test function for alert manager."""
    from config import Config
    
    config = Config()
    manager = AlertManager(config.alert, config.system.output_dir)
    
    print("Testing alert manager...")
    
    # Create test event
    event = SafetyEvent(
        event_type=EventType.PPE_VIOLATION,
        risk_level=RiskLevel.HIGH,
        title="Critical PPE Violation",
        description="Worker in hazardous area without hard hat",
        location="Assembly Line A",
        people_involved=1,
        confidence=0.9,
        severity_score=8.0,
        urgency="high",
        recommended_actions=[
            "Stop work immediately",
            "Ensure worker dons hard hat",
            "Review PPE procedures"
        ]
    )
    
    # Process event
    alert = manager.process_event(event)
    
    if alert:
        print(f"\nAlert generated and sent!")
        print(f"Alert ID: {alert.alert_id}")
    else:
        print("\nNo alert generated")
    
    # Statistics
    stats = manager.get_statistics()
    print(f"\nStatistics: {stats}")


if __name__ == "__main__":
    from models import EventType, SafetyEvent, RiskLevel
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_alert_manager()

"""
Event aggregation and temporal analysis module.

This module aggregates safety events over time windows to:
- Reduce noise and false positives
- Detect patterns and trends
- Identify escalating risk situations
- Provide higher-level situational awareness

Key Design Decisions:
- Sliding window approach for continuous monitoring
- Event clustering to identify recurring issues
- Escalation detection for worsening situations
- Spatial clustering to identify high-risk areas
- Configurable thresholds for flexibility
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from collections import defaultdict, deque

from models import SafetyEvent, AggregatedRisk, RiskLevel, EventType
from config import AggregationConfig

logger = logging.getLogger(__name__)


class EventAggregator:
    """
    Aggregates and analyzes safety events over time windows.
    
    This class implements temporal pattern detection and risk trending
    to provide context-aware risk assessment beyond individual frames.
    
    Design Pattern: Sliding Window with Event History
    - Maintains a fixed-size history of recent events
    - Analyzes events within configurable time windows
    - Detects patterns: recurring, escalating, spatial clusters
    """
    
    def __init__(self, config: AggregationConfig):
        """
        Initialize event aggregator.
        
        Args:
            config: Aggregation configuration
        """
        self.config = config
        
        # Event storage - bounded deque for memory efficiency
        # Events older than TTL are automatically removed
        max_events = 1000  # Reasonable upper bound
        self.event_history: deque[SafetyEvent] = deque(maxlen=max_events)
        
        # Aggregation cache
        self.last_aggregation: Optional[AggregatedRisk] = None
        self.last_aggregation_time: Optional[datetime] = None
        
        # Statistics
        self.total_events_processed = 0
        self.total_aggregations = 0
    
    def add_event(self, event: SafetyEvent):
        """
        Add a new safety event to the history.
        
        Args:
            event: Safety event to add
        """
        self.event_history.append(event)
        self.total_events_processed += 1
        logger.debug(f"Added event: {event.title} (total in history: {len(self.event_history)})")
    
    def add_events(self, events: List[SafetyEvent]):
        """
        Add multiple events at once.
        
        Args:
            events: List of safety events
        """
        for event in events:
            self.add_event(event)
    
    def _cleanup_old_events(self):
        """Remove events older than TTL."""
        if not self.event_history:
            return
        
        cutoff_time = datetime.now() - timedelta(seconds=self.config.event_ttl)
        
        # Remove old events from the left (oldest)
        while self.event_history and self.event_history[0].timestamp < cutoff_time:
            removed = self.event_history.popleft()
            logger.debug(f"Removed expired event: {removed.event_id}")
    
    def _get_events_in_window(
        self,
        window_start: datetime,
        window_end: datetime
    ) -> List[SafetyEvent]:
        """
        Get events within specified time window.
        
        Args:
            window_start: Start of time window
            window_end: End of time window
            
        Returns:
            List of events in window
        """
        events = [
            event for event in self.event_history
            if window_start <= event.timestamp <= window_end
        ]
        return events
    
    def _analyze_event_types(self, events: List[SafetyEvent]) -> Dict[str, int]:
        """
        Analyze distribution of event types.
        
        Args:
            events: List of events to analyze
            
        Returns:
            Dictionary mapping event type to count
        """
        distribution = defaultdict(int)
        for event in events:
            distribution[event.event_type.value] += 1
        return dict(distribution)
    
    def _detect_recurring_issues(self, events: List[SafetyEvent]) -> List[str]:
        """
        Detect recurring safety issues.
        
        An issue is considered recurring if it appears multiple times
        in the window with similar characteristics.
        
        Args:
            events: List of events to analyze
            
        Returns:
            List of recurring issue descriptions
        """
        recurring = []
        
        # Group by event type
        type_groups = defaultdict(list)
        for event in events:
            type_groups[event.event_type].append(event)
        
        # Check for recurrence
        for event_type, type_events in type_groups.items():
            if len(type_events) >= 2:  # At least 2 occurrences
                # Check if they're similar (same location or similar description)
                locations = [e.location for e in type_events if e.location]
                
                if len(locations) >= 2:
                    # Check for location clustering
                    location_counts = defaultdict(int)
                    for loc in locations:
                        location_counts[loc] += 1
                    
                    for loc, count in location_counts.items():
                        if count >= 2:
                            recurring.append(
                                f"Recurring {event_type.value} in {loc} "
                                f"({count} occurrences)"
                            )
                else:
                    # Generic recurrence
                    recurring.append(
                        f"Multiple {event_type.value} events "
                        f"({len(type_events)} occurrences)"
                    )
        
        return recurring
    
    def _detect_escalating_risks(self, events: List[SafetyEvent]) -> bool:
        """
        Detect if risks are escalating over time.
        
        Escalation indicators:
        - Increasing risk levels over time
        - Increasing frequency of events
        - Higher severity scores in recent events
        
        Args:
            events: List of events (should be time-ordered)
            
        Returns:
            True if risks appear to be escalating
        """
        if len(events) < 3:
            return False
        
        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        # Split into first half and second half
        mid_point = len(sorted_events) // 2
        first_half = sorted_events[:mid_point]
        second_half = sorted_events[mid_point:]
        
        # Compare average risk levels
        def avg_risk_level(event_list):
            if not event_list:
                return 0
            risk_values = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
            return sum(risk_values[e.risk_level.value] for e in event_list) / len(event_list)
        
        first_avg = avg_risk_level(first_half)
        second_avg = avg_risk_level(second_half)
        
        # Escalation if second half has significantly higher risk
        if second_avg > first_avg * 1.3:  # 30% increase threshold
            return True
        
        # Check for increasing severity scores
        first_severity = sum(e.severity_score for e in first_half) / len(first_half)
        second_severity = sum(e.severity_score for e in second_half) / len(second_half)
        
        if second_severity > first_severity * 1.4:  # 40% increase threshold
            return True
        
        return False
    
    def _detect_spatial_clusters(self, events: List[SafetyEvent]) -> List[str]:
        """
        Detect spatial clustering of events.
        
        Areas with multiple events may indicate systemic issues
        or particularly hazardous zones.
        
        Args:
            events: List of events to analyze
            
        Returns:
            List of areas with event clusters
        """
        # Count events by location
        location_counts = defaultdict(int)
        for event in events:
            if event.location:
                location_counts[event.location] += 1
        
        # Identify clusters (multiple events in same location)
        clusters = [
            f"{location} ({count} events)"
            for location, count in location_counts.items()
            if count >= 2
        ]
        
        return clusters
    
    def _calculate_overall_risk_score(self, events: List[SafetyEvent]) -> float:
        """
        Calculate overall risk score for the window.
        
        Considers:
        - Maximum risk level present
        - Average severity scores
        - Number of high-confidence events
        - Event frequency
        
        Args:
            events: List of events to assess
            
        Returns:
            Overall risk score (0-10)
        """
        if not events:
            return 0.0
        
        # Weight by confidence
        weighted_events = [e for e in events if e.confidence >= 0.6]
        
        if not weighted_events:
            return 0.0
        
        # Maximum risk level contribution (0-4)
        risk_values = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}
        max_risk = max(risk_values[e.risk_level.value] for e in weighted_events)
        max_risk_contribution = max_risk * 1.5  # 0-6
        
        # Average severity contribution (0-10)
        avg_severity = sum(e.severity_score for e in weighted_events) / len(weighted_events)
        severity_contribution = avg_severity * 0.3  # 0-3
        
        # Frequency contribution (normalized)
        # More events = higher concern, but with diminishing returns
        frequency_contribution = min(len(weighted_events) * 0.2, 2.0)  # 0-2
        
        # Combine (max possible = 6 + 3 + 2 = 11, normalize to 10)
        overall_score = max_risk_contribution + severity_contribution + frequency_contribution
        overall_score = min(overall_score, 10.0)
        
        return overall_score
    
    def _generate_summary(self, aggregation: AggregatedRisk) -> str:
        """
        Generate human-readable summary of aggregated risks.
        
        Args:
            aggregation: Aggregated risk assessment
            
        Returns:
            Summary string
        """
        if aggregation.event_count == 0:
            return "No safety events detected in this time window."
        
        summary_parts = []
        
        # Event count and max risk
        summary_parts.append(
            f"{aggregation.event_count} safety event(s) detected. "
            f"Maximum risk level: {aggregation.max_risk_level.value}."
        )
        
        # Event types
        if aggregation.event_types_distribution:
            top_types = sorted(
                aggregation.event_types_distribution.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
            types_str = ", ".join(f"{t.replace('_', ' ')} ({c})" for t, c in top_types)
            summary_parts.append(f"Primary concerns: {types_str}.")
        
        # Patterns
        if aggregation.recurring_issues:
            summary_parts.append(
                f"Recurring issues: {aggregation.recurring_issues[0]}."
            )
        
        if aggregation.escalating_risks:
            summary_parts.append("⚠ ALERT: Risks appear to be escalating.")
        
        if aggregation.spatial_clusters:
            summary_parts.append(
                f"Event clusters in: {', '.join(aggregation.spatial_clusters[:2])}."
            )
        
        # Overall assessment
        if aggregation.overall_risk_score >= 7.0:
            summary_parts.append("Overall risk level: HIGH - immediate attention recommended.")
        elif aggregation.overall_risk_score >= 4.0:
            summary_parts.append("Overall risk level: MODERATE - monitoring advised.")
        else:
            summary_parts.append("Overall risk level: LOW - routine monitoring.")
        
        return " ".join(summary_parts)
    
    def aggregate(self, window_size: Optional[float] = None) -> Optional[AggregatedRisk]:
        """
        Perform aggregation over recent time window.
        
        Args:
            window_size: Time window in seconds (uses config default if None)
            
        Returns:
            AggregatedRisk or None if insufficient data
        """
        # Clean up old events
        self._cleanup_old_events()
        
        # Use configured window size if not specified
        if window_size is None:
            window_size = self.config.window_size
        
        # Define time window
        window_end = datetime.now()
        window_start = window_end - timedelta(seconds=window_size)
        
        # Get events in window
        events = self._get_events_in_window(window_start, window_end)
        
        # Check minimum events threshold
        if len(events) < 1:  # Changed from min_events_for_alert to 1 for continuous monitoring
            logger.debug(f"Insufficient events for aggregation ({len(events)} events)")
            return None
        
        # Analyze events
        event_types_dist = self._analyze_event_types(events)
        recurring_issues = self._detect_recurring_issues(events)
        escalating = self._detect_escalating_risks(events)
        spatial_clusters = self._detect_spatial_clusters(events)
        overall_risk = self._calculate_overall_risk_score(events)
        
        # Determine maximum risk level
        max_risk = RiskLevel.LOW
        for event in events:
            if event.risk_level > max_risk:
                max_risk = event.risk_level
        
        # Calculate average confidence
        avg_confidence = sum(e.confidence for e in events) / len(events)
        
        # Create aggregation
        aggregation = AggregatedRisk(
            timestamp=datetime.now(),
            window_start=window_start,
            window_end=window_end,
            events=events,
            event_count=len(events),
            max_risk_level=max_risk,
            avg_confidence=avg_confidence,
            event_types_distribution=event_types_dist,
            recurring_issues=recurring_issues,
            escalating_risks=escalating,
            spatial_clusters=spatial_clusters,
            overall_risk_score=overall_risk
        )
        
        # Determine if intervention required
        aggregation.requires_intervention = (
            overall_risk >= 7.0 or
            max_risk in [RiskLevel.HIGH, RiskLevel.CRITICAL] or
            escalating
        )
        
        # Generate summary
        aggregation.summary = self._generate_summary(aggregation)
        
        # Cache aggregation
        self.last_aggregation = aggregation
        self.last_aggregation_time = datetime.now()
        self.total_aggregations += 1
        
        logger.info(f"Aggregation completed: {len(events)} events, "
                   f"risk score: {overall_risk:.1f}/10")
        
        return aggregation
    
    def get_statistics(self) -> Dict:
        """Get aggregator statistics."""
        return {
            "total_events_processed": self.total_events_processed,
            "events_in_history": len(self.event_history),
            "total_aggregations": self.total_aggregations,
            "last_aggregation_time": self.last_aggregation_time.isoformat() 
                                     if self.last_aggregation_time else None,
            "last_aggregation_risk_score": self.last_aggregation.overall_risk_score
                                          if self.last_aggregation else None
        }


def test_event_aggregator():
    """Test function for event aggregator."""
    from config import Config
    
    config = Config()
    aggregator = EventAggregator(config.aggregation)
    
    # Create mock events
    print("Creating test events...")
    for i in range(5):
        event = SafetyEvent(
            event_type=EventType.PPE_VIOLATION if i % 2 == 0 else EventType.ENVIRONMENTAL_HAZARD,
            risk_level=RiskLevel.MEDIUM if i < 3 else RiskLevel.HIGH,
            title=f"Test Event {i+1}",
            description=f"Test description {i+1}",
            location="Assembly Line A" if i < 3 else "Loading Dock",
            confidence=0.8,
            severity_score=5.0 + i,
            urgency="normal"
        )
        aggregator.add_event(event)
    
    # Perform aggregation
    print("\nPerforming aggregation...")
    aggregation = aggregator.aggregate()
    
    if aggregation:
        print(f"\nAggregation Results:")
        print(f"Events: {aggregation.event_count}")
        print(f"Max Risk: {aggregation.max_risk_level.value}")
        print(f"Overall Risk Score: {aggregation.overall_risk_score:.1f}/10")
        print(f"Event Types: {aggregation.event_types_distribution}")
        print(f"Recurring Issues: {aggregation.recurring_issues}")
        print(f"Escalating: {aggregation.escalating_risks}")
        print(f"Spatial Clusters: {aggregation.spatial_clusters}")
        print(f"\nSummary: {aggregation.summary}")
    else:
        print("No aggregation generated")
    
    # Statistics
    stats = aggregator.get_statistics()
    print(f"\nStatistics: {stats}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_event_aggregator()

"""
Main application orchestrator for Factory Safety Monitoring System.

This is the central controller that:
- Initializes all system components
- Orchestrates the real-time processing pipeline
- Manages the processing loop
- Handles graceful shutdown
- Provides monitoring and status reporting

Architecture:
    Video Stream → Vision Model → Risk Reasoner → Event Aggregator → Alert Manager
                                        ↓
                                  Performance Monitor

Real-time Strategy:
- Frame-level processing (Vision + Reasoning) runs for each sampled frame
- Temporal aggregation runs periodically (every N seconds)
- Non-blocking where possible to maintain throughput
- Configurable parallelism for CPU-bound operations
"""

import logging
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path

from config import Config
from video_stream import VideoStream
from vision_model import VisionModelFactory
from risk_reasoner import RiskReasonerFactory
from event_aggregator import EventAggregator
from alert_manager import AlertManager
from utils import (
    setup_logging,
    PerformanceMonitor,
    print_banner,
    print_config_summary
)
from models import Frame

logger = logging.getLogger(__name__)


class SafetyMonitoringSystem:
    """
    Main orchestrator for the factory safety monitoring system.
    
    This class implements the complete pipeline from video capture
    through alert generation, with proper error handling and monitoring.
    """
    
    def __init__(self, config: Config):
        """
        Initialize the safety monitoring system.
        
        Args:
            config: System configuration
        """
        self.config = config
        self.is_running = False
        self.should_stop = False
        
        # Initialize components
        logger.info("Initializing system components...")
        
        self.video_stream = VideoStream(config.video)
        self.vision_model = VisionModelFactory.create(config.vlm)
        self.risk_reasoner = RiskReasonerFactory.create(config.reasoning)
        self.event_aggregator = EventAggregator(config.aggregation)
        self.alert_manager = AlertManager(config.alert, config.system.output_dir)
        
        # Performance monitoring
        self.performance_monitor = PerformanceMonitor() if config.system.enable_metrics else None
        
        # Aggregation timing
        self.last_aggregation_time = None
        self.aggregation_interval = config.aggregation.window_step
        
        # Statistics
        self.start_time = None
        self.frames_analyzed = 0
        self.total_events = 0
        self.total_alerts = 0
        
        logger.info("System initialization complete")
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(sig, frame):
            logger.info("Shutdown signal received")
            self.should_stop = True
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _process_frame(self, frame: Frame):
        """
        Process a single frame through the complete pipeline.
        
        Pipeline:
        1. Vision analysis (scene understanding)
        2. Risk reasoning (safety assessment)
        3. Event handling (aggregation and alerting)
        
        Args:
            frame: Frame to process
        """
        frame_start_time = time.time()
        frame.processing_started = datetime.now()
        
        try:
            # Step 1: Vision Analysis
            logger.debug(f"Processing frame {frame.frame_number}")
            
            vision_start = time.time()
            vision_analysis = self.vision_model.analyze_frame(frame)
            vision_time = time.time() - vision_start
            
            if self.performance_monitor:
                self.performance_monitor.record_vision_inference_time(vision_time)
            
            logger.info(f"Vision analysis: {len(vision_analysis.detected_people)} people, "
                       f"{len(vision_analysis.hazards_visible)} hazards")
            
            # Step 2: Risk Reasoning
            reasoning_start = time.time()
            safety_events = self.risk_reasoner.assess_risks(vision_analysis)
            reasoning_time = time.time() - reasoning_start
            
            if self.performance_monitor:
                self.performance_monitor.record_reasoning_time(reasoning_time)
            
            logger.info(f"Risk assessment: {len(safety_events)} events identified")
            
            # Step 3: Event Handling
            if safety_events:
                # Add events to aggregator
                self.event_aggregator.add_events(safety_events)
                self.total_events += len(safety_events)
                
                if self.performance_monitor:
                    for _ in safety_events:
                        self.performance_monitor.record_event_detected()
                
                # Process high-priority events immediately
                for event in safety_events:
                    if event.risk_level.value in ['HIGH', 'CRITICAL']:
                        alert = self.alert_manager.process_event(event)
                        if alert:
                            self.total_alerts += 1
                            if self.performance_monitor:
                                self.performance_monitor.record_alert_generated()
            
            # Mark processing complete
            frame.processing_completed = datetime.now()
            self.frames_analyzed += 1
            
            if self.performance_monitor:
                self.performance_monitor.record_frame_processed()
                end_to_end_time = time.time() - frame_start_time
                self.performance_monitor.record_end_to_end_time(end_to_end_time)
            
            # Log summary
            total_time = time.time() - frame_start_time
            logger.info(f"Frame {frame.frame_number} processed in {total_time:.2f}s "
                       f"(vision: {vision_time:.2f}s, reasoning: {reasoning_time:.2f}s)")
            
        except Exception as e:
            logger.error(f"Error processing frame {frame.frame_number}: {e}", exc_info=True)
            if self.performance_monitor:
                self.performance_monitor.record_processing_error()
    
    def _perform_aggregation(self):
        """
        Perform temporal aggregation of recent events.
        
        This runs periodically (not for every frame) to:
        - Detect patterns across multiple events
        - Generate aggregated alerts for systemic issues
        - Provide higher-level situational awareness
        """
        try:
            logger.debug("Performing event aggregation...")
            aggregation = self.event_aggregator.aggregate()
            
            if aggregation:
                logger.info(f"Aggregation: {aggregation.event_count} events, "
                           f"risk score: {aggregation.overall_risk_score:.1f}/10")
                
                # Generate alert if needed
                alert = self.alert_manager.process_aggregation(aggregation)
                if alert:
                    self.total_alerts += 1
                    if self.performance_monitor:
                        self.performance_monitor.record_alert_generated()
            
            self.last_aggregation_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error during aggregation: {e}", exc_info=True)
    
    def _should_perform_aggregation(self) -> bool:
        """
        Determine if aggregation should be performed now.
        
        Returns:
            True if aggregation should run
        """
        if self.last_aggregation_time is None:
            return True
        
        time_since_last = (datetime.now() - self.last_aggregation_time).total_seconds()
        return time_since_last >= self.aggregation_interval
    
    def _print_status(self):
        """Print current system status."""
        if not self.start_time:
            return
        
        elapsed = (datetime.now() - self.start_time).total_seconds()
        fps = self.frames_analyzed / elapsed if elapsed > 0 else 0
        
        print(f"\n{'='*80}")
        print(f"System Status - Runtime: {elapsed:.0f}s")
        print(f"{'='*80}")
        print(f"Frames Analyzed: {self.frames_analyzed} ({fps:.2f} FPS)")
        print(f"Events Detected: {self.total_events}")
        print(f"Alerts Generated: {self.total_alerts}")
        
        # Component statistics
        stream_stats = self.video_stream.get_statistics()
        print(f"\nVideo Stream:")
        print(f"  Frames captured: {stream_stats['frames_captured']}")
        print(f"  Sampling ratio: {stream_stats['sampling_ratio']:.1%}")
        
        agg_stats = self.event_aggregator.get_statistics()
        print(f"\nEvent Aggregator:")
        print(f"  Events in history: {agg_stats['events_in_history']}")
        print(f"  Last risk score: {agg_stats['last_aggregation_risk_score']}")
        
        alert_stats = self.alert_manager.get_statistics()
        print(f"\nAlert Manager:")
        print(f"  Alerts sent: {alert_stats['total_sent']}")
        print(f"  Deduplicated: {alert_stats['total_deduplicated']}")
        print(f"  Active alerts: {alert_stats['active_alerts']}")
        
        if self.performance_monitor:
            print(f"\nPerformance:")
            metrics = self.performance_monitor.get_metrics()
            print(f"  Avg vision inference: {metrics.avg_vision_inference_time*1000:.0f}ms")
            print(f"  Avg risk reasoning: {metrics.avg_reasoning_time*1000:.0f}ms")
            print(f"  Avg end-to-end: {metrics.avg_end_to_end_latency*1000:.0f}ms")
            print(f"  CPU: {metrics.cpu_usage_percent:.1f}%")
            print(f"  Memory: {metrics.memory_usage_mb:.0f}MB")
        
        print(f"{'='*80}\n")
    
    def run(self):
        """
        Run the main monitoring loop.
        
        This is the core of the system, implementing the real-time
        processing pipeline with proper error handling and monitoring.
        """
        logger.info("Starting Factory Safety Monitoring System")
        
        # Setup
        self._setup_signal_handlers()
        
        # Validate configuration
        is_valid, errors = self.config.validate()
        if not is_valid:
            logger.error("Configuration validation failed:")
            for error in errors:
                logger.error(f"  - {error}")
            return
        
        # Open video stream
        if not self.video_stream.open():
            logger.error("Failed to open video stream")
            return
        
        # Start processing
        self.is_running = True
        self.start_time = datetime.now()
        last_status_print = time.time()
        status_print_interval = 30.0  # Print status every 30 seconds
        
        try:
            logger.info("Entering main processing loop...")
            
            # Main processing loop
            for frame in self.video_stream.stream():
                # Check for shutdown signal
                if self.should_stop:
                    logger.info("Shutdown requested, stopping...")
                    break
                
                # Process frame
                self._process_frame(frame)
                
                # Periodic aggregation
                if self._should_perform_aggregation():
                    self._perform_aggregation()
                
                # Periodic status reporting
                current_time = time.time()
                if current_time - last_status_print >= status_print_interval:
                    self._print_status()
                    last_status_print = current_time
            
        except KeyboardInterrupt:
            logger.info("Interrupted by user")
        
        except Exception as e:
            logger.error(f"Fatal error in main loop: {e}", exc_info=True)
        
        finally:
            # Cleanup
            self._shutdown()
    
    def _shutdown(self):
        """Perform cleanup and shutdown."""
        logger.info("Shutting down system...")
        
        self.is_running = False
        
        # Close video stream
        self.video_stream.close()
        
        # Final aggregation
        if self.event_aggregator:
            logger.info("Performing final aggregation...")
            self._perform_aggregation()
        
        # Print final statistics
        print("\n" + "="*80)
        print("FINAL SYSTEM STATISTICS")
        print("="*80)
        
        if self.start_time:
            total_runtime = (datetime.now() - self.start_time).total_seconds()
            print(f"Total Runtime: {total_runtime:.1f}s")
            print(f"Frames Analyzed: {self.frames_analyzed}")
            print(f"Events Detected: {self.total_events}")
            print(f"Alerts Generated: {self.total_alerts}")
            
            if self.performance_monitor:
                print("\n")
                self.performance_monitor.print_metrics()
        
        print("="*80)
        logger.info("Shutdown complete")


def main():
    """Main entry point."""
    # Print banner
    print_banner()
    
    # Load configuration
    config = Config()
    
    # Setup logging
    log_file = config.system.output_dir / "system.log"
    setup_logging(
        log_level=config.system.log_level,
        log_file=log_file
    )
    
    logger.info("Factory Safety Monitoring System starting...")
    
    # Print configuration
    print_config_summary(config)
    
    # Create and run system
    system = SafetyMonitoringSystem(config)
    system.run()


if __name__ == "__main__":
    main()

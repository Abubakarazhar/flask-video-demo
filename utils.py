"""
Utility functions for the Factory Safety Monitoring System.

This module provides cross-cutting concerns like logging setup,
performance monitoring, visualization, and file I/O utilities.
"""

import logging
import sys
import time
import psutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import numpy as np
import cv2

from models import Frame, PerformanceMetrics


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[Path] = None,
    log_format: Optional[str] = None
):
    """
    Setup application logging.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
        log_format: Optional custom log format
    """
    if log_format is None:
        log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=handlers
    )
    
    # Reduce noise from verbose libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('openai').setLevel(logging.WARNING)


class PerformanceMonitor:
    """
    Monitors system performance metrics.
    
    Tracks:
    - Processing latencies
    - Throughput (FPS)
    - Resource utilization (CPU, memory)
    - Error rates
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.start_time = time.time()
        self.frames_processed = 0
        self.events_detected = 0
        self.alerts_generated = 0
        
        # Latency tracking
        self.frame_capture_times = []
        self.vision_inference_times = []
        self.reasoning_times = []
        self.end_to_end_times = []
        
        # Error tracking
        self.api_errors = 0
        self.processing_errors = 0
        
        # Keep recent measurements (last 100)
        self.max_samples = 100
    
    def record_frame_processed(self):
        """Record that a frame was processed."""
        self.frames_processed += 1
    
    def record_event_detected(self):
        """Record that an event was detected."""
        self.events_detected += 1
    
    def record_alert_generated(self):
        """Record that an alert was generated."""
        self.alerts_generated += 1
    
    def record_frame_capture_time(self, duration: float):
        """Record frame capture time."""
        self.frame_capture_times.append(duration)
        if len(self.frame_capture_times) > self.max_samples:
            self.frame_capture_times.pop(0)
    
    def record_vision_inference_time(self, duration: float):
        """Record vision inference time."""
        self.vision_inference_times.append(duration)
        if len(self.vision_inference_times) > self.max_samples:
            self.vision_inference_times.pop(0)
    
    def record_reasoning_time(self, duration: float):
        """Record reasoning time."""
        self.reasoning_times.append(duration)
        if len(self.reasoning_times) > self.max_samples:
            self.reasoning_times.pop(0)
    
    def record_end_to_end_time(self, duration: float):
        """Record end-to-end processing time."""
        self.end_to_end_times.append(duration)
        if len(self.end_to_end_times) > self.max_samples:
            self.end_to_end_times.pop(0)
    
    def record_api_error(self):
        """Record an API error."""
        self.api_errors += 1
    
    def record_processing_error(self):
        """Record a processing error."""
        self.processing_errors += 1
    
    def get_metrics(self) -> PerformanceMetrics:
        """
        Get current performance metrics.
        
        Returns:
            PerformanceMetrics object
        """
        # Calculate averages
        def avg(lst):
            return sum(lst) / len(lst) if lst else 0.0
        
        # Calculate FPS
        elapsed = time.time() - self.start_time
        fps = self.frames_processed / elapsed if elapsed > 0 else 0.0
        
        # Get resource utilization
        process = psutil.Process()
        cpu_percent = process.cpu_percent(interval=0.1)
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            frames_processed=self.frames_processed,
            frames_per_second=fps,
            events_detected=self.events_detected,
            alerts_generated=self.alerts_generated,
            avg_frame_capture_time=avg(self.frame_capture_times),
            avg_vision_inference_time=avg(self.vision_inference_times),
            avg_reasoning_time=avg(self.reasoning_times),
            avg_end_to_end_latency=avg(self.end_to_end_times),
            cpu_usage_percent=cpu_percent,
            memory_usage_mb=memory_mb,
            api_errors=self.api_errors,
            processing_errors=self.processing_errors
        )
        
        return metrics
    
    def print_metrics(self):
        """Print metrics to console."""
        metrics = self.get_metrics()
        
        print("\n" + "="*60)
        print("PERFORMANCE METRICS")
        print("="*60)
        print(f"Frames Processed: {metrics.frames_processed}")
        print(f"Processing Rate: {metrics.frames_per_second:.2f} FPS")
        print(f"Events Detected: {metrics.events_detected}")
        print(f"Alerts Generated: {metrics.alerts_generated}")
        print(f"\nLatencies:")
        print(f"  Frame Capture: {metrics.avg_frame_capture_time*1000:.1f} ms")
        print(f"  Vision Inference: {metrics.avg_vision_inference_time*1000:.1f} ms")
        print(f"  Risk Reasoning: {metrics.avg_reasoning_time*1000:.1f} ms")
        print(f"  End-to-End: {metrics.avg_end_to_end_latency*1000:.1f} ms")
        print(f"\nResource Usage:")
        print(f"  CPU: {metrics.cpu_usage_percent:.1f}%")
        print(f"  Memory: {metrics.memory_usage_mb:.1f} MB")
        print(f"\nErrors:")
        print(f"  API Errors: {metrics.api_errors}")
        print(f"  Processing Errors: {metrics.processing_errors}")
        print("="*60 + "\n")


class FrameVisualizer:
    """
    Adds visualization overlays to frames.
    
    Useful for debugging and demonstrations.
    """
    
    @staticmethod
    def add_text_overlay(
        frame: np.ndarray,
        text: str,
        position: tuple = (10, 30),
        font_scale: float = 0.7,
        color: tuple = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        """
        Add text overlay to frame.
        
        Args:
            frame: Frame array (RGB)
            text: Text to overlay
            position: (x, y) position
            font_scale: Font size scale
            color: RGB color tuple
            thickness: Line thickness
            
        Returns:
            Frame with overlay
        """
        # Convert RGB to BGR for OpenCV
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Add text
        cv2.putText(
            frame_bgr,
            text,
            position,
            cv2.FONT_HERSHEY_SIMPLEX,
            font_scale,
            color,
            thickness,
            cv2.LINE_AA
        )
        
        # Convert back to RGB
        return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    
    @staticmethod
    def add_status_overlay(
        frame: np.ndarray,
        status_info: Dict[str, Any]
    ) -> np.ndarray:
        """
        Add comprehensive status overlay to frame.
        
        Args:
            frame: Frame array (RGB)
            status_info: Dictionary with status information
            
        Returns:
            Frame with overlay
        """
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Add semi-transparent background for better readability
        overlay = frame_bgr.copy()
        cv2.rectangle(overlay, (0, 0), (400, 150), (0, 0, 0), -1)
        frame_bgr = cv2.addWeighted(frame_bgr, 0.7, overlay, 0.3, 0)
        
        # Add status text
        y_offset = 25
        for key, value in status_info.items():
            text = f"{key}: {value}"
            cv2.putText(
                frame_bgr,
                text,
                (10, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                1,
                cv2.LINE_AA
            )
            y_offset += 25
        
        return cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)


def save_frame(frame: Frame, output_dir: Path, prefix: str = "frame"):
    """
    Save frame to disk.
    
    Args:
        frame: Frame to save
        output_dir: Output directory
        prefix: Filename prefix
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"{prefix}_{frame.frame_number}_{frame.timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"
    filepath = output_dir / filename
    
    # Convert RGB to BGR for saving
    frame_bgr = cv2.cvtColor(frame.image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(str(filepath), frame_bgr)


def save_json(data: Dict[str, Any], filepath: Path):
    """
    Save dictionary as JSON file.
    
    Args:
        data: Dictionary to save
        filepath: Output file path
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)


def load_json(filepath: Path) -> Dict[str, Any]:
    """
    Load JSON file.
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Loaded dictionary
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def format_timestamp(dt: datetime) -> str:
    """Format timestamp for display."""
    return dt.strftime('%Y-%m-%d %H:%M:%S')


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


class RateLimiter:
    """
    Simple rate limiter for API calls or other operations.
    
    Ensures operations don't exceed specified rate.
    """
    
    def __init__(self, max_per_second: float):
        """
        Initialize rate limiter.
        
        Args:
            max_per_second: Maximum operations per second
        """
        self.max_per_second = max_per_second
        self.min_interval = 1.0 / max_per_second if max_per_second > 0 else 0
        self.last_operation_time = 0.0
    
    def wait_if_needed(self):
        """Wait if necessary to maintain rate limit."""
        if self.min_interval == 0:
            return
        
        current_time = time.time()
        time_since_last = current_time - self.last_operation_time
        
        if time_since_last < self.min_interval:
            sleep_time = self.min_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_operation_time = time.time()


def print_banner():
    """Print application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════════╗
    ║                                                                   ║
    ║   Factory Safety Monitoring System                                ║
    ║   Real-Time Vision-Language Model Based Safety Analysis           ║
    ║                                                                   ║
    ╚═══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_config_summary(config):
    """
    Print configuration summary.
    
    Args:
        config: Configuration object
    """
    summary = config.get_summary()
    
    print("\nConfiguration Summary:")
    print("-" * 60)
    print(f"Video Source: {summary['video']['source']}")
    print(f"Resolution: {summary['video']['resolution']}")
    print(f"Target FPS: {summary['video']['target_fps']}")
    print(f"\nVLM: {summary['vlm']['provider']} / {summary['vlm']['model']}")
    if summary['vlm']['mock_mode']:
        print("  ⚠ Running in MOCK mode (no API key)")
    print(f"\nReasoning: {summary['reasoning']['provider']} / {summary['reasoning']['model']}")
    print(f"\nAggregation Window: {summary['aggregation']['window_size']}s")
    print(f"Async Processing: {summary['system']['async_enabled']}")
    print("-" * 60 + "\n")

"""
Video stream capture and intelligent frame sampling module.

This module implements adaptive frame sampling based on scene change detection,
optimizing the trade-off between latency and completeness of coverage.

Key Design Decisions:
- Not every frame needs analysis (computational waste, API cost)
- Scene change detection prevents missing important transitions
- Configurable min/max intervals ensure coverage even in static scenes
- Non-blocking capture allows parallel processing
"""

import cv2
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, Iterator
import logging
from pathlib import Path
import time

from models import Frame
from config import VideoConfig

logger = logging.getLogger(__name__)


class SceneChangeDetector:
    """
    Detects significant scene changes using histogram comparison.
    
    This is a lightweight method that doesn't require deep learning inference,
    making it suitable for real-time frame filtering.
    
    Algorithm:
    1. Convert frame to HSV color space (more perceptually uniform)
    2. Compute color histogram
    3. Compare with previous frame using correlation
    4. Threshold to determine if change is significant
    """
    
    def __init__(self, threshold: float = 15.0):
        """
        Initialize scene change detector.
        
        Args:
            threshold: Scene change threshold (0-100). Lower = more sensitive.
        """
        self.threshold = threshold
        self.prev_hist = None
        
    def detect_change(self, frame: np.ndarray) -> tuple[bool, float]:
        """
        Detect if frame has significant change from previous frame.
        
        Args:
            frame: Current frame (BGR format)
            
        Returns:
            Tuple of (is_changed, change_score)
            change_score is 0-100, where higher means more change
        """
        # Convert to HSV for better color representation
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Compute histogram for H and S channels
        # Ignore V (brightness) to be robust to lighting changes
        hist = cv2.calcHist([hsv], [0, 1], None, [50, 60], [0, 180, 0, 256])
        hist = cv2.normalize(hist, hist).flatten()
        
        if self.prev_hist is None:
            self.prev_hist = hist
            return True, 100.0  # First frame is always "changed"
        
        # Compare histograms using correlation
        # Returns value in [-1, 1] where 1 = identical
        correlation = cv2.compareHist(self.prev_hist, hist, cv2.HISTCMP_CORREL)
        
        # Convert to change score (0-100)
        # correlation = 1.0 -> change_score = 0 (no change)
        # correlation = 0.0 -> change_score = 100 (complete change)
        change_score = (1.0 - correlation) * 100
        
        # Update history
        self.prev_hist = hist
        
        # Determine if change exceeds threshold
        is_changed = change_score >= self.threshold
        
        return is_changed, change_score
    
    def reset(self):
        """Reset detector state (useful when video source changes)."""
        self.prev_hist = None


class VideoStream:
    """
    Manages video capture and intelligent frame sampling.
    
    This class implements:
    - Video capture from webcam or file
    - Adaptive frame sampling based on scene change
    - Configurable frame intervals
    - Frame preprocessing (resize, format conversion)
    - Graceful error handling and recovery
    """
    
    def __init__(self, config: VideoConfig):
        """
        Initialize video stream.
        
        Args:
            config: Video configuration parameters
        """
        self.config = config
        self.cap: Optional[cv2.VideoCapture] = None
        self.scene_detector = SceneChangeDetector(config.scene_change_threshold)
        
        self.frame_count = 0
        self.last_processed_time = None
        self.is_running = False
        
        # Statistics
        self.total_frames_captured = 0
        self.total_frames_yielded = 0
        self.total_scene_changes = 0
        
    def open(self) -> bool:
        """
        Open video source.
        
        Returns:
            True if successfully opened, False otherwise
        """
        try:
            self.cap = cv2.VideoCapture(self.config.source)
            
            if not self.cap.isOpened():
                logger.error(f"Failed to open video source: {self.config.source}")
                return False
            
            # Set capture properties if using webcam
            if isinstance(self.config.source, int):
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.frame_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.frame_height)
                self.cap.set(cv2.CAP_PROP_FPS, 30)  # Capture FPS (not processing FPS)
            
            # Get actual properties
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            actual_fps = self.cap.get(cv2.CAP_PROP_FPS)
            
            logger.info(f"Video source opened: {self.config.source}")
            logger.info(f"Resolution: {actual_width}x{actual_height}, FPS: {actual_fps}")
            
            self.is_running = True
            return True
            
        except Exception as e:
            logger.error(f"Error opening video source: {e}")
            return False
    
    def close(self):
        """Close video source and cleanup."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        
        self.is_running = False
        logger.info("Video stream closed")
        
        # Log statistics
        if self.total_frames_captured > 0:
            sampling_ratio = self.total_frames_yielded / self.total_frames_captured
            logger.info(f"Stream statistics:")
            logger.info(f"  Frames captured: {self.total_frames_captured}")
            logger.info(f"  Frames yielded: {self.total_frames_yielded}")
            logger.info(f"  Sampling ratio: {sampling_ratio:.2%}")
            logger.info(f"  Scene changes detected: {self.total_scene_changes}")
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess frame (resize, color conversion, etc.).
        
        Args:
            frame: Raw frame from capture
            
        Returns:
            Preprocessed frame
        """
        # Resize if needed
        height, width = frame.shape[:2]
        if width != self.config.frame_width or height != self.config.frame_height:
            frame = cv2.resize(
                frame,
                (self.config.frame_width, self.config.frame_height),
                interpolation=cv2.INTER_AREA
            )
        
        # OpenCV uses BGR, convert to RGB for consistency with most APIs
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        return frame_rgb
    
    def _should_process_frame(self, frame_bgr: np.ndarray, current_time: datetime) -> tuple[bool, float]:
        """
        Determine if frame should be processed based on adaptive sampling strategy.
        
        Args:
            frame_bgr: Current frame in BGR format
            current_time: Current timestamp
            
        Returns:
            Tuple of (should_process, scene_change_score)
        """
        # First frame should always be processed
        if self.last_processed_time is None:
            return True, 100.0
        
        time_since_last = (current_time - self.last_processed_time).total_seconds()
        
        # Enforce maximum interval (don't miss slow developments)
        if time_since_last >= self.config.max_frame_interval:
            logger.debug(f"Max interval reached ({time_since_last:.1f}s), forcing processing")
            return True, 0.0
        
        # Enforce minimum interval (rate limiting)
        if time_since_last < self.config.min_frame_interval:
            return False, 0.0
        
        # Check for scene change
        is_changed, change_score = self.scene_detector.detect_change(frame_bgr)
        
        if is_changed:
            logger.debug(f"Scene change detected (score: {change_score:.1f})")
            self.total_scene_changes += 1
            return True, change_score
        
        return False, change_score
    
    def stream(self) -> Iterator[Frame]:
        """
        Stream frames with intelligent sampling.
        
        Yields:
            Frame objects that should be processed
            
        This is the main interface for frame consumption. It handles:
        - Continuous capture
        - Scene change detection
        - Interval-based sampling
        - Frame preprocessing
        - Error recovery
        """
        if not self.is_running:
            logger.error("Cannot stream: video source not opened")
            return
        
        logger.info("Starting video stream...")
        logger.info(f"Target processing rate: {self.config.target_fps} FPS")
        logger.info(f"Frame interval: {self.config.min_frame_interval}-{self.config.max_frame_interval}s")
        
        consecutive_failures = 0
        max_failures = 10
        
        while self.is_running:
            try:
                ret, frame_bgr = self.cap.read()
                
                if not ret:
                    consecutive_failures += 1
                    
                    if consecutive_failures >= max_failures:
                        logger.error("Too many consecutive capture failures, stopping stream")
                        break
                    
                    # Check if we've reached end of video file
                    if isinstance(self.config.source, (str, Path)):
                        logger.info("Reached end of video file")
                        break
                    
                    logger.warning(f"Failed to capture frame ({consecutive_failures}/{max_failures})")
                    time.sleep(0.1)
                    continue
                
                consecutive_failures = 0
                self.total_frames_captured += 1
                self.frame_count += 1
                current_time = datetime.now()
                
                # Adaptive sampling decision
                should_process, scene_change_score = self._should_process_frame(
                    frame_bgr, current_time
                )
                
                if not should_process:
                    # Skip this frame
                    continue
                
                # Preprocess frame
                frame_rgb = self._preprocess_frame(frame_bgr)
                
                # Create Frame object
                frame_obj = Frame(
                    timestamp=current_time,
                    image=frame_rgb,
                    frame_number=self.frame_count,
                    source=str(self.config.source),
                    width=frame_rgb.shape[1],
                    height=frame_rgb.shape[0],
                    channels=frame_rgb.shape[2],
                    scene_change_score=scene_change_score
                )
                
                self.last_processed_time = current_time
                self.total_frames_yielded += 1
                
                yield frame_obj
                
                # Rate limiting to match target FPS
                # This prevents overwhelming downstream processing
                if self.config.target_fps > 0:
                    sleep_time = 1.0 / self.config.target_fps
                    time.sleep(max(0, sleep_time - 0.001))  # Slight adjustment for overhead
                
            except KeyboardInterrupt:
                logger.info("Stream interrupted by user")
                break
                
            except Exception as e:
                logger.error(f"Error in stream loop: {e}", exc_info=True)
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    break
                time.sleep(0.1)
    
    def get_statistics(self) -> dict:
        """Get streaming statistics."""
        sampling_ratio = 0.0
        if self.total_frames_captured > 0:
            sampling_ratio = self.total_frames_yielded / self.total_frames_captured
        
        return {
            "frames_captured": self.total_frames_captured,
            "frames_yielded": self.total_frames_yielded,
            "sampling_ratio": sampling_ratio,
            "scene_changes": self.total_scene_changes,
            "is_running": self.is_running
        }
    
    def __enter__(self):
        """Context manager entry."""
        self.open()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def test_video_stream():
    """Test function for video stream module."""
    from config import Config
    
    config = Config()
    config.video.source = 0  # Webcam
    config.video.target_fps = 1.0
    
    print("Testing video stream (will capture 10 frames)...")
    
    with VideoStream(config.video) as stream:
        for i, frame in enumerate(stream.stream()):
            print(f"Frame {i+1}: {frame.frame_number}, "
                  f"Scene change: {frame.scene_change_score:.1f}, "
                  f"Size: {frame.width}x{frame.height}")
            
            if i >= 9:  # Capture 10 frames
                break
    
    stats = stream.get_statistics()
    print(f"\nStatistics: {stats}")


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    test_video_stream()

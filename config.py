"""
Configuration module for Factory Safety Monitoring System.

This module centralizes all configuration parameters, making the system
easily tunable for different deployment scenarios and performance requirements.
"""

import os
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class VideoConfig:
    """Video stream configuration parameters."""
    
    # Input source: 0 for webcam, path for video file
    source: str | int = 0
    
    # Target FPS for processing (not capture FPS)
    # Processing every frame is computationally wasteful for real-time monitoring
    target_fps: float = 2.0
    
    # Frame dimensions (resize for faster processing)
    frame_width: int = 1280
    frame_height: int = 720
    
    # Scene change threshold for adaptive sampling (0-100)
    # Higher = more change required to trigger new frame analysis
    scene_change_threshold: float = 15.0
    
    # Minimum interval between frames (seconds) regardless of scene change
    min_frame_interval: float = 0.5
    
    # Maximum interval between frames (seconds) even if scene is static
    # Ensures we don't miss slow-developing situations
    max_frame_interval: float = 5.0


@dataclass
class VLMConfig:
    """Vision-Language Model configuration."""
    
    # Model provider: 'openai', 'anthropic', 'local'
    provider: str = "openai"
    
    # Model name
    model_name: str = "gpt-4o"  # GPT-4 with vision
    
    # API key (load from environment)
    api_key: Optional[str] = None
    
    # Max tokens for vision model response
    max_tokens: int = 500
    
    # Temperature for generation
    temperature: float = 0.3  # Low temperature for consistent, factual descriptions
    
    # Request timeout (seconds)
    timeout: int = 30
    
    # Enable mock mode if no API key (for testing)
    enable_mock: bool = True
    
    # Detail level for image analysis
    detail: str = "high"  # 'low', 'high', 'auto'


@dataclass
class ReasoningConfig:
    """Risk reasoning configuration."""
    
    # Model for reasoning (can be different from VLM)
    provider: str = "openai"
    model_name: str = "gpt-4o"
    
    # API key
    api_key: Optional[str] = None
    
    # Temperature for reasoning (slightly higher for nuanced analysis)
    temperature: float = 0.4
    
    # Max tokens for reasoning
    max_tokens: int = 800
    
    # Request timeout
    timeout: int = 20
    
    # Risk severity levels
    risk_levels: tuple = ("LOW", "MEDIUM", "HIGH", "CRITICAL")
    
    # Minimum confidence for alert generation (0-1)
    min_confidence: float = 0.6


@dataclass
class AggregationConfig:
    """Event aggregation configuration."""
    
    # Time window for event aggregation (seconds)
    window_size: float = 30.0
    
    # Sliding window step (seconds)
    window_step: float = 5.0
    
    # Minimum events in window to trigger alert
    min_events_for_alert: int = 2
    
    # Event persistence time (how long to keep in memory)
    event_ttl: float = 300.0  # 5 minutes
    
    # Enable temporal pattern detection
    enable_pattern_detection: bool = True


@dataclass
class AlertConfig:
    """Alert management configuration."""
    
    # Alert cooldown period (seconds) - prevent alert spam
    # Reduced for short videos - prevents spam in 7-30 second clips
    alert_cooldown: float = 10.0
    
    # Maximum alerts per time window
    max_alerts_per_window: int = 5
    
    # Alert priority thresholds
    critical_requires_immediate: bool = True
    
    # Enable alert deduplication
    enable_deduplication: bool = True
    
    # Deduplication similarity threshold (0-1)
    # Lowered to catch more duplicates (same issue across frames)
    dedup_similarity_threshold: float = 0.70
    
    # Alert output modes: 'console', 'file', 'webhook', 'all'
    output_modes: list = None
    
    def __post_init__(self):
        if self.output_modes is None:
            self.output_modes = ['console']


@dataclass
class SystemConfig:
    """Overall system configuration."""
    
    # Enable async processing
    enable_async: bool = True
    
    # Number of worker threads for parallel processing
    num_workers: int = 2
    
    # Enable performance metrics
    enable_metrics: bool = True
    
    # Logging level
    log_level: str = "INFO"
    
    # Output directory for logs, alerts, etc.
    output_dir: Path = Path("./output")
    
    # Enable visualization overlay on frames
    enable_visualization: bool = True
    
    # Save processed frames
    save_frames: bool = False
    
    # Frame save interval (seconds)
    frame_save_interval: float = 10.0


class Config:
    """
    Main configuration class that aggregates all configuration components.
    
    This class implements the singleton pattern to ensure consistent
    configuration across the application.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Load environment variables
        self._load_env()
        
        # Initialize configuration components
        self.video = VideoConfig()
        self.vlm = VLMConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            provider=os.getenv("VLM_PROVIDER", "openai"),
            model_name=os.getenv("VLM_MODEL", "gpt-4o")
        )
        self.reasoning = ReasoningConfig(
            api_key=os.getenv("OPENAI_API_KEY"),
            provider=os.getenv("REASONING_PROVIDER", "openai"),
            model_name=os.getenv("REASONING_MODEL", "gpt-4o")
        )
        self.aggregation = AggregationConfig()
        self.alert = AlertConfig()
        self.system = SystemConfig()
        
        # Create output directory
        self.system.output_dir.mkdir(parents=True, exist_ok=True)
        
        self._initialized = True
    
    def _load_env(self):
        """Load environment variables from .env file if present."""
        env_path = Path(".env")
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, _, value = line.partition("=")
                        os.environ.setdefault(key.strip(), value.strip())
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration and return status with any errors.
        
        Returns:
            Tuple of (is_valid, list of error messages)
        """
        errors = []
        
        # Check API keys if not in mock mode
        if not self.vlm.enable_mock and not self.vlm.api_key:
            errors.append("VLM API key is required when mock mode is disabled")
        
        if not self.reasoning.api_key and self.vlm.provider == self.reasoning.provider:
            # Can share API key
            self.reasoning.api_key = self.vlm.api_key
        
        # Validate frame intervals
        if self.video.min_frame_interval >= self.video.max_frame_interval:
            errors.append("min_frame_interval must be less than max_frame_interval")
        
        # Validate risk levels
        if len(self.reasoning.risk_levels) < 2:
            errors.append("At least 2 risk levels required")
        
        return len(errors) == 0, errors
    
    def get_summary(self) -> dict:
        """Get a summary of current configuration."""
        return {
            "video": {
                "source": self.video.source,
                "target_fps": self.video.target_fps,
                "resolution": f"{self.video.frame_width}x{self.video.frame_height}"
            },
            "vlm": {
                "provider": self.vlm.provider,
                "model": self.vlm.model_name,
                "mock_mode": self.vlm.enable_mock and not self.vlm.api_key
            },
            "reasoning": {
                "provider": self.reasoning.provider,
                "model": self.reasoning.model_name
            },
            "aggregation": {
                "window_size": self.aggregation.window_size,
                "min_events": self.aggregation.min_events_for_alert
            },
            "system": {
                "async_enabled": self.system.enable_async,
                "workers": self.system.num_workers
            }
        }


# Global configuration instance
config = Config()

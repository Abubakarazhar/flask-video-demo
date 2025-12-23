#!/usr/bin/env python3
"""
Quick test to verify analysis is working.
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import Config
from models import Frame
from vision_model import VisionModelFactory
from risk_reasoner import RiskReasonerFactory
import numpy as np
import cv2
from datetime import datetime

print("🧪 Testing Analysis System...")
print("="*60)

# Create a test frame with obvious features
test_image = np.zeros((720, 1280, 3), dtype=np.uint8)
test_image[:] = [100, 100, 100]  # Gray background

# Add a person (skin tone)
cv2.rectangle(test_image, (500, 300), (600, 600), (200, 180, 140), -1)  # Skin tone

# Add hard hat (bright yellow)
cv2.ellipse(test_image, (550, 280), (40, 20), 0, 0, 360, (255, 220, 0), -1)

# Add safety vest (orange)
cv2.rectangle(test_image, (480, 350), (620, 500), (255, 120, 0), -1)

frame = Frame(
    image=test_image,
    frame_number=1,
    source="test",
    width=1280,
    height=720,
    timestamp=datetime.now()
)

# Test vision model
print("\n1. Testing Vision Model...")
config = Config()
vision_model = VisionModelFactory.create(config.vlm)
vision_analysis = vision_model.analyze_frame(frame)

print(f"   ✅ Detected people: {len(vision_analysis.detected_people)}")
print(f"   ✅ Hazards: {len(vision_analysis.hazards_visible)}")
print(f"   ✅ Scene: {vision_analysis.scene_description[:80]}...")

# Test risk reasoner
print("\n2. Testing Risk Reasoner...")
risk_reasoner = RiskReasonerFactory.create(config.reasoning)
events = risk_reasoner.assess_risks(vision_analysis)

print(f"   ✅ Events found: {len(events)}")
for event in events:
    print(f"      - {event.title} ({event.risk_level.value})")

if len(events) > 0:
    print("\n✅✅✅ ANALYSIS IS WORKING!")
    print("   The system detected and analyzed the test frame.")
    print("   If you're not seeing results in the web interface,")
    print("   it might be because your video doesn't have detectable features.")
else:
    print("\n⚠️  No events detected in test frame.")
    print("   This might indicate detection sensitivity needs adjustment.")

print("\n" + "="*60)

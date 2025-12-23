#!/usr/bin/env python3
"""
Generate a realistic factory safety monitoring demo video.

Creates a professional-looking factory scene with:
- Realistic factory environment
- Animated workers
- Safety violations (missing PPE)
- Machinery and equipment
- Professional graphics
"""

import cv2
import numpy as np
from pathlib import Path
from datetime import datetime
import math

def create_realistic_factory_frame(frame_num, width=1920, height=1080):
    """Create a realistic factory frame with professional graphics."""
    
    # Create base image
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Factory floor - realistic concrete texture
    frame[:] = [75, 75, 80]  # Base gray
    # Add texture with noise
    noise = np.random.randint(-8, 8, (height, width, 3), dtype=np.int16)
    frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Industrial lighting (brighter in center, darker at edges)
    center_y, center_x = height // 2, width // 2
    for y in range(height):
        for x in range(width):
            dist = math.sqrt((x - center_x)**2 + (y - center_y)**2)
            max_dist = math.sqrt(center_x**2 + center_y**2)
            brightness = int(30 * (1 - dist / max_dist))
            frame[y, x] = np.clip(frame[y, x].astype(int) + brightness, 0, 255)
    
    # === BACKGROUND ELEMENTS ===
    
    # Large CNC Machine (left side) - detailed
    machine1_x, machine1_y = 200, 300
    machine1_w, machine1_h = 350, 500
    
    # Machine base
    cv2.rectangle(frame, 
                  (machine1_x, machine1_y), 
                  (machine1_x + machine1_w, machine1_y + machine1_h),
                  (45, 45, 50), -1)
    cv2.rectangle(frame, 
                  (machine1_x, machine1_y), 
                  (machine1_x + machine1_w, machine1_y + machine1_h),
                  (120, 120, 130), 4)
    
    # Machine details
    # Control panel
    cv2.rectangle(frame, 
                  (machine1_x + 20, machine1_y + 50), 
                  (machine1_x + machine1_w - 20, machine1_y + 150),
                  (30, 30, 35), -1)
    cv2.rectangle(frame, 
                  (machine1_x + 20, machine1_y + 50), 
                  (machine1_x + machine1_w - 20, machine1_y + 150),
                  (80, 80, 90), 2)
    
    # Status lights
    light_state = (frame_num // 30) % 2
    light_color = (0, 255, 0) if light_state else (0, 150, 0)
    cv2.circle(frame, (machine1_x + 100, machine1_y + 100), 12, light_color, -1)
    cv2.circle(frame, (machine1_x + 200, machine1_y + 100), 12, (255, 200, 0), -1)
    
    # Machine label
    cv2.putText(frame, "CNC MILLING", 
                (machine1_x + 80, machine1_y + 200),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (200, 200, 200), 3)
    cv2.putText(frame, "MACHINE #12", 
                (machine1_x + 100, machine1_y + 240),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (150, 150, 150), 2)
    
    # Hydraulic Press (right side)
    machine2_x, machine2_y = 1400, 250
    machine2_w, machine2_h = 400, 550
    
    cv2.rectangle(frame, 
                  (machine2_x, machine2_y), 
                  (machine2_x + machine2_w, machine2_y + machine2_h),
                  (50, 50, 55), -1)
    cv2.rectangle(frame, 
                  (machine2_x, machine2_y), 
                  (machine2_x + machine2_w, machine2_y + machine2_h),
                  (110, 110, 120), 5)
    
    # Press ram (moving)
    ram_y = machine2_y + 100 + int(30 * math.sin(frame_num * 0.1))
    cv2.rectangle(frame, 
                  (machine2_x + 50, ram_y), 
                  (machine2_x + machine2_w - 50, ram_y + 80),
                  (60, 60, 70), -1)
    
    cv2.putText(frame, "HYDRAULIC", 
                (machine2_x + 120, machine2_y + 400),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
    cv2.putText(frame, "PRESS", 
                (machine2_x + 150, machine2_y + 440),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
    
    # Conveyor belt system (center)
    conv_y = 750
    cv2.rectangle(frame, (600, conv_y), (1320, conv_y + 100), (40, 40, 45), -1)
    cv2.rectangle(frame, (600, conv_y), (1320, conv_y + 100), (70, 70, 80), 3)
    
    # Conveyor rollers
    for x in range(630, 1290, 60):
        cv2.circle(frame, (x, conv_y + 50), 20, (55, 55, 60), -1)
        cv2.circle(frame, (x, conv_y + 50), 20, (90, 90, 100), 2)
    
    # Moving belt pattern
    belt_offset = (frame_num * 2) % 60
    for x in range(610 + belt_offset, 1310, 60):
        cv2.line(frame, (x, conv_y + 45), (x, conv_y + 55), (100, 100, 100), 2)
    
    # === WORKERS ===
    
    # Worker 1 (moving around)
    worker1_x = int(800 + 300 * math.sin(frame_num * 0.03))
    worker1_y = 700
    
    # Worker body (realistic proportions)
    # Head
    cv2.circle(frame, (worker1_x, worker1_y - 100), 30, (220, 180, 140), -1)
    cv2.circle(frame, (worker1_x, worker1_y - 100), 30, (180, 140, 100), 2)
    
    # Torso
    cv2.rectangle(frame, 
                  (worker1_x - 25, worker1_y - 70), 
                  (worker1_x + 25, worker1_y + 50),
                  (30, 30, 150), -1)  # Blue shirt
    
    # Arms
    arm_swing = int(15 * math.sin(frame_num * 0.2))
    cv2.rectangle(frame, 
                  (worker1_x - 35, worker1_y - 50 + arm_swing), 
                  (worker1_x - 25, worker1_y + 30),
                  (220, 180, 140), -1)  # Left arm
    cv2.rectangle(frame, 
                  (worker1_x + 25, worker1_y - 50 - arm_swing), 
                  (worker1_x + 35, worker1_y + 30),
                  (220, 180, 140), -1)  # Right arm
    
    # Legs
    cv2.rectangle(frame, 
                  (worker1_x - 20, worker1_y + 50), 
                  (worker1_x - 8, worker1_y + 120),
                  (40, 40, 40), -1)  # Left leg
    cv2.rectangle(frame, 
                  (worker1_x + 8, worker1_y + 50), 
                  (worker1_x + 20, worker1_y + 120),
                  (40, 40, 40), -1)  # Right leg
    
    # Boots
    cv2.ellipse(frame, (worker1_x - 14, worker1_y + 120), (8, 5), 0, 0, 360, (20, 20, 20), -1)
    cv2.ellipse(frame, (worker1_x + 14, worker1_y + 120), (8, 5), 0, 0, 360, (20, 20, 20), -1)
    
    # PPE - Hard hat (sometimes missing for violations)
    hat_frame = (frame_num // 60) % 4
    if hat_frame < 3:  # Wearing hat 75% of time
        # Yellow hard hat
        cv2.ellipse(frame, (worker1_x, worker1_y - 120), (32, 15), 0, 0, 360, (255, 200, 0), -1)
        cv2.ellipse(frame, (worker1_x, worker1_y - 120), (32, 15), 0, 0, 360, (200, 150, 0), 3)
        # Hat brim
        cv2.ellipse(frame, (worker1_x, worker1_y - 105), (35, 8), 0, 0, 360, (200, 150, 0), -1)
    else:
        # VIOLATION - No hard hat!
        cv2.putText(frame, "NO HARD HAT!", 
                   (worker1_x - 80, worker1_y - 140),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 3)
        cv2.putText(frame, "VIOLATION", 
                   (worker1_x - 60, worker1_y - 110),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
    
    # Safety vest (high-visibility orange)
    vest_frame = (frame_num // 80) % 5
    if vest_frame < 4:  # Wearing vest 80% of time
        cv2.rectangle(frame, 
                      (worker1_x - 22, worker1_y - 65), 
                      (worker1_x + 22, worker1_y + 45),
                      (255, 120, 0), -1)  # Orange vest
        # Reflective strips
        cv2.rectangle(frame, 
                      (worker1_x - 18, worker1_y - 60), 
                      (worker1_x + 18, worker1_y - 50),
                      (255, 255, 255), -1)  # Top strip
        cv2.rectangle(frame, 
                      (worker1_x - 18, worker1_y + 15), 
                      (worker1_x + 18, worker1_y + 25),
                      (255, 255, 255), -1)  # Bottom strip
    
    # Worker 2 (stationary, inspecting)
    worker2_x = 1100
    worker2_y = 650
    
    # Head
    cv2.circle(frame, (worker2_x, worker2_y - 100), 30, (200, 160, 120), -1)
    
    # Torso (bent over inspecting)
    cv2.rectangle(frame, 
                  (worker2_x - 25, worker2_y - 70), 
                  (worker2_x + 25, worker2_y + 30),
                  (50, 50, 200), -1)
    
    # Arms (inspecting position)
    cv2.rectangle(frame, 
                  (worker2_x - 35, worker2_y - 40), 
                  (worker2_x - 25, worker2_y + 20),
                  (200, 160, 120), -1)
    cv2.rectangle(frame, 
                  (worker2_x + 25, worker2_y - 20), 
                  (worker2_x + 35, worker2_y + 10),
                  (200, 160, 120), -1)
    
    # Legs
    cv2.rectangle(frame, (worker2_x - 20, worker2_y + 30), (worker2_x - 8, worker2_y + 100), (40, 40, 40), -1)
    cv2.rectangle(frame, (worker2_x + 8, worker2_y + 30), (worker2_x + 20, worker2_y + 100), (40, 40, 40), -1)
    
    # Hard hat (always wearing)
    cv2.ellipse(frame, (worker2_x, worker2_y - 120), (32, 15), 0, 0, 360, (255, 200, 0), -1)
    cv2.ellipse(frame, (worker2_x, worker2_y - 120), (32, 15), 0, 0, 360, (200, 150, 0), 3)
    cv2.ellipse(frame, (worker2_x, worker2_y - 105), (35, 8), 0, 0, 360, (200, 150, 0), -1)
    
    # Safety vest
    cv2.rectangle(frame, 
                  (worker2_x - 22, worker2_y - 65), 
                  (worker2_x + 22, worker2_y + 25),
                  (255, 120, 0), -1)
    cv2.rectangle(frame, 
                  (worker2_x - 18, worker2_y - 60), 
                  (worker2_x + 18, worker2_y - 50),
                  (255, 255, 255), -1)
    cv2.rectangle(frame, 
                  (worker2_x - 18, worker2_y + 5), 
                  (worker2_x + 18, worker2_y + 15),
                  (255, 255, 255), -1)
    
    # === SAFETY EQUIPMENT ===
    
    # Fire extinguisher (wall mounted)
    cv2.rectangle(frame, (100, 200), (150, 350), (200, 0, 0), -1)
    cv2.rectangle(frame, (100, 200), (150, 350), (150, 0, 0), 3)
    cv2.putText(frame, "FIRE", (105, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    # First aid station
    cv2.rectangle(frame, (1700, 150), (1800, 250), (255, 255, 255), -1)
    cv2.rectangle(frame, (1700, 150), (1800, 250), (200, 0, 0), 4)
    cv2.circle(frame, (1750, 200), 30, (200, 0, 0), 4)
    cv2.putText(frame, "+", (1740, 210), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 0, 0), 3)
    cv2.putText(frame, "FIRST AID", (1680, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 1)
    
    # Emergency stop button
    cv2.circle(frame, (1750, 400), 25, (200, 0, 0), -1)
    cv2.circle(frame, (1750, 400), 25, (150, 0, 0), 3)
    cv2.putText(frame, "E-STOP", (1720, 440), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    # Warning signs
    cv2.rectangle(frame, (850, 200), (1050, 300), (255, 200, 0), -1)
    cv2.rectangle(frame, (850, 200), (1050, 300), (200, 150, 0), 4)
    cv2.putText(frame, "CAUTION", (880, 250), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 3)
    cv2.putText(frame, "MACHINERY", (870, 280), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    # Floor markings
    cv2.line(frame, (0, 900), (width, 900), (100, 100, 100), 4)
    cv2.putText(frame, "SAFETY WALKWAY - KEEP CLEAR", 
                (600, 895), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)
    
    # Yellow safety lines
    for x in range(0, width, 200):
        cv2.line(frame, (x, 850), (x + 100, 850), (255, 200, 0), 3)
    
    # === OVERHEAD CRANE (optional, moving) ===
    crane_x = 500 + int(200 * math.sin(frame_num * 0.02))
    cv2.line(frame, (crane_x, 100), (crane_x, 400), (80, 80, 90), 8)  # Vertical beam
    cv2.line(frame, (crane_x - 100, 100), (crane_x + 100, 100), (80, 80, 90), 8)  # Horizontal beam
    cv2.circle(frame, (crane_x, 400), 15, (100, 100, 110), -1)  # Hook
    
    # === INFO OVERLAY (subtle) ===
    overlay = frame.copy()
    cv2.rectangle(overlay, (width - 350, 50), (width - 20, 150), (0, 0, 0), -1)
    frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
    
    cv2.putText(frame, f"Frame {frame_num:04d}", 
                (width - 340, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, datetime.now().strftime("%H:%M:%S"), 
                (width - 340, 120), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
    cv2.putText(frame, "FACTORY SAFETY MONITORING", 
                (width - 340, 145), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    return frame


def generate_factory_video(output_path="factory_demo.mp4", duration_seconds=30, fps=30):
    """Generate a professional factory safety monitoring demo video."""
    
    print(f"🎬 Generating factory safety demo video...")
    print(f"   Duration: {duration_seconds} seconds")
    print(f"   FPS: {fps}")
    print(f"   Resolution: 1920x1080 (Full HD)")
    
    width, height = 1920, 1080
    total_frames = duration_seconds * fps
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    for frame_num in range(total_frames):
        # Create frame
        frame = create_realistic_factory_frame(frame_num, width, height)
        
        # Convert RGB to BGR for OpenCV
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        # Write frame
        out.write(frame_bgr)
        
        # Progress indicator
        if frame_num % (fps * 2) == 0:  # Every 2 seconds
            progress = (frame_num / total_frames) * 100
            print(f"   Progress: {progress:.1f}% ({frame_num}/{total_frames} frames)")
    
    out.release()
    
    file_size = Path(output_path).stat().st_size / (1024 * 1024)  # MB
    print(f"\n✅ Video generated successfully!")
    print(f"   File: {output_path}")
    print(f"   Size: {file_size:.1f} MB")
    print(f"   Duration: {duration_seconds} seconds")
    print(f"\n📹 You can now upload this video to the monitoring system!")


if __name__ == "__main__":
    output_file = Path(__file__).parent / "factory_demo_video.mp4"
    generate_factory_video(output_file, duration_seconds=60, fps=30)
    print(f"\n🎉 Done! Video saved to: {output_file}")

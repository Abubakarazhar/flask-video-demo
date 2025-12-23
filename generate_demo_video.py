#!/usr/bin/env python3
"""
Generate a realistic factory safety monitoring demo video.

Creates a high-quality animated video with:
- Realistic factory environment
- Animated workers
- Machinery and equipment
- Safety violations (for demonstration)
- Professional graphics
"""

import cv2
import numpy as np
from pathlib import Path
import math

def create_factory_frame(frame_num, width=1280, height=720):
    """Create a realistic factory frame."""
    frame = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Factory floor (realistic concrete texture)
    frame[:] = [75, 75, 80]
    # Add texture
    noise = np.random.randint(-8, 8, (height, width, 3), dtype=np.int16)
    frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Industrial lighting (overhead lights)
    for x in range(200, width, 300):
        for y in range(150, height, 250):
            # Light cone effect
            center = (x, y)
            for r in range(100, 0, -5):
                intensity = int(255 * (1 - r/100) * 0.3)
                cv2.circle(frame, center, r, (intensity, intensity, intensity), -1)
    
    # Large CNC Machine (left side) - detailed
    machine_x1, machine_y1 = 100, 200
    machine_x2, machine_y2 = 450, 600
    
    # Machine body
    cv2.rectangle(frame, (machine_x1, machine_y1), (machine_x2, machine_y2), (45, 45, 50), -1)
    cv2.rectangle(frame, (machine_x1, machine_y1), (machine_x2, machine_y2), (90, 90, 100), 5)
    
    # Machine details
    # Control panel
    cv2.rectangle(frame, (machine_x1 + 20, machine_y1 + 30), (machine_x2 - 20, machine_y1 + 100), (30, 30, 35), -1)
    cv2.rectangle(frame, (machine_x1 + 20, machine_y1 + 30), (machine_x2 - 20, machine_y1 + 100), (60, 60, 70), 2)
    # Screen
    cv2.rectangle(frame, (machine_x1 + 50, machine_y1 + 40), (machine_x1 + 150, machine_y1 + 90), (20, 20, 100), -1)
    cv2.putText(frame, "CNC", (machine_x1 + 60, machine_y1 + 70), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 255), 1)
    # Status lights
    cv2.circle(frame, (machine_x1 + 200, machine_y1 + 65), 8, (0, 255, 0), -1)  # Green
    cv2.circle(frame, (machine_x1 + 230, machine_y1 + 65), 8, (255, 200, 0), -1)  # Yellow
    # Spindle (rotating)
    spindle_x = (machine_x1 + machine_x2) // 2
    spindle_y = machine_y1 + 200
    angle = frame_num * 5
    for i in range(8):
        x = int(spindle_x + 30 * math.cos(math.radians(angle + i * 45)))
        y = int(spindle_y + 30 * math.sin(math.radians(angle + i * 45)))
        cv2.circle(frame, (x, y), 5, (150, 150, 150), -1)
    cv2.circle(frame, (spindle_x, spindle_y), 15, (100, 100, 100), -1)
    
    # Hydraulic Press (right side)
    press_x1, press_y1 = 830, 150
    press_x2, press_y2 = 1180, 550
    
    # Press frame
    cv2.rectangle(frame, (press_x1, press_y1), (press_x2, press_y2), (50, 50, 55), -1)
    cv2.rectangle(frame, (press_x1, press_y1), (press_x2, press_y2), (100, 100, 110), 5)
    
    # Press details
    cv2.putText(frame, "HYDRAULIC", (press_x1 + 30, press_y1 + 80), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
    cv2.putText(frame, "PRESS", (press_x1 + 50, press_y1 + 120), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
    
    # Press ram (moving)
    ram_y = press_y1 + 150 + int(50 * math.sin(frame_num * 0.1))
    cv2.rectangle(frame, (press_x1 + 50, press_y1 + 150), (press_x2 - 50, ram_y), (60, 60, 70), -1)
    cv2.rectangle(frame, (press_x1 + 50, press_y1 + 150), (press_x2 - 50, ram_y), (120, 120, 130), 2)
    
    # Conveyor belt system (center)
    conv_y = 550
    cv2.rectangle(frame, (500, conv_y - 40), (780, conv_y + 40), (40, 40, 45), -1)
    cv2.rectangle(frame, (500, conv_y - 40), (780, conv_y + 40), (80, 80, 90), 3)
    
    # Conveyor rollers
    for x in range(520, 760, 40):
        cv2.circle(frame, (x, conv_y), 18, (60, 60, 70), -1)
        cv2.circle(frame, (x, conv_y), 18, (100, 100, 110), 2)
    
    # Moving belt pattern
    belt_offset = (frame_num * 2) % 40
    for x in range(510 + belt_offset, 770, 40):
        cv2.rectangle(frame, (x, conv_y - 5), (x + 20, conv_y + 5), (30, 30, 35), -1)
    
    # Worker 1 (animated, moving around)
    worker1_x = int(600 + 150 * math.sin(frame_num * 0.03))
    worker1_y = 520
    
    # Worker body (realistic proportions)
    # Head
    cv2.circle(frame, (worker1_x, worker1_y - 35), 22, (220, 180, 140), -1)
    cv2.circle(frame, (worker1_x, worker1_y - 35), 22, (180, 140, 100), 2)
    
    # Torso
    cv2.rectangle(frame, (worker1_x - 18, worker1_y - 13), (worker1_x + 18, worker1_y + 40), (30, 30, 150), -1)  # Blue shirt
    cv2.rectangle(frame, (worker1_x - 18, worker1_y - 13), (worker1_y + 18, worker1_y + 40), (50, 50, 170), 2)
    
    # Arms (moving)
    arm_swing = int(15 * math.sin(frame_num * 0.2))
    cv2.rectangle(frame, (worker1_x - 28, worker1_y - 5 + arm_swing), (worker1_x - 18, worker1_y + 30), (220, 180, 140), -1)
    cv2.rectangle(frame, (worker1_x + 18, worker1_y - 5 - arm_swing), (worker1_x + 28, worker1_y + 30), (220, 180, 140), -1)
    
    # Legs
    leg_offset = int(5 * math.sin(frame_num * 0.2))
    cv2.rectangle(frame, (worker1_x - 12, worker1_y + 40), (worker1_x - 4, worker1_y + 95 + leg_offset), (40, 40, 40), -1)
    cv2.rectangle(frame, (worker1_x + 4, worker1_y + 40), (worker1_x + 12, worker1_y + 95 - leg_offset), (40, 40, 40), -1)
    
    # PPE - Hard hat (sometimes missing for demo)
    hat_frame = (frame_num // 60) % 4
    if hat_frame < 3:  # Wearing hat 75% of time
        # Yellow hard hat
        cv2.ellipse(frame, (worker1_x, worker1_y - 50), (26, 12), 0, 0, 360, (255, 200, 0), -1)
        cv2.ellipse(frame, (worker1_x, worker1_y - 50), (26, 12), 0, 0, 360, (200, 150, 0), 2)
        # Hat brim
        cv2.ellipse(frame, (worker1_x, worker1_y - 42), (28, 4), 0, 0, 360, (200, 150, 0), -1)
    else:
        # VIOLATION - No hard hat!
        cv2.putText(frame, "NO HARD HAT!", (worker1_x - 50, worker1_y - 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 3)
        cv2.putText(frame, "VIOLATION", (worker1_x - 40, worker1_y - 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
    
    # Safety vest (high-visibility orange)
    vest_frame = (frame_num // 80) % 5
    if vest_frame < 4:  # Wearing vest 80% of time
        cv2.rectangle(frame, (worker1_x - 16, worker1_y - 10), (worker1_x + 16, worker1_y + 35), (255, 120, 0), -1)
        # Reflective strips
        cv2.rectangle(frame, (worker1_x - 14, worker1_y - 8), (worker1_x + 14, worker1_y - 2), (255, 255, 255), -1)
        cv2.rectangle(frame, (worker1_x - 14, worker1_y + 15), (worker1_x + 14, worker1_y + 25), (255, 255, 255), -1)
    
    # Worker 2 (stationary, near press)
    worker2_x = 1000
    worker2_y = 450
    
    # Worker 2 body
    cv2.circle(frame, (worker2_x, worker2_y - 35), 22, (200, 170, 130), -1)
    cv2.rectangle(frame, (worker2_x - 18, worker2_y - 13), (worker2_x + 18, worker2_y + 40), (40, 40, 40), -1)  # Dark shirt
    cv2.rectangle(frame, (worker2_x - 28, worker2_y - 5), (worker2_x - 18, worker2_y + 30), (200, 170, 130), -1)
    cv2.rectangle(frame, (worker2_x + 18, worker2_y - 5), (worker2_x + 28, worker2_y + 30), (200, 170, 130), -1)
    cv2.rectangle(frame, (worker2_x - 12, worker2_y + 40), (worker2_x - 4, worker2_y + 95), (40, 40, 40), -1)
    cv2.rectangle(frame, (worker2_x + 4, worker2_y + 40), (worker2_x + 12, worker2_y + 95), (40, 40, 40), -1)
    
    # Worker 2 PPE - Always wearing (compliant)
    cv2.ellipse(frame, (worker2_x, worker2_y - 50), (26, 12), 0, 0, 360, (255, 200, 0), -1)
    cv2.ellipse(frame, (worker2_x, worker2_y - 50), (26, 12), 0, 0, 360, (200, 150, 0), 2)
    cv2.ellipse(frame, (worker2_x, worker2_y - 42), (28, 4), 0, 0, 360, (200, 150, 0), -1)
    cv2.rectangle(frame, (worker2_x - 16, worker2_y - 10), (worker2_x + 16, worker2_y + 35), (255, 120, 0), -1)
    cv2.rectangle(frame, (worker2_x - 14, worker2_y - 8), (worker2_x + 14, worker2_y - 2), (255, 255, 255), -1)
    cv2.rectangle(frame, (worker2_x - 14, worker2_y + 15), (worker2_x + 14, worker2_y + 25), (255, 255, 255), -1)
    
    # Safety equipment
    # Fire extinguisher
    cv2.rectangle(frame, (50, 50), (90, 180), (200, 0, 0), -1)
    cv2.rectangle(frame, (50, 50), (90, 180), (255, 50, 50), 3)
    cv2.putText(frame, "FIRE", (55, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    cv2.circle(frame, (70, 200), 15, (100, 100, 100), -1)  # Base
    
    # First aid station
    cv2.rectangle(frame, (1190, 50), (1230, 150), (255, 255, 255), -1)
    cv2.rectangle(frame, (1190, 50), (1230, 150), (200, 200, 200), 3)
    cv2.circle(frame, (1210, 100), 25, (200, 0, 0), 3)
    cv2.putText(frame, "+", (1200, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 0, 0), 3)
    
    # Warning signs
    cv2.rectangle(frame, (550, 100), (680, 200), (255, 200, 0), -1)
    cv2.rectangle(frame, (550, 100), (680, 200), (200, 150, 0), 4)
    cv2.putText(frame, "CAUTION", (560, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
    cv2.putText(frame, "MACHINERY", (565, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    # Floor markings
    cv2.line(frame, (0, 650), (width, 650), (100, 100, 100), 4)
    cv2.putText(frame, "SAFETY WALKWAY", (500, 645), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 2)
    
    # Yellow safety lines
    for x in range(0, width, 50):
        cv2.line(frame, (x, 200), (x + 25, 200), (255, 200, 0), 3)
    
    # Info overlay (subtle)
    overlay = frame.copy()
    cv2.rectangle(overlay, (1000, 600), (1250, 700), (0, 0, 0), -1)
    frame = cv2.addWeighted(frame, 0.85, overlay, 0.15, 0)
    
    cv2.putText(frame, f"Frame {frame_num}", (1020, 640), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(frame, "Factory Safety Demo", (1020, 670), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    cv2.putText(frame, "HD Quality", (1020, 690), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)
    
    return frame


def generate_demo_video(output_path="factory_demo_video.mp4", duration_seconds=30, fps=30):
    """Generate a high-quality factory demo video."""
    print(f"🎬 Generating factory demo video...")
    print(f"   Duration: {duration_seconds}s")
    print(f"   FPS: {fps}")
    print(f"   Resolution: 1280x720 (HD)")
    
    width, height = 1280, 720
    total_frames = duration_seconds * fps
    
    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
    
    for frame_num in range(total_frames):
        # Create frame
        frame_bgr = create_factory_frame(frame_num, width, height)
        
        # Convert RGB to BGR for OpenCV
        frame_bgr = cv2.cvtColor(frame_bgr, cv2.COLOR_RGB2BGR)
        
        # Write frame
        out.write(frame_bgr)
        
        # Progress
        if (frame_num + 1) % (fps * 5) == 0:
            progress = (frame_num + 1) / total_frames * 100
            print(f"   Progress: {progress:.1f}% ({frame_num + 1}/{total_frames} frames)")
    
    out.release()
    
    file_size = Path(output_path).stat().st_size / (1024 * 1024)  # MB
    print(f"\n✅ Video generated successfully!")
    print(f"   File: {output_path}")
    print(f"   Size: {file_size:.2f} MB")
    print(f"   Frames: {total_frames}")
    print(f"\n📹 Video features:")
    print(f"   ✅ Realistic factory environment")
    print(f"   ✅ Animated workers (one with PPE violations)")
    print(f"   ✅ Moving machinery (CNC, hydraulic press)")
    print(f"   ✅ Conveyor belt with animation")
    print(f"   ✅ Safety equipment and signage")
    print(f"   ✅ Professional HD quality")
    
    return output_path


if __name__ == "__main__":
    output_file = Path(__file__).parent / "factory_demo_video.mp4"
    generate_demo_video(str(output_file), duration_seconds=30, fps=30)
    print(f"\n🎉 Done! Upload this video to test the system:")
    print(f"   {output_file}")

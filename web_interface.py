#!/usr/bin/env python3
"""
Web-based dashboard for Factory Safety Monitoring System.

A real-time web interface with:
- Live camera feed display
- Real-time alert stream
- System statistics
- Event timeline
- Risk score visualization
"""

import json
import base64
import threading
import time
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import List, Dict
import numpy as np

from flask import Flask, render_template, Response, jsonify, request
from flask_cors import CORS
from werkzeug.utils import secure_filename
import os

from config import Config
from models import Frame, Alert, SafetyEvent
from vision_model import VisionModelFactory
from risk_reasoner import RiskReasonerFactory
from event_aggregator import EventAggregator
from alert_manager import AlertManager
from utils import setup_logging, PerformanceMonitor
# Chatbot removed
import cv2

# Setup
setup_logging(log_level="INFO")
app = Flask(__name__)
CORS(app)

# Global state
config = Config()
alert_queue = Queue(maxsize=100)
event_queue = Queue(maxsize=100)
latest_frame = None
latest_stats = {}
is_running = False
processing_thread = None
video_thread = None
frame_counter = 0

# Video file handling
video_file_path = None
video_cap = None
video_playing = True  # Video playback control
UPLOAD_FOLDER = Path(__file__).parent / 'uploads'
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'webm'}


def frame_to_base64(frame: np.ndarray) -> str:
    """Convert frame to base64 for web display."""
    # Resize for web display
    height, width = frame.shape[:2]
    if width > 800:
        scale = 800 / width
        new_width = 800
        new_height = int(height * scale)
        frame = cv2.resize(frame, (new_width, new_height))
    
    # Convert RGB to BGR for encoding
    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
    
    # Encode as JPEG
    _, buffer = cv2.imencode('.jpg', frame_bgr)
    
    # Convert to base64
    jpg_as_text = base64.b64encode(buffer).decode('utf-8')
    return f"data:image/jpeg;base64,{jpg_as_text}"


def create_test_frame(frame_number: int) -> Frame:
    """Create realistic factory demo frame - only for display when no video uploaded."""
    import cv2
    
    # Create realistic factory scene
    test_image = np.zeros((720, 1280, 3), dtype=np.uint8)  # HD resolution
    
    # Factory floor (realistic gray concrete texture)
    test_image[:] = [70, 70, 75]
    # Add texture with noise
    noise = np.random.randint(-10, 10, (720, 1280, 3), dtype=np.int16)
    test_image = np.clip(test_image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    # Industrial lighting (brighter in center)
    center_y, center_x = 360, 640
    for y in range(720):
        for x in range(1280):
            dist = np.sqrt((x - center_x)**2 + (y - center_y)**2)
            brightness = max(0, 255 - dist // 3)
            test_image[y, x] = np.clip(test_image[y, x].astype(int) + brightness // 20, 0, 255)
    
    # Large machinery - CNC Machine (left)
    cv2.rectangle(test_image, (100, 200), (400, 600), (50, 50, 55), -1)
    cv2.rectangle(test_image, (100, 200), (400, 600), (100, 100, 110), 5)
    cv2.putText(test_image, "CNC MILL", (150, 420), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (200, 200, 200), 3)
    # Machine details
    cv2.rectangle(test_image, (120, 250), (380, 300), (30, 30, 35), -1)  # Control panel
    cv2.circle(test_image, (250, 275), 15, (0, 255, 0), -1)  # Status light
    
    # Press Machine (right)
    cv2.rectangle(test_image, (880, 150), (1180, 550), (50, 50, 55), -1)
    cv2.rectangle(test_image, (880, 150), (1180, 550), (100, 100, 110), 5)
    cv2.putText(test_image, "HYDRAULIC", (920, 350), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
    cv2.putText(test_image, "PRESS", (960, 390), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (200, 200, 200), 2)
    
    # Conveyor belt system (center)
    cv2.rectangle(test_image, (450, 500), (830, 580), (40, 40, 45), -1)
    cv2.rectangle(test_image, (450, 500), (830, 580), (80, 80, 90), 3)
    # Conveyor rollers
    for x in range(470, 810, 40):
        cv2.circle(test_image, (x, 540), 15, (60, 60, 70), -1)
    
    # Worker figure (realistic size and movement)
    worker_x = int(640 + 200 * np.sin(frame_number * 0.05))  # Smooth movement
    worker_y = 550
    
    # Worker body (realistic proportions)
    # Head
    cv2.circle(test_image, (worker_x, worker_y - 80), 25, (220, 180, 140), -1)
    # Torso
    cv2.rectangle(test_image, (worker_x - 20, worker_y - 55), (worker_x + 20, worker_y + 30), (30, 30, 150), -1)  # Blue shirt
    # Arms
    cv2.rectangle(test_image, (worker_x - 30, worker_y - 40), (worker_x - 20, worker_y + 20), (220, 180, 140), -1)  # Left arm
    cv2.rectangle(test_image, (worker_x + 20, worker_y - 40), (worker_x + 30, worker_y + 20), (220, 180, 140), -1)  # Right arm
    # Legs
    cv2.rectangle(test_image, (worker_x - 15, worker_y + 30), (worker_x - 5, worker_y + 90), (40, 40, 40), -1)  # Left leg
    cv2.rectangle(test_image, (worker_x + 5, worker_y + 30), (worker_x + 15, worker_y + 90), (40, 40, 40), -1)  # Right leg
    
    # PPE - Hard hat (sometimes missing for demo violations)
    hat_wearing = (frame_number // 30) % 3 != 0  # Wearing 2/3 of time
    if hat_wearing:
        # Yellow hard hat
        cv2.ellipse(test_image, (worker_x, worker_y - 95), (28, 12), 0, 0, 360, (255, 200, 0), -1)
        cv2.ellipse(test_image, (worker_x, worker_y - 95), (28, 12), 0, 0, 360, (200, 150, 0), 2)
    else:
        # Violation - no hard hat!
        cv2.putText(test_image, "NO HARD HAT!", (worker_x - 60, worker_y - 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 3)
    
    # Safety vest (high-visibility orange)
    vest_wearing = (frame_number // 40) % 4 != 0  # Wearing 3/4 of time
    if vest_wearing:
        cv2.rectangle(test_image, (worker_x - 18, worker_y - 50), (worker_x + 18, worker_y + 25), (255, 120, 0), -1)
        # Reflective strips
        cv2.rectangle(test_image, (worker_x - 15, worker_y - 45), (worker_x + 15, worker_y - 35), (255, 255, 255), -1)
        cv2.rectangle(test_image, (worker_x - 15, worker_y + 10), (worker_x + 15, worker_y + 20), (255, 255, 255), -1)
    
    # Safety equipment around factory
    # Fire extinguisher
    cv2.rectangle(test_image, (50, 50), (80, 150), (200, 0, 0), -1)
    cv2.putText(test_image, "FIRE", (45, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
    
    # First aid station
    cv2.rectangle(test_image, (1200, 50), (1230, 120), (255, 255, 255), -1)
    cv2.circle(test_image, (1215, 85), 20, (200, 0, 0), 3)
    cv2.putText(test_image, "+", (1208, 92), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 0, 0), 2)
    
    # Floor markings (safety zones)
    cv2.line(test_image, (0, 650), (1280, 650), (100, 100, 100), 3)
    cv2.putText(test_image, "SAFETY WALKWAY", (500, 645), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    # Warning signs
    cv2.rectangle(test_image, (500, 100), (600, 180), (255, 200, 0), -1)
    cv2.putText(test_image, "CAUTION", (510, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
    
    # Info overlay (subtle, bottom right)
    overlay = test_image.copy()
    cv2.rectangle(overlay, (1000, 600), (1250, 700), (0, 0, 0), -1)
    test_image = cv2.addWeighted(test_image, 0.8, overlay, 0.2, 0)
    
    cv2.putText(test_image, f"Frame {frame_number}", (1020, 640), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.putText(test_image, datetime.now().strftime("%H:%M:%S"), (1020, 670), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    cv2.putText(test_image, "DEMO MODE", (1020, 690), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)
    
    return Frame(
        image=test_image,
        frame_number=frame_number,
        source="demo",
        width=1280,
        height=720,
        timestamp=datetime.now()
    )


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def video_frame_loop():
    """Continuous video frame capture from uploaded file or camera."""
    global latest_frame, frame_counter, video_cap, video_file_path, video_playing, is_running
    
    frame_counter = 0
    paused_frame = None  # Store frame when paused
    video_ended = False  # Track if video has ended
    
    while True:
        try:
            # If we have a video file, use it
            if video_file_path and video_cap is not None:
                if video_playing:
                    # Video is playing - read next frame
                    ret, frame_bgr = video_cap.read()
                    if ret:
                        # Convert BGR to RGB
                        frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                        latest_frame = frame_rgb
                        paused_frame = frame_rgb  # Update paused frame
                        frame_counter += 1
                        video_ended = False  # Reset ended flag
                        time.sleep(0.033)  # ~30 FPS
                    else:
                        # Video ended - STOP and pause everything
                        if not video_ended:
                            video_ended = True
                            video_playing = False  # Auto-pause video
                            is_running = False  # Stop analysis to save tokens
                            print("[VIDEO] Video ended - auto-paused video and analysis")
                            
                            # Show "Video Ended" message on frame
                            if paused_frame is not None:
                                ended_frame = paused_frame.copy()
                                h, w = ended_frame.shape[:2]
                                cv2.rectangle(ended_frame, (w//4, h//2-30), (3*w//4, h//2+30), (0, 0, 0), -1)
                                cv2.putText(ended_frame, "Video Ended", (w//2-100, h//2),
                                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (255, 255, 255), 2)
                                cv2.putText(ended_frame, "Click Play to restart", (w//2-120, h//2+25),
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
                                latest_frame = ended_frame
                                paused_frame = ended_frame
                        time.sleep(0.1)
                else:
                    # Video is paused - keep showing the last frame
                    if paused_frame is not None:
                        latest_frame = paused_frame
                    time.sleep(0.1)  # Check pause status frequently
            else:
                # No video uploaded - show placeholder
                if latest_frame is None:
                    # Create a simple placeholder
                    placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
                    placeholder[:] = [40, 40, 45]  # Dark gray
                    cv2.putText(placeholder, "Upload a video to begin", (150, 220),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
                    cv2.putText(placeholder, "Click 'Upload Video' button", (120, 260),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (150, 150, 150), 2)
                    latest_frame = placeholder
                time.sleep(0.5)
        except Exception as e:
            print(f"Error in video loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)


def processing_loop():
    """Background processing loop - analyzes ACTUAL video frames."""
    global latest_frame, latest_stats, is_running, video_file_path, video_cap, video_playing
    
    print("[PROCESSING] Starting analysis loop...")
    
    # Initialize components
    vision_model = VisionModelFactory.create(config.vlm)
    risk_reasoner = RiskReasonerFactory.create(config.reasoning)
    event_aggregator = EventAggregator(config.aggregation)
    alert_manager = AlertManager(config.alert, config.system.output_dir)
    perf_monitor = PerformanceMonitor()
    
    processing_frame_number = 0
    last_processed_timestamp = None
    consecutive_no_video = 0
    
    while is_running:
        try:
            # Check if we have a REAL video uploaded
            has_real_video = video_file_path and video_cap is not None
            
            # Only analyze if we have a real video uploaded
            if not has_real_video:
                print("[PROCESSING] ⏳ Waiting for video upload...")
                time.sleep(1.0)
                continue
            
            # IMPORTANT: Only analyze when video is actually playing
            if not video_playing:
                print("[PROCESSING] ⏸ Video is paused - analysis paused")
                time.sleep(0.5)
                continue
            
            # Real video uploaded and playing - analyze it
            if latest_frame is None:
                print("[PROCESSING] ⏳ Waiting for video frames...")
                time.sleep(0.5)
                continue
            
            print("[PROCESSING] 📹 Analyzing uploaded video (playing)")
            
            consecutive_no_video = 0
            
            # Avoid processing the same frame multiple times
            current_time = time.time()
            if last_processed_timestamp and (current_time - last_processed_timestamp) < 1.5:
                time.sleep(0.5)
                continue
            
            # Create Frame object from the current frame (demo or real video)
            processing_frame_number += 1
            frame_source = video_file_path if has_real_video else "demo"
            current_frame = Frame(
                image=latest_frame.copy(),  # Use current frame (demo or real video)
                frame_number=processing_frame_number,
                source=frame_source,
                width=latest_frame.shape[1],
                height=latest_frame.shape[0],
                timestamp=datetime.now()
            )
            
            last_processed_timestamp = current_time
            
            print(f"[PROCESSING] 🔍 Analyzing frame {processing_frame_number} from video...")
            
            # Vision analysis on ACTUAL video frame
            print(f"[PROCESSING] 📸 Running vision analysis...")
            vision_analysis = vision_model.analyze_frame(current_frame)
            perf_monitor.record_vision_inference_time(vision_analysis.processing_time)
            print(f"[PROCESSING] ✅ Vision: {len(vision_analysis.detected_people)} people, {len(vision_analysis.hazards_visible)} hazards")
            
            # Risk reasoning
            print(f"[PROCESSING] 🧠 Assessing risks...")
            safety_events = risk_reasoner.assess_risks(vision_analysis)
            perf_monitor.record_frame_processed()
            print(f"[PROCESSING] ✅ Risk assessment: {len(safety_events)} events found")
            
            # Add to aggregator
            if safety_events:
                event_aggregator.add_events(safety_events)
                print(f"[PROCESSING] 📊 Added {len(safety_events)} events to aggregator")
                
                # Queue events for display
                for event in safety_events:
                    if not event_queue.full():
                        event_queue.put(event.to_dict())
                        print(f"[PROCESSING] 📋 Queued event: {event.title}")
                    
                    perf_monitor.record_event_detected()
                    
                    # Process alerts - only for HIGH/CRITICAL, and with better deduplication
                    if event.risk_level.value in ['HIGH', 'CRITICAL']:
                        alert = alert_manager.process_event(event)
                        if alert:
                            # Check if we already have a very similar alert in the queue
                            # This prevents duplicate alerts in the UI even if deduplication missed it
                            alert_dict = alert.to_dict()
                            is_duplicate = False
                            
                            # Quick check: if queue has similar title recently, skip
                            temp_check_queue = Queue()
                            while not alert_queue.empty():
                                existing = alert_queue.get()
                                temp_check_queue.put(existing)
                                # Check title similarity
                                from difflib import SequenceMatcher
                                title_sim = SequenceMatcher(None, 
                                    alert_dict['title'].lower()[:30], 
                                    existing.get('title', '').lower()[:30]).ratio()
                                if title_sim > 0.8:  # Very similar
                                    is_duplicate = True
                                    break
                            
                            # Put alerts back
                            while not temp_check_queue.empty():
                                alert_queue.put(temp_check_queue.get())
                            
                            if not is_duplicate and not alert_queue.full():
                                alert_queue.put(alert_dict)
                                perf_monitor.record_alert_generated()
                                print(f"[PROCESSING] 🚨 Generated alert: {alert.title}")
                            else:
                                print(f"[PROCESSING] ⏭️  Skipped duplicate alert: {alert.title}")
            else:
                print(f"[PROCESSING] ✅ No safety issues detected in this frame")
            
            # Update stats
            metrics = perf_monitor.get_metrics()
            latest_stats = {
                'frames_processed': metrics.frames_processed,
                'fps': round(metrics.frames_per_second, 2),
                'events_detected': metrics.events_detected,
                'alerts_generated': metrics.alerts_generated,
                'avg_latency': round(metrics.avg_end_to_end_latency * 1000, 0),
                'cpu_percent': round(metrics.cpu_usage_percent, 1),
                'memory_mb': round(metrics.memory_usage_mb, 0)
            }
            
        except Exception as e:
            print(f"Error in processing loop: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/frame')
def get_frame():
    """Get latest frame as base64."""
    try:
        if latest_frame is not None:
            frame_b64 = frame_to_base64(latest_frame)
            return jsonify({
                'frame': frame_b64, 
                'timestamp': datetime.now().isoformat(),
                'status': 'ok'
            })
        else:
            # Create placeholder if no video
            placeholder = np.zeros((480, 640, 3), dtype=np.uint8)
            placeholder[:] = [40, 40, 45]
            cv2.putText(placeholder, "Upload a video to begin", (150, 220),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
            frame_b64 = frame_to_base64(placeholder)
            return jsonify({
                'frame': frame_b64,
                'timestamp': datetime.now().isoformat(),
                'status': 'placeholder'
            })
    except Exception as e:
        return jsonify({'frame': None, 'error': str(e)}), 500


@app.route('/api/stats')
def get_stats():
    """Get system statistics."""
    stats = latest_stats.copy()
    stats['is_analyzing'] = is_running
    stats['has_video'] = video_file_path is not None
    return jsonify(stats)


@app.route('/api/alerts')
def get_alerts():
    """Get recent alerts."""
    alerts = []
    while not alert_queue.empty() and len(alerts) < 10:
        alerts.append(alert_queue.get())
    return jsonify(alerts)


@app.route('/api/events')
def get_events():
    """Get recent events."""
    events = []
    while not event_queue.empty() and len(events) < 20:
        events.append(event_queue.get())
    return jsonify(events)


@app.route('/api/start')
def start_processing():
    """Start processing - but only if video is playing."""
    global is_running, processing_thread, video_playing, video_file_path, video_cap
    
    # Check if video is uploaded
    if not video_file_path or video_cap is None:
        return jsonify({'status': 'error', 'message': 'Please upload a video first'}), 400
    
    # Check if video is playing
    if not video_playing:
        return jsonify({'status': 'error', 'message': 'Please start video playback first'}), 400
    
    if is_running:
        return jsonify({'status': 'already_running', 'video_playing': video_playing})
    
    is_running = True
    
    # Start processing thread if not already running
    if processing_thread is None or not processing_thread.is_alive():
        processing_thread = threading.Thread(target=processing_loop, daemon=True)
        processing_thread.start()
    
    return jsonify({'status': 'started', 'message': 'Analysis started', 'video_playing': video_playing})


@app.route('/api/stop')
def stop_processing():
    """Stop processing."""
    global is_running
    # Don't pause video when stopping analysis - they're separate controls
    is_running = False
    return jsonify({'status': 'stopped'})


@app.route('/api/upload', methods=['POST'])
def upload_video():
    """Handle video file upload."""
    global video_file_path, video_cap, video_playing, latest_frame
    
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['video']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Allowed: mp4, avi, mov, mkv, webm'}), 400
        
        filename = secure_filename(file.filename)
        filepath = UPLOAD_FOLDER / filename
        
        # Save file
        file.save(str(filepath))
        
        # Close existing video if any
        if video_cap is not None:
            video_cap.release()
        
        # Open new video
        new_cap = cv2.VideoCapture(str(filepath))
        
        if not new_cap.isOpened():
            return jsonify({'error': 'Failed to open video file. Please check file format.'}), 400
        
        # Update globals
        video_cap = new_cap
        video_file_path = str(filepath)
        video_playing = False  # Don't auto-play - let user control it
        
        # Get video info
        fps = video_cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = frame_count / fps if fps > 0 else 0
        
        # Read first frame immediately
        ret, frame_bgr = video_cap.read()
        if ret:
            latest_frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)  # Reset to start
        
        return jsonify({
            'status': 'success',
            'filename': filename,
            'fps': fps,
            'frame_count': frame_count,
            'duration': duration,
            'message': 'Video loaded successfully!'
        })
    
    except Exception as e:
        import traceback
        error_msg = str(e)
        print(f"[UPLOAD ERROR] {error_msg}")
        traceback.print_exc()
        return jsonify({'error': f'Upload failed: {error_msg}'}), 500


@app.route('/api/video/status')
def video_status():
    """Get current video status."""
    global video_file_path, video_cap, video_playing
    
    if video_file_path and video_cap is not None:
        current_frame = int(video_cap.get(cv2.CAP_PROP_POS_FRAMES))
        total_frames = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = video_cap.get(cv2.CAP_PROP_FPS)
        
        return jsonify({
            'has_video': True,
            'filename': Path(video_file_path).name,
            'current_frame': current_frame,
            'total_frames': total_frames,
            'fps': fps,
            'progress': (current_frame / total_frames * 100) if total_frames > 0 else 0,
            'playing': video_playing
        })
    
    return jsonify({'has_video': False, 'playing': video_playing})


@app.route('/api/video/play', methods=['POST'])
def video_play_control():
    """Control video playback (play/pause)."""
    global video_playing, is_running, video_cap
    
    data = request.get_json()
    if 'play' in data:
        play = bool(data['play'])
        
        # If starting playback, check if video ended and restart if needed
        if play and video_cap is not None:
            current_frame = int(video_cap.get(cv2.CAP_PROP_POS_FRAMES))
            total_frames = int(video_cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # If at end, restart from beginning
            if current_frame >= total_frames - 1:
                video_cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                print("[VIDEO] Restarted from beginning")
        
        video_playing = play
        
        # If video is paused, automatically pause analysis too
        if not video_playing and is_running:
            is_running = False
            return jsonify({
                'status': 'success', 
                'playing': video_playing,
                'analysis_paused': True,
                'message': 'Video paused - analysis automatically paused'
            })
        
        return jsonify({'status': 'success', 'playing': video_playing})
    
    return jsonify({'error': 'Invalid request'}), 400


@app.route('/api/video/remove', methods=['POST'])
def remove_video():
    """Remove uploaded video and clear all analysis data."""
    global video_file_path, video_cap, video_playing, is_running, latest_frame
    global alert_queue, event_queue, latest_stats
    
    # Stop analysis if running
    is_running = False
    
    # Close video capture
    if video_cap is not None:
        video_cap.release()
        video_cap = None
    
    # Clear video file path
    if video_file_path:
        # Optionally delete the file (or just clear reference)
        try:
            video_path = Path(video_file_path)
            if video_path.exists():
                video_path.unlink()  # Delete the file
        except Exception as e:
            print(f"[WARNING] Could not delete video file: {e}")
    
    video_file_path = None
    video_playing = False
    latest_frame = None
    
    # Clear all queues and stats
    while not alert_queue.empty():
        alert_queue.get()
    while not event_queue.empty():
        event_queue.get()
    
    latest_stats = {
        'frames_processed': 0,
        'fps': 0.0,
        'events_detected': 0,
        'alerts_generated': 0
    }
    
    return jsonify({
        'status': 'success',
        'message': 'Video removed and analysis data cleared'
    })


def create_html_template():
    """Create HTML dashboard template."""
    template_dir = Path(__file__).parent / 'templates'
    template_dir.mkdir(exist_ok=True)
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Factory Safety Monitoring Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
            color: white;
        }
        
        .header h1 {
            font-size: 36px;
            font-weight: 700;
            margin-bottom: 8px;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 16px;
            opacity: 0.95;
        }
        
        .grid {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 25px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.25);
        }
        
        .card h2 {
            color: #1f2937;
            font-size: 22px;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 600;
        }
        
        .status-indicator {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #10b981;
            animation: pulse 2s infinite;
            box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.7; transform: scale(1.1); }
        }
        
        #videoFrame {
            width: 100%;
            border-radius: 12px;
            background: #1f2937;
            min-height: 450px;
            object-fit: contain;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin-top: 15px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            border-radius: 12px;
            color: white;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: 700;
            margin: 8px 0;
        }
        
        .stat-label {
            font-size: 13px;
            opacity: 0.95;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }
        
        .alert-item {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 14px;
            margin-bottom: 12px;
            border-radius: 8px;
            transition: transform 0.2s;
        }
        
        .alert-item:hover {
            transform: translateX(4px);
        }
        
        .alert-item.critical {
            background: #fee2e2;
            border-left-color: #ef4444;
        }
        
        .alert-item.high {
            background: #fed7aa;
            border-left-color: #f97316;
        }
        
        .alert-title {
            font-weight: 600;
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 14px;
        }
        
        .alert-time {
            font-size: 11px;
            color: #666;
        }
        
        .event-item {
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
            transition: background 0.2s;
        }
        
        .event-item:hover {
            background: #f9fafb;
        }
        
        .event-item:last-child {
            border-bottom: none;
        }
        
        .risk-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 10px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-right: 8px;
        }
        
        .risk-critical { background: #fee2e2; color: #991b1b; }
        .risk-high { background: #fed7aa; color: #9a3412; }
        .risk-medium { background: #fef3c7; color: #92400e; }
        .risk-low { background: #d1fae5; color: #065f46; }
        
        .button-group {
            display: flex;
            gap: 12px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            flex: 1;
            min-width: 140px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.2);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-upload {
            background: linear-gradient(135deg, #10b981 0%, #059669 100%);
            color: white;
        }
        
        .btn-upload:hover:not(:disabled) {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
        }
        
        .btn-analysis {
            background: linear-gradient(135deg, #667eea 0%, #5568d3 100%);
            color: white;
        }
        
        .btn-analysis:hover:not(:disabled) {
            background: linear-gradient(135deg, #5568d3 0%, #4c51bf 100%);
        }
        
        .btn-analysis.stop {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }
        
        .btn-analysis.stop:hover:not(:disabled) {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
        }
        
        .btn-video {
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            color: white;
        }
        
        .btn-video:hover:not(:disabled) {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        }
        
        .btn-video.pause {
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
        }
        
        .btn-video.pause:hover:not(:disabled) {
            background: linear-gradient(135deg, #d97706 0%, #b45309 100%);
        }
        
        .upload-section {
            margin: 20px 0;
            padding: 15px;
            background: #f9fafb;
            border-radius: 10px;
            border: 2px dashed #d1d5db;
        }
        
        .upload-section.has-video {
            border-color: #10b981;
            background: #ecfdf5;
        }
        
        #videoStatus {
            display: block;
            margin-top: 10px;
            color: #059669;
            font-size: 13px;
            font-weight: 500;
        }
        
        .alerts-container, .events-container {
            max-height: 450px;
            overflow-y: auto;
            padding-right: 5px;
        }
        
        .alerts-container::-webkit-scrollbar,
        .events-container::-webkit-scrollbar {
            width: 6px;
        }
        
        .alerts-container::-webkit-scrollbar-track,
        .events-container::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        
        .alerts-container::-webkit-scrollbar-thumb,
        .events-container::-webkit-scrollbar-thumb {
            background: #cbd5e1;
            border-radius: 10px;
        }
        
        .empty-state {
            text-align: center;
            padding: 50px 20px;
            color: #9ca3af;
            font-size: 14px;
        }
        
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏭 Factory Safety Monitoring System</h1>
            <p>Real-Time Vision-Language Model Based Safety Analysis</p>
        </div>
        
        <div class="grid">
            <!-- Left column: Video feed -->
            <div>
                <div class="card">
                    <h2>
                        <span class="status-indicator"></span>
                        Live Monitoring
                    </h2>
                    <img id="videoFrame" src="" alt="Video feed">
                    <div class="upload-section" id="uploadSection">
                        <input type="file" id="videoUpload" accept="video/*" style="display: none;" onchange="uploadVideo(this.files[0])">
                        <div style="display: flex; gap: 10px; align-items: center;">
                            <button class="btn btn-upload" onclick="document.getElementById('videoUpload').click()">
                                📁 Upload Video
                            </button>
                            <button class="btn" id="removeVideoBtn" onclick="removeVideo()" style="background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: white; display: none;">
                                🗑️ Remove Video
                            </button>
                        </div>
                        <span id="videoStatus"></span>
                    </div>
                    <div class="button-group">
                        <button class="btn btn-analysis" onclick="toggleAnalysis()" id="analysisBtn">▶ Start Analysis</button>
                        <button class="btn btn-video" onclick="toggleVideoPlayback()" id="playPauseBtn">▶ Play Video</button>
                    </div>
                </div>
                
                <div class="card" style="margin-top: 20px;">
                    <h2>📊 System Statistics</h2>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-label">Frames Processed</div>
                            <div class="stat-value" id="framesProcessed">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Processing Rate</div>
                            <div class="stat-value" id="fps">0.0</div>
                            <div class="stat-label">FPS</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Events Detected</div>
                            <div class="stat-value" id="eventsDetected">0</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-label">Alerts Generated</div>
                            <div class="stat-value" id="alertsGenerated">0</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Right column: Alerts and Events -->
            <div>
                <div class="card">
                    <h2>🚨 Recent Alerts</h2>
                    <div class="alerts-container" id="alertsContainer">
                        <div class="empty-state">
                            <p>No alerts yet. System will display safety alerts here.</p>
                        </div>
                    </div>
                </div>
                
                <div class="card" style="margin-top: 20px;">
                    <h2>📋 Safety Events</h2>
                    <div class="events-container" id="eventsContainer">
                        <div class="empty-state">
                            <p>No events yet. Detected safety events will appear here.</p>
                        </div>
                    </div>
                </div>
                
            </div>
        </div>
    </div>
    
    <script>
        let isRunning = false;
        
        let videoPlaying = true;
        
        function toggleAnalysis() {
            const btn = document.getElementById('analysisBtn');
            if (isRunning) {
                // Stop analysis
                fetch('/api/stop')
                    .then(r => r.json())
                    .then(data => {
                        isRunning = false;
                        btn.textContent = '▶ Start Analysis';
                        btn.classList.remove('stop');
                        console.log('Stopped analysis');
                    })
                    .catch(err => {
                        console.error('Stop error:', err);
                        alert('Failed to stop: ' + err.message);
                    });
            } else {
                // Start analysis - but check if video is playing first
                if (!videoPlaying) {
                    alert('⚠️ Please start video playback first!');
                    return;
                }
                
                fetch('/api/start')
                    .then(r => {
                        if (!r.ok) {
                            return r.json().then(data => {
                                throw new Error(data.message || 'Failed to start');
                            });
                        }
                        return r.json();
                    })
                    .then(data => {
                        isRunning = true;
                        btn.textContent = '⏹ Stop Analysis';
                        btn.classList.add('stop');
                        console.log('Started analysis');
                    })
                    .catch(err => {
                        console.error('Start error:', err);
                        alert(err.message || 'Failed to start: ' + err.message);
                    });
            }
        }
        
        function toggleVideoPlayback() {
            videoPlaying = !videoPlaying;
            fetch('/api/video/play', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({play: videoPlaying})
            })
            .then(r => {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(data => {
                if (data.status === 'success') {
                    const btn = document.getElementById('playPauseBtn');
                    const analysisBtn = document.getElementById('analysisBtn');
                    
                    if (btn) {
                        if (videoPlaying) {
                            btn.textContent = '⏸ Pause Video';
                            btn.classList.add('pause');
                        } else {
                            btn.textContent = '▶ Play Video';
                            btn.classList.remove('pause');
                        }
                    }
                    
                    // If video was paused, analysis was automatically paused
                    if (data.analysis_paused) {
                        isRunning = false;
                        if (analysisBtn) {
                            analysisBtn.textContent = '▶ Start Analysis';
                            analysisBtn.classList.remove('stop');
                        }
                        console.log('Analysis automatically paused because video paused');
                    }
                    
                    console.log('Video playback:', videoPlaying ? 'playing' : 'paused');
                } else {
                    throw new Error(data.error || 'Failed to toggle playback');
                }
            })
            .catch(err => {
                console.error('Playback toggle error:', err);
                alert('Failed to toggle video: ' + err.message);
                // Revert state on error
                videoPlaying = !videoPlaying;
            });
        }
        
        // Check if video ended and update UI
        function checkVideoEnded() {
            fetch('/api/video/status')
                .then(r => r.json())
                .then(data => {
                    if (data.has_video && !data.playing) {
                        // Check if we're at the end
                        const current = data.current_frame || 0;
                        const total = data.total_frames || 0;
                        
                        if (current >= total - 1 && total > 0) {
                            // Video ended - update button
                            const btn = document.getElementById('playPauseBtn');
                            const analysisBtn = document.getElementById('analysisBtn');
                            
                            if (btn) {
                                btn.textContent = '▶ Play Video';
                                btn.classList.remove('pause');
                            }
                            
                            // Make sure analysis is stopped
                            if (isRunning) {
                                isRunning = false;
                                if (analysisBtn) {
                                    analysisBtn.textContent = '▶ Start Analysis';
                                    analysisBtn.classList.remove('stop');
                                }
                            }
                            
                            videoPlaying = false;
                        }
                    }
                })
                .catch(err => console.error('Error checking video status:', err));
        }
        
        function updateFrame() {
            fetch('/api/frame')
                .then(r => r.json())
                .then(data => {
                    if (data.frame && data.frame.length > 0) {
                        const img = document.getElementById('videoFrame');
                        img.src = data.frame;
                        img.style.display = 'block';
                    } else {
                        console.log('No frame data received');
                    }
                })
                .catch(error => {
                    console.error('Error fetching frame:', error);
                });
        }
        
        function updateStats() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('framesProcessed').textContent = data.frames_processed || 0;
                    document.getElementById('fps').textContent = (data.fps || 0).toFixed(2);
                    document.getElementById('eventsDetected').textContent = data.events_detected || 0;
                    document.getElementById('alertsGenerated').textContent = data.alerts_generated || 0;
                    
                    // Show analysis status
                    const statusIndicator = document.querySelector('.status-indicator');
                    if (data.is_analyzing) {
                        if (statusIndicator) statusIndicator.style.background = '#10b981'; // Green
                    } else {
                        if (statusIndicator) statusIndicator.style.background = '#9ca3af'; // Gray
                    }
                });
        }
        
        function updateAlerts() {
            fetch('/api/alerts')
                .then(r => r.json())
                .then(alerts => {
                    if (alerts.length > 0) {
                        const container = document.getElementById('alertsContainer');
                        alerts.forEach(alert => {
                            const alertDiv = document.createElement('div');
                            alertDiv.className = `alert-item ${alert.priority}`;
                            alertDiv.innerHTML = `
                                <div class="alert-title">
                                    <span>${alert.title}</span>
                                    <span class="alert-time">${new Date(alert.timestamp).toLocaleTimeString()}</span>
                                </div>
                                <div>${alert.message}</div>
                            `;
                            container.insertBefore(alertDiv, container.firstChild);
                            
                            // Remove empty state
                            const emptyState = container.querySelector('.empty-state');
                            if (emptyState) emptyState.remove();
                            
                            // Keep only last 10
                            while (container.children.length > 10) {
                                container.removeChild(container.lastChild);
                            }
                        });
                    }
                });
        }
        
        function updateEvents() {
            fetch('/api/events')
                .then(r => r.json())
                .then(events => {
                    const container = document.getElementById('eventsContainer');
                    
                    if (events.length > 0) {
                        events.forEach(event => {
                            // Check if event already displayed (avoid duplicates)
                            const eventId = event.event_id || event.title + event.timestamp;
                            if (container.querySelector(`[data-event-id="${eventId}"]`)) {
                                return; // Already displayed
                            }
                            
                            const eventDiv = document.createElement('div');
                            eventDiv.className = 'event-item';
                            eventDiv.setAttribute('data-event-id', eventId);
                            eventDiv.innerHTML = `
                                <div>
                                    <span class="risk-badge risk-${event.risk_level.toLowerCase()}">${event.risk_level}</span>
                                    <strong>${event.title}</strong>
                                </div>
                                <div style="font-size: 12px; color: #666; margin-top: 3px;">
                                    ${event.description || ''}
                                </div>
                                <div style="font-size: 11px; color: #999; margin-top: 2px;">
                                    ${new Date(event.timestamp).toLocaleTimeString()}
                                </div>
                            `;
                            container.insertBefore(eventDiv, container.firstChild);
                            
                            // Remove empty state
                            const emptyState = container.querySelector('.empty-state');
                            if (emptyState) emptyState.remove();
                            
                            // Keep only last 20
                            while (container.children.length > 20) {
                                container.removeChild(container.lastChild);
                            }
                        });
                    } else {
                        // Show message if analysis is running but no events yet
                        const emptyState = container.querySelector('.empty-state');
                        if (!emptyState && container.children.length === 0) {
                            const msg = document.createElement('div');
                            msg.className = 'empty-state';
                            msg.textContent = 'Analysis running... No events detected yet.';
                            container.appendChild(msg);
                        }
                    }
                })
                .catch(err => console.error('Error fetching events:', err));
        }
        
        function uploadVideo(file) {
            if (!file) return;
            
            const uploadSection = document.getElementById('uploadSection');
            const statusSpan = document.getElementById('videoStatus');
            const removeBtn = document.getElementById('removeVideoBtn');
            const formData = new FormData();
            formData.append('video', file);
            
            statusSpan.textContent = 'Uploading...';
            
            fetch('/api/upload', {
                method: 'POST',
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    statusSpan.textContent = `✅ Loaded: ${data.filename} (${data.duration.toFixed(1)}s)`;
                    uploadSection.classList.add('has-video');
                    if (removeBtn) removeBtn.style.display = 'block';
                    console.log('Video uploaded:', data);
                } else {
                    statusSpan.textContent = `❌ Error: ${data.error || 'Upload failed'}`;
                    uploadSection.classList.remove('has-video');
                    if (removeBtn) removeBtn.style.display = 'none';
                }
            })
            .catch(error => {
                statusSpan.textContent = `❌ Upload error: ${error.message}`;
                uploadSection.classList.remove('has-video');
                if (removeBtn) removeBtn.style.display = 'none';
                console.error('Upload error:', error);
            });
        }
        
        function removeVideo() {
            if (!confirm('Remove video and clear all analysis data?')) {
                return;
            }
            
            fetch('/api/video/remove', {
                method: 'POST'
            })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    // Reset UI
                    const uploadSection = document.getElementById('uploadSection');
                    const statusSpan = document.getElementById('videoStatus');
                    const removeBtn = document.getElementById('removeVideoBtn');
                    const analysisBtn = document.getElementById('analysisBtn');
                    const playPauseBtn = document.getElementById('playPauseBtn');
                    const videoFrame = document.getElementById('videoFrame');
                    
                    // Clear video display
                    if (videoFrame) {
                        videoFrame.src = '';
                    }
                    
                    // Reset upload section
                    uploadSection.classList.remove('has-video');
                    statusSpan.textContent = '';
                    if (removeBtn) removeBtn.style.display = 'none';
                    
                    // Reset buttons
                    if (analysisBtn) {
                        analysisBtn.textContent = '▶ Start Analysis';
                        analysisBtn.classList.remove('stop');
                    }
                    if (playPauseBtn) {
                        playPauseBtn.textContent = '▶ Play Video';
                        playPauseBtn.classList.remove('pause');
                    }
                    
                    // Clear stats
                    document.getElementById('framesProcessed').textContent = '0';
                    document.getElementById('fps').textContent = '0.0';
                    document.getElementById('eventsDetected').textContent = '0';
                    document.getElementById('alertsGenerated').textContent = '0';
                    
                    // Clear alerts and events
                    const alertsContainer = document.getElementById('alertsContainer');
                    const eventsContainer = document.getElementById('eventsContainer');
                    if (alertsContainer) {
                        alertsContainer.innerHTML = '<div class="empty-state"><p>No alerts yet. System will display safety alerts here.</p></div>';
                    }
                    if (eventsContainer) {
                        eventsContainer.innerHTML = '<div class="empty-state"><p>No events yet. Detected safety events will appear here.</p></div>';
                    }
                    
                    // Reset state
                    isRunning = false;
                    videoPlaying = false;
                    
                    console.log('Video removed and data cleared');
                } else {
                    alert('Failed to remove video: ' + (data.error || 'Unknown error'));
                }
            })
            .catch(error => {
                console.error('Remove video error:', error);
                alert('Failed to remove video: ' + error.message);
            });
        }
        
        function checkVideoStatus() {
            fetch('/api/video/status')
                .then(r => r.json())
                .then(data => {
                    const uploadSection = document.getElementById('uploadSection');
                    const statusEl = document.getElementById('videoStatus');
                    const removeBtn = document.getElementById('removeVideoBtn');
                    
                    if (data.has_video) {
                        uploadSection.classList.add('has-video');
                        if (removeBtn) removeBtn.style.display = 'block';
                        if (statusEl && !statusEl.textContent.includes('✅')) {
                            statusEl.textContent = `📹 Playing: ${data.filename}`;
                        }
                    } else {
                        uploadSection.classList.remove('has-video');
                        if (removeBtn) removeBtn.style.display = 'none';
                    }
                });
        }
        
        // Clear everything on page load
        window.addEventListener('load', function() {
            // Reset all state
            isRunning = false;
            videoPlaying = false;
            
            // Clear stats
            document.getElementById('framesProcessed').textContent = '0';
            document.getElementById('fps').textContent = '0.0';
            document.getElementById('eventsDetected').textContent = '0';
            document.getElementById('alertsGenerated').textContent = '0';
            
            // Clear alerts and events
            const alertsContainer = document.getElementById('alertsContainer');
            const eventsContainer = document.getElementById('eventsContainer');
            if (alertsContainer && alertsContainer.children.length === 0) {
                alertsContainer.innerHTML = '<div class="empty-state"><p>No alerts yet. System will display safety alerts here.</p></div>';
            }
            if (eventsContainer && eventsContainer.children.length === 0) {
                eventsContainer.innerHTML = '<div class="empty-state"><p>No events yet. Detected safety events will appear here.</p></div>';
            }
            
            // Hide remove button initially
            const removeBtn = document.getElementById('removeVideoBtn');
            if (removeBtn) removeBtn.style.display = 'none';
            
            // Check if there's a video on load
            checkVideoStatus();
        });
        
        // Update intervals
        setInterval(updateFrame, 1000);
        setInterval(updateStats, 1000);
        setInterval(updateAlerts, 1000);
        setInterval(updateEvents, 1000);
        setInterval(checkVideoStatus, 2000);
        setInterval(checkVideoEnded, 1000);  // Check if video ended
        
        // Don't auto-start - user must click button
    </script>
</body>
</html>"""
    
    with open(template_dir / 'dashboard.html', 'w') as f:
        f.write(html_content)


if __name__ == '__main__':
    # Create HTML template
    create_html_template()
    
    # Start video frame loop (always runs)
    video_thread = threading.Thread(target=video_frame_loop, daemon=True)
    video_thread.start()
    
    # Give it a moment to start
    time.sleep(0.5)
    
    print("\n" + "="*70)
    print("🌐 Factory Safety Monitoring Web Dashboard")
    print("="*70)
    print("\n📍 Starting web server...")
    print("\n🔗 Open your browser to: http://localhost:8080")
    print("\n✅ Upload a video to begin analysis")
    print("⏹  Press Ctrl+C to stop the server\n")
    print("="*70 + "\n")
    
    # Get port from environment (for deployment) or use 8080
    port = int(os.getenv('PORT', 8080))
    
    # Run Flask app
    # In production, use gunicorn instead: gunicorn -w 4 -b 0.0.0.0:PORT web_interface:app
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

# Factory Safety Monitoring - Quick Start Guide

Get up and running in 5 minutes.

---

## Prerequisites

- Python 3.9 or higher
- Webcam or video file
- (Optional) OpenAI API key

---

## Installation

```bash
# Navigate to project directory
cd drowsiness_detection

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## Configuration Options

### Option 1: Run with Mock Mode (No API Key)

Perfect for testing the system without API costs.

```bash
# Just run it - system auto-detects missing API key and uses mock mode
python app.py
```

Expected output:
```
⚠ Running in MOCK mode (no API key)
```

### Option 2: Run with OpenAI API

For real Vision-Language Model analysis.

```bash
# Set your API key
export OPENAI_API_KEY="your_key_here"

# Run the system
python app.py
```

Or create `.env` file:
```bash
# Copy example
cp env.example .env

# Edit .env and add your key
OPENAI_API_KEY=your_key_here

# Run
python app.py
```

---

## Video Source Configuration

### Webcam (Default)

No configuration needed - system uses webcam automatically.

### Video File

Edit `config.py`:
```python
# Change this line (around line 160)
config.video.source = "path/to/your/video.mp4"
```

---

## Understanding the Output

### Console Output

```
════════════════════════════════════════════════════════════════════════════════
[HIGH ALERT] 2025-12-17 14:23:47
PPE Violation: Missing hard hat
Worker at near forklift is missing required PPE: hard hat

Recommended Actions:
  • Ensure worker dons hard hat
  • Verify PPE compliance before allowing work to continue
════════════════════════════════════════════════════════════════════════════════
```

- **Priority**: LOW | NORMAL | HIGH | CRITICAL
- **Title**: Brief description
- **Description**: Detailed explanation
- **Actions**: Recommended steps

### Status Reports

Printed every 30 seconds:
```
System Status - Runtime: 120s
════════════════════════════════════════════════════════════════════════════════
Frames Analyzed: 48 (0.40 FPS)
Events Detected: 5
Alerts Generated: 2
...
```

---

## Testing Individual Components

Each module can be tested independently:

```bash
# Test video capture and frame sampling
python video_stream.py

# Test vision analysis (mock mode)
python vision_model.py

# Test risk reasoning (mock mode)
python risk_reasoner.py

# Test event aggregation
python event_aggregator.py

# Test alert management
python alert_manager.py
```

---

## Tuning Parameters

### Increase/Decrease Sensitivity

Edit `config.py`:

```python
# More sensitive (detect smaller changes)
config.video.scene_change_threshold = 10.0  # Default: 15.0

# Less sensitive (only major changes)
config.video.scene_change_threshold = 25.0
```

### Adjust Processing Rate

```python
# Faster processing (more frames)
config.video.target_fps = 3.0  # Default: 2.0
config.video.min_frame_interval = 0.3  # Default: 0.5

# Slower processing (fewer frames, lower cost)
config.video.target_fps = 1.0
config.video.min_frame_interval = 1.0
```

### Change Alert Cooldown

```python
# More frequent alerts
config.alert.alert_cooldown = 30.0  # Default: 60.0

# Less frequent alerts
config.alert.alert_cooldown = 120.0
```

---

## Common Issues

### Issue: "Failed to open video source"

**Cause**: Camera not accessible or video file not found

**Solution**:
```bash
# Check camera access
ls /dev/video*  # Linux
# or
system_profiler SPCameraDataType  # macOS

# Verify video file path
ls path/to/video.mp4
```

### Issue: "API key not found"

**Cause**: Environment variable not set

**Solution**:
```bash
# Check if set
echo $OPENAI_API_KEY

# Set temporarily
export OPENAI_API_KEY="your_key"

# Or use .env file (persistent)
```

### Issue: Slow performance

**Cause**: API latency or network issues

**Solutions**:
- Increase `min_frame_interval` to process fewer frames
- Use smaller model (GPT-4o-mini) - edit `config.py`:
  ```python
  config.vlm.model_name = "gpt-4o-mini"
  ```
- Check network connection

### Issue: Too many/few alerts

**Solutions**:
- Adjust `scene_change_threshold` (higher = fewer frames = fewer alerts)
- Adjust `min_confidence` in risk reasoner (higher = fewer alerts)
- Adjust alert cooldown period

---

## Performance Expectations

### Mock Mode
- Processing rate: ~1-2 FPS
- Latency: 0.5s per frame
- CPU: 10-15%
- Memory: 150-200 MB

### API Mode (OpenAI)
- Processing rate: ~0.3-0.4 FPS
- Latency: 2.5-4s per frame
- CPU: 15-25%
- Memory: 200-300 MB
- API cost: ~$0.015 per frame

### Webcam Sampling
- Typical sampling rate: 0.5-2 FPS (adaptive)
- Scene changes detected: 5-15% of frames
- Coverage: Continuous, no gaps

---

## Next Steps

1. **Test with different video sources**: Try various factory videos to see performance
2. **Tune parameters**: Adjust thresholds for your specific environment
3. **Review documentation**:
   - `README.md` - Comprehensive system overview
   - `TECHNICAL_EXPLANATION.md` - Deep technical dive
4. **Extend the system**: Add custom safety rules, integrate with other systems
5. **Deploy to production**: Follow Phase 2/3 architecture in technical docs

---

## Stopping the System

Press `Ctrl+C` to gracefully shutdown.

The system will:
- Close video stream
- Perform final aggregation
- Print statistics
- Save logs

---

## Output Files

After running, check the `output/` directory:

```
output/
├── alerts/
│   └── alert_log.jsonl     # All generated alerts
└── system.log              # System logs
```

---

## Getting Help

1. **Check logs**: `output/system.log`
2. **Read documentation**: `README.md` and `TECHNICAL_EXPLANATION.md`
3. **Test components**: Run individual modules to isolate issues
4. **Enable debug logging**: Edit `config.py`:
   ```python
   config.system.log_level = "DEBUG"
   ```

---

**You're all set! Run `python app.py` to start monitoring.**

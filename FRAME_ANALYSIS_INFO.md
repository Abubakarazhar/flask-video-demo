# 📊 Frame Analysis Rate Information

## Current Settings

### Analysis Frequency:
- **1 frame every 1.5 seconds** (minimum interval)
- **~0.67 frames per second** (FPS)
- **~40 frames per minute**
- **~2,400 frames per hour**

### Configuration Details:

From `config.py`:
- `target_fps: 2.0` - Target processing rate (not currently used in web interface)
- `min_frame_interval: 0.5` seconds - Minimum time between frames
- `max_frame_interval: 5.0` seconds - Maximum time between frames

From `processing_loop()`:
- **Actual rate: 1 frame every 1.5 seconds** (hardcoded in line 318)
- This prevents processing the same frame multiple times

## Example Calculations:

### For a 30-second video:
- **20 frames analyzed** (30 seconds ÷ 1.5 seconds per frame)
- **~$0.20 - $0.40** in API costs (if using OpenAI GPT-4o)
- **~$0.00** in mock mode (free)

### For a 5-minute video:
- **200 frames analyzed** (300 seconds ÷ 1.5 seconds per frame)
- **~$2.00 - $4.00** in API costs (if using OpenAI GPT-4o)
- **~$0.00** in mock mode (free)

### For a 1-hour video:
- **2,400 frames analyzed** (3600 seconds ÷ 1.5 seconds per frame)
- **~$24.00 - $48.00** in API costs (if using OpenAI GPT-4o)
- **~$0.00** in mock mode (free)

## Cost Estimation (OpenAI GPT-4o):

- **Input (image)**: ~$0.01 per frame
- **Output (text)**: ~$0.01 per frame
- **Total**: ~$0.02 per frame analyzed

**Note**: Mock mode is FREE and uses basic computer vision instead of API calls.

## How to Change the Rate:

To analyze more or fewer frames, modify line 318 in `web_interface.py`:

```python
# Current: 1.5 seconds between frames
if last_processed_timestamp and (current_time - last_processed_timestamp) < 1.5:
    time.sleep(0.5)
    continue

# To analyze every 3 seconds (slower, cheaper):
if last_processed_timestamp and (current_time - last_processed_timestamp) < 3.0:

# To analyze every 0.5 seconds (faster, more expensive):
if last_processed_timestamp and (current_time - last_processed_timestamp) < 0.5:
```

## Recommendations:

- **For testing**: Use mock mode (free, no API costs)
- **For production**: 1.5 seconds is a good balance between coverage and cost
- **For high-risk areas**: Consider 0.5-1.0 seconds for faster detection
- **For low-risk monitoring**: 3-5 seconds saves costs while still catching issues

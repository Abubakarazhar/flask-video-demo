# 🌐 Web Dashboard Guide

## Quick Start

```bash
# Start the web interface
cd /Users/abubakarsmacbook/Downloads/factory_safety_monitoring
python3 web_interface.py
```

Then open: **http://localhost:5000**

---

## Features

### 🎥 **Live Video Feed**
- Real-time frame display
- Updates every second
- Test frames with frame counter
- Can be replaced with actual camera feed

### 📊 **System Statistics**
Real-time metrics displayed in gradient cards:
- **Frames Processed**: Total frames analyzed
- **Processing Rate**: Frames per second (FPS)
- **Events Detected**: Safety events identified
- **Alerts Generated**: Critical alerts sent

### 🚨 **Alert Feed**
- Color-coded by severity:
  - 🔴 **CRITICAL**: Red background
  - 🟠 **HIGH**: Orange background
  - 🟡 **MEDIUM**: Yellow background
  - 🟢 **LOW**: Green background
- Shows timestamp
- Auto-scrolling
- Keeps last 10 alerts

### 📋 **Event Timeline**
- All safety events
- Risk level badges
- Chronological order
- Keeps last 20 events

---

## Controls

### Start Button ▶
- Starts the processing loop
- Begins frame analysis
- Activates all monitoring

### Stop Button ⏹
- Stops processing
- Freezes current state
- Can be restarted anytime

---

## Technical Details

### Architecture
```
Browser (Frontend)
    ↕ AJAX (JSON)
Flask Server (Backend)
    ↕
Processing Thread
    ├── Vision Model
    ├── Risk Reasoner
    ├── Event Aggregator
    └── Alert Manager
```

### API Endpoints

- `GET /` - Dashboard page
- `GET /api/frame` - Latest frame (base64)
- `GET /api/stats` - System statistics
- `GET /api/alerts` - Recent alerts
- `GET /api/events` - Recent events
- `GET /api/start` - Start processing
- `GET /api/stop` - Stop processing

### Update Frequency
- Frame: 1 second
- Stats: 1 second
- Alerts: 1 second
- Events: 1 second

---

## Customization

### Change Port
Edit `web_interface.py`, line at bottom:
```python
app.run(host='0.0.0.0', port=5000)  # Change 5000 to your port
```

### Connect Real Camera
Replace `create_test_frame()` with actual camera capture:
```python
# In processing_loop()
cap = cv2.VideoCapture(0)  # Webcam
ret, frame_bgr = cap.read()
frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
```

### Customize Colors
Edit the `<style>` section in `templates/dashboard.html`:
```css
background: linear-gradient(135deg, #YOUR_COLOR 0%, #YOUR_COLOR2 100%);
```

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000

# Kill it
kill -9 <PID>

# Or change port in web_interface.py
```

### Server Not Starting
```bash
# Check if Flask is installed
pip3 list | grep -i flask

# Reinstall if needed
pip3 install flask flask-cors
```

### No Alerts Appearing
- System is in MOCK mode (generates fake data)
- Alerts trigger on HIGH/CRITICAL events only
- Check console output for errors

---

## Production Deployment

For production use:

1. **Use Production Server**
   ```bash
   pip3 install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 web_interface:app
   ```

2. **Add Authentication**
   - Implement login system
   - Use Flask-Login
   - Add session management

3. **HTTPS**
   - Use nginx reverse proxy
   - Add SSL certificate
   - Force HTTPS redirect

4. **Database**
   - Store alerts in PostgreSQL
   - Historical analytics
   - Event replay

5. **WebSocket**
   - Use Flask-SocketIO
   - True real-time updates
   - Lower latency

---

## Screenshots

### Main Dashboard
- Gradient purple background
- White cards with shadows
- Real-time counters
- Color-coded alerts

### Alert Feed
- Time-stamped entries
- Border colors by severity
- Scrollable list
- Auto-updates

### Event Timeline
- Risk badges
- Event titles
- Timestamps
- Clean layout

---

## Stopping the Server

```bash
# Graceful shutdown
# Press Ctrl+C in terminal

# Force kill
pkill -f web_interface.py

# Or if you know PID
kill $(cat web_server.pid)
```

---

## Next Steps

1. **Connect Real Camera**: Replace test frames with webcam
2. **Add OpenAI API**: Get real vision analysis
3. **Customize Alerts**: Adjust thresholds in config.py
4. **Deploy**: Use gunicorn + nginx for production
5. **Extend**: Add historical charts, user management, etc.

---

**The web interface is production-ready and extensible!** 🚀

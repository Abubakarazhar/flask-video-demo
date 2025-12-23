# Why Did Localhost Close?

## Common Reasons the Server Stops

### 1. **Terminal Window Closed** ⚠️
- If you close the terminal window where the server is running, the server stops
- **Solution**: Keep the terminal open, or run in background

### 2. **Ctrl+C Pressed** ⏹️
- Pressing Ctrl+C in the terminal stops the server
- This is normal - it's how you stop the server intentionally
- **Solution**: Just restart it

### 3. **Terminal Session Ended** 🔌
- If your computer sleeps or the terminal session ends, the server stops
- **Solution**: Restart the server after waking up

### 4. **Python Error/Crash** 💥
- If there's an error in the code, the server crashes
- **Solution**: Check logs for errors

### 5. **Port Already in Use** 🔒
- If port 8080 is already in use, the server can't start
- **Solution**: Kill the process using port 8080

---

## How to Check What Happened

### Check Logs
```bash
tail -50 web_server.log
```

### Check if Server is Still Running
```bash
ps aux | grep "python.*web_interface"
```

### Check if Port 8080 is in Use
```bash
lsof -i :8080
```

---

## How to Restart the Server

### Method 1: Simple Restart (Recommended)
```bash
cd /Users/abubakarsmacbook/Downloads/factory_safety_monitoring
python3 web_interface.py
```

### Method 2: Run in Background (Keeps Running)
```bash
cd /Users/abubakarsmacbook/Downloads/factory_safety_monitoring
nohup python3 web_interface.py > server.log 2>&1 &
```

Then check it's running:
```bash
ps aux | grep "python.*web_interface"
```

To stop background server:
```bash
pkill -f "python.*web_interface"
```

### Method 3: Using Screen (Keeps Running After Terminal Closes)
```bash
# Install screen (if not installed)
brew install screen  # macOS

# Start server in screen
screen -S factory_server
python3 web_interface.py

# Detach: Press Ctrl+A then D
# Reattach: screen -r factory_server
```

---

## Keep Server Running Permanently

### Option 1: Use nohup (Simple)
```bash
nohup python3 web_interface.py > server.log 2>&1 &
echo $! > server.pid  # Save process ID
```

### Option 2: Use tmux (Better)
```bash
# Install tmux
brew install tmux  # macOS

# Start new session
tmux new -s factory_server

# Run server
python3 web_interface.py

# Detach: Ctrl+B then D
# Reattach: tmux attach -t factory_server
```

### Option 3: Create a Service (Advanced)
Create a launchd service on macOS or systemd service on Linux.

---

## Quick Fix: Restart Now

Just run:
```bash
cd /Users/abubakarsmacbook/Downloads/factory_safety_monitoring
python3 web_interface.py
```

Then open: **http://localhost:8080**

---

## Prevent Server from Closing

### Keep Terminal Open
- Don't close the terminal window
- Don't press Ctrl+C
- Keep your computer awake

### Run in Background
Use one of the methods above (nohup, screen, tmux)

### Check Server Status
```bash
# Check if running
curl http://localhost:8080/api/stats

# If you get JSON response, server is running
# If connection refused, server is stopped
```

---

## Troubleshooting

### "Port 8080 already in use"
```bash
# Find what's using port 8080
lsof -i :8080

# Kill it
kill -9 <PID>
```

### "Module not found"
```bash
pip3 install -r requirements.txt
```

### "Permission denied"
```bash
chmod +x web_interface.py
```

---

## Summary

**Most likely reason**: You closed the terminal or pressed Ctrl+C.

**Quick fix**: Just restart it:
```bash
python3 web_interface.py
```

**To keep it running**: Use `nohup`, `screen`, or `tmux` (see above).

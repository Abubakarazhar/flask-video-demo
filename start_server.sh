#!/bin/bash
# Simple script to start the web server

cd "$(dirname "$0")"

echo "🚀 Starting Factory Safety Monitoring Server..."
echo ""

# Kill any existing server
pkill -f "python3 web_interface.py" 2>/dev/null
sleep 2

# Start server
python3 web_interface.py > web_server.log 2>&1 &
SERVER_PID=$!

echo "Server starting (PID: $SERVER_PID)..."
echo ""

# Wait a bit
sleep 5

# Check if it's running
if curl -s http://localhost:8080 > /dev/null 2>&1; then
    echo "✅ Server is RUNNING!"
    echo ""
    echo "🌐 Open in your browser:"
    echo "   http://localhost:8080"
    echo ""
    echo "📋 To stop the server:"
    echo "   pkill -f web_interface.py"
    echo ""
    echo "📄 Logs: web_server.log"
else
    echo "❌ Server failed to start"
    echo "Check web_server.log for errors"
    tail -20 web_server.log
fi

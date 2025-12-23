#!/bin/bash
# Quick script to start the Factory Safety Monitoring server

cd "$(dirname "$0")"

echo "🌐 Starting Factory Safety Monitoring Server..."
echo ""
echo "📍 Server will be available at: http://localhost:8080"
echo ""
echo "⚠️  Keep this terminal window open!"
echo "⏹️  Press Ctrl+C to stop the server"
echo ""
echo "=" | head -c 70 && echo ""
echo ""

python3 web_interface.py

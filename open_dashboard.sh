#!/bin/bash
# Quick script to open the dashboard

echo "🌐 Opening Factory Safety Monitoring Dashboard..."
echo ""
echo "URL: http://localhost:8080"
echo ""

# Open in default browser
open http://localhost:8080 2>/dev/null || \
  python3 -m webbrowser http://localhost:8080 2>/dev/null || \
  echo "Please manually open: http://localhost:8080"

echo ""
echo "✅ Dashboard should open in your browser!"

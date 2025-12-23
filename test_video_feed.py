#!/usr/bin/env python3
"""Quick test to verify video feed is working."""

import requests
import json
import time

print("Testing Factory Safety Monitoring Video Feed...")
print("="*60)

# Wait for server
time.sleep(2)

try:
    response = requests.get('http://localhost:8080/api/frame', timeout=5)
    data = response.json()
    
    if data.get('frame'):
        frame_size = len(data['frame'])
        print(f"✅ SUCCESS! Frame data received")
        print(f"   Frame size: {frame_size:,} characters")
        print(f"   Status: {data.get('status', 'ok')}")
        print(f"   Timestamp: {data.get('timestamp', 'N/A')}")
        print(f"\n🌐 Open http://localhost:8080 in your browser")
        print(f"   The demo video should be visible in the 'Video feed' area")
    else:
        print("❌ No frame data in response")
        print(f"   Response: {json.dumps(data, indent=2)}")
        
except requests.exceptions.ConnectionError:
    print("❌ Cannot connect to server")
    print("   Make sure the server is running: python3 web_interface.py")
except Exception as e:
    print(f"❌ Error: {e}")

#!/usr/bin/env python3
"""
Download a realistic factory video from free sources.

This script helps you get a real factory video for testing.
"""

import requests
import os
from pathlib import Path

def download_sample_video():
    """Download a sample factory video from a free source."""
    
    # Using a free video from Pexels (factory/industrial videos)
    # Note: We'll use a direct download link or provide instructions
    
    print("📹 Getting Real Factory Video...")
    print("="*60)
    print("\nOption 1: Download from Pexels (Free, Real Videos)")
    print("   Visit: https://www.pexels.com/search/factory/")
    print("   Download any factory video")
    print("   Save it as 'factory_video.mp4' in this folder")
    
    print("\nOption 2: Use Your Own Video")
    print("   Any factory/warehouse/industrial video works")
    print("   Formats: MP4, AVI, MOV, MKV, WebM")
    
    print("\nOption 3: I'll create a more realistic one...")
    
    # Create a script to help download
    download_script = """
# Quick download script for factory video
# Run this in terminal:

# Option 1: Using youtube-dl (if installed)
# youtube-dl -f bestvideo[ext=mp4] "YOUTUBE_VIDEO_URL" -o factory_video.mp4

# Option 2: Direct download from free video sites
# Visit: https://www.pexels.com/search/factory/
# Or: https://pixabay.com/videos/search/factory/

# Option 3: Use any factory video you have
"""
    
    print(download_script)
    
    # Check if user has a video already
    video_path = Path(__file__).parent / "factory_video.mp4"
    if video_path.exists():
        print(f"\n✅ Found existing video: {video_path}")
        print(f"   Size: {video_path.stat().st_size / (1024*1024):.2f} MB")
        return str(video_path)
    
    print(f"\n💡 Place your factory video here: {video_path}")
    return None


if __name__ == "__main__":
    download_sample_video()

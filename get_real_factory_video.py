#!/usr/bin/env python3
"""
Instructions to get a real factory video from free sources.
"""

from pathlib import Path

def download_from_pexels():
    """Instructions to download from Pexels."""
    print("="*70)
    print("📹 GET A REAL FACTORY VIDEO")
    print("="*70)
    print()
    print("✅ BEST OPTION: Download from Pexels (Free, Real Videos)")
    print()
    print("1. Visit: https://www.pexels.com/search/factory/")
    print("   Or: https://www.pexels.com/search/warehouse/")
    print("   Or: https://www.pexels.com/search/manufacturing/")
    print()
    print("2. Click any video you like")
    print("3. Click 'Download' button (free, no signup needed)")
    print("4. Save it as 'factory_video.mp4' in this folder:")
    print(f"   {Path(__file__).parent}")
    print()
    print("="*70)
    print("ALTERNATIVE: Pixabay")
    print("="*70)
    print("1. Visit: https://pixabay.com/videos/search/factory/")
    print("2. Download any factory video")
    print("3. Save as 'factory_video.mp4'")
    print()
    print("="*70)
    print("QUICK TEST: Use Any Video You Have")
    print("="*70)
    print("The system accepts ANY video format:")
    print("  • MP4, AVI, MOV, MKV, WebM")
    print("  • Just upload through the web interface!")
    print()
    print("="*70)
    
    # Check if video already exists
    video_path = Path(__file__).parent / "factory_video.mp4"
    if video_path.exists():
        size_mb = video_path.stat().st_size / (1024 * 1024)
        print(f"✅ Found video: {video_path}")
        print(f"   Size: {size_mb:.2f} MB")
        return str(video_path)
    
    return None


if __name__ == "__main__":
    download_from_pexels()

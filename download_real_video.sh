#!/bin/bash
# Script to download a real factory video from free sources

echo "📹 Downloading Real Factory Video..."
echo ""

# Check if youtube-dl or yt-dlp is available
if command -v yt-dlp &> /dev/null; then
    DOWNLOADER="yt-dlp"
elif command -v youtube-dl &> /dev/null; then
    DOWNLOADER="youtube-dl"
else
    echo "❌ youtube-dl not installed"
    echo ""
    echo "Install it with:"
    echo "  pip install yt-dlp"
    echo ""
    echo "Or download manually from:"
    echo "  https://www.pexels.com/search/factory/"
    echo "  https://pixabay.com/videos/search/factory/"
    exit 1
fi

echo "Using: $DOWNLOADER"
echo ""
echo "📋 Free Factory Video Sources:"
echo ""
echo "1. Pexels (Recommended - Free, No Attribution):"
echo "   https://www.pexels.com/search/factory/"
echo ""
echo "2. Pixabay:"
echo "   https://pixabay.com/videos/search/factory/"
echo ""
echo "3. Or use this command to download from YouTube:"
echo "   $DOWNLOADER -f 'bestvideo[ext=mp4]' 'YOUTUBE_URL' -o factory_video.mp4"
echo ""
echo "💡 Best option: Visit Pexels, download any factory video,"
echo "   save it as 'factory_video.mp4' in this folder"
echo ""

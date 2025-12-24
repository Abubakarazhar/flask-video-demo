#!/bin/bash
# Cleanup redundant and problematic files

cd "$(dirname "$0")"

echo "🧹 Cleaning up redundant files..."
echo ""

# Files to remove (redundant/unused)
FILES_TO_REMOVE=(
    # Old app files (conflict with web_interface.py)
    "app.py"
    "app_opencv.py"
    
    # Removed chatbot feature
    "chatbot.py"
    "CHATBOT_SETUP.md"
    
    # Redundant video generation scripts
    "generate_demo_video.py"
    "generate_factory_video.py"
    "download_factory_video.py"
    "get_real_factory_video.py"
    "download_real_video.sh"
    
    # PDF conversion (keep md_to_pdf.py, remove convert_to_pdf.py)
    "convert_to_pdf.py"
    
    # Redundant documentation
    "ANALYSIS_FIXED.md"
    "COMPLETE_SETUP.md"
    "DEBUG_ANALYSIS.md"
    "DEPLOY_LOVABLE.md"
    "DEPLOY_VERCEL.md"
    "FEATURE_RECOMMENDATIONS.md"
    "FRAME_ANALYSIS_INFO.md"
    "GET_REAL_VIDEO.md"
    "QUICK_FIX.md"
    "QUICK_DEPLOY.md"
    "README_DEPLOY.md"
    "SETUP_REAL_VIDEO.md"
    "VIDEO_GENERATION_PROMPTS.md"
    "VIDEO_SOURCES.md"
    "WEB_INTERFACE.md"
    "MOCK_VS_API_COMPARISON.md"
    "PROJECT_STRUCTURE.txt"
    
    # Old scripts
    "open_dashboard.sh"
    "deploy.sh"
)

# Count files to remove
COUNT=0
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        COUNT=$((COUNT + 1))
    fi
done

echo "📋 Files to remove: $COUNT"
echo ""

# Ask for confirmation
read -p "Remove these files? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "❌ Cancelled"
    exit 0
fi

# Remove files
REMOVED=0
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "  ✅ Removed: $file"
        REMOVED=$((REMOVED + 1))
    fi
done

echo ""
echo "✅ Cleanup complete! Removed $REMOVED files"
echo ""
echo "📁 Essential files kept:"
echo "   - web_interface.py (main app)"
echo "   - Core modules (config.py, models.py, etc.)"
echo "   - README.md"
echo "   - QUICKSTART.md"
echo "   - DEPLOY.md"
echo "   - DEPLOY_NOW.md"
echo "   - PRODUCT_BRIEF.md"
echo "   - TECHNICAL_EXPLANATION.md"
echo ""

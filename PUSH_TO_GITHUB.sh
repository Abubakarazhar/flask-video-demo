#!/bin/bash
# Script to push code to GitHub repository

echo "🚀 Pushing Factory Safety Monitoring to GitHub"
echo ""
echo "📋 Please provide your GitHub repository URL"
echo "   Example: https://github.com/YOUR_USERNAME/factory-safety-monitoring.git"
echo ""
read -p "Enter your GitHub repository URL: " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "❌ Error: Repository URL is required"
    exit 1
fi

echo ""
echo "🔄 Adding remote repository..."
git remote add origin "$REPO_URL" 2>/dev/null || git remote set-url origin "$REPO_URL"

echo "✅ Remote added: $REPO_URL"
echo ""
echo "🔄 Pushing code to GitHub..."
echo ""

# Ensure we're on main branch
git branch -M main

# Push to GitHub
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Success! Your code is now on GitHub!"
    echo ""
    echo "🌐 View your repository at:"
    echo "   ${REPO_URL%.git}"
    echo ""
else
    echo ""
    echo "❌ Push failed. Common issues:"
    echo "   1. Authentication required (use Personal Access Token)"
    echo "   2. Repository doesn't exist or wrong URL"
    echo "   3. Network connection issue"
    echo ""
    echo "💡 Try manually:"
    echo "   git remote add origin $REPO_URL"
    echo "   git push -u origin main"
fi

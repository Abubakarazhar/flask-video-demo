#!/bin/bash
# Quick deployment script for Railway

echo "🚀 Deploying Factory Safety Monitoring System..."
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    npm i -g @railway/cli
fi

# Login if not already
echo "🔐 Logging in to Railway..."
railway login

# Initialize and deploy
echo "📤 Deploying to Railway..."
railway init
railway up

echo ""
echo "✅ Deployment complete!"
echo "🌐 Your app is live! Check Railway dashboard for URL."

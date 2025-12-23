"""
Vercel serverless function entry point for Factory Safety Monitoring.
"""

from web_interface import app

# Vercel expects the app to be exported
handler = app

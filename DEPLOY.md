# 🚀 Deploy Factory Safety Monitoring System

## Quick Options (Easiest)

### Option 1: Railway (Recommended - Free & Easy)

1. **Sign up**: https://railway.app (free tier available)

2. **Install Railway CLI**:
   ```bash
   npm i -g @railway/cli
   railway login
   ```

3. **Deploy**:
   ```bash
   cd factory_safety_monitoring
   railway init
   railway up
   ```

4. **Set environment variables** (optional):
   ```bash
   railway variables set OPENAI_API_KEY=your-key
   ```

5. **Get your URL**: Railway will give you a public URL like `https://your-app.railway.app`

---

### Option 2: Render (Free Tier)

1. **Sign up**: https://render.com

2. **Create New Web Service**:
   - Connect your GitHub repo OR upload files
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn -w 4 -b 0.0.0.0:$PORT web_interface:app`

3. **Set Environment Variables** (optional):
   - `OPENAI_API_KEY` (if using paid API)
   - `PORT` (auto-set by Render)

4. **Deploy**: Click "Deploy"

---

### Option 3: ngrok (Quick Testing - 2 minutes)

**For quick testing/sharing:**

1. **Install ngrok**:
   ```bash
   # macOS
   brew install ngrok
   
   # Or download from https://ngrok.com
   ```

2. **Start your server locally**:
   ```bash
   cd factory_safety_monitoring
   python3 web_interface.py
   ```

3. **In another terminal, expose it**:
   ```bash
   ngrok http 8080
   ```

4. **Share the URL**: ngrok gives you a public URL like `https://abc123.ngrok.io`
   - **Free tier**: URL changes each time
   - **Paid tier**: Custom domain

---

## Production Deployment

### Using Gunicorn (Recommended)

1. **Install gunicorn**:
   ```bash
   pip install gunicorn
   ```

2. **Run with gunicorn**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8080 web_interface:app
   ```

3. **For production, use**:
   ```bash
   gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 120 web_interface:app
   ```

---

## Platform-Specific Guides

### Railway

**railway.json** (optional):
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn -w 4 -b 0.0.0.0:$PORT web_interface:app",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Render

**render.yaml**:
```yaml
services:
  - type: web
    name: factory-safety-monitoring
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -w 4 -b 0.0.0.0:$PORT web_interface:app
    envVars:
      - key: OPENAI_API_KEY
        sync: false
```

### Heroku

1. **Install Heroku CLI**: https://devcenter.heroku.com/articles/heroku-cli

2. **Deploy**:
   ```bash
   heroku create your-app-name
   git push heroku main
   heroku config:set OPENAI_API_KEY=your-key
   ```

3. **Procfile** (already created):
   ```
   web: gunicorn -w 4 -b 0.0.0.0:$PORT web_interface:app
   ```

---

## Environment Variables

Set these in your hosting platform:

- `OPENAI_API_KEY` (optional) - For paid API mode
- `PORT` (auto-set by most platforms)

---

## File Upload Limits

**Important**: Most free hosting has file size limits:
- Railway: 100MB
- Render: 100MB
- Heroku: 30MB

For larger videos, consider:
- Using cloud storage (S3, Cloudinary)
- Compressing videos before upload
- Using direct video URLs instead of uploads

---

## Quick Start Commands

### Local Testing with Public URL (ngrok):
```bash
# Terminal 1
python3 web_interface.py

# Terminal 2
ngrok http 8080
```

### Deploy to Railway:
```bash
railway init
railway up
```

### Deploy to Render:
1. Connect GitHub repo
2. Set build/start commands
3. Deploy

---

## Troubleshooting

**"Port already in use"**:
- Change port in code or use `PORT` env variable

**"File upload fails"**:
- Check file size limits
- Ensure `uploads/` directory is writable

**"Module not found"**:
- Run `pip install -r requirements.txt`

---

**Recommended**: Start with **Railway** or **Render** - both have free tiers and are easy to use!

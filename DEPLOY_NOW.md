# 🚀 Deploy Your Factory Safety Monitoring System

## ⚡ Quick Deploy (Choose One)

### Option 1: Railway (Easiest - 5 minutes) ⭐ RECOMMENDED

**Why Railway:**
- ✅ Free tier available
- ✅ Auto-deploys from GitHub
- ✅ Easy setup
- ✅ No credit card required (for free tier)

**Steps:**

1. **Sign up for Railway**
   - Go to: https://railway.app
   - Click "Start a New Project"
   - Sign up with GitHub (easiest)

2. **Deploy from GitHub**
   - Click "Deploy from GitHub repo"
   - Select your repository: `flask-video-demo`
   - Railway will auto-detect it's a Python app

3. **Configure (if needed)**
   - Railway will use your `Procfile` automatically
   - If you need to set environment variables:
     - Go to your project → Variables
     - Add: `OPENAI_API_KEY` (if using paid API)

4. **Get Your URL**
   - Railway gives you a URL like: `https://your-app.railway.app`
   - Click "Generate Domain" for a custom subdomain

5. **Done!** Your app is live! 🎉

---

### Option 2: Render (Free Tier - 10 minutes)

**Why Render:**
- ✅ Free tier available
- ✅ Auto-deploys from GitHub
- ✅ Good for production

**Steps:**

1. **Sign up for Render**
   - Go to: https://render.com
   - Sign up with GitHub

2. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository: `flask-video-demo`
   - Render will auto-detect settings

3. **Configure**
   - **Name**: `factory-safety-monitoring` (or your choice)
   - **Region**: Choose closest to you
   - **Branch**: `main`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 120 web_interface:app`

4. **Environment Variables** (optional)
   - Add: `OPENAI_API_KEY` (if using paid API)
   - `PORT` is auto-set by Render

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (2-5 minutes)
   - Get your URL: `https://your-app.onrender.com`

6. **Done!** 🎉

---

### Option 3: ngrok (Quick Testing - 2 minutes)

**For quick testing/sharing (not permanent):**

1. **Install ngrok**
   ```bash
   brew install ngrok
   # Or download from https://ngrok.com
   ```

2. **Start your server locally**
   ```bash
   cd /Users/abubakarsmacbook/Downloads/factory_safety_monitoring
   ./start_server.sh
   ```

3. **Expose it with ngrok** (in another terminal)
   ```bash
   ngrok http 8080
   ```

4. **Share the URL**
   - ngrok gives you: `https://abc123.ngrok.io`
   - Share this URL with others
   - **Note**: Free tier URL changes each time you restart

---

## 📋 Pre-Deployment Checklist

Before deploying, make sure:

- [x] Code is pushed to GitHub ✅
- [ ] `Procfile` exists (already done ✅)
- [ ] `requirements.txt` is up to date ✅
- [ ] `runtime.txt` specifies Python version ✅
- [ ] Environment variables documented (`.env.example` exists ✅)

---

## 🔧 Platform-Specific Details

### Railway Configuration

Your `railway.json` is already configured:
```json
{
  "deploy": {
    "startCommand": "gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 120 web_interface:app"
  }
}
```

Railway will automatically:
- Detect Python
- Install dependencies from `requirements.txt`
- Use your `Procfile`

### Render Configuration

Your `render.yaml` is already configured:
```yaml
services:
  - type: web
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 120 web_interface:app
```

---

## 🌐 After Deployment

### Test Your Deployment

1. **Visit your URL**
   - Railway: `https://your-app.railway.app`
   - Render: `https://your-app.onrender.com`

2. **Test Features**
   - Upload a video
   - Start analysis
   - Check alerts

### Update Your README

Add deployment badge to your README:
```markdown
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template)
```

---

## 🐛 Troubleshooting

### "Application Error" or "502 Bad Gateway"

**Common causes:**
1. **Port not set correctly**
   - Make sure your app uses `$PORT` environment variable
   - Your `Procfile` already does this ✅

2. **Dependencies missing**
   - Check `requirements.txt` has all packages
   - Railway/Render installs from this file

3. **Start command wrong**
   - Verify `Procfile` has correct command
   - Should be: `gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 120 web_interface:app`

### "Module not found"

**Solution:**
- Check `requirements.txt` includes all dependencies
- Rebuild the deployment

### "Timeout" errors

**Solution:**
- Increase timeout in `Procfile`: `--timeout 300`
- Check your app starts quickly

---

## 💰 Cost Comparison

| Platform | Free Tier | Paid Plans |
|----------|-----------|------------|
| **Railway** | $5 credit/month | Pay as you go |
| **Render** | Free (with limits) | $7+/month |
| **ngrok** | Free (URL changes) | $8+/month (static URL) |

---

## 🎯 Recommended: Railway

**Why Railway is best for this project:**
- ✅ Easiest setup
- ✅ Auto-deploys from GitHub
- ✅ Free tier is generous
- ✅ Good documentation
- ✅ Your config files are ready

**Quick Start:**
1. Go to https://railway.app
2. Sign up with GitHub
3. Deploy from repo: `flask-video-demo`
4. Done!

---

## 📚 More Options

See `DEPLOY.md` for:
- Heroku deployment
- AWS/GCP/Azure
- Docker deployment
- Custom VPS setup

---

## ✅ Success Checklist

After deploying:

- [ ] App is accessible at public URL
- [ ] Can upload videos
- [ ] Analysis works
- [ ] Alerts display correctly
- [ ] Share URL with others
- [ ] Update README with deployment link

---

## 🎉 You're Live!

Once deployed, your Factory Safety Monitoring System will be accessible to anyone with the URL!

**Next Steps:**
- Share with testers
- Get feedback
- Monitor usage
- Iterate and improve

---

## 🆘 Need Help?

- Railway Docs: https://docs.railway.app
- Render Docs: https://render.com/docs
- Check deployment logs in platform dashboard

# ⚡ Quick Deploy Guide (5 Minutes)

## 🚀 Fastest Way: Railway (Recommended)

### Step 1: Install Railway CLI
```bash
npm i -g @railway/cli
```

### Step 2: Login
```bash
railway login
```

### Step 3: Deploy
```bash
cd factory_safety_monitoring
railway init
railway up
```

### Step 4: Get Your URL
Railway will show you a public URL like:
```
https://your-app.up.railway.app
```

**Done!** Share that URL with anyone.

---

## 🔥 Alternative: ngrok (2 Minutes)

### Step 1: Install ngrok
```bash
# macOS
brew install ngrok

# Or download: https://ngrok.com/download
```

### Step 2: Start Server
```bash
cd factory_safety_monitoring
python3 web_interface.py
```

### Step 3: Expose Publicly
```bash
# In another terminal
ngrok http 8080
```

### Step 4: Share URL
ngrok gives you: `https://abc123.ngrok.io`

**Note**: Free ngrok URLs change each time you restart.

---

## 📋 What You Need

- ✅ Python 3.9+
- ✅ All files in `factory_safety_monitoring/` folder
- ✅ `requirements.txt` (already created)
- ✅ `Procfile` (already created)

---

## 🌐 After Deployment

Your site will be live at:
- Railway: `https://your-app.up.railway.app`
- ngrok: `https://random-id.ngrok.io`
- Render: `https://your-app.onrender.com`

**Share the URL and anyone can test it!**

---

## 💡 Tips

1. **Railway** = Permanent URL, free tier
2. **ngrok** = Quick testing, URL changes
3. **Render** = Also good, free tier

**Start with Railway - it's the easiest!**

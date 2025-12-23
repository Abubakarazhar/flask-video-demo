# 🎯 Complete Setup Guide - Real Factory Video Analysis

## ✅ **Current Status:**

✅ **Server:** Running at http://localhost:8080  
✅ **Video Upload:** Working  
✅ **Analysis:** Fixed - Now analyzes uploaded videos  
📹 **Video:** Need one real factory video

---

## 📹 **STEP 1: Get a Real Factory Video**

### **Option A: Pexels (Easiest - Recommended)**

1. **Visit:** https://www.pexels.com/search/factory/
2. **Choose a video** showing:
   - Factory floor/warehouse
   - Workers (optional but better)
   - Industrial setting
3. **Download:**
   - Click video → Click "Download"
   - Save as `factory_video.mp4`
   - Place in: `factory_safety_monitoring/` folder

### **Option B: Your Own Video**

- Any factory/warehouse/industrial video
- Upload directly through web interface
- Formats: MP4, AVI, MOV, MKV, WebM

### **Option C: AI-Generated**

- Use Runway ML, Pika, or other AI video tools
- Generate factory scene
- Download and use

---

## 🚀 **STEP 2: Upload & Analyze**

1. **Open:** http://localhost:8080
2. **Upload Video:**
   - Click "📁 Upload Video"
   - Select your factory video
   - Wait for "✅ Loaded" message
3. **Start Analysis:**
   - Click "▶ Start Analysis"
   - Watch the video play
4. **Monitor Results:**
   - Check "Safety Events" panel
   - Check "Recent Alerts" panel
   - Watch statistics update

---

## 📊 **What You'll See When It Works:**

### **In Browser:**
- Video playing
- Events appearing in "Safety Events"
- Alerts in "Recent Alerts" (if issues found)
- Statistics updating (frames processed, events detected)

### **In Logs (web_server.log):**
```
[PROCESSING] 🔍 Analyzing frame 1 from video...
[PROCESSING] 📸 Running vision analysis...
[PROCESSING] ✅ Vision: 2 people, 1 hazards
[PROCESSING] 🧠 Assessing risks...
[PROCESSING] ✅ Risk assessment: 1 events found
[PROCESSING] 📊 Added 1 events to aggregator
[PROCESSING] 📋 Queued event: PPE Violation: Missing hard hat
[PROCESSING] 🚨 Generated alert: PPE Violation: Missing hard hat
```

---

## 🔧 **Troubleshooting:**

### **If No Events Appear:**

1. **Check logs:**
   ```bash
   tail -f web_server.log
   ```

2. **Verify video uploaded:**
   - Should see "✅ Loaded: filename.mp4"

3. **Check if analysis started:**
   - Click "Start Analysis" button
   - Should see processing messages in logs

4. **Verify video has content:**
   - Safe videos (no people, no hazards) = No alerts (correct!)
   - Videos with people/equipment = Should see analysis

---

## 💡 **For Best Results:**

### **With Mock Mode (No API Key):**
- Uses basic computer vision
- Detects: people, hard hats (yellow), safety vests (orange)
- Only alerts if it actually detects issues
- Less accurate than AI

### **With OpenAI API Key:**
```bash
export OPENAI_API_KEY="your_key_here"
# Restart server
```
- Real AI analysis
- Much more accurate
- Understands context better
- Detects subtle issues

---

## 🎯 **Your Plan:**

1. ✅ **Get ONE real factory video** (Pexels is easiest)
2. ✅ **Upload it** through web interface
3. ✅ **Click "Start Analysis"**
4. ✅ **Watch it analyze YOUR video**
5. ✅ **See real results** based on YOUR video content

---

## 📋 **Quick Commands:**

```bash
# Start server
cd factory_safety_monitoring
./start_server.sh

# View logs
tail -f web_server.log

# Stop server
pkill -f web_interface.py
```

---

**Once you have a real factory video, upload it and the system will analyze it properly!**

The analysis is now fixed and will work with your uploaded video. 🚀

# 💬 Safety Assistant Chatbot Setup

## 🎯 Overview

The Safety Assistant is a **Gemini-powered chatbot** that helps you understand video analysis results. It can answer questions about:
- Current video frame
- Safety events and alerts
- Analysis results
- General safety questions

## ✅ Why This is a Great Idea!

1. **FREE API** - Gemini has a generous free tier
2. **Context-Aware** - Understands your video and analysis
3. **Interactive** - Ask questions, get explanations
4. **User-Friendly** - Makes the system more accessible
5. **Educational** - Helps users understand safety issues

## 🚀 Setup (Optional but Recommended)

### Step 1: Get Free Gemini API Key

1. Go to: https://makersuite.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API Key"
4. Copy your API key

### Step 2: Add to Environment

**Option A: .env file (Recommended)**
```bash
cd factory_safety_monitoring
echo "GEMINI_API_KEY=your-api-key-here" >> .env
```

**Option B: Environment Variable**
```bash
export GEMINI_API_KEY=your-api-key-here
```

### Step 3: Install Dependency

```bash
pip install google-generativeai
```

Or install all requirements:
```bash
pip install -r requirements.txt
```

## 📋 How to Use

### Without API Key (Mock Mode):
- Basic responses
- Can answer general questions
- Limited context understanding

### With API Key (Full Mode):
- **Full AI-powered responses**
- **Sees current video frame**
- **Understands analysis context**
- **Detailed explanations**

## 💡 Example Questions

### About Current Video:
- "What do you see in this frame?"
- "How many people are visible?"
- "What safety equipment is present?"
- "Describe the scene"

### About Analysis:
- "What safety issues do you see?"
- "Explain the latest safety event"
- "What PPE violations are there?"
- "What hazards were detected?"

### General Safety:
- "What PPE is required in a factory?"
- "What are common safety violations?"
- "How should workers protect themselves?"

## 🎨 Features

- **Real-time chat** - Ask questions anytime
- **Context-aware** - Knows about current video and analysis
- **Image understanding** - Can see and describe current frame (with API key)
- **Event explanations** - Understands safety events
- **Free to use** - Gemini free tier is generous

## 🔧 Technical Details

- **Model**: Gemini Pro Vision (free tier)
- **Context**: Current frame + latest analysis + recent events
- **Fallback**: Mock mode if no API key
- **Cost**: FREE (Gemini free tier)

## 📊 Comparison

| Feature | Without API Key | With API Key |
|---------|----------------|--------------|
| Basic Q&A | ✅ | ✅ |
| Video Frame Analysis | ❌ | ✅ |
| Context Understanding | Limited | Full |
| Event Explanations | Basic | Detailed |
| Image Description | ❌ | ✅ |

## 🚨 Troubleshooting

**"google-generativeai not installed"**
```bash
pip install google-generativeai
```

**"No API key"**
- Chatbot works in mock mode
- Add GEMINI_API_KEY for full features

**"Chat not responding"**
- Check browser console (F12)
- Check server logs: `tail -f web_server.log`

## 💰 Cost

**FREE!** Gemini has a generous free tier:
- 60 requests per minute
- 1,500 requests per day
- Perfect for this use case!

---

**The chatbot makes the system much more user-friendly and educational!**

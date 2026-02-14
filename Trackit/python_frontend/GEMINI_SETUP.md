# TrackIt AI Chat Setup Guide

## ✅ Chat Works Offline & Online!

The TrackIt AI chatbox now works **out of the box** with intelligent fallback responses. When you have a Gemini API key set, it uses real AI. When you don't, it provides smart rule-based responses based on your habit data.

---

## 🚀 Quick Start (No Setup Required!)

The chat works immediately! Click the 💬 button and start asking questions:
- "How can I improve my routine?"
- "Give me motivation"
- "How's my progress?"
- "I'm struggling with habits"

You'll get **smart, personalized responses** based on your current habits!

---

## 🤖 Optional: Use Real Gemini AI (For Better Responses)

Want even smarter AI responses? Add your free Gemini API key:

### Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio](https://ai.google.dev/)
2. Click "Get API Key"
3. Create a new project or use an existing one
4. Click "Create API Key"
5. Copy the API key (looks like a long alphanumeric string)

### Step 2: Add to `.env`

1. Open `.env` in the project root:
   ```
   GEMINI_API_KEY=your_api_key_here
   TRACKIT_SECRET=trackit-dev-secret
   ```

2. Replace `your_api_key_here` with your actual key

3. Save the file

### Step 3: Restart the App

```bash
# Stop: Ctrl+C
# Restart:
python app.py
```

🎉 Now you have **real Gemini AI** responses with full context from your habits!

---

## 💬 How the Chat Works

### Without API Key (Fallback Mode):
- Detects keywords in your message
- Provides smart, encouraging responses
- Uses your habit data for personalization
- **Always works** - never needs internet for these responses

### With Gemini API Key (AI Mode):
- Sends your message to Google's Gemini model
- AI understands context and habits
- Provides creative, personalized coaching
- Falls back to smart responses if Gemini has issues

---

## 🎯 Example Conversations

**You:** "How can I improve my routine?"  
**AI:** "Great question! Pick your hardest habit and focus on 3 days in a row. Once you break through, momentum builds itself! 💪"

**You:** "I need motivation"  
**AI:** "You're already here checking on your habits - that's the hardest part! Every single day you show up is a win. Keep crushing it! 🌿"

**You:** "How's my progress?"  
**AI:** "Your Reading is at 100%! Keep that momentum going!"

---

## ⚙️ Troubleshooting

**Q: Chat says "Network error"?**  
A: Refresh the page. The chat should work even without internet (uses mock responses).

**Q: I set the API key but it's not working?**  
A: 
1. Make sure `.env` file exists in the project root
2. Verify the API key is correct at [Google AI Studio](https://ai.google.dev/)
3. Restart the Flask app
4. Check browser console for errors (F12 → Console)

**Q: Is my API key secure?**  
A: 
- ✅ Never sent to the browser - only used server-side
- ✅ `.env` is in `.gitignore` - never committed to Git
- ✅ Safe for development

**Q: Can I disable the AI?**  
A: Yes, just leave `GEMINI_API_KEY` empty. Mock responses still work!

---

## 📊 What the AI Knows

The AI coach has context about:
- Your name
- All your habits and their completion rates
- Your overall progress percentage
- Today's date

It uses this to give personalized encouragement and practical tips!

---

## 🔧 Environment Setup (Optional)

### Requirements:
- Python 3.8+
- `google-generativeai` (auto-installed)
- `python-dotenv` (auto-installed)

### Files:
- `.env` - Your secret API keys (⚠️ never commit this!)
- `.env.example` - Template (safe to commit)

---

## 📝 Notes

- The Gemini API has a **free tier** - perfect for development!
- Rate limits: 60 requests per minute (more than enough for casual use)
- Responses are instant with good internet
- Chat persists within a session only (no database storage)

---

Enjoy your AI-powered habit coach! 🌿✨


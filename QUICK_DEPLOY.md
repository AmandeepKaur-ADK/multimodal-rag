# 🚀 Quick Deploy - Get Live Demo in 5 Minutes

## Option 1: Render (Recommended - No CLI needed)

1. **Go to Render**: https://render.com
2. **Sign up** with GitHub
3. **Create Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub: `AmandeepKaur-ADK/multimodal-rag`
   - Name: `ai-assistant-demo`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind 0.0.0.0:$PORT web_app:app`
   - Instance Type: Free

4. **Deploy**: Click "Create Web Service"

5. **Get URL**: After 3-5 minutes, you'll get:
   ```
   https://ai-assistant-demo.onrender.com
   ```

## Option 2: Railway (Fast)

1. **Go to Railway**: https://railway.app
2. **Sign up** with GitHub
3. **New Project** → **Deploy from GitHub repo**
4. **Select**: `AmandeepKaur-ADK/multimodal-rag`
5. **Deploy**: Railway auto-detects and deploys
6. **Get URL**: `https://your-app.railway.app`

## Option 3: Heroku (Classic)

1. **Go to Heroku**: https://heroku.com
2. **Create account** and install CLI
3. **Deploy**:
   ```bash
   heroku create ai-assistant-demo
   git push heroku main
   heroku open
   ```

## 🎯 Expected Live Demo Features

Your live demo will have:

- ✅ **Web Interface**: Beautiful chat interface
- ✅ **AI Responses**: Free AI models (no API keys)
- ✅ **Web Search**: Real-time web search
- ✅ **Health Monitoring**: `/api/health` endpoint
- ✅ **Statistics**: `/api/stats` endpoint
- ✅ **Error Handling**: Comprehensive error management

## 📊 Test Your Live Demo

Once deployed, test these URLs:

```bash
# Main interface
https://your-app.onrender.com/

# Health check
https://your-app.onrender.com/api/health

# Ask a question (POST)
curl -X POST https://your-app.onrender.com/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is artificial intelligence?"}'
```

## 🚨 Troubleshooting

**Build fails?**
- Check `requirements.txt` is complete
- Ensure Python 3.11 is specified in `runtime.txt`

**App crashes?**
- Check logs in platform dashboard
- Verify all dependencies are installed

**Slow responses?**
- First request takes 30-60s (model loading)
- Subsequent requests are faster (2-8s)

## 🎉 Share Your Demo

Once live, share:

```markdown
🤖 **Live AI Assistant Demo**: https://your-app.onrender.com
📊 **Health Check**: https://your-app.onrender.com/api/health
📈 **Statistics**: https://your-app.onrender.com/api/stats
🔗 **GitHub**: https://github.com/AmandeepKaur-ADK/multimodal-rag
```

**Estimated Deploy Time**: 3-7 minutes
**Cost**: Free tier on all platforms
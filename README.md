# 🤖 Free AI Assistant - Production Web Application

A production-ready AI assistant web application that uses **completely free AI models** with web search capabilities. No API keys required!

## 🚀 Deployment Status

✅ **Live Demo**: [https://multimodal-rag-khaki.vercel.app](https://multimodal-rag-khaki.vercel.app)  
✅ **GitHub**: [https://github.com/AmandeepKaur-ADK/multimodal-rag](https://github.com/AmandeepKaur-ADK/multimodal-rag)  
✅ **Platform**: Vercel (Free Tier)  
✅ **Status**: Production Ready  

> **Note**: First request may take 30-60 seconds as the AI models load. Subsequent requests are much faster (2-8 seconds).

## 🚀 Quick Deploy

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/AmandeepKaur-ADK/multimodal-rag)

## 🌟 Live Demo

🔗 **[Try the Live Demo](https://multimodal-rag-khaki.vercel.app)** ← Click here to test it now!

### 📊 Demo Endpoints

- 🌐 **Web Interface**: https://multimodal-rag-khaki.vercel.app
- 🏥 **Health Check**: https://multimodal-rag-khaki.vercel.app/health
- 📈 **API Status**: https://multimodal-rag-khaki.vercel.app/api/status
- 📚 **GitHub Repository**: https://github.com/AmandeepKaur-ADK/multimodal-rag

## ✨ Features

- 🆓 **100% Free** - Uses open-source AI models (no OpenAI/API costs)
- 🌐 **Web Search** - Real-time web search for current information
- 🛡️ **Error Handling** - Comprehensive error handling and fallback strategies
- 📊 **Monitoring** - Built-in health checks and usage statistics
- 🚀 **Production Ready** - Docker, Nginx, rate limiting, security headers
- 🔒 **Privacy First** - All processing happens locally/on your server

## 🚀 Local Development

```bash
# Clone and setup
git clone https://github.com/AmandeepKaur-ADK/multimodal-rag.git
cd multimodal-rag

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python web_app.py

# Access at http://localhost:5000
```

## 🐳 Docker Deployment

```bash
# Build and run with Docker
docker build -t ai-assistant .
docker run -p 5000:5000 ai-assistant

# Or use Docker Compose
docker-compose up -d
```

## 📊 API Endpoints

### Ask Question
```bash
POST /api/ask
Content-Type: application/json

{
  "question": "What is artificial intelligence?"
}
```

### Health Check
```bash
GET /api/health
```

### Statistics
```bash
GET /api/stats
```

## 📈 Performance

- **Response Time**: 2-8 seconds (after initial model load)
- **First Request**: 30-60 seconds (model initialization)
- **Accuracy**: 70-90% confidence scores
- **Cost**: $0 (completely free to run)

## 🧪 Testing

### Test Live Demo

```bash
# Health check
curl https://multimodal-rag-ai-assistant.onrender.com/api/health

# Test question
curl -X POST https://multimodal-rag-ai-assistant.onrender.com/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?"}'

# Get statistics
curl https://multimodal-rag-ai-assistant.onrender.com/api/stats
```

### Test Local Development

```bash
# Run health check
curl http://localhost:5000/api/health

# Test question
curl -X POST http://localhost:5000/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is machine learning?"}'
```

## 📝 Example Questions

- "What is artificial intelligence?"
- "How does machine learning work?"
- "Latest developments in AI"
- "Explain quantum computing"
- "What are neural networks?"

## 📄 License

MIT License - feel free to use this for personal or commercial projects!

## 🆘 Support

- 📧 Email: amandeepakuramuadk@gmail.com
- 🐛 Issues: [GitHub Issues](https://github.com/AmandeepKaur-ADK/multimodal-rag/issues)
- 📖 Documentation: [Wiki](https://github.com/AmandeepKaur-ADK/multimodal-rag/wiki)
- 🌐 Live Demo: [https://multimodal-rag-ai-assistant.onrender.com](https://multimodal-rag-ai-assistant.onrender.com)

## 🙏 Acknowledgments

- Hugging Face for free AI models
- Flask for the web framework
- All the open-source contributors

---

**Made with ❤️ and completely free AI models**
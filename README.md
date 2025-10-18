# 🤖 Free AI Assistant - Production Web Application

A production-ready AI assistant web application that uses **completely free AI models** with web search capabilities. No API keys required!

## 🚀 Deployment Status

✅ **Live Demo**: [https://multimodal-rag-ai-assistant.onrender.com](https://multimodal-rag-ai-assistant.onrender.com)  
✅ **GitHub**: [https://github.com/AmandeepKaur-ADK/multimodal-rag](https://github.com/AmandeepKaur-ADK/multimodal-rag)  
✅ **Platform**: Render (Free Tier)  
✅ **Status**: Production Ready  

> **Note**: First request may take 30-60 seconds as the AI models load. Subsequent requests are much faster (2-8 seconds).

## 🚀 One-Click Deploy

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/AmandeepKaur-ADK/multimodal-rag)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template/your-template-id)
[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/AmandeepKaur-ADK/multimodal-rag)

## 🌟 Live Demo

🔗 **[Try the Live Demo](https://multimodal-rag-ai-assistant.onrender.com)** ← Click here to test it now!

### 📊 Demo Endpoints

- 🌐 **Web Interface**: https://multimodal-rag-ai-assistant.onrender.com
- 🏥 **Health Check**: https://multimodal-rag-ai-assistant.onrender.com/api/health
- 📈 **Statistics**: https://multimodal-rag-ai-assistant.onrender.com/api/stats
- 📚 **GitHub Repository**: https://github.com/AmandeepKaur-ADK/multimodal-rag

## ✨ Features

- 🆓 **100% Free** - Uses open-source AI models (no OpenAI/API costs)
- 🌐 **Web Search** - Real-time web search for current information
- 🛡️ **Error Handling** - Comprehensive error handling and fallback strategies
- 📊 **Monitoring** - Built-in health checks and usage statistics
- 🚀 **Production Ready** - Docker, Nginx, rate limiting, security headers
- 🔒 **Privacy First** - All processing happens locally/on your server

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/AmandeepKaur-ADK/multimodal-rag.git
cd multimodal-rag

# Start with Docker Compose
docker-compose up -d

# Access at http://localhost
```

### Option 2: Local Development

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

## 🌐 Deployment Options

### Heroku Deployment

```bash
# Install Heroku CLI and login
heroku login

# Create app
heroku create your-ai-assistant

# Deploy
git push heroku main

# Open your app
heroku open
```

### Railway Deployment

1. Connect your GitHub repository to Railway
2. Railway will automatically detect and deploy using the Dockerfile
3. Your app will be live at `https://your-app.railway.app`

### DigitalOcean App Platform

1. Create new app from GitHub repository
2. Use the detected Dockerfile
3. Set environment variables if needed
4. Deploy!

### AWS/Google Cloud/Azure

Use the provided Dockerfile and docker-compose.yml for container deployment.

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

## ⚙️ Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Basic Configuration
FLASK_ENV=production
DEFAULT_MODEL=microsoft/DialoGPT-small
ENABLE_WEB_SEARCH=True
MAX_SEARCH_RESULTS=3

# Server Configuration
HOST=0.0.0.0
PORT=5000
WORKERS=2
```

## 🛡️ Security Features

- Rate limiting (10 requests/minute for API, 30 for web)
- Security headers (XSS protection, content type sniffing prevention)
- Input validation and sanitization
- Non-root Docker user
- CORS protection

## 📈 Performance

- **Response Time**: 2-8 seconds (depending on question complexity)
- **Concurrent Users**: 10-50+ (with proper scaling)
- **Accuracy**: 70-90% confidence scores
- **Cost**: $0 (completely free to run)

## 🔧 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │───▶│   Nginx Proxy   │───▶│  Flask App      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
                                               ┌─────────────────┐
                                               │  Free AI Models │
                                               │  + Web Search   │
                                               └─────────────────┘
```

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

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
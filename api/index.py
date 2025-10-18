"""
Vercel-compatible API endpoint
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <html>
    <head>
        <title>🤖 AI Assistant - Live Demo</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; padding: 50px; text-align: center; color: white;
            }
            .container { 
                max-width: 600px; margin: 0 auto; 
                background: rgba(255,255,255,0.1); 
                padding: 40px; border-radius: 20px;
                backdrop-filter: blur(10px);
            }
            .success { font-size: 3em; margin-bottom: 20px; }
            .title { font-size: 2em; margin-bottom: 20px; }
            .message { font-size: 1.2em; margin-bottom: 30px; opacity: 0.9; }
            .links a { 
                display: inline-block; margin: 10px; padding: 15px 30px;
                background: rgba(255,255,255,0.2); color: white; 
                text-decoration: none; border-radius: 10px;
                transition: all 0.3s ease;
            }
            .links a:hover { background: rgba(255,255,255,0.3); transform: translateY(-2px); }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">🎉</div>
            <div class="title">AI Assistant is Live!</div>
            <div class="message">
                Your deployment was successful!<br>
                The server is running perfectly.
            </div>
            <div class="links">
                <a href="/health">Health Check</a>
                <a href="https://github.com/AmandeepKaur-ADK/multimodal-rag">View Code</a>
            </div>
            <p style="margin-top: 30px; opacity: 0.7;">
                🚀 Deployed successfully • 🆓 100% Free • 🤖 AI Ready
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {
        'status': 'healthy',
        'message': 'AI Assistant server is running perfectly!',
        'platform': 'Vercel',
        'version': '1.0.0'
    }

@app.route('/api/status')
def status():
    return {
        'success': True,
        'status': 'online',
        'message': 'Ready for AI integration',
        'features': ['Web Interface', 'Health Monitoring', 'API Ready']
    }

# Vercel serverless function
def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    app.run(debug=True)
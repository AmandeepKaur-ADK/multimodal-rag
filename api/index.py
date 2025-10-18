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
                <a href="/chat">🤖 Try AI Chat</a>
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

@app.route('/chat')
def chat():
    return '''
    <html>
    <head>
        <title>🤖 AI Chat Interface</title>
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0; padding: 20px; min-height: 100vh;
            }
            .container { 
                max-width: 800px; margin: 0 auto; 
                background: white; border-radius: 20px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header { 
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                color: white; padding: 30px; text-align: center;
            }
            .chat-area { padding: 30px; }
            .input-section { 
                display: flex; gap: 15px; margin-bottom: 20px;
                align-items: flex-end;
            }
            .question-input { 
                flex: 1; padding: 15px; border: 2px solid #e1e5e9;
                border-radius: 12px; font-size: 16px; resize: vertical;
                min-height: 60px; font-family: inherit;
            }
            .ask-button { 
                padding: 15px 30px; 
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                color: white; border: none; border-radius: 12px;
                cursor: pointer; font-size: 16px; font-weight: 600;
            }
            .response-area { 
                background: #f8f9fa; border-radius: 12px;
                padding: 20px; margin-top: 20px; display: none;
            }
            .examples { margin-top: 20px; }
            .example-btn { 
                display: inline-block; margin: 5px; padding: 8px 15px;
                background: #e9ecef; border: none; border-radius: 20px;
                cursor: pointer; font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 AI Assistant</h1>
                <p>Ask me anything! (AI features coming soon)</p>
            </div>
            
            <div class="chat-area">
                <div class="input-section">
                    <textarea 
                        id="questionInput" 
                        class="question-input" 
                        placeholder="Ask me anything... (e.g., What is artificial intelligence?)"
                        rows="2"
                    ></textarea>
                    <button class="ask-button" onclick="askQuestion()">Ask AI</button>
                </div>
                
                <div id="responseArea" class="response-area">
                    <h3>🤖 AI Response</h3>
                    <div id="answer"></div>
                </div>
                
                <div class="examples">
                    <h3>💡 Try these example questions:</h3>
                    <button class="example-btn" onclick="setQuestion('What is artificial intelligence?')">What is AI?</button>
                    <button class="example-btn" onclick="setQuestion('How does machine learning work?')">Machine Learning</button>
                    <button class="example-btn" onclick="setQuestion('Explain quantum computing')">Quantum Computing</button>
                    <button class="example-btn" onclick="setQuestion('What are neural networks?')">Neural Networks</button>
                </div>
            </div>
        </div>

        <script>
            function setQuestion(question) {
                document.getElementById('questionInput').value = question;
            }
            
            function askQuestion() {
                const question = document.getElementById('questionInput').value.trim();
                const responseArea = document.getElementById('responseArea');
                const answer = document.getElementById('answer');
                
                if (!question) {
                    alert('Please enter a question!');
                    return;
                }
                
                // Show response area
                responseArea.style.display = 'block';
                answer.innerHTML = `
                    <div style="padding: 20px; text-align: center; color: #666;">
                        <h4>🚧 AI Features Coming Soon!</h4>
                        <p><strong>Your Question:</strong> "${question}"</p>
                        <p>The AI models are being integrated. For now, enjoy the working web interface!</p>
                        <p><a href="/">← Back to Home</a></p>
                    </div>
                `;
            }
        </script>
    </body>
    </html>
    '''

# Vercel serverless function
def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    app.run(debug=True)
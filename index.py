"""
AI Assistant - Main Application
"""
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🤖 Free AI Assistant</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh; padding: 20px;
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
            .header h1 { font-size: 2.5em; margin-bottom: 10px; }
            .header p { font-size: 1.1em; opacity: 0.9; }
            .chat-container { padding: 30px; }
            .input-section { 
                display: flex; gap: 15px; margin-bottom: 30px;
                align-items: flex-end;
            }
            .question-input { 
                flex: 1; padding: 15px; border: 2px solid #e1e5e9; 
                border-radius: 12px; font-size: 16px; resize: vertical;
                min-height: 60px; font-family: inherit;
            }
            .question-input:focus { 
                outline: none; border-color: #4facfe; 
                box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
            }
            .ask-button { 
                padding: 15px 30px; 
                background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
                color: white; border: none; border-radius: 12px; 
                cursor: pointer; font-size: 16px; font-weight: 600;
                transition: transform 0.2s;
            }
            .ask-button:hover { transform: translateY(-2px); }
            .response-section { 
                background: #f8f9fa; border-radius: 12px; 
                padding: 25px; margin-top: 20px; display: none;
            }
            .examples { 
                margin-top: 20px; padding: 20px; 
                background: #f8f9fa; border-radius: 12px;
            }
            .examples h3 { margin-bottom: 15px; color: #495057; }
            .example-questions { display: flex; flex-wrap: wrap; gap: 10px; }
            .example-btn { 
                background: white; border: 2px solid #dee2e6; 
                padding: 8px 15px; border-radius: 20px; 
                cursor: pointer; font-size: 14px; transition: all 0.2s;
            }
            .example-btn:hover { 
                border-color: #4facfe; color: #4facfe; 
            }
            .status-info {
                text-align: center; padding: 20px;
                background: #e8f5e8; border-radius: 10px;
                margin: 20px 0; color: #2d5a2d;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 Free AI Assistant</h1>
                <p>Ask me anything! I'll search the web and give you intelligent answers using free AI models.</p>
            </div>
            
            <div class="chat-container">
                <div class="status-info">
                    <h3>🎉 Your AI Assistant is Live!</h3>
                    <p>The web interface is working perfectly. AI models are being integrated.</p>
                </div>
                
                <div class="input-section">
                    <textarea 
                        id="questionInput" 
                        class="question-input" 
                        placeholder="Ask me anything... (e.g., What is artificial intelligence?)"
                        rows="2"
                    ></textarea>
                    <button id="askButton" class="ask-button" onclick="askQuestion()">Ask AI</button>
                </div>
                
                <div id="responseSection" class="response-section">
                    <div class="response-header">
                        <h3>🤖 AI Response</h3>
                    </div>
                    <div id="answer" class="answer"></div>
                </div>
                
                <div class="examples">
                    <h3>💡 Try these example questions:</h3>
                    <div class="example-questions">
                        <button class="example-btn" onclick="setQuestion('What is artificial intelligence?')">What is AI?</button>
                        <button class="example-btn" onclick="setQuestion('How does machine learning work?')">Machine Learning</button>
                        <button class="example-btn" onclick="setQuestion('Explain quantum computing')">Quantum Computing</button>
                        <button class="example-btn" onclick="setQuestion('What are neural networks?')">Neural Networks</button>
                        <button class="example-btn" onclick="setQuestion('Latest developments in AI')">AI News</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            function setQuestion(question) {
                document.getElementById('questionInput').value = question;
            }
            
            function askQuestion() {
                const question = document.getElementById('questionInput').value.trim();
                
                if (!question) {
                    alert('Please enter a question!');
                    return;
                }
                
                // Show response
                document.getElementById('answer').innerHTML = `
                    <div style="padding: 20px; text-align: center;">
                        <h4>🚧 AI Models Loading...</h4>
                        <p><strong>Your Question:</strong> "${question}"</p>
                        <p>The AI functionality is being integrated. Your web interface is working perfectly!</p>
                        <p style="margin-top: 15px;">
                            <a href="/health" style="color: #4facfe;">Check System Health</a> | 
                            <a href="https://github.com/AmandeepKaur-ADK/multimodal-rag" style="color: #4facfe;">View Source Code</a>
                        </p>
                    </div>
                `;
                
                document.getElementById('responseSection').style.display = 'block';
            }
        </script>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {
        'status': 'healthy',
        'message': 'AI Assistant is running perfectly!',
        'platform': 'Vercel',
        'version': '1.0.0',
        'features': ['Web Interface', 'Health Monitoring', 'AI Ready']
    }

@app.route('/api/status')
def status():
    return {
        'success': True,
        'status': 'online',
        'message': 'Ready for AI integration',
        'deployment': 'Vercel',
        'features': ['Web Interface', 'Health Monitoring', 'API Ready']
    }

# Vercel handler
def handler(request):
    return app(request.environ, lambda *args: None)

if __name__ == '__main__':
    app.run(debug=True)
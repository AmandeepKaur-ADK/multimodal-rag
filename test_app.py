"""
Ultra-simple test app
"""
from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return '''
    <html>
    <head><title>AI Assistant Test</title></head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h1>🎉 SUCCESS!</h1>
        <h2>Your AI Assistant is Working!</h2>
        <p>The server is running successfully.</p>
        <p><a href="/health">Health Check</a></p>
    </body>
    </html>
    '''

@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'Server is running'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
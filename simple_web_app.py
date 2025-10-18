"""
Simple Web Application - Minimal version for debugging
"""

import os
from flask import Flask, jsonify, render_template_string
from datetime import datetime

# Create Flask app
app = Flask(__name__)

# Simple HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 AI Assistant - Starting Up</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .container { max-width: 600px; margin: 0 auto; }
        .status { padding: 20px; background: #f0f8ff; border-radius: 10px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Free AI Assistant</h1>
        <div class="status">
            <h2>✅ Server is Running!</h2>
            <p>The application is starting up successfully.</p>
            <p>AI models will be loaded on first request.</p>
            <p><strong>Status:</strong> Ready to receive requests</p>
        </div>
        <p><a href="/api/health">Check Health Status</a></p>
    </div>
</body>
</html>
"""

@app.route('/')
def home():
    """Main web interface."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/ping')
def ping():
    """Simple ping endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'Server is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/health')
def health():
    """Basic health check."""
    return jsonify({
        'status': 'healthy',
        'message': 'AI Assistant server is running',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/ask', methods=['POST'])
def ask():
    """Placeholder for AI endpoint."""
    return jsonify({
        'success': False,
        'message': 'AI models are loading. Please try the full application.',
        'status': 'initializing'
    })

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Starting simple web server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
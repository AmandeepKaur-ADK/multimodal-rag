"""
Production-Ready Web Application for Free RAG Pipeline
Deployable AI Assistant with Web Interface - No API Keys Required!
"""

import sys
import os
import time
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_cors import CORS

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.free_rag_pipeline import create_free_rag_pipeline
from src.validation_manager import validation_manager

# Configure logging (create logs directory if it doesn't exist)
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/web_app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for API access

# Global pipeline instance (initialized once for performance)
pipeline = None
app_stats = {
    'total_queries': 0,
    'successful_queries': 0,
    'start_time': datetime.now(),
    'last_query_time': None
}

# Pipeline initialization moved to get_or_create_pipeline() for lazy loading

@app.route('/')
def home():
    """Main web interface."""
    return render_template('index.html')

@app.route('/ping')
def ping():
    """Simple ping endpoint for basic health check."""
    return jsonify({
        'status': 'ok',
        'message': 'AI Assistant is running',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/ask', methods=['POST'])
def ask_question():
    """API endpoint to process questions."""
    global app_stats
    
    try:
        # Get question from request
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({
                'success': False,
                'error': 'No question provided',
                'message': 'Please provide a question in the request body'
            }), 400
        
        question = data['question'].strip()
        
        # Update stats
        app_stats['total_queries'] += 1
        app_stats['last_query_time'] = datetime.now()
        
        logger.info(f"Processing question: {question[:100]}...")
        
        # Validate input
        validation_report = validation_manager.validate_user_input(question)
        
        if not validation_report.is_valid:
            return jsonify({
                'success': False,
                'error': 'Invalid input',
                'message': validation_report.get_user_message(),
                'suggestions': validation_report.recommendations
            }), 400
        
        # Get or initialize pipeline
        current_pipeline = get_or_create_pipeline()
        if current_pipeline is None:
            return jsonify({
                'success': False,
                'error': 'Pipeline initialization failed',
                'message': 'AI models are currently unavailable. Please try again later.'
            }), 503
        
        # Process with pipeline
        start_time = time.time()
        
        result = current_pipeline.process_query(
            text=question,
            max_results=3,
            request_id=f"web_query_{app_stats['total_queries']}"
        )
        
        processing_time = time.time() - start_time
        
        if result.success:
            app_stats['successful_queries'] += 1
            
            # Clean up answer for web display
            answer = result.response.answer
            if '**Sources:**' in answer:
                answer_parts = answer.split('**Sources:**')
                clean_answer = answer_parts[0].strip()
            else:
                clean_answer = answer
            
            response_data = {
                'success': True,
                'answer': clean_answer,
                'confidence': round(result.response.confidence_score * 100, 1),
                'model': result.response.model_used,
                'processing_time': round(processing_time, 2),
                'sources': result.response.sources,
                'warnings': result.warnings,
                'fallback_strategies': result.fallback_strategies_used,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Question processed successfully in {processing_time:.2f}s")
            return jsonify(response_data)
        
        else:
            logger.warning(f"Question processing failed: {result.error_message}")
            return jsonify({
                'success': False,
                'error': 'Processing failed',
                'message': result.error_message,
                'processing_time': round(processing_time, 2)
            }), 500
    
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': 'An unexpected error occurred. Please try again.'
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Get system health
        is_ready, warnings, critical_issues = validation_manager.check_system_readiness()
        
        # Get pipeline health if available
        pipeline_health = None
        pipeline_initialized = pipeline is not None
        if pipeline_initialized:
            try:
                pipeline_health = pipeline.get_pipeline_health()
            except:
                pipeline_health = "Pipeline health check failed"
        
        # Calculate uptime
        uptime_seconds = (datetime.now() - app_stats['start_time']).total_seconds()
        
        health_data = {
            'status': 'healthy' if is_ready and len(critical_issues) == 0 else 'degraded',
            'uptime_seconds': uptime_seconds,
            'system_ready': is_ready,
            'pipeline_initialized': pipeline_initialized,
            'warnings': warnings,
            'critical_issues': critical_issues,
            'pipeline_health': pipeline_health,
            'stats': {
                'total_queries': app_stats['total_queries'],
                'successful_queries': app_stats['successful_queries'],
                'success_rate': (app_stats['successful_queries'] / max(app_stats['total_queries'], 1)) * 100,
                'last_query': app_stats['last_query_time'].isoformat() if app_stats['last_query_time'] else None
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(health_data)
    
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/stats')
def get_stats():
    """Get application statistics."""
    try:
        uptime_seconds = (datetime.now() - app_stats['start_time']).total_seconds()
        
        stats_data = {
            'total_queries': app_stats['total_queries'],
            'successful_queries': app_stats['successful_queries'],
            'failed_queries': app_stats['total_queries'] - app_stats['successful_queries'],
            'success_rate': (app_stats['successful_queries'] / max(app_stats['total_queries'], 1)) * 100,
            'uptime_seconds': uptime_seconds,
            'uptime_hours': uptime_seconds / 3600,
            'start_time': app_stats['start_time'].isoformat(),
            'last_query_time': app_stats['last_query_time'].isoformat() if app_stats['last_query_time'] else None,
            'queries_per_hour': (app_stats['total_queries'] / max(uptime_seconds / 3600, 0.01)),
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(stats_data)
    
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}")
        return jsonify({'error': str(e)}), 500

# Create templates directory and HTML template
def create_templates():
    """Create templates directory and HTML file if they don't exist."""
    templates_dir = os.path.join(os.path.dirname(__file__), 'templates')
    os.makedirs(templates_dir, exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
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
            min-height: 100vh;
            padding: 20px;
        }
        .container { 
            max-width: 800px; 
            margin: 0 auto; 
            background: white; 
            border-radius: 20px; 
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white; 
            padding: 30px; 
            text-align: center; 
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .chat-container { padding: 30px; }
        .input-section { 
            display: flex; 
            gap: 15px; 
            margin-bottom: 30px;
            align-items: flex-end;
        }
        .question-input { 
            flex: 1; 
            padding: 15px; 
            border: 2px solid #e1e5e9; 
            border-radius: 12px; 
            font-size: 16px;
            resize: vertical;
            min-height: 60px;
            font-family: inherit;
        }
        .question-input:focus { 
            outline: none; 
            border-color: #4facfe; 
            box-shadow: 0 0 0 3px rgba(79, 172, 254, 0.1);
        }
        .ask-button { 
            padding: 15px 30px; 
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white; 
            border: none; 
            border-radius: 12px; 
            cursor: pointer; 
            font-size: 16px;
            font-weight: 600;
            transition: transform 0.2s;
        }
        .ask-button:hover { transform: translateY(-2px); }
        .ask-button:disabled { 
            opacity: 0.6; 
            cursor: not-allowed; 
            transform: none;
        }
        .response-section { 
            background: #f8f9fa; 
            border-radius: 12px; 
            padding: 25px; 
            margin-top: 20px;
            display: none;
        }
        .response-header { 
            display: flex; 
            justify-content: space-between; 
            align-items: center; 
            margin-bottom: 15px;
        }
        .confidence-badge { 
            background: #28a745; 
            color: white; 
            padding: 5px 12px; 
            border-radius: 20px; 
            font-size: 14px;
            font-weight: 600;
        }
        .answer { 
            font-size: 16px; 
            line-height: 1.6; 
            margin-bottom: 20px;
            color: #2c3e50;
        }
        .sources { margin-top: 20px; }
        .sources h4 { color: #495057; margin-bottom: 10px; }
        .source-item { 
            background: white; 
            padding: 12px; 
            border-radius: 8px; 
            margin-bottom: 8px;
            border-left: 4px solid #4facfe;
        }
        .source-url { 
            color: #4facfe; 
            text-decoration: none; 
            font-weight: 500;
        }
        .source-url:hover { text-decoration: underline; }
        .loading { 
            text-align: center; 
            padding: 40px;
            color: #6c757d;
        }
        .spinner { 
            border: 3px solid #f3f3f3;
            border-top: 3px solid #4facfe;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .error { 
            background: #f8d7da; 
            color: #721c24; 
            padding: 15px; 
            border-radius: 8px; 
            margin-top: 15px;
        }
        .stats { 
            display: flex; 
            justify-content: space-around; 
            background: #e9ecef; 
            padding: 15px; 
            border-radius: 8px; 
            margin-top: 15px;
            font-size: 14px;
        }
        .stat-item { text-align: center; }
        .stat-value { font-weight: 600; color: #495057; }
        .examples { 
            margin-top: 20px; 
            padding: 20px; 
            background: #f8f9fa; 
            border-radius: 12px;
        }
        .examples h3 { margin-bottom: 15px; color: #495057; }
        .example-questions { display: flex; flex-wrap: wrap; gap: 10px; }
        .example-btn { 
            background: white; 
            border: 2px solid #dee2e6; 
            padding: 8px 15px; 
            border-radius: 20px; 
            cursor: pointer; 
            font-size: 14px;
            transition: all 0.2s;
        }
        .example-btn:hover { 
            border-color: #4facfe; 
            color: #4facfe; 
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
                    <span id="confidenceBadge" class="confidence-badge"></span>
                </div>
                <div id="answer" class="answer"></div>
                <div id="sources" class="sources"></div>
                <div id="stats" class="stats"></div>
            </div>
            
            <div id="loading" class="loading" style="display: none;">
                <div class="spinner"></div>
                <p>🔍 Searching web and generating AI response...</p>
            </div>
            
            <div id="error" class="error" style="display: none;"></div>
            
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
        
        function showLoading() {
            document.getElementById('loading').style.display = 'block';
            document.getElementById('responseSection').style.display = 'none';
            document.getElementById('error').style.display = 'none';
            document.getElementById('askButton').disabled = true;
        }
        
        function hideLoading() {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('askButton').disabled = false;
        }
        
        function showError(message) {
            document.getElementById('error').innerHTML = message;
            document.getElementById('error').style.display = 'block';
            document.getElementById('responseSection').style.display = 'none';
        }
        
        function showResponse(data) {
            document.getElementById('answer').innerHTML = data.answer;
            document.getElementById('confidenceBadge').innerHTML = data.confidence + '% Confidence';
            
            // Show sources
            const sourcesDiv = document.getElementById('sources');
            if (data.sources && data.sources.length > 0) {
                let sourcesHtml = '<h4>📚 Sources:</h4>';
                data.sources.forEach((source, index) => {
                    sourcesHtml += `
                        <div class="source-item">
                            <a href="${source.url}" target="_blank" class="source-url">
                                ${index + 1}. ${source.url}
                            </a>
                            <div style="font-size: 12px; color: #6c757d; margin-top: 5px;">
                                Relevance: ${Math.round(source.similarity_score * 100)}%
                            </div>
                        </div>
                    `;
                });
                sourcesDiv.innerHTML = sourcesHtml;
            } else {
                sourcesDiv.innerHTML = '';
            }
            
            // Show stats
            document.getElementById('stats').innerHTML = `
                <div class="stat-item">
                    <div class="stat-value">${data.model}</div>
                    <div>Model</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.processing_time}s</div>
                    <div>Response Time</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value">${data.sources ? data.sources.length : 0}</div>
                    <div>Sources</div>
                </div>
            `;
            
            document.getElementById('responseSection').style.display = 'block';
            document.getElementById('error').style.display = 'none';
        }
        
        async function askQuestion() {
            const question = document.getElementById('questionInput').value.trim();
            
            if (!question) {
                showError('Please enter a question!');
                return;
            }
            
            showLoading();
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question: question })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showResponse(data);
                } else {
                    showError(`❌ ${data.message || data.error}`);
                }
                
            } catch (error) {
                showError('❌ Network error. Please check your connection and try again.');
                console.error('Error:', error);
            }
            
            hideLoading();
        }
        
        // Allow Enter key to submit (Shift+Enter for new line)
        document.getElementById('questionInput').addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
    </script>
</body>
</html>'''
    
    html_file = os.path.join(templates_dir, 'index.html')
    if not os.path.exists(html_file):
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

def get_or_create_pipeline():
    """Get existing pipeline or create new one (lazy initialization)."""
    global pipeline
    if pipeline is None:
        logger.info("Initializing RAG Pipeline on first request...")
        try:
            pipeline = create_free_rag_pipeline(
                model_name="microsoft/DialoGPT-small",
                enable_web_retrieval=True
            )
            logger.info("RAG Pipeline initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize pipeline: {e}")
            return None
    return pipeline

def main():
    """Main function to run the web application."""
    print("🚀 STARTING PRODUCTION WEB APPLICATION")
    print("=" * 60)
    print("Free AI Assistant - No API Keys Required!")
    print("=" * 60)
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    
    # Create templates
    create_templates()
    
    print("\n🌐 Starting web server...")
    print("📍 Access your AI Assistant at: http://localhost:5000")
    print("📊 Health check endpoint: http://localhost:5000/api/health")
    print("📈 Statistics endpoint: http://localhost:5000/api/stats")
    print("\n💡 Features:")
    print("   • Web search enabled for current information")
    print("   • Free AI models - no API costs")
    print("   • Comprehensive error handling")
    print("   • Real-time health monitoring")
    print("   • Usage statistics tracking")
    print("   • Lazy pipeline initialization (faster startup)")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        # Get port from environment (for Render deployment)
        port = int(os.environ.get('PORT', 5000))
        
        # Run Flask app
        app.run(
            host='0.0.0.0',  # Allow external connections
            port=port,
            debug=False,  # Production mode
            threaded=True  # Handle multiple requests
        )
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down web application...")
        if pipeline:
            pipeline.close()
        print("✅ Shutdown complete. Goodbye!")
    except Exception as e:
        logger.error(f"Web application error: {e}")
        print(f"❌ Application error: {e}")

if __name__ == "__main__":
    main()
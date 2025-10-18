"""
Web Interface for the multimodal RAG pipeline.
Provides user-facing web interface for query submission and API endpoints.
"""

import os
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string, redirect, url_for, flash
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
import logging
from pathlib import Path
from PIL import Image

from src.rag_pipeline import RAGPipeline, create_rag_pipeline, UserQuery
from src.admin_interface import AdminInterface
from config.settings import settings

logger = logging.getLogger(__name__)


class WebInterface:
    """
    Extended web interface that includes both user-facing and admin functionality.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080, upload_folder: str = "uploads"):
        """
        Initialize web interface.
        
        Args:
            host: Host to bind to
            port: Port to listen on
            upload_folder: Directory for uploaded files
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.app.secret_key = "rag_web_interface_secret_key"
        
        # Setup upload configuration
        self.upload_folder = Path(upload_folder)
        self.upload_folder.mkdir(exist_ok=True)
        
        self.app.config['UPLOAD_FOLDER'] = str(self.upload_folder)
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        
        # Allowed file extensions for images
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        
        # Initialize RAG pipeline
        self.pipeline = None
        self._initialize_pipeline()
        
        # Setup routes
        self._setup_routes()
        
        logger.info("Web interface initialized with user functionality")
    
    def run(self, debug: bool = False):
        """Run the web interface server."""
        self.app.run(host=self.host, port=self.port, debug=debug)
    
    def _setup_routes(self):
        """Setup all Flask routes."""
        self._setup_user_routes()
        self._setup_admin_routes()
    
    def _initialize_pipeline(self):
        """Initialize the RAG pipeline for query processing."""
        try:
            self.pipeline = create_rag_pipeline(
                vector_db_path=settings.VECTOR_DB_PATH,
                openai_api_key=settings.OPENAI_API_KEY,
                enable_web_retrieval=True
            )
            logger.info("RAG pipeline initialized for web interface")
        except Exception as e:
            logger.error(f"Failed to initialize RAG pipeline: {e}")
            self.pipeline = None
    
    def _allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed."""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in self.allowed_extensions
    

    
    def _setup_user_routes(self):
        """Setup Flask routes for user interface."""
        
        @self.app.route('/query')
        def query_interface():
            """Main query interface page."""
            return render_template_string(QUERY_INTERFACE_TEMPLATE)
        
        @self.app.route('/api/query', methods=['POST'])
        def process_query():
            """Process user query with optional image uploads."""
            try:
                # Check if pipeline is available
                if not self.pipeline:
                    return jsonify({
                        "status": "error",
                        "message": "RAG pipeline not available. Please check system configuration."
                    }), 503
                
                # Get query text
                query_text = request.form.get('query', '').strip()
                if not query_text:
                    return jsonify({
                        "status": "error",
                        "message": "Query text is required"
                    }), 400
                
                # Process uploaded images
                uploaded_images = []
                if 'images' in request.files:
                    files = request.files.getlist('images')
                    for file in files:
                        if file and file.filename and self._allowed_file(file.filename):
                            try:
                                # Save uploaded file
                                filename = secure_filename(file.filename)
                                unique_filename = f"{uuid.uuid4()}_{filename}"
                                file_path = self.upload_folder / unique_filename
                                file.save(str(file_path))
                                
                                # Validate image
                                try:
                                    with Image.open(file_path) as img:
                                        img.verify()  # Verify it's a valid image
                                    uploaded_images.append(str(file_path))
                                except Exception as img_error:
                                    logger.warning(f"Invalid image file {filename}: {img_error}")
                                    # Clean up invalid file
                                    if file_path.exists():
                                        file_path.unlink()
                                    
                            except Exception as e:
                                logger.error(f"Failed to process uploaded file {file.filename}: {e}")
                
                # Process query through pipeline
                start_time = time.time()
                
                result = self.pipeline.process_query(
                    text=query_text,
                    images=uploaded_images,
                    max_results=settings.TOP_K_RESULTS,
                    enable_fallback=True
                )
                
                processing_time = time.time() - start_time
                
                # Clean up uploaded files after processing
                for image_path in uploaded_images:
                    try:
                        Path(image_path).unlink(missing_ok=True)
                    except Exception as e:
                        logger.warning(f"Failed to clean up uploaded file {image_path}: {e}")
                
                # Format response with enhanced retrieval reporting
                response_data = {
                    "query_id": result.query.query_id,
                    "answer": result.response.answer if result.response else "No response generated",
                    "sources": self._format_sources(result.response.sources if result.response else []),
                    "confidence": result.response.confidence_score if result.response else 0.0,
                    "processing_time": processing_time,
                    "success": result.success,
                    "retrieval_summary": self._create_retrieval_summary(result),
                    "metadata": {
                        "retrieved_sources": result.retrieval_stats.get('sources_successful', 0),
                        "failed_sources": result.retrieval_stats.get('sources_failed', 0),
                        "embeddings_created": result.processing_stats.get('embeddings_created', 0),
                        "validation_passed": result.response.validation_passed if result.response else False,
                        "timestamp": datetime.now().isoformat(),
                        "search_strategy": result.retrieval_stats.get('search_strategy', 'web_search'),
                        "fallback_used": result.retrieval_stats.get('fallback_used', False)
                    }
                }
                
                if result.error_message:
                    response_data["error"] = result.error_message
                
                # Add query refinement suggestions if no sources found
                if len(result.response.sources if result.response else []) == 0:
                    response_data["query_suggestions"] = self._generate_query_suggestions(query_text)
                
                return jsonify({
                    "status": "success",
                    "data": response_data
                })
                
            except Exception as e:
                logger.error(f"Query processing failed: {e}")
                return jsonify({
                    "status": "error",
                    "message": f"Failed to process query: {str(e)}"
                }), 500
        
        @self.app.route('/api/query/status/<query_id>')
        def get_query_status(query_id: str):
            """Get status of a specific query (for future async processing)."""
            # For now, return simple status since we process synchronously
            return jsonify({
                "status": "success",
                "data": {
                    "query_id": query_id,
                    "status": "completed",
                    "message": "Query processing completed",
                    "progress": {
                        "current_step": "completed",
                        "steps_completed": 4,
                        "total_steps": 4,
                        "estimated_time_remaining": 0
                    }
                }
            })
        
        @self.app.route('/api/query/validate', methods=['POST'])
        def validate_query():
            """Validate query input before processing."""
            try:
                query_text = request.form.get('query', '').strip()
                
                validation_result = {
                    "valid": True,
                    "issues": [],
                    "suggestions": []
                }
                
                # Basic validation
                if not query_text:
                    validation_result["valid"] = False
                    validation_result["issues"].append("Query text is required")
                elif len(query_text) < 3:
                    validation_result["issues"].append("Query is very short - consider adding more details")
                elif len(query_text) > 1000:
                    validation_result["issues"].append("Query is very long - consider breaking it into smaller parts")
                
                # Check for uploaded files
                if 'images' in request.files:
                    files = request.files.getlist('images')
                    valid_images = 0
                    for file in files:
                        if file and file.filename and self._allowed_file(file.filename):
                            valid_images += 1
                        elif file and file.filename:
                            validation_result["issues"].append(f"Unsupported image format: {file.filename}")
                    
                    if valid_images > 0:
                        validation_result["suggestions"].append(f"Found {valid_images} valid image(s) for multimodal analysis")
                
                # Add helpful suggestions
                if validation_result["valid"] and not validation_result["issues"]:
                    if "?" not in query_text:
                        validation_result["suggestions"].append("Consider phrasing as a question for better results")
                    
                    if not any(word in query_text.lower() for word in ["latest", "recent", "current", "new"]):
                        validation_result["suggestions"].append("Add time-related keywords for current information")
                
                return jsonify({
                    "status": "success",
                    "data": validation_result
                })
                
            except Exception as e:
                logger.error(f"Query validation failed: {e}")
                return jsonify({
                    "status": "error",
                    "message": f"Validation failed: {str(e)}"
                }), 500
        
        @self.app.route('/api/pipeline/health')
        def get_pipeline_health():
            """Get RAG pipeline health status."""
            try:
                if not self.pipeline:
                    return jsonify({
                        "status": "error",
                        "message": "Pipeline not initialized"
                    }), 503
                
                health = self.pipeline.get_pipeline_health()
                
                return jsonify({
                    "status": "success",
                    "data": health
                })
                
            except Exception as e:
                logger.error(f"Failed to get pipeline health: {e}")
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        @self.app.route('/api/pipeline/clear', methods=['POST'])
        def clear_pipeline_data():
            """Clear pipeline vector database."""
            try:
                if not self.pipeline:
                    return jsonify({
                        "status": "error",
                        "message": "Pipeline not initialized"
                    }), 503
                
                self.pipeline.clear_vector_database()
                
                return jsonify({
                    "status": "success",
                    "message": "Pipeline data cleared successfully"
                })
                
            except Exception as e:
                logger.error(f"Failed to clear pipeline data: {e}")
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
        
        # Main dashboard route
        @self.app.route('/', endpoint='main_dashboard')
        def main_dashboard():
            """Main dashboard with links to both admin and user interfaces."""
            return render_template_string(MAIN_DASHBOARD_TEMPLATE)
    
    def _setup_admin_routes(self):
        """Setup admin routes."""
        @self.app.route('/admin')
        def admin_dashboard():
            """Admin dashboard page."""
            from src.admin_interface import DASHBOARD_TEMPLATE
            return render_template_string(DASHBOARD_TEMPLATE)
        
        @self.app.route('/api/status')
        def get_status():
            """Get system status and configuration."""
            try:
                from src.config_manager import config_manager
                from src.resource_manager import resource_manager
                
                config = config_manager.get_config()
                resource_stats = resource_manager.get_resource_stats()
                performance = config_manager.get_performance_summary()
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "config": {
                            "version": config.version,
                            "last_updated": config.last_updated,
                            "retrieval": {
                                "max_concurrent_requests": config.retrieval.max_concurrent_requests,
                                "max_retrieval_time": config.retrieval.max_retrieval_time,
                                "request_timeout": config.retrieval.request_timeout
                            },
                            "domains": {
                                "blocked_count": len(config.domains.blocked_domains),
                                "blocked_domains": config.domains.blocked_domains[:10]
                            }
                        },
                        "resource_stats": resource_stats,
                        "performance": performance,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Failed to get system status: {e}")
                return jsonify({
                    "status": "error",
                    "message": str(e)
                }), 500
    
    def _format_sources(self, sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Format sources for display in the web interface."""
        formatted_sources = []
        
        for source in sources:
            formatted_source = {
                "url": source.get("url", "Unknown"),
                "title": source.get("title", "Untitled"),
                "relevance_score": round(source.get("relevance_score", 0.0), 3),
                "timestamp": source.get("timestamp", "Unknown"),
                "content_preview": (source.get("content", "")[:200] + "...") if len(source.get("content", "")) > 200 else source.get("content", ""),
                "retrieval_status": source.get("retrieval_status", "success")
            }
            formatted_sources.append(formatted_source)
        
        return formatted_sources
    
    def _create_retrieval_summary(self, result) -> Dict[str, Any]:
        """Create a summary of the retrieval process for transparency."""
        retrieval_stats = result.retrieval_stats
        
        summary = {
            "total_sources_attempted": retrieval_stats.get('sources_attempted', 0),
            "successful_retrievals": retrieval_stats.get('sources_successful', 0),
            "failed_retrievals": retrieval_stats.get('sources_failed', 0),
            "search_terms_used": retrieval_stats.get('search_terms', []),
            "domains_consulted": retrieval_stats.get('domains_consulted', []),
            "retrieval_time": retrieval_stats.get('retrieval_time', 0),
            "strategy_used": retrieval_stats.get('search_strategy', 'web_search')
        }
        
        # Add failure details if any
        if retrieval_stats.get('failed_sources'):
            summary["failure_details"] = retrieval_stats['failed_sources']
        
        return summary
    
    def _generate_query_suggestions(self, query: str) -> List[str]:
        """Generate query refinement suggestions when no sources are found."""
        suggestions = []
        
        # Basic suggestions based on query analysis
        if len(query.split()) < 3:
            suggestions.append("Try adding more specific keywords to your query")
        
        if "?" not in query:
            suggestions.append("Try rephrasing as a specific question")
        
        if not any(word in query.lower() for word in ["latest", "recent", "current", "new"]):
            suggestions.append("Add time-related keywords like 'latest' or 'recent' for current information")
        
        # Generic helpful suggestions
        suggestions.extend([
            "Try using different synonyms or related terms",
            "Break complex questions into simpler parts",
            "Include specific names, dates, or locations if relevant"
        ])
        
        return suggestions[:4]  # Limit to 4 suggestions
    
    def close(self):
        """Clean up resources."""
        try:
            if self.pipeline:
                self.pipeline.close()
            
            # Clean up upload folder
            if self.upload_folder.exists():
                for file_path in self.upload_folder.glob("*"):
                    try:
                        file_path.unlink()
                    except Exception as e:
                        logger.warning(f"Failed to clean up file {file_path}: {e}")
            
            logger.info("Web interface closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing web interface: {e}")


# HTML template for the main dashboard
MAIN_DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Multimodal RAG Pipeline</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 30px; border-radius: 8px; margin-bottom: 30px; text-align: center; }
        .card { background: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
        .btn { display: inline-block; background: #3498db; color: white; padding: 15px 30px; text-decoration: none; border-radius: 4px; margin: 10px; font-size: 16px; }
        .btn:hover { background: #2980b9; }
        .btn-admin { background: #e74c3c; }
        .btn-admin:hover { background: #c0392b; }
        .description { color: #7f8c8d; margin-bottom: 20px; line-height: 1.6; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Multimodal RAG Pipeline</h1>
            <p>Intelligent Question Answering with Real-time Web Retrieval</p>
        </div>
        
        <div class="card">
            <h2>Query Interface</h2>
            <p class="description">
                Ask questions and upload images to get comprehensive answers powered by real-time web retrieval 
                and multimodal AI understanding.
            </p>
            <a href="/query" class="btn">Start Asking Questions</a>
        </div>
        
        <div class="card">
            <h2>System Administration</h2>
            <p class="description">
                Configure system settings, monitor performance, and manage the RAG pipeline components.
            </p>
            <a href="/admin" class="btn btn-admin">Admin Dashboard</a>
        </div>
    </div>
</body>
</html>
"""

# HTML template for the query interface
QUERY_INTERFACE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>RAG Pipeline - Ask Questions</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .form-group { margin-bottom: 20px; }
        .form-group label { display: block; margin-bottom: 8px; font-weight: bold; color: #2c3e50; }
        .form-group textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; font-size: 16px; min-height: 100px; resize: vertical; }
        .form-group input[type="file"] { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background: #3498db; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
        .btn:hover { background: #2980b9; }
        .btn:disabled { background: #bdc3c7; cursor: not-allowed; }
        .btn-secondary { background: #95a5a6; }
        .btn-secondary:hover { background: #7f8c8d; }
        .loading { display: none; text-align: center; padding: 20px; color: #7f8c8d; }
        .loading.show { display: block; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #3498db; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 0 auto 10px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .result { margin-top: 20px; }
        .answer { background: #e8f5e8; padding: 20px; border-radius: 4px; border-left: 4px solid #27ae60; margin-bottom: 20px; }
        .sources { background: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 4px solid #3498db; }
        .source-item { margin-bottom: 15px; padding: 10px; background: white; border-radius: 4px; border: 1px solid #e9ecef; }
        .source-url { color: #3498db; text-decoration: none; font-weight: bold; }
        .source-url:hover { text-decoration: underline; }
        .source-relevance { color: #7f8c8d; font-size: 12px; }
        .metadata { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 15px; }
        .metadata-item { display: inline-block; margin-right: 20px; color: #7f8c8d; font-size: 14px; }
        .error { background: #fdf2f2; color: #e74c3c; padding: 15px; border-radius: 4px; border-left: 4px solid #e74c3c; }
        .file-preview { margin-top: 10px; }
        .file-preview img { max-width: 200px; max-height: 200px; border-radius: 4px; margin: 5px; border: 1px solid #ddd; }
        .example-queries { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-bottom: 20px; }
        .example-query { background: white; padding: 10px; margin: 5px 0; border-radius: 4px; cursor: pointer; border: 1px solid #e9ecef; }
        .example-query:hover { background: #e9ecef; }
        .nav { margin-bottom: 20px; }
        .nav a { color: #3498db; text-decoration: none; margin-right: 15px; }
        .nav a:hover { text-decoration: underline; }
        .retrieval-summary { background: #f8f9fa; padding: 15px; border-radius: 4px; margin-top: 15px; border-left: 4px solid #17a2b8; }
        .summary-stats { display: flex; flex-wrap: wrap; gap: 15px; margin-bottom: 10px; }
        .summary-item { display: flex; flex-direction: column; }
        .summary-label { font-size: 12px; color: #6c757d; text-transform: uppercase; }
        .summary-value { font-weight: bold; }
        .summary-value.success { color: #28a745; }
        .summary-value.failed { color: #dc3545; }
        .domains-consulted { margin-top: 10px; font-size: 14px; color: #6c757d; }
        .query-suggestions { background: #fff3cd; padding: 15px; border-radius: 4px; margin-top: 15px; border-left: 4px solid #ffc107; }
        .query-suggestions ul { margin: 10px 0; padding-left: 20px; }
        .query-suggestions li { margin-bottom: 5px; color: #856404; }
        .progress-indicator { display: none; position: fixed; top: 20px; right: 20px; background: white; padding: 15px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); z-index: 1000; }
        .progress-indicator.show { display: block; }
        .progress-step { margin: 5px 0; font-size: 14px; }
        .progress-step.active { color: #3498db; font-weight: bold; }
        .progress-step.completed { color: #27ae60; }
        .progress-step.failed { color: #e74c3c; }
        .validation-feedback { margin-top: 8px; font-size: 14px; }
        .validation-feedback.valid { color: #28a745; }
        .validation-feedback.invalid { color: #dc3545; }
        .validation-feedback.suggestion { color: #17a2b8; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Ask Questions</h1>
            <p>Get intelligent answers powered by real-time web retrieval and multimodal AI</p>
        </div>
        
        <div class="nav">
            <a href="/">← Back to Dashboard</a>
            <a href="/admin">Admin Panel</a>
        </div>
        
        <div class="card">
            <div class="example-queries">
                <h3>Example Questions</h3>
                <div class="example-query" onclick="setQuery('What are the latest developments in artificial intelligence?')">
                    What are the latest developments in artificial intelligence?
                </div>
                <div class="example-query" onclick="setQuery('How does renewable energy impact climate change?')">
                    How does renewable energy impact climate change?
                </div>
                <div class="example-query" onclick="setQuery('What are the current trends in machine learning?')">
                    What are the current trends in machine learning?
                </div>
            </div>
            
            <form id="query-form" enctype="multipart/form-data">
                <div class="form-group">
                    <label for="query">Your Question</label>
                    <textarea id="query" name="query" placeholder="Ask any question... You can also upload images to provide additional context." required oninput="validateQuery()"></textarea>
                    <div id="query-validation" class="validation-feedback"></div>
                </div>
                
                <div class="form-group">
                    <label for="images">Upload Images (Optional)</label>
                    <input type="file" id="images" name="images" multiple accept="image/*" onchange="previewFiles()">
                    <div id="file-preview" class="file-preview"></div>
                    <small style="color: #7f8c8d;">Supported formats: PNG, JPG, JPEG, GIF, WebP (Max 16MB per file)</small>
                </div>
                
                <button type="submit" class="btn" id="submit-btn">Get Answer</button>
                <button type="button" class="btn btn-secondary" onclick="clearForm()">Clear</button>
            </form>
            
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Processing your question and retrieving relevant information...</p>
            </div>
        </div>
        
        <div id="result" class="result" style="display: none;"></div>
        
        <!-- Progress Indicator -->
        <div id="progress-indicator" class="progress-indicator">
            <h4>Processing Query...</h4>
            <div id="progress-step-1" class="progress-step">🔍 Analyzing query</div>
            <div id="progress-step-2" class="progress-step">🌐 Retrieving web content</div>
            <div id="progress-step-3" class="progress-step">🧠 Processing information</div>
            <div id="progress-step-4" class="progress-step">✍️ Generating response</div>
        </div>
    </div>

    <script>
        document.getElementById('query-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const submitBtn = document.getElementById('submit-btn');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            const progressIndicator = document.getElementById('progress-indicator');
            
            // Show loading state and progress
            submitBtn.disabled = true;
            loading.classList.add('show');
            result.style.display = 'none';
            progressIndicator.classList.add('show');
            
            // Simulate progress steps
            const steps = ['progress-step-1', 'progress-step-2', 'progress-step-3', 'progress-step-4'];
            let currentStep = 0;
            
            const progressInterval = setInterval(() => {
                if (currentStep < steps.length) {
                    // Mark current step as active
                    document.getElementById(steps[currentStep]).classList.add('active');
                    
                    // Mark previous step as completed
                    if (currentStep > 0) {
                        const prevStep = document.getElementById(steps[currentStep - 1]);
                        prevStep.classList.remove('active');
                        prevStep.classList.add('completed');
                    }
                    
                    currentStep++;
                }
            }, 800);
            
            try {
                const formData = new FormData(e.target);
                
                const response = await fetch('/api/query', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                // Complete all progress steps
                clearInterval(progressInterval);
                steps.forEach(stepId => {
                    const step = document.getElementById(stepId);
                    step.classList.remove('active');
                    step.classList.add('completed');
                });
                
                if (data.status === 'success') {
                    displayResult(data.data);
                } else {
                    displayError(data.message);
                }
                
            } catch (error) {
                // Mark current step as failed
                clearInterval(progressInterval);
                if (currentStep < steps.length) {
                    document.getElementById(steps[currentStep]).classList.add('failed');
                }
                displayError('Failed to process query: ' + error.message);
            } finally {
                submitBtn.disabled = false;
                loading.classList.remove('show');
                progressIndicator.classList.remove('show');
                
                // Reset progress steps
                setTimeout(() => {
                    steps.forEach(stepId => {
                        const step = document.getElementById(stepId);
                        step.classList.remove('active', 'completed', 'failed');
                    });
                }, 2000);
            }
        });
        
        function displayResult(data) {
            const result = document.getElementById('result');
            
            let sourcesHtml = '';
            if (data.sources && data.sources.length > 0) {
                sourcesHtml = `
                    <div class="sources">
                        <h3>Sources (${data.sources.length})</h3>
                        ${data.sources.map(source => `
                            <div class="source-item">
                                <a href="${source.url}" target="_blank" class="source-url">${source.title || source.url}</a>
                                <div class="source-relevance">Relevance: ${(source.relevance_score * 100).toFixed(1)}%</div>
                                <div style="margin-top: 5px; color: #7f8c8d; font-size: 14px;">${source.content_preview}</div>
                                ${source.retrieval_status !== 'success' ? `<div style="color: #e74c3c; font-size: 12px;">⚠️ ${source.retrieval_status}</div>` : ''}
                            </div>
                        `).join('')}
                    </div>
                `;
            }
            
            // Retrieval summary section
            let retrievalSummaryHtml = '';
            if (data.retrieval_summary) {
                const summary = data.retrieval_summary;
                retrievalSummaryHtml = `
                    <div class="retrieval-summary">
                        <h3>Retrieval Summary</h3>
                        <div class="summary-stats">
                            <div class="summary-item">
                                <span class="summary-label">Sources Attempted:</span>
                                <span class="summary-value">${summary.total_sources_attempted || 0}</span>
                            </div>
                            <div class="summary-item">
                                <span class="summary-label">Successful:</span>
                                <span class="summary-value success">${summary.successful_retrievals || 0}</span>
                            </div>
                            ${summary.failed_retrievals > 0 ? `
                                <div class="summary-item">
                                    <span class="summary-label">Failed:</span>
                                    <span class="summary-value failed">${summary.failed_retrievals}</span>
                                </div>
                            ` : ''}
                            <div class="summary-item">
                                <span class="summary-label">Strategy:</span>
                                <span class="summary-value">${summary.strategy_used || 'web_search'}</span>
                            </div>
                        </div>
                        ${summary.domains_consulted && summary.domains_consulted.length > 0 ? `
                            <div class="domains-consulted">
                                <strong>Domains Consulted:</strong> ${summary.domains_consulted.join(', ')}
                            </div>
                        ` : ''}
                    </div>
                `;
            }
            
            // Query suggestions section (when no sources found)
            let suggestionsHtml = '';
            if (data.query_suggestions && data.query_suggestions.length > 0) {
                suggestionsHtml = `
                    <div class="query-suggestions">
                        <h3>💡 Suggestions to Improve Your Query</h3>
                        <ul>
                            ${data.query_suggestions.map(suggestion => `<li>${suggestion}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            
            result.innerHTML = `
                <div class="card">
                    <div class="answer">
                        <h3>Answer</h3>
                        <p>${data.answer.replace(/\\n/g, '<br>')}</p>
                    </div>
                    
                    ${sourcesHtml}
                    ${retrievalSummaryHtml}
                    ${suggestionsHtml}
                    
                    <div class="metadata">
                        <div class="metadata-item"><strong>Confidence:</strong> ${(data.confidence * 100).toFixed(1)}%</div>
                        <div class="metadata-item"><strong>Processing Time:</strong> ${data.processing_time.toFixed(2)}s</div>
                        <div class="metadata-item"><strong>Sources Retrieved:</strong> ${data.metadata.retrieved_sources}</div>
                        ${data.metadata.failed_sources > 0 ? `<div class="metadata-item"><strong>Failed Sources:</strong> ${data.metadata.failed_sources}</div>` : ''}
                        <div class="metadata-item"><strong>Query ID:</strong> ${data.query_id}</div>
                    </div>
                    
                    ${data.error ? `<div class="error">Warning: ${data.error}</div>` : ''}
                </div>
            `;
            
            result.style.display = 'block';
            result.scrollIntoView({ behavior: 'smooth' });
        }
        
        function displayError(message) {
            const result = document.getElementById('result');
            result.innerHTML = `
                <div class="card">
                    <div class="error">
                        <h3>Error</h3>
                        <p>${message}</p>
                    </div>
                </div>
            `;
            result.style.display = 'block';
        }
        
        function setQuery(query) {
            document.getElementById('query').value = query;
        }
        
        function clearForm() {
            document.getElementById('query-form').reset();
            document.getElementById('file-preview').innerHTML = '';
            document.getElementById('result').style.display = 'none';
        }
        
        function previewFiles() {
            const fileInput = document.getElementById('images');
            const preview = document.getElementById('file-preview');
            preview.innerHTML = '';
            
            for (let i = 0; i < fileInput.files.length; i++) {
                const file = fileInput.files[i];
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        preview.appendChild(img);
                    };
                    reader.readAsDataURL(file);
                }
            }
            
            // Trigger validation after file selection
            validateQuery();
        }
        
        let validationTimeout;
        function validateQuery() {
            clearTimeout(validationTimeout);
            
            validationTimeout = setTimeout(async () => {
                const query = document.getElementById('query').value.trim();
                const validationDiv = document.getElementById('query-validation');
                
                if (!query) {
                    validationDiv.innerHTML = '';
                    return;
                }
                
                try {
                    const formData = new FormData();
                    formData.append('query', query);
                    
                    // Add images if any
                    const fileInput = document.getElementById('images');
                    if (fileInput.files.length > 0) {
                        for (let i = 0; i < fileInput.files.length; i++) {
                            formData.append('images', fileInput.files[i]);
                        }
                    }
                    
                    const response = await fetch('/api/query/validate', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    if (data.status === 'success') {
                        const validation = data.data;
                        let html = '';
                        
                        if (validation.issues && validation.issues.length > 0) {
                            html += `<div class="invalid">⚠️ ${validation.issues.join(', ')}</div>`;
                        }
                        
                        if (validation.suggestions && validation.suggestions.length > 0) {
                            html += `<div class="suggestion">💡 ${validation.suggestions.join(', ')}</div>`;
                        }
                        
                        if (validation.valid && !validation.issues.length) {
                            html += `<div class="valid">✅ Query looks good!</div>`;
                        }
                        
                        validationDiv.innerHTML = html;
                    }
                } catch (error) {
                    // Silently fail validation - don't show errors for this
                    console.log('Validation request failed:', error);
                }
            }, 500); // Debounce validation requests
        }
    </script>
</body>
</html>
"""


# Factory function to create web interface
def create_web_interface(host: str = "127.0.0.1", port: int = 8080, upload_folder: str = "uploads") -> WebInterface:
    """
    Create a web interface instance.
    
    Args:
        host: Host to bind to
        port: Port to listen on
        upload_folder: Directory for uploaded files
        
    Returns:
        WebInterface instance
    """
    return WebInterface(host=host, port=port, upload_folder=upload_folder)
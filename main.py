"""
Main execution script for the Multimodal RAG Pipeline.
Demonstrates end-to-end usage of the RAG Pipeline orchestrator with administration features.
"""

import os
import sys
import logging
import argparse
from typing import List, Optional
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from config.settings import settings
from src.rag_pipeline import RAGPipeline, create_rag_pipeline
from src.config_manager import config_manager
from src.resource_manager import resource_manager
from src.admin_interface import create_admin_interface
from src.web_interface import create_web_interface

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def process_query_simple(pipeline: RAGPipeline, query: str) -> dict:
    """
    Simple wrapper to process a query and return formatted results.
    
    Args:
        pipeline: RAG pipeline instance
        query: User's question
        
    Returns:
        Dictionary with response and metadata
    """
    try:
        # Process query through the pipeline
        result = pipeline.process_query(
            text=query,
            max_results=settings.TOP_K_RESULTS,
            enable_fallback=True
        )
        
        # Format response for display
        return {
            "answer": result.response.answer,
            "sources": result.response.sources,
            "confidence": result.response.confidence_score,
            "validation_passed": result.response.validation_passed,
            "retrieved_content_count": result.retrieval_stats.get('sources_successful', 0),
            "stored_embeddings_count": result.processing_stats.get('embeddings_stored', 0),
            "search_results_count": len(result.response.sources),
            "processing_time": result.pipeline_stats.get('total_time', 0),
            "success": result.success,
            "error": result.error_message
        }
        
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        return {
            "answer": f"I apologize, but I encountered an error: {str(e)}",
            "sources": [],
            "confidence": 0.0,
            "error": str(e),
            "success": False
        }


def run_interactive_mode():
    """Run the interactive query mode."""
    print("=== Multimodal RAG Pipeline ===\n")
    
    # Check environment setup
    if not settings.OPENAI_API_KEY:
        print("❌ Error: OPENAI_API_KEY not set in environment variables")
        print("Please copy .env.example to .env and add your OpenAI API key")
        return
    
    try:
        # Initialize pipeline
        print("🚀 Initializing RAG pipeline...")
        pipeline = create_rag_pipeline(
            vector_db_path=settings.VECTOR_DB_PATH,
            openai_api_key=settings.OPENAI_API_KEY,
            enable_web_retrieval=True
        )
        print("✅ Pipeline initialized successfully\n")
        
        # Show current stats
        health = pipeline.get_pipeline_health()
        print(f"📊 Pipeline status: {health.get('status', 'unknown')}")
        print(f"📊 Total embeddings: {health.get('vector_db', {}).get('total_embeddings', 0)}")
        print(f"📊 Web retrieval: {'enabled' if health.get('web_retrieval_enabled') else 'disabled'}\n")
        
        # Example queries
        example_queries = [
            "What are the latest developments in artificial intelligence?",
            "How does machine learning work?",
            "What are the benefits of renewable energy?"
        ]
        
        print("🔍 Example queries you can try:")
        for i, query in enumerate(example_queries, 1):
            print(f"  {i}. {query}")
        
        print("\n" + "="*50)
        print("Interactive Mode - Enter your queries (type 'quit' to exit)")
        print("="*50)
        
        while True:
            try:
                # Get user input
                user_query = input("\n💬 Your question: ").strip()
                
                if user_query.lower() in ['quit', 'exit', 'q']:
                    break
                
                if not user_query:
                    continue
                
                print(f"\n🔄 Processing: {user_query}")
                print("-" * 40)
                
                # Process query
                result = process_query_simple(pipeline, user_query)
                
                # Display results
                print(f"\n📝 Answer:")
                print(result['answer'])
                
                print(f"\n📈 Metadata:")
                print(f"  • Confidence: {result['confidence']:.2f}")
                print(f"  • Sources used: {len(result['sources'])}")
                print(f"  • Content retrieved: {result.get('retrieved_content_count', 0)}")
                print(f"  • Processing time: {result.get('processing_time', 0):.2f}s")
                print(f"  • Success: {result.get('success', False)}")
                
                if result.get('error'):
                    print(f"  • Error: {result['error']}")
                
                # Show sources if available
                if result['sources']:
                    print(f"\n📚 Sources:")
                    for i, source in enumerate(result['sources'][:3], 1):
                        print(f"  {i}. {source.get('url', 'Unknown')} (relevance: {source.get('relevance_score', 0):.2f})")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error processing query: {e}")
                continue
        
        # Clean up
        print("\n🧹 Cleaning up...")
        pipeline.close()
        print("✅ Pipeline closed successfully")
    
    except Exception as e:
        print(f"❌ Failed to initialize pipeline: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check your .env file has the correct API keys")
        print("3. Ensure data directories exist: mkdir -p data/vector_db logs")
        print("4. Check that all required models can be downloaded (sentence-transformers, CLIP)")


def run_admin_interface(host: str = "127.0.0.1", port: int = 8080, debug: bool = False):
    """Run the web admin interface."""
    print(f"🌐 Starting RAG Pipeline Web Interface on http://{host}:{port}")
    print("Press Ctrl+C to stop")
    
    try:
        web_interface = create_web_interface(host=host, port=port)
        web_interface.run(debug=debug)
    except KeyboardInterrupt:
        print("\n👋 Web interface stopped")
    except Exception as e:
        print(f"❌ Failed to start web interface: {e}")


def show_system_status():
    """Show current system status."""
    print("=== RAG Pipeline System Status ===\n")
    
    try:
        # Get configuration
        config = config_manager.get_config()
        print(f"📋 Configuration Version: {config.version}")
        print(f"📋 Last Updated: {config.last_updated}")
        
        # Get resource stats
        resource_stats = resource_manager.get_resource_stats()
        print(f"\n💾 Resource Usage:")
        print(f"  Memory: {resource_stats['current']['memory_usage_mb']:.1f} MB")
        print(f"  CPU: {resource_stats['current']['cpu_usage_percent']:.1f}%")
        print(f"  Active Requests: {resource_stats['current']['active_requests']}")
        print(f"  Disk Usage: {resource_stats['current']['disk_usage_mb']:.1f} MB")
        
        # Get performance summary
        performance = config_manager.get_performance_summary()
        print(f"\n⚡ Performance:")
        print(f"  Status: {performance.get('status', 'unknown')}")
        if performance.get('avg_response_time'):
            print(f"  Avg Response Time: {performance['avg_response_time']:.2f}s")
        if performance.get('failure_rate') is not None:
            print(f"  Failure Rate: {performance['failure_rate']:.1%}")
        
        # Show configuration highlights
        print(f"\n⚙️  Configuration:")
        print(f"  Max Concurrent Requests: {config.retrieval.max_concurrent_requests}")
        print(f"  Max Retrieval Time: {config.retrieval.max_retrieval_time}s")
        print(f"  Request Timeout: {config.retrieval.request_timeout}s")
        print(f"  Blocked Domains: {len(config.domains.blocked_domains)}")
        
        if config.domains.blocked_domains:
            print(f"    - {', '.join(config.domains.blocked_domains[:3])}")
            if len(config.domains.blocked_domains) > 3:
                print(f"    - ... and {len(config.domains.blocked_domains) - 3} more")
        
    except Exception as e:
        print(f"❌ Failed to get system status: {e}")


def main():
    """Main entry point with command-line argument parsing."""
    parser = argparse.ArgumentParser(
        description="Multimodal RAG Pipeline with Administration Features",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Run interactive query mode
  python main.py --admin            # Start web admin interface
  python main.py --status           # Show system status
  python main.py --admin --port 9000  # Start admin on custom port
        """
    )
    
    parser.add_argument('--admin', action='store_true', 
                       help='Start web interface (includes both user and admin functionality)')
    parser.add_argument('--status', action='store_true',
                       help='Show system status and exit')
    parser.add_argument('--host', default='127.0.0.1',
                       help='Host for admin interface (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080,
                       help='Port for admin interface (default: 8080)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode for web interface')
    
    args = parser.parse_args()
    
    if args.status:
        show_system_status()
    elif args.admin:
        run_admin_interface(host=args.host, port=args.port, debug=args.debug)
    else:
        run_interactive_mode()


if __name__ == "__main__":
    main()
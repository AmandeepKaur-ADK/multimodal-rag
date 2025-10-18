"""
Demonstration of the multimodal RAG pipeline web interface.
Shows how to start the web server and interact with it programmatically.
"""

import os
import sys
import time
import threading
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.web_interface import create_web_interface
from examples.api_client_example import RAGPipelineClient


def start_web_server(host="127.0.0.1", port=8080):
    """
    Start the web interface server in a separate thread.
    
    Args:
        host: Host to bind to
        port: Port to listen on
    """
    print(f"🌐 Starting RAG Pipeline Web Interface on http://{host}:{port}")
    print("📝 Available endpoints:")
    print(f"   • Main Dashboard: http://{host}:{port}/")
    print(f"   • Query Interface: http://{host}:{port}/query")
    print(f"   • Admin Panel: http://{host}:{port}/admin")
    print(f"   • API Health: http://{host}:{port}/api/pipeline/health")
    print(f"   • Submit Query: POST http://{host}:{port}/api/query")
    print()
    
    try:
        # Create web interface
        web_interface = create_web_interface(host=host, port=port)
        
        # Start server (this will block)
        web_interface.run(debug=False)
        
    except KeyboardInterrupt:
        print("\n👋 Web interface stopped by user")
    except Exception as e:
        print(f"❌ Failed to start web interface: {e}")


def demo_api_client(host="127.0.0.1", port=8080):
    """
    Demonstrate API client functionality.
    
    Args:
        host: Host of the web interface
        port: Port of the web interface
    """
    print("🔧 Testing API Client...")
    
    # Wait a moment for server to start
    time.sleep(2)
    
    client = RAGPipelineClient(f"http://{host}:{port}")
    
    # Test health endpoint
    print("1. Checking pipeline health...")
    health = client.get_pipeline_health()
    if health.get("status") == "success":
        print(f"   ✅ Pipeline Status: {health['data'].get('status', 'unknown')}")
    else:
        print(f"   ❌ Health check failed: {health.get('message', 'Unknown error')}")
    
    # Test query submission
    print("\n2. Submitting test query...")
    test_query = "What are the latest developments in artificial intelligence?"
    
    result = client.submit_query(test_query)
    if result.get("status") == "success":
        data = result["data"]
        print(f"   ✅ Query processed successfully")
        print(f"   📝 Answer: {data['answer'][:100]}...")
        print(f"   📊 Confidence: {data['confidence']:.1%}")
        print(f"   📚 Sources: {len(data['sources'])}")
    else:
        print(f"   ❌ Query failed: {result.get('message', 'Unknown error')}")
    
    print("\n🎉 API client demo completed!")


def main():
    """
    Main demonstration function.
    """
    print("=== Multimodal RAG Pipeline Web Interface Demo ===\n")
    
    # Configuration
    HOST = "127.0.0.1"
    PORT = 8080
    
    print("This demo will:")
    print("1. Start the web interface server")
    print("2. Show available endpoints")
    print("3. Test API functionality")
    print("4. Keep the server running for manual testing")
    print()
    
    # Check environment
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️  Warning: .env file not found")
        print("   Copy .env.example to .env and add your OpenAI API key for full functionality")
        print()
    
    try:
        # Start API client demo in a separate thread
        api_thread = threading.Thread(
            target=demo_api_client, 
            args=(HOST, PORT),
            daemon=True
        )
        api_thread.start()
        
        # Start web server (this will block until interrupted)
        start_web_server(HOST, PORT)
        
    except KeyboardInterrupt:
        print("\n👋 Demo stopped by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")


def show_usage_examples():
    """Show usage examples for the web interface."""
    print("=== Web Interface Usage Examples ===\n")
    
    print("🌐 Web Interface:")
    print("   • Open http://127.0.0.1:8080/ in your browser")
    print("   • Click 'Start Asking Questions' to use the query interface")
    print("   • Upload images along with text queries for multimodal analysis")
    print("   • View sources and citations in the response")
    print()
    
    print("🔧 API Usage:")
    print("   • POST /api/query - Submit text and image queries")
    print("   • GET /api/pipeline/health - Check system health")
    print("   • GET /api/status - Get system status")
    print("   • POST /api/pipeline/clear - Clear vector database")
    print()
    
    print("📝 Example API Request:")
    print("""
    import requests
    
    # Submit a text query
    response = requests.post('http://127.0.0.1:8080/api/query', data={
        'query': 'What are the latest AI developments?'
    })
    
    # Submit query with image
    with open('image.jpg', 'rb') as f:
        response = requests.post('http://127.0.0.1:8080/api/query', 
            data={'query': 'What is in this image?'},
            files={'images': f}
        )
    """)
    
    print("🎯 Features:")
    print("   • Real-time web retrieval for current information")
    print("   • Multimodal processing (text + images)")
    print("   • Source citations with relevance scores")
    print("   • Progress indicators and error handling")
    print("   • Admin interface for system configuration")
    print("   • RESTful API for programmatic access")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG Pipeline Web Interface Demo")
    parser.add_argument('--examples', action='store_true', help='Show usage examples')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    
    args = parser.parse_args()
    
    if args.examples:
        show_usage_examples()
    else:
        main()
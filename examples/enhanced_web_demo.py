"""
Enhanced Web Interface Demo
Demonstrates the new features implemented in task 8:
- Progress indicators
- Enhanced error handling
- Retrieval transparency
- Query validation
- Source citation improvements
"""

import os
import sys
import time
import threading
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

sys.path.append(os.path.join(os.path.dirname(__file__)))
from api_client_example import RAGPipelineClient


def demo_enhanced_features():
    """Demonstrate the enhanced web interface features."""
    print("=== Enhanced Web Interface Features Demo ===\n")
    
    client = RAGPipelineClient()
    
    # 1. Query Validation Demo
    print("1. 🔍 Query Validation Demo")
    print("-" * 40)
    
    test_queries = [
        "",  # Empty query
        "AI",  # Short query
        "What are the latest developments in artificial intelligence?",  # Good query
        "Tell me about machine learning" * 50  # Very long query
    ]
    
    for i, query in enumerate(test_queries, 1):
        if not query:
            print(f"   Test {i}: [Empty Query]")
        elif len(query) > 50:
            print(f"   Test {i}: {query[:50]}... [Very Long Query]")
        else:
            print(f"   Test {i}: {query}")
        
        validation = client.validate_query(query)
        if validation.get("status") == "success":
            val_data = validation.get("data", {})
            print(f"      Valid: {val_data.get('valid', False)}")
            
            if val_data.get("issues"):
                print(f"      Issues: {', '.join(val_data['issues'])}")
            
            if val_data.get("suggestions"):
                print(f"      Suggestions: {val_data['suggestions'][0]}")
        
        print()
    
    # 2. Enhanced Query Processing Demo
    print("2. 🧠 Enhanced Query Processing Demo")
    print("-" * 40)
    
    # Test with a query that might not find many sources
    test_query = "What happened in the year 3024?"
    print(f"Query: {test_query}")
    print("Processing...")
    
    result = client.submit_query(test_query)
    
    if result.get("status") == "success":
        data = result.get("data", {})
        
        print(f"\n📝 Answer: {data.get('answer', 'No answer')[:150]}...")
        print(f"🎯 Confidence: {data.get('confidence', 0):.1%}")
        
        # Show enhanced retrieval summary
        retrieval_summary = data.get('retrieval_summary', {})
        if retrieval_summary:
            print(f"\n📊 Retrieval Summary:")
            print(f"   Sources Attempted: {retrieval_summary.get('total_sources_attempted', 0)}")
            print(f"   Successful: {retrieval_summary.get('successful_retrievals', 0)}")
            print(f"   Failed: {retrieval_summary.get('failed_retrievals', 0)}")
            print(f"   Strategy: {retrieval_summary.get('strategy_used', 'unknown')}")
            
            if retrieval_summary.get('domains_consulted'):
                print(f"   Domains: {', '.join(retrieval_summary['domains_consulted'][:3])}")
        
        # Show query suggestions if available
        suggestions = data.get('query_suggestions', [])
        if suggestions:
            print(f"\n💡 Query Improvement Suggestions:")
            for suggestion in suggestions[:3]:
                print(f"   • {suggestion}")
        
        # Show sources with enhanced information
        sources = data.get('sources', [])
        if sources:
            print(f"\n📚 Sources ({len(sources)}):")
            for i, source in enumerate(sources[:2], 1):
                print(f"   {i}. {source.get('title', 'Untitled')}")
                print(f"      URL: {source.get('url', 'Unknown')}")
                print(f"      Relevance: {source.get('relevance_score', 0):.1%}")
                if source.get('retrieval_status') and source['retrieval_status'] != 'success':
                    print(f"      Status: ⚠️ {source['retrieval_status']}")
        
        # Show metadata
        metadata = data.get('metadata', {})
        print(f"\n📈 Processing Metadata:")
        print(f"   Processing Time: {data.get('processing_time', 0):.2f}s")
        print(f"   Retrieved Sources: {metadata.get('retrieved_sources', 0)}")
        print(f"   Failed Sources: {metadata.get('failed_sources', 0)}")
        print(f"   Fallback Used: {metadata.get('fallback_used', False)}")
        
    else:
        print(f"❌ Error: {result.get('message', 'Unknown error')}")
    
    print("\n3. 🌐 Web Interface Features")
    print("-" * 40)
    print("The enhanced web interface now includes:")
    print("   ✅ Real-time query validation with suggestions")
    print("   ✅ Progress indicators during processing")
    print("   ✅ Detailed retrieval transparency")
    print("   ✅ Enhanced error handling and reporting")
    print("   ✅ Source citation with retrieval status")
    print("   ✅ Query refinement suggestions")
    print("   ✅ Multimodal file upload with preview")
    print("   ✅ Responsive design with better UX")
    
    print(f"\n🌐 Access the enhanced interface at: http://127.0.0.1:8080/")
    print(f"📊 Admin dashboard at: http://127.0.0.1:8080/admin")


def show_api_endpoints():
    """Show all available API endpoints."""
    print("=== Enhanced API Endpoints ===\n")
    
    endpoints = [
        ("POST /api/query", "Submit text and image queries with enhanced response format"),
        ("POST /api/query/validate", "Validate query before submission with suggestions"),
        ("GET /api/query/status/<id>", "Get query processing status (for future async support)"),
        ("GET /api/pipeline/health", "Get RAG pipeline health and performance metrics"),
        ("POST /api/pipeline/clear", "Clear vector database and reset pipeline"),
        ("GET /api/status", "Get comprehensive system status and configuration"),
        ("GET /", "Main dashboard with user and admin interface links"),
        ("GET /query", "Interactive query interface with file upload"),
        ("GET /admin", "Admin dashboard for system management")
    ]
    
    for endpoint, description in endpoints:
        print(f"📡 {endpoint}")
        print(f"   {description}")
        print()


def main():
    """Main demo function."""
    print("This demo showcases the enhanced web interface features implemented in Task 8.")
    print("Make sure the web interface is running before testing API features.\n")
    
    import argparse
    parser = argparse.ArgumentParser(description="Enhanced Web Interface Demo")
    parser.add_argument('--endpoints', action='store_true', help='Show API endpoints')
    parser.add_argument('--features', action='store_true', help='Demo enhanced features')
    
    args = parser.parse_args()
    
    if args.endpoints:
        show_api_endpoints()
    elif args.features:
        demo_enhanced_features()
    else:
        print("Choose an option:")
        print("  --endpoints  : Show all API endpoints")
        print("  --features   : Demo enhanced features")
        print("\nOr start the web interface with:")
        print("  python main.py --admin")


if __name__ == "__main__":
    main()
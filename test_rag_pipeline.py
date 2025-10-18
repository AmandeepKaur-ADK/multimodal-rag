"""
Simple test script for the RAG Pipeline orchestrator.
Tests basic functionality without requiring external APIs.
"""

import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.rag_pipeline import RAGPipeline, create_rag_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pipeline_initialization():
    """Test that the pipeline can be initialized."""
    print("Testing pipeline initialization...")
    
    try:
        # Create pipeline with web retrieval disabled to avoid API calls
        pipeline = create_rag_pipeline(
            vector_db_path="./data/test_vector_db",
            enable_web_retrieval=False  # Disable to avoid needing API keys
        )
        
        print("✓ Pipeline initialized successfully")
        
        # Test health check
        health = pipeline.get_pipeline_health()
        print(f"✓ Pipeline health: {health.get('status', 'unknown')}")
        
        # Clean up
        pipeline.close()
        print("✓ Pipeline closed successfully")
        
        return True
        
    except Exception as e:
        print(f"✗ Pipeline initialization failed: {e}")
        return False

def test_pipeline_with_mock_query():
    """Test pipeline with a simple query (no web retrieval)."""
    print("\nTesting pipeline with mock query...")
    
    try:
        # Create pipeline without web retrieval
        pipeline = create_rag_pipeline(
            vector_db_path="./data/test_vector_db",
            enable_web_retrieval=False
        )
        
        # Test query (should use fallback since no web retrieval)
        test_query = "What is artificial intelligence?"
        
        result = pipeline.process_query(
            text=test_query,
            enable_fallback=True
        )
        
        print(f"✓ Query processed: {result.success}")
        print(f"✓ Response generated: {len(result.response.answer) > 0}")
        print(f"✓ Processing time: {result.pipeline_stats.get('total_time', 0):.2f}s")
        
        # Clean up
        pipeline.close()
        
        return True
        
    except Exception as e:
        print(f"✗ Pipeline query test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=== RAG Pipeline Test Suite ===\n")
    
    tests = [
        test_pipeline_initialization,
        test_pipeline_with_mock_query
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
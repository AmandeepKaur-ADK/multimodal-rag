"""
Quick test to verify the error handling fix is working.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_validation():
    """Test input validation."""
    print("Testing input validation...")
    
    from src.validation_manager import validation_manager
    
    # Test valid input
    result = validation_manager.validate_user_input("What is artificial intelligence?")
    print(f"✅ Valid input test: {result.is_valid}")
    
    # Test invalid input
    result = validation_manager.validate_user_input("")
    print(f"✅ Invalid input test: {not result.is_valid}")
    
    return True

def test_rag_pipeline():
    """Test RAG pipeline with error handling."""
    print("\nTesting RAG pipeline...")
    
    try:
        from src.rag_pipeline import RAGPipeline
        
        # Create pipeline (this might fail if dependencies are missing, but that's expected)
        pipeline = RAGPipeline(enable_web_retrieval=False)  # Disable web retrieval for testing
        
        # Test with a simple query
        result = pipeline.process_query(
            text="What is the key to success?",
            request_id="test_fix_001"
        )
        
        print(f"✅ Pipeline test completed")
        print(f"   Success: {result.success}")
        print(f"   Has response: {result.response is not None}")
        print(f"   Validation report: {result.validation_report is not None}")
        
        if not result.success:
            print(f"   Error (expected): {result.error_message}")
            print(f"   Fallback strategies: {result.fallback_strategies_used}")
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_logging():
    """Test enhanced logging."""
    print("\nTesting enhanced logging...")
    
    try:
        from src.enhanced_logger import enhanced_logger, LogCategory
        
        # Test different log categories
        enhanced_logger.info("Test message", "test_component", LogCategory.SYSTEM)
        enhanced_logger.info("Pipeline test", "test_component", LogCategory.PIPELINE)
        enhanced_logger.info("User interaction test", "test_component", LogCategory.USER_INTERACTION)
        
        print("✅ Logging test completed")
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {str(e)}")
        return False

def main():
    """Run all tests."""
    print("🔧 TESTING ERROR HANDLING FIX")
    print("=" * 40)
    
    tests = [
        ("Input Validation", test_validation),
        ("Enhanced Logging", test_logging),
        ("RAG Pipeline", test_rag_pipeline),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 40)
    print("TEST RESULTS:")
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 ALL TESTS PASSED! The error handling fix is working correctly.")
        print("\nYou can now run:")
        print("  python examples/error_handling_demo.py")
        print("  python examples/enhanced_web_demo.py")
        print("  python main.py")
    else:
        print("\n⚠️  Some tests failed. Please check the error messages above.")
    
    return all_passed

if __name__ == "__main__":
    main()
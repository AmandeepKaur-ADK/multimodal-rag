"""
Super simple test to verify the system works.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """Test the most basic functionality."""
    print("🧪 SIMPLE FUNCTIONALITY TEST")
    print("=" * 40)
    
    try:
        # Test 1: Basic validation
        print("1. Testing input validation...")
        from src.validation_manager import validation_manager
        
        result = validation_manager.validate_user_input("What is AI?")
        if result.is_valid:
            print("   ✅ Validation works!")
        else:
            print("   ❌ Validation failed")
            return False
        
        # Test 2: Error handling
        print("2. Testing error handling...")
        from src.error_handler import input_validator
        
        text_result = input_validator.validate_text_query("Hello world")
        if text_result.is_valid:
            print("   ✅ Error handling works!")
        else:
            print("   ❌ Error handling failed")
            return False
        
        # Test 3: Enhanced logging
        print("3. Testing enhanced logging...")
        from src.enhanced_logger import enhanced_logger, LogCategory
        
        enhanced_logger.info("Test message", "test_component", LogCategory.SYSTEM)
        print("   ✅ Logging works!")
        
        # Test 4: Free response generator (without full pipeline)
        print("4. Testing free response generator...")
        from src.free_response_generator import FreeResponseGenerator
        
        generator = FreeResponseGenerator()
        response = generator.generate_fallback_response("Test query")
        if response and response.answer:
            print("   ✅ Free response generator works!")
        else:
            print("   ❌ Free response generator failed")
            return False
        
        print("\n🎉 ALL BASIC TESTS PASSED!")
        print("\nThe system is working correctly.")
        print("You can now try:")
        print("  • python examples/free_rag_demo.py")
        print("  • python examples/demo_without_openai.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_web_interface():
    """Test if web interface can be imported."""
    print("\n🌐 TESTING WEB INTERFACE...")
    
    try:
        # Check if streamlit is available
        import streamlit as st
        print("   ✅ Streamlit available - you can run web interface!")
        print("   Command: streamlit run examples/free_web_demo.py")
        return True
    except ImportError:
        print("   ⚠️ Streamlit not installed")
        print("   Install with: pip install streamlit")
        print("   Then run: streamlit run examples/free_web_demo.py")
        return False

def main():
    """Run simple tests."""
    success = test_basic_functionality()
    
    if success:
        test_web_interface()
        
        print("\n" + "=" * 40)
        print("🚀 READY TO USE!")
        print("=" * 40)
        
        print("\n📋 Available Commands:")
        print("  1. python examples/free_rag_demo.py          # Full free demo")
        print("  2. python examples/demo_without_openai.py    # Basic demo")
        print("  3. python simple_test.py                     # This test")
        print("  4. streamlit run examples/free_web_demo.py   # Web interface")
        
        print("\n💡 If you're still having issues:")
        print("  • Tell me the exact command you're running")
        print("  • Copy and paste the error message you see")
        print("  • I'll help you fix it!")
    
    else:
        print("\n❌ Basic tests failed. Please share the error message above.")

if __name__ == "__main__":
    main()
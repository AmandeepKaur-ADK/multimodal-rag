"""
Quick setup test to verify all components can be imported and initialized.
Run this to check if your environment is set up correctly.
"""

import sys
import os

def test_imports():
    """Test that all required modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        # Test core dependencies
        import requests
        import openai
        import chromadb
        from sentence_transformers import SentenceTransformer
        print("✅ Core dependencies imported successfully")
        
        # Test project modules
        sys.path.append('src')
        from config.settings import settings
        from src.vector_db import VectorDB
        from src.content_processor import ContentProcessor
        from src.response_generator import ResponseGenerator
        print("✅ Project modules imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def test_environment():
    """Test environment configuration."""
    print("\n🔧 Testing environment...")
    
    # Check .env file exists
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("Run: cp .env.example .env")
        return False
    
    # Check API key
    sys.path.append('src')
    from config.settings import settings
    
    if not settings.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set in .env file")
        return False
    
    print("✅ Environment configured correctly")
    return True

def test_directories():
    """Test required directories exist."""
    print("\n📁 Testing directories...")
    
    required_dirs = ['data/vector_db', 'logs']
    
    for dir_path in required_dirs:
        if not os.path.exists(dir_path):
            print(f"❌ Directory missing: {dir_path}")
            print(f"Run: mkdir -p {dir_path}")
            return False
    
    print("✅ All required directories exist")
    return True

def main():
    """Run all setup tests."""
    print("=== Multimodal RAG Pipeline Setup Test ===\n")
    
    tests = [
        test_imports,
        test_environment, 
        test_directories
    ]
    
    all_passed = True
    for test in tests:
        if not test():
            all_passed = False
    
    print("\n" + "="*50)
    if all_passed:
        print("🎉 All tests passed! You're ready to run the pipeline.")
        print("Run: python main.py")
    else:
        print("❌ Some tests failed. Please fix the issues above.")
    print("="*50)

if __name__ == "__main__":
    main()
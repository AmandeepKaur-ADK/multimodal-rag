"""
Script to help diagnose and fix OpenAI API configuration issues.
"""

import os
from pathlib import Path

def check_openai_config():
    """Check OpenAI API configuration and provide guidance."""
    
    print("🔍 OPENAI API CONFIGURATION CHECKER")
    print("=" * 50)
    
    # Check for .env file
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file found")
        
        # Read .env file
        with open(env_file, 'r') as f:
            content = f.read()
        
        if "OPENAI_API_KEY" in content:
            print("✅ OPENAI_API_KEY found in .env file")
            
            # Check if key looks valid (starts with sk-)
            lines = content.split('\n')
            for line in lines:
                if line.startswith('OPENAI_API_KEY='):
                    key = line.split('=', 1)[1].strip()
                    if key.startswith('sk-'):
                        print("✅ API key format looks correct")
                    else:
                        print("❌ API key format looks incorrect (should start with 'sk-')")
                    break
        else:
            print("❌ OPENAI_API_KEY not found in .env file")
    else:
        print("❌ .env file not found")
    
    # Check environment variable
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        print("✅ OPENAI_API_KEY environment variable is set")
        if api_key.startswith('sk-'):
            print("✅ Environment API key format looks correct")
        else:
            print("❌ Environment API key format looks incorrect")
    else:
        print("❌ OPENAI_API_KEY environment variable not set")
    
    print("\n" + "=" * 50)
    print("📋 RECOMMENDATIONS:")
    
    if not env_file.exists():
        print("\n1. Create a .env file in your project root:")
        print("   OPENAI_API_KEY=your_actual_api_key_here")
        print("   LOG_LEVEL=INFO")
        print("   MAX_TEXT_LENGTH=10000")
    
    if not api_key or not api_key.startswith('sk-'):
        print("\n2. Get a valid OpenAI API key:")
        print("   • Go to: https://platform.openai.com/api-keys")
        print("   • Create a new API key")
        print("   • Copy the key (starts with 'sk-')")
        print("   • Add it to your .env file")
    
    print("\n3. Check your OpenAI account:")
    print("   • Go to: https://platform.openai.com/usage")
    print("   • Check your usage and billing")
    print("   • Free tier has very limited usage")
    print("   • Consider upgrading to a paid plan")
    
    print("\n4. Alternative: Use the system without OpenAI:")
    print("   • Run: python examples/demo_without_openai.py")
    print("   • This shows all features except response generation")
    print("   • Perfect for testing validation and error handling")

def create_sample_env():
    """Create a sample .env file."""
    
    env_content = """# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/rag_pipeline.log

# Pipeline Configuration
MAX_TEXT_LENGTH=10000
MAX_RETRIEVAL_TIME=30
MAX_CONCURRENT_REQUESTS=5
REQUEST_TIMEOUT=10

# Image Processing
SUPPORTED_IMAGE_FORMATS=JPEG,PNG,WebP,GIF
MAX_IMAGE_SIZE=800,600

# Vector Database
VECTOR_DB_PATH=./data/vector_db
TOP_K_RESULTS=5

# Response Generation
MAX_RESPONSE_LENGTH=1000
TEMPERATURE=0.7
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ Created sample .env file")
        print("📝 Please edit .env and add your actual OpenAI API key")
    else:
        print("ℹ️ .env file already exists")

def main():
    """Main function."""
    check_openai_config()
    
    print("\n" + "=" * 50)
    response = input("Would you like me to create a sample .env file? (y/n): ")
    
    if response.lower() in ['y', 'yes']:
        create_sample_env()
    
    print("\n🚀 Next steps:")
    print("1. Fix your OpenAI API key configuration")
    print("2. OR run: python examples/demo_without_openai.py")
    print("3. OR run: python examples/error_handling_demo.py")

if __name__ == "__main__":
    main()
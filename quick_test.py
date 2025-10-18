"""
Quick test to get actual AI responses.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_with_web_retrieval():
    """Test with web retrieval enabled for better responses."""
    print("🤖 QUICK TEST - BETTER RESPONSES")
    print("=" * 40)
    
    from src.free_rag_pipeline import create_free_rag_pipeline
    
    # Create pipeline with web retrieval
    print("📦 Loading pipeline with web retrieval...")
    pipeline = create_free_rag_pipeline(
        enable_web_retrieval=True  # This makes the difference!
    )
    
    # Test one question
    print("\n🤔 Question: What is artificial intelligence?")
    print("🔄 Processing with web search...")
    
    result = pipeline.process_query(
        "What is artificial intelligence?",
        max_results=2
    )
    
    if result.success:
        print(f"\n✅ SUCCESS!")
        print(f"🎯 Confidence: {result.response.confidence_score:.1%}")
        print(f"📝 Answer:")
        print(f"   {result.response.answer}")
        
        if result.response.sources:
            print(f"\n📚 Found {len(result.response.sources)} sources")
    else:
        print(f"\n❌ Failed: {result.error_message}")
    
    pipeline.close()

if __name__ == "__main__":
    test_with_web_retrieval()
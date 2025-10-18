"""
Quick Ask - Single Question AI Assistant
Ask one question and get an AI answer with web search.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Ask a single question and get an AI answer."""
    
    # Get question from command line or user input
    if len(sys.argv) > 1:
        # Question provided as command line argument
        question = ' '.join(sys.argv[1:])
        print(f"🤔 Question: {question}")
    else:
        # Ask user for question
        print("🤖 QUICK AI ASSISTANT")
        print("=" * 30)
        question = input("🤔 Your question: ").strip()
    
    if not question:
        print("❌ Please provide a question!")
        print("\n💡 Usage:")
        print('   python quick_ask.py "What is artificial intelligence?"')
        print("   OR just run: python quick_ask.py")
        return
    
    try:
        print("🔍 Searching web and generating answer...")
        
        from src.free_rag_pipeline import create_free_rag_pipeline
        
        # Create AI pipeline
        pipeline = create_free_rag_pipeline(
            model_name="microsoft/DialoGPT-small",
            enable_web_retrieval=True
        )
        
        # Get AI answer
        result = pipeline.process_query(
            text=question,
            max_results=3,
            request_id="quick_ask"
        )
        
        if result.success:
            print(f"\n✅ AI Answer:")
            print("=" * 40)
            
            # Clean and display answer
            answer = result.response.answer
            if '**Sources:**' in answer:
                answer = answer.split('**Sources:**')[0].strip()
            
            print(answer)
            
            # Show sources
            if result.response.sources:
                print(f"\n📚 Sources:")
                for i, source in enumerate(result.response.sources, 1):
                    print(f"   {i}. {source.get('url', 'Unknown')}")
            
            print(f"\n📊 Confidence: {result.response.confidence_score:.1%} | "
                  f"Model: {result.response.model_used}")
        
        else:
            print(f"\n❌ Failed: {result.error_message}")
        
        pipeline.close()
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("💡 Make sure you're in the virtual environment and have internet access.")


if __name__ == "__main__":
    main()
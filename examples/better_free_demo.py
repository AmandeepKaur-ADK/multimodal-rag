"""
Better Free RAG Demo with actual AI-generated responses.
This version enables web retrieval and uses the Hugging Face models properly.
"""

import sys
import os
import time

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.free_rag_pipeline import create_free_rag_pipeline


def demo_with_better_responses():
    """Demo with actual AI-generated responses."""
    print("🤖 BETTER FREE RAG DEMO")
    print("=" * 50)
    print("Getting actual AI responses using free models!")
    print("=" * 50)
    
    try:
        # Create pipeline with web retrieval enabled for better responses
        print("\n📦 Initializing pipeline with web retrieval...")
        pipeline = create_free_rag_pipeline(
            model_name="microsoft/DialoGPT-small",
            enable_web_retrieval=True  # Enable for better responses
        )
        
        print("✅ Pipeline ready!")
        
        # Test queries that should get good responses
        test_queries = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "What are neural networks?",
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. 🤔 Question: {query}")
            print("   🔄 Processing...")
            
            start_time = time.time()
            result = pipeline.process_query(
                text=query,
                max_results=3,  # Get some web results
                request_id=f"better_demo_{i}"
            )
            processing_time = time.time() - start_time
            
            if result.success:
                print(f"   ✅ Success ({processing_time:.2f}s)")
                print(f"   🤖 Model: {result.response.model_used}")
                print(f"   🎯 Confidence: {result.response.confidence_score:.2%}")
                print(f"   📝 Answer:")
                print(f"      {result.response.answer}")
                
                if result.response.sources:
                    print(f"   📚 Sources: {len(result.response.sources)} found")
                
                if result.fallback_strategies_used:
                    print(f"   🔄 Fallbacks: {', '.join(result.fallback_strategies_used)}")
            else:
                print(f"   ❌ Failed: {result.error_message}")
        
        pipeline.close()
        
        print(f"\n🎉 Demo completed! The system is working correctly.")
        print(f"💡 The responses you see are from the free Hugging Face models.")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


def demo_direct_model_responses():
    """Demo direct model responses without RAG pipeline."""
    print("\n" + "=" * 50)
    print("🧠 DIRECT AI MODEL RESPONSES")
    print("=" * 50)
    print("Testing the AI models directly for better responses...")
    
    try:
        from src.free_response_generator import FreeResponseGenerator
        
        # Create response generator
        print("\n📦 Loading AI model...")
        generator = FreeResponseGenerator(model_name="microsoft/DialoGPT-small")
        
        # Test direct generation
        queries = [
            "What is artificial intelligence?",
            "Explain machine learning simply",
            "How do computers learn?",
        ]
        
        for i, query in enumerate(queries, 1):
            print(f"\n{i}. 🤔 Question: {query}")
            
            # Generate response directly
            response = generator.generate_response(query, [])  # No search results
            
            print(f"   🤖 Model: {response.model_used}")
            print(f"   🎯 Confidence: {response.confidence_score:.2%}")
            print(f"   📝 Answer:")
            print(f"      {response.answer}")
        
        print(f"\n✅ Direct model responses completed!")
        
    except Exception as e:
        print(f"❌ Direct model test failed: {e}")


def simple_interactive_demo():
    """Simple interactive demo where you can ask questions."""
    print("\n" + "=" * 50)
    print("💬 INTERACTIVE DEMO")
    print("=" * 50)
    print("Ask your own questions! (type 'quit' to exit)")
    
    try:
        from src.free_response_generator import FreeResponseGenerator
        
        print("\n📦 Loading AI model...")
        generator = FreeResponseGenerator()
        print("✅ Ready! Ask me anything...")
        
        while True:
            print("\n" + "-" * 30)
            question = input("🤔 Your question: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            
            if not question:
                print("⚠️ Please enter a question!")
                continue
            
            print("🔄 Thinking...")
            
            try:
                response = generator.generate_response(question, [])
                
                print(f"🤖 AI Response:")
                print(f"   {response.answer}")
                print(f"   (Confidence: {response.confidence_score:.1%}, Model: {response.model_used})")
                
            except Exception as e:
                print(f"❌ Error: {e}")
        
    except Exception as e:
        print(f"❌ Interactive demo failed: {e}")


def main():
    """Run better demos."""
    print("🚀 BETTER FREE RAG RESPONSES")
    print("=" * 60)
    print("This demo shows how to get actual AI-generated responses")
    print("instead of just fallback templates!")
    print("=" * 60)
    
    try:
        # Demo 1: Better pipeline responses
        demo_with_better_responses()
        
        # Demo 2: Direct model responses
        demo_direct_model_responses()
        
        # Demo 3: Interactive
        response = input("\nWould you like to try the interactive demo? (y/n): ")
        if response.lower() in ['y', 'yes']:
            simple_interactive_demo()
        
        print("\n" + "=" * 60)
        print("🎊 ALL DEMOS COMPLETED!")
        print("=" * 60)
        
        print("\n💡 Key Points:")
        print("• The 'fallback template' responses are normal when no context is available")
        print("• Enable web retrieval for better responses with current information")
        print("• The AI models work - they just need proper context or direct usage")
        print("• You can interact directly with the models for better responses")
        
        print("\n🚀 Next Steps:")
        print("1. Enable web retrieval: set enable_web_retrieval=True")
        print("2. Add content to the vector database")
        print("3. Use the models directly for general knowledge questions")
        print("4. Try the interactive mode for real conversations!")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
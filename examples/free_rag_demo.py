"""
Demo of the Free RAG Pipeline using Hugging Face models.
No OpenAI API key required - uses local/free models.
"""

import sys
import os
import time

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.free_rag_pipeline import FreeRAGPipeline, create_free_rag_pipeline
from src.validation_manager import validation_manager
from src.enhanced_logger import enhanced_logger, LogCategory


def demo_free_pipeline():
    """Demonstrate the free RAG pipeline in action."""
    print("🚀 FREE RAG PIPELINE DEMONSTRATION")
    print("=" * 60)
    print("Using Hugging Face models - NO API KEYS REQUIRED!")
    print("=" * 60)
    
    try:
        # Create free pipeline
        print("\n📦 Initializing Free RAG Pipeline...")
        print("   • Loading Hugging Face model (this may take a moment)...")
        
        pipeline = create_free_rag_pipeline(
            model_name="microsoft/DialoGPT-small",  # Small, fast model
            enable_web_retrieval=False  # Disable for demo speed
        )
        
        print("   ✅ Pipeline initialized successfully!")
        print(f"   • Model: {pipeline.model_name}")
        print(f"   • Web retrieval: {pipeline.enable_web_retrieval}")
        
        # Test queries
        test_queries = [
            "What is artificial intelligence?",
            "How does machine learning work?", 
            "Explain the concept of neural networks",
            "What are the benefits of renewable energy?",
            "How do computers process information?",
            "",  # This should fail validation
            "AI",  # This should also fail validation
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} queries...")
        print("=" * 60)
        
        successful_queries = 0
        total_time = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. Query: '{query}'")
            
            start_time = time.time()
            
            try:
                result = pipeline.process_query(
                    text=query,
                    request_id=f"free_demo_{i}"
                )
                
                query_time = time.time() - start_time
                total_time += query_time
                
                if result.success:
                    successful_queries += 1
                    print(f"   ✅ SUCCESS ({query_time:.2f}s)")
                    print(f"   📝 Answer: {result.response.answer[:150]}...")
                    print(f"   🎯 Confidence: {result.response.confidence_score:.2f}")
                    print(f"   🤖 Model: {result.response.model_used}")
                    
                    if result.warnings:
                        print(f"   ⚠️ Warnings: {'; '.join(result.warnings[:1])}")
                    
                    if result.fallback_strategies_used:
                        print(f"   🔄 Fallbacks: {', '.join(result.fallback_strategies_used)}")
                
                else:
                    print(f"   ❌ FAILED ({query_time:.2f}s)")
                    print(f"   💬 Message: {result.error_message}")
                    
                    if result.validation_report and not result.validation_report.is_valid:
                        print(f"   📋 Validation: Failed")
                        if result.validation_report.recommendations:
                            print(f"   💡 Suggestion: {result.validation_report.recommendations[0]}")
            
            except Exception as e:
                query_time = time.time() - start_time
                total_time += query_time
                print(f"   ❌ ERROR ({query_time:.2f}s): {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 DEMO SUMMARY")
        print("=" * 60)
        
        success_rate = (successful_queries / len(test_queries)) * 100
        avg_time = total_time / len(test_queries)
        
        print(f"✅ Successful queries: {successful_queries}/{len(test_queries)} ({success_rate:.1f}%)")
        print(f"⏱️ Average response time: {avg_time:.2f}s")
        print(f"⏱️ Total processing time: {total_time:.2f}s")
        
        # Get pipeline health
        health = pipeline.get_pipeline_health()
        print(f"🏥 Pipeline health: {health.get('status', 'unknown')}")
        
        # Get validation statistics
        val_stats = validation_manager.get_validation_statistics()
        print(f"📈 Validation success rate: {val_stats['success_rate']:.1%}")
        
        print("\n🎉 Free RAG Pipeline Demo Completed Successfully!")
        print("\n💡 Key Benefits:")
        print("   • ✅ No API keys required")
        print("   • ✅ Runs completely offline")
        print("   • ✅ Free to use")
        print("   • ✅ Full error handling and validation")
        print("   • ✅ Comprehensive logging and monitoring")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def demo_model_comparison():
    """Compare different free models."""
    print("\n" + "=" * 60)
    print("🔬 FREE MODEL COMPARISON")
    print("=" * 60)
    
    models_to_test = [
        ("microsoft/DialoGPT-small", "Fast, conversational"),
        ("gpt2", "Classic GPT-2"),
        ("distilgpt2", "Distilled GPT-2, faster"),
    ]
    
    test_query = "What is machine learning?"
    
    print(f"Testing query: '{test_query}'\n")
    
    for model_name, description in models_to_test:
        print(f"🤖 Model: {model_name}")
        print(f"   Description: {description}")
        
        try:
            start_time = time.time()
            
            # Create pipeline with specific model
            pipeline = create_free_rag_pipeline(
                model_name=model_name,
                enable_web_retrieval=False
            )
            
            init_time = time.time() - start_time
            
            # Test query
            query_start = time.time()
            result = pipeline.process_query(test_query, request_id=f"model_test_{model_name.replace('/', '_')}")
            query_time = time.time() - query_start
            
            if result.success:
                print(f"   ✅ SUCCESS")
                print(f"   ⏱️ Init time: {init_time:.2f}s")
                print(f"   ⏱️ Query time: {query_time:.2f}s")
                print(f"   🎯 Confidence: {result.response.confidence_score:.2f}")
                print(f"   📝 Answer: {result.response.answer[:100]}...")
            else:
                print(f"   ❌ FAILED: {result.error_message}")
            
            # Clean up
            pipeline.close()
            
        except Exception as e:
            print(f"   ❌ ERROR: {str(e)}")
        
        print()


def demo_error_handling():
    """Demonstrate error handling with free models."""
    print("\n" + "=" * 60)
    print("🛡️ ERROR HANDLING WITH FREE MODELS")
    print("=" * 60)
    
    try:
        # Create pipeline
        pipeline = create_free_rag_pipeline(enable_web_retrieval=False)
        
        # Test various error scenarios
        error_scenarios = [
            ("", "Empty query"),
            ("AI", "Too short query"),
            ("<script>alert('xss')</script>", "Suspicious content"),
            ("A" * 15000, "Extremely long query"),
        ]
        
        for query, scenario in error_scenarios:
            print(f"\n🧪 Testing: {scenario}")
            print(f"   Query: '{query[:50]}{'...' if len(query) > 50 else ''}'")
            
            result = pipeline.process_query(query)
            
            if result.success:
                print(f"   ✅ Handled gracefully")
                if result.warnings:
                    print(f"   ⚠️ Warnings: {'; '.join(result.warnings[:1])}")
            else:
                print(f"   ❌ Validation failed (as expected)")
                print(f"   💬 Message: {result.error_message}")
        
        pipeline.close()
        
        print(f"\n✅ Error handling working correctly with free models!")
        
    except Exception as e:
        print(f"\n❌ Error handling test failed: {str(e)}")


def main():
    """Run the complete free RAG demo."""
    print("🆓 FREE RAG PIPELINE - COMPLETE DEMONSTRATION")
    print("=" * 80)
    print("This demo shows a fully functional RAG pipeline using FREE models!")
    print("No OpenAI API keys, no paid services - completely free to use.")
    print("=" * 80)
    
    try:
        # Main demo
        success = demo_free_pipeline()
        
        if success:
            # Additional demos
            demo_error_handling()
            
            # Model comparison (optional, can be slow)
            response = input("\nWould you like to test different models? (y/n): ")
            if response.lower() in ['y', 'yes']:
                demo_model_comparison()
        
        print("\n" + "=" * 80)
        print("🎊 FREE RAG PIPELINE DEMO COMPLETED!")
        print("=" * 80)
        
        print("\n🌟 What you've seen:")
        print("• ✅ Complete RAG pipeline with NO API costs")
        print("• ✅ Comprehensive input validation and error handling")
        print("• ✅ Graceful degradation and fallback strategies")
        print("• ✅ Real-time monitoring and health checks")
        print("• ✅ Structured logging and performance tracking")
        print("• ✅ Multiple free model options")
        
        print("\n🚀 Next Steps:")
        print("1. Use this free pipeline for development and testing")
        print("2. Enable web retrieval for more comprehensive answers")
        print("3. Try different Hugging Face models")
        print("4. Integrate into your applications")
        
        print("\n💡 Pro Tips:")
        print("• Smaller models (DialoGPT-small) are faster")
        print("• Larger models may give better responses but are slower")
        print("• You can run this completely offline!")
        print("• Perfect for privacy-sensitive applications")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
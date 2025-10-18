"""
Free RAG Pipeline Demo with Web Retrieval ENABLED.
This will give you actual AI responses with current web information!
"""

import sys
import os
import time

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.free_rag_pipeline import create_free_rag_pipeline


def main():
    """Demo with web retrieval enabled for better responses."""
    print("🌐 FREE RAG PIPELINE - WEB RETRIEVAL ENABLED")
    print("=" * 60)
    print("This demo searches the web and gives you AI-generated responses")
    print("with current information from the internet!")
    print("=" * 60)
    
    try:
        # Create pipeline with web retrieval ENABLED
        print("\n📦 Initializing pipeline with web search capabilities...")
        print("   • Loading AI models...")
        print("   • Enabling web retrieval...")
        print("   • Setting up vector database...")
        
        pipeline = create_free_rag_pipeline(
            model_name="microsoft/DialoGPT-small",
            enable_web_retrieval=True  # 🌐 WEB RETRIEVAL ENABLED!
        )
        
        print("✅ Pipeline ready with web search!")
        
        # Test queries that will benefit from web search
        test_queries = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "What are the latest developments in AI?",
            "Explain neural networks simply",
            "What is the difference between AI and machine learning?"
        ]
        
        print(f"\n🧪 Testing {len(test_queries)} queries with web search...")
        print("=" * 60)
        
        successful_queries = 0
        total_time = 0
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n{i}. 🤔 Question: {query}")
            print("   🔍 Searching the web...")
            print("   🤖 Generating AI response...")
            
            start_time = time.time()
            
            try:
                result = pipeline.process_query(
                    text=query,
                    max_results=3,  # Get 3 web sources
                    request_id=f"web_demo_{i}"
                )
                
                query_time = time.time() - start_time
                total_time += query_time
                
                if result.success:
                    successful_queries += 1
                    print(f"   ✅ SUCCESS ({query_time:.2f}s)")
                    print(f"   🎯 Confidence: {result.response.confidence_score:.1%}")
                    print(f"   🤖 Model: {result.response.model_used}")
                    
                    # Show the AI response
                    print(f"   📝 AI Response:")
                    answer_lines = result.response.answer.split('\n')
                    for line in answer_lines[:5]:  # Show first 5 lines
                        if line.strip():
                            print(f"      {line.strip()}")
                    
                    if len(answer_lines) > 5:
                        print("      ...")
                    
                    # Show sources found
                    if result.response.sources:
                        print(f"   📚 Sources found: {len(result.response.sources)}")
                        for j, source in enumerate(result.response.sources[:2], 1):
                            print(f"      {j}. {source.get('url', 'Unknown URL')}")
                    
                    # Show any fallback strategies used
                    if result.fallback_strategies_used:
                        print(f"   🔄 Fallbacks: {', '.join(result.fallback_strategies_used)}")
                    
                    # Show warnings if any
                    if result.warnings:
                        print(f"   ⚠️ Warnings: {'; '.join(result.warnings[:1])}")
                
                else:
                    print(f"   ❌ FAILED ({query_time:.2f}s)")
                    print(f"   💬 Error: {result.error_message}")
                    
                    if result.validation_report and not result.validation_report.is_valid:
                        print(f"   📋 Validation failed")
            
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
        try:
            health = pipeline.get_pipeline_health()
            print(f"🏥 Pipeline health: {health.get('status', 'unknown')}")
        except:
            print(f"🏥 Pipeline health: monitoring unavailable")
        
        print("\n🎉 Web-Enabled RAG Pipeline Demo Completed!")
        
        print("\n💡 What you just saw:")
        print("• ✅ Real web search for current information")
        print("• ✅ AI-generated responses using free models")
        print("• ✅ Source citations from web content")
        print("• ✅ Comprehensive error handling and validation")
        print("• ✅ Performance monitoring and statistics")
        
        print("\n🌟 Key Benefits:")
        print("• 🌐 Current information from the web")
        print("• 🆓 Completely free - no API costs")
        print("• 🔒 Privacy-first - processing happens locally")
        print("• 🛡️ Robust error handling and graceful degradation")
        print("• 📊 Full monitoring and logging")
        
        # Interactive option
        response = input("\nWould you like to ask your own question? (y/n): ")
        if response.lower() in ['y', 'yes']:
            print("\n" + "=" * 60)
            print("💬 ASK YOUR OWN QUESTION")
            print("=" * 60)
            
            user_question = input("🤔 Your question: ").strip()
            
            if user_question:
                print("🔍 Searching web and generating response...")
                
                try:
                    result = pipeline.process_query(
                        text=user_question,
                        max_results=3,
                        request_id="user_question"
                    )
                    
                    if result.success:
                        print(f"\n✅ SUCCESS!")
                        print(f"🎯 Confidence: {result.response.confidence_score:.1%}")
                        print(f"📝 AI Response:")
                        print(f"   {result.response.answer}")
                        
                        if result.response.sources:
                            print(f"\n📚 Sources ({len(result.response.sources)}):")
                            for i, source in enumerate(result.response.sources, 1):
                                print(f"   {i}. {source.get('url', 'Unknown')}")
                    else:
                        print(f"\n❌ Failed: {result.error_message}")
                
                except Exception as e:
                    print(f"\n❌ Error: {str(e)}")
        
        # Clean up
        pipeline.close()
        
        print(f"\n🚀 Ready for production use!")
        print(f"You can now integrate this into your applications.")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        print(f"\n💡 Troubleshooting:")
        print(f"• Make sure you're using the virtual environment")
        print(f"• Check your internet connection for web retrieval")
        print(f"• Try running: python simple_test.py")


if __name__ == "__main__":
    main()
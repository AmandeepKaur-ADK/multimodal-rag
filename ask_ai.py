"""
Interactive AI Assistant - Ask Your Own Questions!
Uses free models with web search - no API keys required.
"""

import sys
import os
import time

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.free_rag_pipeline import create_free_rag_pipeline


def main():
    """Interactive AI assistant where you can ask any question."""
    print("🤖 INTERACTIVE AI ASSISTANT")
    print("=" * 50)
    print("Ask me anything! I'll search the web and give you AI-generated answers.")
    print("Type 'quit', 'exit', or 'q' to stop.")
    print("=" * 50)
    
    try:
        # Initialize the AI pipeline
        print("\n📦 Loading AI assistant...")
        print("   • Initializing free AI models...")
        print("   • Enabling web search...")
        print("   • Setting up knowledge database...")
        
        pipeline = create_free_rag_pipeline(
            model_name="microsoft/DialoGPT-small",
            enable_web_retrieval=True  # Web search enabled!
        )
        
        print("✅ AI Assistant ready!")
        print("\n💡 Tips:")
        print("   • Ask specific questions for better answers")
        print("   • I can search the web for current information")
        print("   • Try questions like 'What is...', 'How does...', 'Explain...'")
        
        question_count = 0
        
        while True:
            print("\n" + "─" * 50)
            
            # Get user question
            question = input("🤔 Your question: ").strip()
            
            # Check for quit commands
            if question.lower() in ['quit', 'exit', 'q', '']:
                print("👋 Thanks for using the AI Assistant! Goodbye!")
                break
            
            question_count += 1
            
            print(f"🔍 Searching web and generating answer...")
            
            start_time = time.time()
            
            try:
                # Process the question
                result = pipeline.process_query(
                    text=question,
                    max_results=3,  # Search 3 web sources
                    request_id=f"user_q_{question_count}"
                )
                
                processing_time = time.time() - start_time
                
                if result.success:
                    print(f"\n✅ Answer ready! ({processing_time:.2f}s)")
                    print(f"🎯 Confidence: {result.response.confidence_score:.1%}")
                    
                    # Display the AI answer
                    print(f"\n🤖 AI Answer:")
                    print("─" * 30)
                    
                    # Format the answer nicely
                    answer_lines = result.response.answer.split('\n')
                    for line in answer_lines:
                        if line.strip() and not line.startswith('**Sources:**'):
                            print(f"   {line.strip()}")
                        elif line.startswith('**Sources:**'):
                            break
                    
                    # Show sources if found
                    if result.response.sources:
                        print(f"\n📚 Sources ({len(result.response.sources)}):")
                        for i, source in enumerate(result.response.sources, 1):
                            url = source.get('url', 'Unknown URL')
                            similarity = source.get('similarity_score', 0)
                            print(f"   {i}. {url} (relevance: {similarity:.1%})")
                    
                    # Show any warnings
                    if result.warnings:
                        print(f"\n⚠️ Note: {result.warnings[0]}")
                    
                    # Show performance info
                    print(f"\n📊 Stats: Model: {result.response.model_used} | "
                          f"Time: {processing_time:.2f}s | "
                          f"Sources: {len(result.response.sources)}")
                
                else:
                    print(f"\n❌ Sorry, I couldn't process your question.")
                    print(f"💬 Issue: {result.error_message}")
                    
                    if result.validation_report and not result.validation_report.is_valid:
                        print(f"\n💡 Suggestions:")
                        for suggestion in result.validation_report.recommendations[:2]:
                            print(f"   • {suggestion}")
            
            except KeyboardInterrupt:
                print("\n\n👋 Interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                print("💡 Try rephrasing your question or check your internet connection.")
        
        # Clean up
        pipeline.close()
        
        print(f"\n📊 Session Summary:")
        print(f"   Questions asked: {question_count}")
        print(f"   Thank you for using the AI Assistant! 🚀")
        
    except KeyboardInterrupt:
        print("\n\n👋 Startup interrupted. Goodbye!")
    except Exception as e:
        print(f"\n❌ Failed to start AI Assistant: {str(e)}")
        print("\n💡 Troubleshooting:")
        print("   • Make sure you're in the virtual environment")
        print("   • Check your internet connection")
        print("   • Try: venv\\Scripts\\activate")


if __name__ == "__main__":
    main()
"""
Demo of the RAG pipeline without OpenAI API dependency.
Shows error handling and validation working with mock responses.
"""

import sys
import os
import time
from PIL import Image

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.validation_manager import validation_manager
from src.enhanced_logger import enhanced_logger, LogCategory, RequestLoggingContext
from src.health_monitor import health_monitor


class MockRAGPipeline:
    """Mock RAG pipeline that works without OpenAI API."""
    
    def __init__(self):
        self.enable_web_retrieval = False  # Disable for demo
        
    def process_query(self, text: str, images=None, request_id=None):
        """Process query with comprehensive error handling but mock response."""
        
        if request_id is None:
            request_id = f"mock_req_{int(time.time() * 1000)}"
        
        with RequestLoggingContext(request_id) as logger:
            
            # Step 1: Input validation (this works without API)
            logger.info(
                f"Processing query: {text[:50]}...",
                component="mock_pipeline",
                category=LogCategory.PIPELINE
            )
            
            validation_report = validation_manager.validate_user_input(text, images, request_id)
            
            if not validation_report.is_valid:
                logger.warning(
                    f"Input validation failed",
                    component="mock_pipeline",
                    category=LogCategory.USER_INTERACTION
                )
                
                return {
                    'success': False,
                    'error_message': validation_report.get_user_message(),
                    'validation_report': validation_report,
                    'response': None
                }
            
            # Step 2: Mock processing (simulate what would happen)
            logger.info(
                "Input validation passed, processing with mock pipeline",
                component="mock_pipeline",
                category=LogCategory.PIPELINE
            )
            
            # Simulate processing time
            time.sleep(0.1)
            
            # Create mock response
            mock_response = {
                'answer': f"Mock response for: '{text}'. This demonstrates that the error handling and validation system is working correctly, even without OpenAI API access.",
                'sources': [],
                'confidence_score': 0.8,
                'generation_time': time.time(),
                'context_used': [],
                'validation_passed': True
            }
            
            logger.info(
                "Mock response generated successfully",
                component="mock_pipeline",
                category=LogCategory.RESPONSE_GENERATION
            )
            
            return {
                'success': True,
                'error_message': None,
                'validation_report': validation_report,
                'response': mock_response,
                'warnings': validation_report.warnings,
                'fallback_strategies_used': ['mock_response']
            }


def demo_validation_system():
    """Demonstrate the validation system working."""
    print("\n" + "="*60)
    print("🔍 INPUT VALIDATION DEMONSTRATION")
    print("="*60)
    
    test_cases = [
        ("What is artificial intelligence?", None, "✅ Valid query"),
        ("", None, "❌ Empty query"),
        ("AI", None, "❌ Too short"),
        ("<script>alert('xss')</script>", None, "❌ Suspicious content"),
        ("What's in this image?", [Image.new('RGB', (100, 100))], "✅ Valid with image"),
        ("Analyze this", ["/fake/path.jpg"], "❌ Invalid image path"),
    ]
    
    for i, (text, images, expected) in enumerate(test_cases, 1):
        print(f"\n{i}. {expected}")
        text_display = text[:30] + ('...' if len(text) > 30 else '')
        print(f"   Input: '{text_display}'")
        
        report = validation_manager.validate_user_input(text, images, f"demo_{i}")
        
        status = "✅ VALID" if report.is_valid else "❌ INVALID"
        print(f"   Result: {status}")
        print(f"   Message: {report.get_user_message()}")
        
        if report.warnings:
            print(f"   Warnings: {'; '.join(report.warnings[:1])}")
        
        if not report.is_valid and report.recommendations:
            print(f"   Suggestions: {'; '.join(report.recommendations[:1])}")


def demo_mock_pipeline():
    """Demonstrate the pipeline working with mock responses."""
    print("\n" + "="*60)
    print("🤖 MOCK PIPELINE DEMONSTRATION")
    print("="*60)
    
    pipeline = MockRAGPipeline()
    
    test_queries = [
        "What is the key to success?",
        "How does machine learning work?",
        "Explain quantum computing",
        "",  # This should fail validation
        "AI",  # This should also fail
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        
        result = pipeline.process_query(query, request_id=f"demo_query_{i}")
        
        if result['success']:
            print(f"   ✅ SUCCESS")
            print(f"   Answer: {result['response']['answer'][:100]}...")
            if result['warnings']:
                print(f"   Warnings: {'; '.join(result['warnings'])}")
        else:
            print(f"   ❌ FAILED")
            print(f"   Error: {result['error_message']}")


def demo_system_health():
    """Demonstrate system health monitoring."""
    print("\n" + "="*60)
    print("🏥 SYSTEM HEALTH DEMONSTRATION")
    print("="*60)
    
    # Check system readiness
    is_ready, warnings, critical_issues = validation_manager.check_system_readiness()
    
    print(f"\n📊 System Status:")
    print(f"   Ready: {'✅ Yes' if is_ready else '❌ No'}")
    
    if warnings:
        print(f"   Warnings: {len(warnings)}")
        for warning in warnings[:2]:
            print(f"     ⚠️ {warning}")
    
    if critical_issues:
        print(f"   Critical Issues: {len(critical_issues)}")
        for issue in critical_issues[:2]:
            print(f"     🚨 {issue}")
    
    # Get validation statistics
    stats = validation_manager.get_validation_statistics()
    print(f"\n📈 Validation Statistics:")
    print(f"   Total Validations: {stats['total_validations']}")
    print(f"   Success Rate: {stats['success_rate']:.1%}")
    print(f"   Warnings Issued: {stats['warnings_issued']}")


def demo_error_handling():
    """Demonstrate error handling capabilities."""
    print("\n" + "="*60)
    print("🛡️ ERROR HANDLING DEMONSTRATION")
    print("="*60)
    
    from src.validation_manager import validation_manager
    
    # Simulate various errors
    error_scenarios = [
        ("web_retriever", ConnectionError("Network timeout"), "Network issue"),
        ("content_processor", MemoryError("Out of memory"), "Memory issue"),
        ("response_generator", Exception("API quota exceeded"), "API issue"),
    ]
    
    for i, (component, error, description) in enumerate(error_scenarios, 1):
        print(f"\n{i}. {description}")
        print(f"   Component: {component}")
        print(f"   Error: {type(error).__name__}")
        
        error_details, fallback = validation_manager.handle_processing_error(component, error)
        
        print(f"   ✅ Handled gracefully")
        print(f"   User Message: {error_details.user_message}")
        print(f"   Fallback: {fallback.get('strategy', 'None')}")
        print(f"   Recoverable: {'Yes' if error_details.recoverable else 'No'}")


def main():
    """Run the complete demo."""
    print("🚀 RAG PIPELINE DEMO - NO OPENAI API REQUIRED")
    print("=" * 80)
    print("This demo shows the comprehensive error handling and validation")
    print("system working WITHOUT requiring OpenAI API access.")
    print("All the core functionality works independently!")
    
    try:
        demo_validation_system()
        demo_error_handling()
        demo_system_health()
        demo_mock_pipeline()
        
        print("\n" + "="*80)
        print("🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("="*80)
        
        print("\n✨ Key Features Demonstrated:")
        print("• ✅ Comprehensive input validation")
        print("• ✅ Intelligent error classification and handling")
        print("• ✅ Graceful degradation with fallback strategies")
        print("• ✅ System health monitoring")
        print("• ✅ Structured logging and performance tracking")
        print("• ✅ User-friendly error messages")
        
        print("\n🔧 To use with OpenAI API:")
        print("1. Get an OpenAI API key with sufficient quota")
        print("2. Add it to your .env file: OPENAI_API_KEY=your_key_here")
        print("3. Run: python examples/enhanced_web_demo.py")
        
        print("\n💡 The system works great even without OpenAI!")
        print("You can use it for validation, error handling, and monitoring.")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
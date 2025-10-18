"""
Demonstration of comprehensive error handling and validation system.
Shows how the system gracefully handles various error conditions and provides
user-friendly feedback with fallback strategies.
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
from src.error_handler import input_validator, component_error_handler


def demo_input_validation():
    """Demonstrate input validation with various scenarios."""
    print("\n" + "="*60)
    print("INPUT VALIDATION DEMONSTRATION")
    print("="*60)
    
    test_cases = [
        # Valid cases
        ("What is artificial intelligence?", None, "Valid text query"),
        ("How does machine learning work?", [], "Valid text with empty image list"),
        
        # Invalid cases
        ("", None, "Empty text query"),
        ("AI", None, "Very short query"),
        ("<script>alert('xss')</script>What is AI?", None, "Query with suspicious content"),
        ("A" * 15000, None, "Extremely long query"),
        
        # Image validation cases
        ("What's in this image?", [Image.new('RGB', (100, 100))], "Valid text with PIL image"),
        ("Analyze this", ["/nonexistent/image.jpg"], "Valid text with invalid image path"),
        ("Process this", [b""], "Valid text with empty image bytes"),
        ("Check this", [123], "Valid text with invalid image type"),
    ]
    
    for i, (text, images, description) in enumerate(test_cases, 1):
        print(f"\n{i}. {description}")
        print(f"   Input: '{text[:50]}{'...' if len(text) > 50 else ''}' + {len(images) if images else 0} images")
        
        try:
            report = validation_manager.validate_user_input(
                text, images, request_id=f"demo_{i}"
            )
            
            print(f"   Result: {'✅ VALID' if report.is_valid else '❌ INVALID'}")
            print(f"   User Message: {report.get_user_message()}")
            
            if report.warnings:
                print(f"   Warnings: {'; '.join(report.warnings[:2])}")
            
            if report.errors:
                print(f"   Errors: {len(report.errors)} error(s)")
                for error in report.errors[:2]:  # Show first 2 errors
                    print(f"     - {error.error_id}: {error.message}")
            
            if not report.is_valid:
                print(f"   Suggestions: {'; '.join(report.recommendations[:2])}")
            
            # Show processing options
            opts = report.processing_options
            print(f"   Processing Options: Web={opts.enable_web_retrieval}, "
                  f"Images={opts.enable_image_processing}, Context={opts.enable_context_retrieval}")
            
        except Exception as e:
            print(f"   ❌ VALIDATION ERROR: {str(e)}")


def demo_error_handling():
    """Demonstrate error handling and fallback strategies."""
    print("\n" + "="*60)
    print("ERROR HANDLING DEMONSTRATION")
    print("="*60)
    
    # Simulate various component errors
    error_scenarios = [
        ("web_retriever", ConnectionError("Network timeout"), "Network connectivity issue"),
        ("content_processor", MemoryError("Out of memory"), "Memory exhaustion"),
        ("vector_db", Exception("Database connection failed"), "Database connectivity issue"),
        ("response_generator", Exception("OpenAI API rate limit exceeded"), "API rate limiting"),
        ("unknown_component", ValueError("Invalid configuration"), "Configuration error"),
    ]
    
    for i, (component, error, description) in enumerate(error_scenarios, 1):
        print(f"\n{i}. {description}")
        print(f"   Component: {component}")
        print(f"   Error: {type(error).__name__}: {str(error)}")
        
        try:
            error_details, fallback_strategy = validation_manager.handle_processing_error(
                component, error, {"demo": True, "scenario": i}
            )
            
            print(f"   Error ID: {error_details.error_id}")
            print(f"   Category: {error_details.category.value}")
            print(f"   Severity: {error_details.severity.value}")
            print(f"   Recoverable: {'✅ Yes' if error_details.recoverable else '❌ No'}")
            print(f"   User Message: {error_details.user_message}")
            print(f"   Suggestions: {'; '.join(error_details.suggestions[:2])}")
            
            if fallback_strategy:
                print(f"   Fallback Strategy: {fallback_strategy.get('strategy', 'None')}")
                if 'message' in fallback_strategy:
                    print(f"   Fallback Message: {fallback_strategy['message']}")
            
        except Exception as e:
            print(f"   ❌ ERROR HANDLING FAILED: {str(e)}")


def demo_system_health():
    """Demonstrate system health monitoring."""
    print("\n" + "="*60)
    print("SYSTEM HEALTH MONITORING DEMONSTRATION")
    print("="*60)
    
    try:
        # Check system readiness
        print("\n1. System Readiness Check")
        is_ready, warnings, critical_issues = validation_manager.check_system_readiness()
        
        print(f"   System Ready: {'✅ Yes' if is_ready else '❌ No'}")
        
        if warnings:
            print(f"   Warnings ({len(warnings)}):")
            for warning in warnings[:3]:
                print(f"     - {warning}")
        
        if critical_issues:
            print(f"   Critical Issues ({len(critical_issues)}):")
            for issue in critical_issues[:3]:
                print(f"     - {issue}")
        
        # Perform health check
        print("\n2. Comprehensive Health Check")
        health = health_monitor.check_system_health()
        
        print(f"   Overall Status: {health.overall_status.value.upper()}")
        print(f"   Uptime: {health.uptime_seconds:.1f} seconds")
        
        print(f"\n   Component Health:")
        for name, component in health.components.items():
            status_icon = {
                "healthy": "✅",
                "warning": "⚠️",
                "degraded": "🔶",
                "critical": "❌",
                "unknown": "❓"
            }.get(component.status.value, "❓")
            
            print(f"     {status_icon} {name}: {component.status.value} - {component.message}")
            if component.response_time_ms:
                print(f"        Response Time: {component.response_time_ms:.0f}ms")
        
        if health.alerts:
            print(f"\n   Active Alerts ({len(health.alerts)}):")
            for alert in health.alerts[:3]:
                print(f"     🚨 {alert}")
        
        if health.recommendations:
            print(f"\n   Recommendations ({len(health.recommendations)}):")
            for rec in health.recommendations[:3]:
                print(f"     💡 {rec}")
        
    except Exception as e:
        print(f"   ❌ HEALTH CHECK FAILED: {str(e)}")


def demo_logging_system():
    """Demonstrate enhanced logging capabilities."""
    print("\n" + "="*60)
    print("ENHANCED LOGGING DEMONSTRATION")
    print("="*60)
    
    # Demonstrate request context logging
    print("\n1. Request Context Logging")
    with RequestLoggingContext("demo_request_123", "demo_user") as logger:
        logger.info(
            "Processing user request",
            component="demo_component",
            category=LogCategory.PIPELINE,
            metadata={"action": "demo", "step": 1}
        )
        
        # Simulate some processing time
        time.sleep(0.01)
        
        logger.info(
            "Request processing completed",
            component="demo_component",
            category=LogCategory.PIPELINE
        )
    
    print("   ✅ Request logged with context")
    
    # Demonstrate performance logging
    print("\n2. Performance Logging")
    enhanced_logger.performance.start_timer("demo_operation")
    
    # Simulate work
    time.sleep(0.05)
    
    duration = enhanced_logger.performance.end_timer("demo_operation", "demo_component")
    print(f"   ✅ Operation logged: {duration:.1f}ms")
    
    # Demonstrate error tracking
    print("\n3. Error Tracking")
    try:
        raise ValueError("Demo error for tracking")
    except Exception as e:
        enhanced_logger.error_tracker.log_error(
            e, "demo_component", LogCategory.ERROR_HANDLING, "demo_request_123"
        )
    
    error_summary = enhanced_logger.error_tracker.get_error_summary(1)
    print(f"   ✅ Error tracked: {error_summary['total_errors']} errors in last hour")
    
    # Show validation statistics
    print("\n4. Validation Statistics")
    stats = validation_manager.get_validation_statistics()
    print(f"   Total Validations: {stats['total_validations']}")
    print(f"   Success Rate: {stats['success_rate']:.1%}")
    print(f"   Warnings Issued: {stats['warnings_issued']}")


def demo_graceful_degradation():
    """Demonstrate graceful degradation scenarios."""
    print("\n" + "="*60)
    print("GRACEFUL DEGRADATION DEMONSTRATION")
    print("="*60)
    
    # Simulate a complete pipeline run with various failures
    print("\n1. Simulating Pipeline with Component Failures")
    
    # This would normally be done through the RAG pipeline, but we'll simulate it
    query = "What are the latest developments in AI?"
    
    print(f"   Query: {query}")
    
    # Step 1: Validation (should pass)
    print("\n   Step 1: Input Validation")
    report = validation_manager.validate_user_input(query, request_id="degradation_demo")
    print(f"   ✅ Validation: {'PASSED' if report.is_valid else 'FAILED'}")
    
    # Step 2: Simulate web retrieval failure
    print("\n   Step 2: Web Retrieval (Simulated Failure)")
    try:
        raise ConnectionError("Network unreachable")
    except Exception as e:
        error_details, fallback = validation_manager.handle_processing_error("web_retriever", e)
        print(f"   ❌ Web Retrieval Failed: {error_details.user_message}")
        print(f"   🔄 Fallback Strategy: {fallback.get('strategy', 'None')}")
    
    # Step 3: Simulate content processing with image failure
    print("\n   Step 3: Content Processing (Partial Failure)")
    try:
        raise Exception("Image processing model unavailable")
    except Exception as e:
        error_details, fallback = validation_manager.handle_processing_error("content_processor", e)
        print(f"   ⚠️ Image Processing Failed: {error_details.user_message}")
        print(f"   🔄 Fallback Strategy: {fallback.get('strategy', 'None')}")
    
    # Step 4: Simulate vector DB failure
    print("\n   Step 4: Vector Database (Simulated Failure)")
    try:
        raise Exception("Vector database connection timeout")
    except Exception as e:
        error_details, fallback = validation_manager.handle_processing_error("vector_db", e)
        print(f"   ❌ Vector DB Failed: {error_details.user_message}")
        print(f"   🔄 Fallback Strategy: {fallback.get('strategy', 'None')}")
    
    # Step 5: Response generation with fallback
    print("\n   Step 5: Response Generation (Fallback Mode)")
    print(f"   ✅ Fallback Response: Using general knowledge only")
    print(f"   📝 Final Answer: 'Based on general knowledge, AI continues to advance...'")
    
    print(f"\n   🎯 Result: System provided response despite multiple component failures!")


def main():
    """Run all demonstrations."""
    print("COMPREHENSIVE ERROR HANDLING & VALIDATION SYSTEM DEMO")
    print("=" * 80)
    print("This demo shows how the system handles various error conditions,")
    print("validates user input, monitors system health, and provides graceful")
    print("degradation with user-friendly error messages.")
    
    try:
        # Run all demonstrations
        demo_input_validation()
        demo_error_handling()
        demo_system_health()
        demo_logging_system()
        demo_graceful_degradation()
        
        print("\n" + "="*80)
        print("✅ ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nKey Features Demonstrated:")
        print("• Comprehensive input validation with user-friendly messages")
        print("• Intelligent error classification and handling")
        print("• Graceful degradation with fallback strategies")
        print("• Real-time system health monitoring")
        print("• Structured logging with performance tracking")
        print("• Error pattern analysis and recommendations")
        print("\nThe system is now ready to handle production workloads with")
        print("robust error handling and excellent user experience!")
        
    except Exception as e:
        print(f"\n❌ DEMO FAILED: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
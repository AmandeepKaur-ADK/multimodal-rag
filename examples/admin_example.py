"""
Example demonstrating the administration and configuration features
of the multimodal RAG pipeline.
"""

import time
import logging
from pathlib import Path

# Add src to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.config_manager import config_manager
from src.resource_manager import resource_manager
from src.admin_interface import create_admin_interface
from src.rag_pipeline import create_rag_pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demonstrate_config_management():
    """Demonstrate configuration management features."""
    print("=== Configuration Management Demo ===")
    
    # Get current configuration
    config = config_manager.get_config()
    print(f"Current max concurrent requests: {config.retrieval.max_concurrent_requests}")
    print(f"Current max retrieval time: {config.retrieval.max_retrieval_time}")
    
    # Update retrieval configuration
    print("\\nUpdating retrieval configuration...")
    success = config_manager.update_retrieval_config(
        max_concurrent_requests=3,
        max_retrieval_time=20,
        request_timeout=8
    )
    
    if success:
        print("✓ Retrieval configuration updated successfully")
        updated_config = config_manager.get_config()
        print(f"New max concurrent requests: {updated_config.retrieval.max_concurrent_requests}")
        print(f"New max retrieval time: {updated_config.retrieval.max_retrieval_time}")
    else:
        print("✗ Failed to update retrieval configuration")
    
    # Demonstrate domain management
    print("\\n=== Domain Management Demo ===")
    
    # Block a domain
    test_domain = "example-spam-site.com"
    print(f"Blocking domain: {test_domain}")
    config_manager.add_blocked_domain(test_domain)
    
    # Check if domain is blocked
    updated_config = config_manager.get_config()
    is_blocked = not updated_config.domains.is_domain_allowed(test_domain)
    print(f"Domain {test_domain} is blocked: {is_blocked}")
    
    # Unblock the domain
    print(f"Unblocking domain: {test_domain}")
    config_manager.remove_blocked_domain(test_domain)
    
    # Verify unblocked
    updated_config = config_manager.get_config()
    is_allowed = updated_config.domains.is_domain_allowed(test_domain)
    print(f"Domain {test_domain} is now allowed: {is_allowed}")


def demonstrate_resource_management():
    """Demonstrate resource management features."""
    print("\\n=== Resource Management Demo ===")
    
    # Get current resource usage
    usage = resource_manager.get_resource_usage()
    print(f"Current memory usage: {usage.memory_usage_mb:.1f} MB")
    print(f"Current CPU usage: {usage.cpu_usage_percent:.1f}%")
    print(f"Active requests: {usage.active_requests}")
    
    # Get resource statistics
    stats = resource_manager.get_resource_stats()
    print(f"\\nResource limits:")
    print(f"  Max memory: {stats['limits']['max_memory_mb']} MB")
    print(f"  Max concurrent requests: {stats['limits']['max_concurrent_requests']}")
    
    # Demonstrate concurrent request limiting
    print("\\n=== Concurrent Request Limiting Demo ===")
    
    # Simulate acquiring request slots
    request_ids = []
    for i in range(3):
        request_id = f"demo_request_{i}"
        try:
            context = resource_manager.acquire_request_slot_sync(request_id, "demo")
            request_ids.append(request_id)
            print(f"✓ Acquired slot for {request_id}")
        except Exception as e:
            print(f"✗ Failed to acquire slot for {request_id}: {e}")
    
    # Show active requests
    active_requests = resource_manager.concurrency_limiter.get_active_requests()
    print(f"\\nActive requests: {len(active_requests)}")
    for req in active_requests:
        print(f"  - {req.request_id} ({req.request_type})")
    
    # Release request slots
    print("\\nReleasing request slots...")
    for request_id in request_ids:
        resource_manager.release_request_slot_sync(request_id)
        print(f"✓ Released slot for {request_id}")
    
    # Force cleanup demonstration
    print("\\n=== Resource Cleanup Demo ===")
    cleanup_results = resource_manager.force_cleanup()
    print(f"Cleanup performed: {cleanup_results['cleanup_performed']}")
    print(f"Memory before: {cleanup_results['before']['memory_mb']:.1f} MB")
    print(f"Memory after: {cleanup_results['after']['memory_mb']:.1f} MB")


def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring features."""
    print("\\n=== Performance Monitoring Demo ===")
    
    # Record some sample performance metrics
    print("Recording sample performance metrics...")
    for i in range(5):
        config_manager.record_performance_metrics({
            'total_time': 2.5 + i * 0.5,
            'retrieval_time': 1.0 + i * 0.2,
            'processing_time': 0.8 + i * 0.1,
            'generation_time': 0.7 + i * 0.2,
            'success': i < 4,  # One failure
            'sources_retrieved': 3 + i
        })
        time.sleep(0.1)  # Small delay
    
    # Get performance summary
    summary = config_manager.get_performance_summary()
    print(f"\\nPerformance Summary:")
    print(f"  Status: {summary.get('status', 'unknown')}")
    print(f"  Average response time: {summary.get('avg_response_time', 0):.2f}s")
    print(f"  Failure rate: {summary.get('failure_rate', 0):.1%}")
    print(f"  Total requests: {summary.get('total_requests', 0)}")
    
    if summary.get('recommendations'):
        print(f"  Recommendations:")
        for rec in summary['recommendations']:
            print(f"    - {rec}")


def demonstrate_pipeline_integration():
    """Demonstrate how the pipeline integrates with administration features."""
    print("\\n=== Pipeline Integration Demo ===")
    
    try:
        # Create a RAG pipeline instance
        print("Creating RAG pipeline with administration features...")
        pipeline = create_rag_pipeline(
            vector_db_path="./data/admin_demo_vector_db",
            enable_web_retrieval=False  # Disable for demo
        )
        
        # Process a sample query to generate metrics
        print("Processing sample query...")
        result = pipeline.process_query(
            text="What is artificial intelligence?",
            images=[],
            enable_fallback=True
        )
        
        print(f"Query processed successfully: {result.success}")
        print(f"Processing time: {result.pipeline_stats['total_time']:.2f}s")
        
        # Get pipeline health
        health = pipeline.get_pipeline_health()
        print(f"\\nPipeline Health:")
        print(f"  Status: {health['status']}")
        print(f"  Success rate: {health.get('success_rate', 0):.1%}")
        print(f"  Average response time: {health.get('average_response_time', 0):.2f}s")
        
        # Clean up
        pipeline.close()
        
    except Exception as e:
        print(f"Pipeline demo failed: {e}")
        logger.error(f"Pipeline demo error: {e}")


def demonstrate_admin_interface():
    """Demonstrate the admin interface (without actually starting the server)."""
    print("\\n=== Admin Interface Demo ===")
    
    print("The admin interface provides:")
    print("  - Web-based dashboard for system monitoring")
    print("  - Real-time resource usage metrics")
    print("  - Configuration management UI")
    print("  - Domain blocking/unblocking controls")
    print("  - Performance monitoring charts")
    print("  - System health status")
    
    print("\\nTo start the web admin interface:")
    print("  python -m src.admin_cli web --host 127.0.0.1 --port 8080")
    print("  Then visit: http://127.0.0.1:8080")
    
    print("\\nCLI administration commands:")
    print("  python -m src.admin_cli status")
    print("  python -m src.admin_cli config show")
    print("  python -m src.admin_cli domains block example.com")
    print("  python -m src.admin_cli resources stats")
    print("  python -m src.admin_cli performance summary")


def main():
    """Run all administration feature demonstrations."""
    print("RAG Pipeline Administration Features Demo")
    print("=" * 50)
    
    try:
        demonstrate_config_management()
        demonstrate_resource_management()
        demonstrate_performance_monitoring()
        demonstrate_pipeline_integration()
        demonstrate_admin_interface()
        
        print("\\n" + "=" * 50)
        print("✓ Administration features demo completed successfully!")
        print("\\nNext steps:")
        print("1. Start the web admin interface: python -m src.admin_cli web")
        print("2. Try CLI commands: python -m src.admin_cli status")
        print("3. Monitor your RAG pipeline in production")
        
    except Exception as e:
        print(f"\\n✗ Demo failed: {e}")
        logger.error(f"Demo error: {e}")


if __name__ == "__main__":
    main()
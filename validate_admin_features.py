"""
Simple validation script for administration features.
Tests basic functionality without requiring external dependencies.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.append('src')

def test_config_manager():
    """Test basic config manager functionality."""
    print("Testing ConfigManager...")
    
    try:
        from config_manager import ConfigManager
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_config = f.name
        
        # Initialize config manager
        config_manager = ConfigManager(temp_config)
        
        # Test basic operations
        config = config_manager.get_config()
        assert config is not None
        assert config.retrieval.max_retrieval_time > 0
        
        # Test config update
        success = config_manager.update_retrieval_config(max_retrieval_time=45)
        assert success is True
        
        updated_config = config_manager.get_config()
        assert updated_config.retrieval.max_retrieval_time == 45
        
        # Test domain management
        success = config_manager.add_blocked_domain("test.com")
        assert success is True
        
        config = config_manager.get_config()
        assert not config.domains.is_domain_allowed("test.com")
        
        # Clean up
        Path(temp_config).unlink(missing_ok=True)
        
        print("✓ ConfigManager tests passed")
        return True
        
    except Exception as e:
        print(f"✗ ConfigManager test failed: {e}")
        return False


def test_resource_manager():
    """Test basic resource manager functionality."""
    print("Testing ResourceManager...")
    
    try:
        from resource_manager import ConcurrencyLimiter, MemoryManager
        
        # Test concurrency limiter
        limiter = ConcurrencyLimiter(max_concurrent=2)
        
        # Acquire slots
        context1 = limiter.acquire_sync("req1", "test")
        context2 = limiter.acquire_sync("req2", "test")
        
        assert context1.request_id == "req1"
        assert context2.request_id == "req2"
        
        # Check active requests
        active = limiter.get_active_requests()
        assert len(active) == 2
        
        # Release slots
        limiter.release_sync("req1")
        limiter.release_sync("req2")
        
        active = limiter.get_active_requests()
        assert len(active) == 0
        
        # Test memory manager
        memory_manager = MemoryManager()
        
        cleanup_called = False
        def test_cleanup():
            nonlocal cleanup_called
            cleanup_called = True
        
        memory_manager.register_cleanup_callback(test_cleanup)
        memory_manager.cleanup_if_needed(force=True)
        
        assert cleanup_called is True
        
        print("✓ ResourceManager tests passed")
        return True
        
    except Exception as e:
        print(f"✗ ResourceManager test failed: {e}")
        return False


def test_admin_interface():
    """Test basic admin interface functionality."""
    print("Testing AdminInterface...")
    
    try:
        from admin_interface import AdminInterface
        
        # Create admin interface
        admin = AdminInterface(host="127.0.0.1", port=8081)
        
        # Test that Flask app was created
        assert admin.app is not None
        assert admin.host == "127.0.0.1"
        assert admin.port == 8081
        
        print("✓ AdminInterface tests passed")
        return True
        
    except Exception as e:
        print(f"✗ AdminInterface test failed: {e}")
        return False


def test_admin_cli():
    """Test basic admin CLI functionality."""
    print("Testing AdminCLI...")
    
    try:
        from admin_cli import AdminCLI
        
        # Create CLI instance
        cli = AdminCLI()
        
        # Test that parser was created
        assert cli.parser is not None
        
        # Test help output (should not raise exception)
        help_text = cli.parser.format_help()
        assert "RAG Pipeline Administration Tool" in help_text
        
        print("✓ AdminCLI tests passed")
        return True
        
    except Exception as e:
        print(f"✗ AdminCLI test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("=== Administration Features Validation ===\n")
    
    tests = [
        test_config_manager,
        test_resource_manager,
        test_admin_interface,
        test_admin_cli
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n=== Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All administration features validated successfully!")
        return True
    else:
        print("✗ Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
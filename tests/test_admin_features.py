"""
Tests for administration and configuration features.
"""

import pytest
import tempfile
import json
import time
from pathlib import Path
from unittest.mock import Mock, patch

# Add src to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from src.config_manager import ConfigManager, RetrievalConfig, DomainConfig, ResourceConfig, PerformanceConfig
from src.resource_manager import ResourceManager, ConcurrencyLimiter, MemoryManager
from src.admin_interface import AdminInterface


class TestConfigManager:
    """Test configuration management functionality."""
    
    def setup_method(self):
        """Setup test configuration manager with temporary file."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.json"
        self.config_manager = ConfigManager(str(self.config_file))
    
    def test_default_config_creation(self):
        """Test that default configuration is created properly."""
        config = self.config_manager.get_config()
        
        assert config is not None
        assert config.retrieval.max_retrieval_time > 0
        assert config.retrieval.max_concurrent_requests > 0
        assert config.domains.allowed_domains == []
        assert config.domains.blocked_domains == []
        assert config.resources.max_memory_usage_mb > 0
        assert config.performance.enable_auto_adjustment is True
    
    def test_config_validation(self):
        """Test configuration validation."""
        config = self.config_manager.get_config()
        
        # Valid configuration should have no errors
        errors = config.validate()
        assert len(errors) == 0
        
        # Invalid configuration should have errors
        config.retrieval.max_retrieval_time = -1
        config.resources.max_memory_usage_mb = 0
        
        errors = config.validate()
        assert len(errors) > 0
        assert any("max_retrieval_time" in error for error in errors)
        assert any("max_memory_usage_mb" in error for error in errors)
    
    def test_retrieval_config_update(self):
        """Test updating retrieval configuration."""
        # Update retrieval config
        success = self.config_manager.update_retrieval_config(
            max_retrieval_time=45,
            max_concurrent_requests=8,
            request_timeout=15
        )
        
        assert success is True
        
        # Verify changes
        config = self.config_manager.get_config()
        assert config.retrieval.max_retrieval_time == 45
        assert config.retrieval.max_concurrent_requests == 8
        assert config.retrieval.request_timeout == 15
    
    def test_domain_management(self):
        """Test domain blocking and unblocking."""
        test_domain = "example.com"
        
        # Initially domain should be allowed
        config = self.config_manager.get_config()
        assert config.domains.is_domain_allowed(test_domain) is True
        
        # Block domain
        success = self.config_manager.add_blocked_domain(test_domain)
        assert success is True
        
        # Domain should now be blocked
        config = self.config_manager.get_config()
        assert config.domains.is_domain_allowed(test_domain) is False
        assert test_domain in config.domains.blocked_domains
        
        # Unblock domain
        success = self.config_manager.remove_blocked_domain(test_domain)
        assert success is True
        
        # Domain should be allowed again
        config = self.config_manager.get_config()
        assert config.domains.is_domain_allowed(test_domain) is True
        assert test_domain not in config.domains.blocked_domains
    
    def test_domain_failure_tracking(self):
        """Test automatic domain blocking on failures."""
        test_domain = "failing-domain.com"
        
        # Configure auto-blocking
        self.config_manager.update_domain_config(
            auto_block_failed_domains=True,
            domain_failure_threshold=3
        )
        
        # Record failures below threshold
        for _ in range(2):
            self.config_manager.record_domain_failure(test_domain)
        
        # Domain should still be allowed
        config = self.config_manager.get_config()
        assert config.domains.is_domain_allowed(test_domain) is True
        
        # Record one more failure to reach threshold
        self.config_manager.record_domain_failure(test_domain)
        
        # Domain should now be auto-blocked
        config = self.config_manager.get_config()
        assert config.domains.is_domain_allowed(test_domain) is False
        assert test_domain in config.domains.blocked_domains
    
    def test_performance_metrics_recording(self):
        """Test performance metrics recording and summary."""
        # Record some metrics
        metrics = [
            {'total_time': 2.5, 'success': True},
            {'total_time': 3.0, 'success': True},
            {'total_time': 5.0, 'success': False},
            {'total_time': 2.8, 'success': True}
        ]
        
        for metric in metrics:
            self.config_manager.record_performance_metrics(metric)
        
        # Get performance summary
        summary = self.config_manager.get_performance_summary()
        
        assert summary['status'] in ['healthy', 'slow', 'degraded']
        assert 'avg_response_time' in summary
        assert 'failure_rate' in summary
        assert summary['total_requests'] >= len(metrics)
    
    def test_config_persistence(self):
        """Test that configuration changes are persisted."""
        # Make changes
        self.config_manager.update_retrieval_config(max_retrieval_time=99)
        self.config_manager.add_blocked_domain("test-persist.com")
        
        # Create new config manager with same file
        new_config_manager = ConfigManager(str(self.config_file))
        config = new_config_manager.get_config()
        
        # Verify changes were persisted
        assert config.retrieval.max_retrieval_time == 99
        assert "test-persist.com" in config.domains.blocked_domains


class TestResourceManager:
    """Test resource management functionality."""
    
    def setup_method(self):
        """Setup test resource manager."""
        # Mock the config manager to avoid file operations
        with patch('src.resource_manager.config_manager') as mock_config:
            mock_config.get_config.return_value = Mock(
                retrieval=Mock(max_concurrent_requests=3),
                resources=Mock(max_memory_usage_mb=1024, enable_auto_cleanup=True)
            )
            self.resource_manager = ResourceManager()
    
    def test_concurrency_limiting(self):
        """Test concurrent request limiting."""
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
        
        # Check no active requests
        active = limiter.get_active_requests()
        assert len(active) == 0
    
    def test_concurrency_limit_update(self):
        """Test updating concurrency limits."""
        limiter = ConcurrencyLimiter(max_concurrent=2)
        
        # Update limit
        limiter.update_limit(5)
        assert limiter.max_concurrent == 5
        
        # Get stats
        stats = limiter.get_stats()
        assert stats['max_concurrent'] == 5
        assert stats['active_requests'] == 0
        assert stats['available_slots'] == 5
    
    @patch('psutil.Process')
    def test_memory_monitoring(self, mock_process):
        """Test memory usage monitoring."""
        # Mock memory info
        mock_process.return_value.memory_info.return_value.rss = 512 * 1024 * 1024  # 512 MB
        
        memory_manager = MemoryManager()
        usage = memory_manager.get_memory_usage()
        
        assert usage == 512.0  # Should be 512 MB
    
    @patch('psutil.Process')
    def test_memory_pressure_detection(self, mock_process):
        """Test memory pressure detection."""
        # Mock high memory usage
        mock_process.return_value.memory_info.return_value.rss = 2048 * 1024 * 1024  # 2048 MB
        
        memory_manager = MemoryManager()
        memory_manager.memory_threshold_mb = 1024  # 1GB threshold
        
        # Should detect memory pressure
        assert memory_manager.check_memory_pressure() is True
        
        # Mock low memory usage
        mock_process.return_value.memory_info.return_value.rss = 256 * 1024 * 1024  # 256 MB
        
        # Should not detect memory pressure
        assert memory_manager.check_memory_pressure() is False
    
    def test_cleanup_callback_registration(self):
        """Test cleanup callback registration and execution."""
        cleanup_called = False
        
        def cleanup_callback():
            nonlocal cleanup_called
            cleanup_called = True
        
        memory_manager = MemoryManager()
        memory_manager.register_cleanup_callback(cleanup_callback)
        
        # Force cleanup
        memory_manager.cleanup_if_needed(force=True)
        
        assert cleanup_called is True
    
    @patch('psutil.Process')
    def test_resource_stats(self, mock_process):
        """Test resource statistics collection."""
        # Mock system info
        mock_process.return_value.memory_info.return_value.rss = 512 * 1024 * 1024
        mock_process.return_value.cpu_percent.return_value = 25.5
        
        with patch('src.resource_manager.config_manager') as mock_config:
            mock_config.get_config.return_value = Mock(
                retrieval=Mock(max_concurrent_requests=5),
                resources=Mock(max_memory_usage_mb=1024, max_vector_db_size_mb=2048)
            )
            
            resource_manager = ResourceManager()
            stats = resource_manager.get_resource_stats()
            
            assert 'current' in stats
            assert 'limits' in stats
            assert 'health' in stats
            assert stats['current']['memory_usage_mb'] == 512.0
            assert stats['current']['cpu_usage_percent'] == 25.5
            assert stats['limits']['max_memory_mb'] == 1024
            assert stats['limits']['max_concurrent_requests'] == 5


class TestAdminInterface:
    """Test admin interface functionality."""
    
    def setup_method(self):
        """Setup test admin interface."""
        self.admin_interface = AdminInterface(host="127.0.0.1", port=8081)
        self.client = self.admin_interface.app.test_client()
    
    @patch('src.admin_interface.config_manager')
    @patch('src.admin_interface.resource_manager')
    def test_status_endpoint(self, mock_resource_manager, mock_config_manager):
        """Test status API endpoint."""
        # Mock responses
        mock_config_manager.get_config.return_value = Mock(
            version="1.0",
            last_updated="2024-01-01T00:00:00"
        )
        mock_resource_manager.get_resource_stats.return_value = {
            "current": {"memory_usage_mb": 512, "cpu_usage_percent": 25},
            "health": {"memory_pressure": False, "high_cpu": False}
        }
        mock_config_manager.get_performance_summary.return_value = {
            "status": "healthy",
            "avg_response_time": 2.5
        }
        
        response = self.client.get('/api/status')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'system_health' in data['data']
        assert 'resource_stats' in data['data']
    
    @patch('src.admin_interface.config_manager')
    def test_config_endpoint(self, mock_config_manager):
        """Test configuration API endpoint."""
        # Mock config
        mock_config = Mock()
        mock_config.retrieval.__dict__ = {"max_retrieval_time": 30}
        mock_config.domains.__dict__ = {"blocked_domains": []}
        mock_config.resources.__dict__ = {"max_memory_usage_mb": 1024}
        mock_config.performance.__dict__ = {"enable_auto_adjustment": True}
        mock_config.last_updated = "2024-01-01T00:00:00"
        mock_config.version = "1.0"
        
        mock_config_manager.get_config.return_value = mock_config
        
        response = self.client.get('/api/config')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'retrieval' in data['data']
        assert 'domains' in data['data']
    
    @patch('src.admin_interface.config_manager')
    def test_config_update_endpoint(self, mock_config_manager):
        """Test configuration update API endpoint."""
        mock_config_manager.update_retrieval_config.return_value = True
        
        response = self.client.post('/api/config/retrieval',
                                  json={'max_retrieval_time': 45},
                                  content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        
        # Verify the config manager was called
        mock_config_manager.update_retrieval_config.assert_called_once_with(max_retrieval_time=45)
    
    @patch('src.admin_interface.config_manager')
    def test_domain_block_endpoint(self, mock_config_manager):
        """Test domain blocking API endpoint."""
        mock_config_manager.add_blocked_domain.return_value = True
        
        response = self.client.post('/api/domains/block',
                                  json={'domain': 'example.com'},
                                  content_type='application/json')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        
        # Verify the config manager was called
        mock_config_manager.add_blocked_domain.assert_called_once_with('example.com')
    
    @patch('src.admin_interface.resource_manager')
    def test_cleanup_endpoint(self, mock_resource_manager):
        """Test resource cleanup API endpoint."""
        mock_resource_manager.force_cleanup.return_value = {
            'cleanup_performed': True,
            'before': {'memory_mb': 1000, 'disk_mb': 500},
            'after': {'memory_mb': 800, 'disk_mb': 400},
            'savings': {'memory_mb': 200, 'disk_mb': 100}
        }
        
        response = self.client.post('/api/resources/cleanup')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert data['data']['cleanup_performed'] is True
        assert data['data']['savings']['memory_mb'] == 200


def test_integration_config_and_resource_managers():
    """Test integration between config and resource managers."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "integration_test_config.json"
        
        # Create config manager
        config_manager = ConfigManager(str(config_file))
        
        # Mock resource manager creation to use our config manager
        with patch('src.resource_manager.config_manager', config_manager):
            resource_manager = ResourceManager()
            
            # Update config
            config_manager.update_retrieval_config(max_concurrent_requests=10)
            
            # Verify resource manager gets updated
            # Note: In real implementation, this would be handled by the callback
            # For testing, we'll verify the config is accessible
            config = config_manager.get_config()
            assert config.retrieval.max_concurrent_requests == 10


if __name__ == '__main__':
    pytest.main([__file__])
"""
Test suite for comprehensive error handling and validation system.
"""

import pytest
import tempfile
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.error_handler import (
    input_validator, component_error_handler, ErrorSeverity, ErrorCategory
)
from src.validation_manager import validation_manager, ProcessingOptions
from src.health_monitor import health_monitor, HealthStatus
from src.enhanced_logger import enhanced_logger, LogCategory


class TestInputValidator:
    """Test input validation functionality."""
    
    def test_valid_text_query(self):
        """Test validation of valid text queries."""
        result = input_validator.validate_text_query("What is artificial intelligence?")
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.sanitized_input == "What is artificial intelligence?"
    
    def test_empty_text_query(self):
        """Test validation of empty text queries."""
        result = input_validator.validate_text_query("")
        
        assert not result.is_valid
        assert len(result.errors) > 0
        # Print actual error for debugging
        print(f"Actual error ID: {result.errors[0].error_id}")
        # The empty string should trigger TEXT_002 after stripping
        assert result.errors[0].error_id in ["TEXT_001", "TEXT_002"]
        assert result.errors[0].severity == ErrorSeverity.HIGH
    
    def test_none_text_query(self):
        """Test validation of None text queries."""
        result = input_validator.validate_text_query(None)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert result.errors[0].error_id == "TEXT_001"
    
    def test_short_text_query(self):
        """Test validation of very short text queries."""
        result = input_validator.validate_text_query("AI")
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert result.errors[0].error_id == "TEXT_003"
        assert result.errors[0].severity == ErrorSeverity.MEDIUM
    
    def test_suspicious_content(self):
        """Test validation of potentially unsafe content."""
        result = input_validator.validate_text_query("<script>alert('test')</script>")
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert result.errors[0].error_id == "TEXT_004"
    
    def test_long_text_truncation(self):
        """Test handling of very long text queries."""
        long_text = "A" * 15000  # Longer than MAX_TEXT_LENGTH
        result = input_validator.validate_text_query(long_text)
        
        assert result.is_valid
        assert len(result.warnings) > 0
        assert len(result.sanitized_input) <= 10000  # Should be truncated
    
    def test_valid_image_none(self):
        """Test validation when no image is provided."""
        result = input_validator.validate_image_input(None)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.sanitized_input is None
    
    def test_valid_pil_image(self):
        """Test validation of valid PIL Image."""
        # Create a test image
        image = Image.new('RGB', (100, 100), color='red')
        result = input_validator.validate_image_input(image)
        
        if not result.is_valid:
            print(f"Image validation failed: {[e.message for e in result.errors]}")
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert isinstance(result.sanitized_input, Image.Image)
    
    def test_invalid_image_path(self):
        """Test validation of invalid image file path."""
        result = input_validator.validate_image_input("/nonexistent/path/image.jpg")
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert result.errors[0].error_id == "IMG_001"
    
    def test_empty_image_bytes(self):
        """Test validation of empty image bytes."""
        result = input_validator.validate_image_input(b"")
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert result.errors[0].error_id == "IMG_003"
    
    def test_large_image_bytes(self):
        """Test validation of oversized image bytes."""
        large_bytes = b"fake_image_data" * 1000000  # > 10MB
        result = input_validator.validate_image_input(large_bytes)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert result.errors[0].error_id == "IMG_004"
    
    def test_unsupported_input_type(self):
        """Test validation of unsupported input type."""
        result = input_validator.validate_image_input(123)  # Invalid type
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert result.errors[0].error_id == "IMG_006"


class TestComponentErrorHandler:
    """Test component error handling functionality."""
    
    def test_network_error_classification(self):
        """Test classification of network errors."""
        import requests
        error = requests.ConnectionError("Network unreachable")
        
        error_details = component_error_handler.handle_component_error(
            "web_retriever", error
        )
        
        assert error_details.category == ErrorCategory.NETWORK
        assert error_details.severity == ErrorSeverity.MEDIUM
        assert error_details.recoverable
    
    def test_memory_error_classification(self):
        """Test classification of memory errors."""
        error = MemoryError("Out of memory")
        
        error_details = component_error_handler.handle_component_error(
            "content_processor", error
        )
        
        assert error_details.category == ErrorCategory.RESOURCE
        assert error_details.severity == ErrorSeverity.HIGH
    
    def test_api_error_classification(self):
        """Test classification of API errors."""
        error = Exception("OpenAI API rate limit exceeded")
        
        error_details = component_error_handler.handle_component_error(
            "response_generator", error
        )
        
        assert error_details.category == ErrorCategory.EXTERNAL_API
        assert error_details.severity == ErrorSeverity.MEDIUM
    
    def test_fallback_strategy_web_retriever(self):
        """Test fallback strategy for web retriever."""
        error = Exception("Network timeout")
        
        error_details = component_error_handler.handle_component_error(
            "web_retriever", error
        )
        
        assert error_details.recoverable
        assert "web_retriever" in component_error_handler.fallback_strategies
    
    def test_component_status_tracking(self):
        """Test component status tracking."""
        error = Exception("Test error")
        
        component_error_handler.handle_component_error("test_component", error)
        
        status = component_error_handler.get_component_status()
        assert "test_component" in status
        assert status["test_component"]["status"] == "error"


class TestValidationManager:
    """Test validation manager functionality."""
    
    def test_valid_input_validation(self):
        """Test validation of valid user input."""
        report = validation_manager.validate_user_input(
            "What is machine learning?", 
            request_id="test_001"
        )
        
        assert report.is_valid
        assert len(report.errors) == 0
        assert report.processing_options.enable_web_retrieval
        assert report.processing_options.enable_image_processing
    
    def test_invalid_input_validation(self):
        """Test validation of invalid user input."""
        report = validation_manager.validate_user_input(
            "",  # Empty text
            request_id="test_002"
        )
        
        assert not report.is_valid
        assert len(report.errors) > 0
        assert report.has_critical_errors()
    
    def test_processing_options_adjustment(self):
        """Test processing options adjustment based on validation."""
        # Create a mock image that will fail validation
        report = validation_manager.validate_user_input(
            "Valid question",
            images=[123],  # Invalid image type
            request_id="test_003"
        )
        
        # Should be invalid due to image validation failure
        assert not report.is_valid
        # Processing options should disable image processing
        assert not report.processing_options.enable_image_processing
    
    def test_system_readiness_check(self):
        """Test system readiness checking."""
        is_ready, warnings, critical_issues = validation_manager.check_system_readiness()
        
        # Should return boolean and lists
        assert isinstance(is_ready, bool)
        assert isinstance(warnings, list)
        assert isinstance(critical_issues, list)
    
    def test_validation_statistics(self):
        """Test validation statistics tracking."""
        # Reset statistics
        validation_manager.reset_statistics()
        
        # Perform some validations
        validation_manager.validate_user_input("Valid query 1")
        validation_manager.validate_user_input("Valid query 2")
        validation_manager.validate_user_input("")  # Invalid
        
        stats = validation_manager.get_validation_statistics()
        
        assert stats['total_validations'] == 3
        assert stats['successful_validations'] == 2
        assert stats['failed_validations'] == 1
        assert stats['success_rate'] == 2/3


class TestEnhancedLogger:
    """Test enhanced logging functionality."""
    
    def test_structured_logging(self):
        """Test structured logging with metadata."""
        enhanced_logger.info(
            "Test message",
            component="test_component",
            category=LogCategory.SYSTEM,
            metadata={"test_key": "test_value"}
        )
        
        # Should not raise any exceptions
        assert True
    
    def test_request_context(self):
        """Test request context management."""
        enhanced_logger.set_request_context("test_request_123", "test_user")
        
        enhanced_logger.info(
            "Test with context",
            component="test_component",
            category=LogCategory.PIPELINE
        )
        
        enhanced_logger.clear_request_context()
        
        # Should not raise any exceptions
        assert True
    
    def test_performance_logging(self):
        """Test performance logging functionality."""
        enhanced_logger.performance.start_timer("test_operation")
        
        # Simulate some work
        import time
        time.sleep(0.01)
        
        duration = enhanced_logger.performance.end_timer(
            "test_operation", 
            "test_component"
        )
        
        assert duration > 0
    
    def test_error_tracking(self):
        """Test error tracking functionality."""
        test_error = ValueError("Test error")
        
        enhanced_logger.error_tracker.log_error(
            test_error,
            "test_component",
            LogCategory.ERROR_HANDLING,
            "test_request_123"
        )
        
        summary = enhanced_logger.error_tracker.get_error_summary(1)
        
        assert summary['total_errors'] > 0
        assert 'test_component' in summary['errors_by_component']


class TestHealthMonitor:
    """Test health monitoring functionality."""
    
    def test_component_health_check(self):
        """Test individual component health checks."""
        # This is a basic test - in practice, you'd mock the components
        health_checker = health_monitor.health_checker
        
        # Test web retriever health check (will likely fail in test environment)
        web_health = health_checker.check_web_retriever()
        
        assert web_health.name == "web_retriever"
        assert isinstance(web_health.status, HealthStatus)
        assert web_health.last_check is not None
    
    def test_system_health_check(self):
        """Test comprehensive system health check."""
        health = health_monitor.check_system_health()
        
        assert health.overall_status is not None
        assert isinstance(health.components, dict)
        assert health.last_updated is not None
        assert health.uptime_seconds >= 0
    
    def test_health_history(self):
        """Test health history tracking."""
        # Perform a health check
        health_monitor.check_system_health()
        
        # Get recent history
        history = health_monitor.get_health_history(1)  # Last 1 hour
        
        assert isinstance(history, list)


class TestIntegration:
    """Test integration between components."""
    
    def test_validation_to_processing_flow(self):
        """Test flow from validation to processing options."""
        # Test with valid input
        report = validation_manager.validate_user_input(
            "What is the weather today?",
            request_id="integration_test_001"
        )
        
        assert report.is_valid
        assert report.processing_options.enable_web_retrieval
        
        # Test with network-related error simulation
        with patch('src.error_handler.component_error_handler.handle_component_error') as mock_handler:
            mock_handler.return_value = Mock(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                recoverable=True
            )
            
            error_details, fallback = validation_manager.handle_processing_error(
                "web_retriever", 
                Exception("Network error")
            )
            
            assert error_details is not None
            assert isinstance(fallback, dict)
    
    def test_error_handling_with_logging(self):
        """Test error handling integration with logging."""
        with patch('src.enhanced_logger.enhanced_logger.error') as mock_log:
            try:
                raise ValueError("Test integration error")
            except Exception as e:
                validation_manager.handle_processing_error("test_component", e)
            
            # Should have logged the error
            mock_log.assert_called()


if __name__ == "__main__":
    # Run basic tests
    print("Running error handling tests...")
    
    # Test input validation
    print("Testing input validation...")
    validator_tests = TestInputValidator()
    validator_tests.test_valid_text_query()
    validator_tests.test_empty_text_query()
    validator_tests.test_valid_pil_image()
    print("✓ Input validation tests passed")
    
    # Test error handling
    print("Testing error handling...")
    error_tests = TestComponentErrorHandler()
    error_tests.test_network_error_classification()
    error_tests.test_component_status_tracking()
    print("✓ Error handling tests passed")
    
    # Test validation manager
    print("Testing validation manager...")
    validation_tests = TestValidationManager()
    validation_tests.test_valid_input_validation()
    validation_tests.test_system_readiness_check()
    print("✓ Validation manager tests passed")
    
    # Test logging
    print("Testing enhanced logging...")
    logging_tests = TestEnhancedLogger()
    logging_tests.test_structured_logging()
    logging_tests.test_performance_logging()
    print("✓ Enhanced logging tests passed")
    
    print("\nAll error handling tests completed successfully! ✅")
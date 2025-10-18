"""
Validation Manager for the multimodal RAG pipeline.
Integrates input validation, error handling, and graceful degradation strategies.
"""

import logging
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from PIL import Image

from src.error_handler import (
    input_validator, component_error_handler, ErrorDetails, 
    ValidationResult, ErrorSeverity, ErrorCategory
)
from src.enhanced_logger import enhanced_logger, LogCategory, RequestLoggingContext
from src.health_monitor import health_monitor, HealthStatus

logger = logging.getLogger(__name__)


@dataclass
class ProcessingOptions:
    """Options for processing with fallback strategies."""
    enable_web_retrieval: bool = True
    enable_image_processing: bool = True
    enable_context_retrieval: bool = True
    enable_advanced_generation: bool = True
    max_retries: int = 3
    timeout_seconds: int = 30
    fallback_to_cached: bool = True
    fallback_to_simple_response: bool = True


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    is_valid: bool
    text_validation: ValidationResult
    image_validation: ValidationResult
    processing_options: ProcessingOptions
    warnings: List[str]
    errors: List[ErrorDetails]
    recommendations: List[str]
    
    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors."""
        return any(error.severity == ErrorSeverity.CRITICAL for error in self.errors)
    
    def get_user_message(self) -> str:
        """Get user-friendly validation message."""
        if not self.is_valid:
            critical_errors = [e for e in self.errors if e.severity == ErrorSeverity.CRITICAL]
            if critical_errors:
                return critical_errors[0].user_message
            else:
                return "There are some issues with your input. Please check the details and try again."
        
        if self.warnings:
            return f"Your input is valid, but note: {'; '.join(self.warnings[:2])}"
        
        return "Your input looks good!"


class ValidationManager:
    """
    Manages comprehensive input validation, error handling, and graceful degradation
    for the multimodal RAG pipeline.
    """
    
    def __init__(self):
        """Initialize validation manager."""
        self.validator = input_validator
        self.error_handler = component_error_handler
        self.logger = enhanced_logger
        
        # Validation statistics
        self.validation_stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'warnings_issued': 0,
            'errors_by_category': {}
        }
    
    def validate_user_input(self, text: str, images: List[Union[str, Image.Image, bytes]] = None,
                           request_id: str = None) -> ValidationReport:
        """
        Perform comprehensive validation of user input.
        
        Args:
            text: User's text query
            images: Optional list of images
            request_id: Optional request ID for tracking
            
        Returns:
            ValidationReport with complete validation results
        """
        if request_id:
            self.logger.set_request_context(request_id)
        
        self.logger.info(
            "Starting input validation",
            component="validation_manager",
            category=LogCategory.PIPELINE,
            metadata={'text_length': len(text) if text else 0, 'image_count': len(images) if images else 0}
        )
        
        try:
            # Update statistics
            self.validation_stats['total_validations'] += 1
            
            # Validate text input
            text_validation = self.validator.validate_text_query(text)
            
            # Validate images
            image_validation = ValidationResult(True, [], [])
            if images:
                for i, image in enumerate(images):
                    img_result = self.validator.validate_image_input(image)
                    if not img_result.is_valid:
                        image_validation.is_valid = False
                        image_validation.errors.extend(img_result.errors)
                    image_validation.warnings.extend(img_result.warnings)
            
            # Determine processing options based on validation results
            processing_options = self._determine_processing_options(text_validation, image_validation)
            
            # Collect all errors and warnings
            all_errors = text_validation.errors + image_validation.errors
            all_warnings = text_validation.warnings + image_validation.warnings
            
            # Generate recommendations
            recommendations = self._generate_recommendations(text_validation, image_validation, all_errors)
            
            # Determine overall validity
            is_valid = text_validation.is_valid and image_validation.is_valid
            
            # Create validation report
            report = ValidationReport(
                is_valid=is_valid,
                text_validation=text_validation,
                image_validation=image_validation,
                processing_options=processing_options,
                warnings=all_warnings,
                errors=all_errors,
                recommendations=recommendations
            )
            
            # Update statistics
            if is_valid:
                self.validation_stats['successful_validations'] += 1
            else:
                self.validation_stats['failed_validations'] += 1
            
            if all_warnings:
                self.validation_stats['warnings_issued'] += 1
            
            # Count errors by category
            for error in all_errors:
                category = error.category.value
                self.validation_stats['errors_by_category'][category] = \
                    self.validation_stats['errors_by_category'].get(category, 0) + 1
            
            # Log validation result
            self.logger.info(
                f"Input validation completed: {'valid' if is_valid else 'invalid'}",
                component="validation_manager",
                category=LogCategory.PIPELINE,
                metadata={
                    'is_valid': is_valid,
                    'error_count': len(all_errors),
                    'warning_count': len(all_warnings),
                    'processing_options': processing_options.__dict__
                }
            )
            
            return report
            
        except Exception as e:
            self.logger.error(
                "Input validation failed",
                component="validation_manager",
                category=LogCategory.ERROR_HANDLING,
                error=e
            )
            
            # Return error report
            error_details = ErrorDetails(
                error_id="VAL_SYSTEM_ERROR",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message="Validation system error",
                user_message="An error occurred while validating your input. Please try again.",
                suggestions=["Try rephrasing your query", "Contact support if the problem persists"],
                technical_details=str(e),
                timestamp=datetime.now().isoformat(),
                component="validation_manager"
            )
            
            return ValidationReport(
                is_valid=False,
                text_validation=ValidationResult(False, [error_details], []),
                image_validation=ValidationResult(False, [], []),
                processing_options=ProcessingOptions(),
                warnings=[],
                errors=[error_details],
                recommendations=["Contact system administrator"]
            )
    
    def handle_processing_error(self, component: str, error: Exception, 
                              context: Dict[str, Any] = None) -> Tuple[ErrorDetails, Dict[str, Any]]:
        """
        Handle processing error with graceful degradation.
        
        Args:
            component: Name of the component that failed
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            Tuple of (error_details, fallback_strategy)
        """
        self.logger.error(
            f"Processing error in {component}",
            component=component,
            category=LogCategory.ERROR_HANDLING,
            error=error,
            metadata=context
        )
        
        # Handle the error and get details
        error_details = self.error_handler.handle_component_error(component, error, context)
        
        # Determine fallback strategy
        fallback_strategy = {}
        if component in self.error_handler.fallback_strategies:
            fallback_strategy = self.error_handler.fallback_strategies[component](context or {})
            
            self.logger.info(
                f"Applying fallback strategy for {component}",
                component="validation_manager",
                category=LogCategory.ERROR_HANDLING,
                metadata={'strategy': fallback_strategy}
            )
        
        return error_details, fallback_strategy
    
    def check_system_readiness(self) -> Tuple[bool, List[str], List[str]]:
        """
        Check if the system is ready to process requests.
        
        Returns:
            Tuple of (is_ready, warnings, critical_issues)
        """
        self.logger.debug(
            "Checking system readiness",
            component="validation_manager",
            category=LogCategory.SYSTEM
        )
        
        warnings = []
        critical_issues = []
        
        try:
            # Get current health status
            health = health_monitor.get_current_health()
            
            if health is None:
                # No health data available, perform basic checks
                warnings.append("Health monitoring data not available")
                return True, warnings, critical_issues
            
            # Check overall system health
            if health.overall_status == HealthStatus.CRITICAL:
                critical_issues.append("System is in critical state")
                critical_issues.extend(health.alerts)
                return False, warnings, critical_issues
            
            elif health.overall_status == HealthStatus.DEGRADED:
                warnings.append("System performance is degraded")
                warnings.extend(health.alerts)
            
            elif health.overall_status == HealthStatus.WARNING:
                warnings.extend(health.alerts)
            
            # Check individual components
            for name, component in health.components.items():
                if component.status == HealthStatus.CRITICAL:
                    critical_issues.append(f"{name} component is not functioning")
                elif component.status == HealthStatus.DEGRADED:
                    warnings.append(f"{name} component has performance issues")
            
            # Check resource usage
            resource_health = health.resource_usage.get("health", {})
            if resource_health.get("memory_pressure", False):
                warnings.append("High memory usage detected")
            if resource_health.get("disk_pressure", False):
                warnings.append("High disk usage detected")
            
            is_ready = len(critical_issues) == 0
            
            self.logger.info(
                f"System readiness check: {'ready' if is_ready else 'not ready'}",
                component="validation_manager",
                category=LogCategory.SYSTEM,
                metadata={
                    'is_ready': is_ready,
                    'warnings_count': len(warnings),
                    'critical_issues_count': len(critical_issues)
                }
            )
            
            return is_ready, warnings, critical_issues
            
        except Exception as e:
            self.logger.error(
                "System readiness check failed",
                component="validation_manager",
                category=LogCategory.ERROR_HANDLING,
                error=e
            )
            
            critical_issues.append("Unable to determine system status")
            return False, warnings, critical_issues
    
    def _determine_processing_options(self, text_validation: ValidationResult, 
                                    image_validation: ValidationResult) -> ProcessingOptions:
        """Determine processing options based on validation results."""
        options = ProcessingOptions()
        
        # Disable image processing if image validation failed
        if not image_validation.is_valid:
            options.enable_image_processing = False
        
        # Check for specific error conditions that affect processing
        all_errors = text_validation.errors + image_validation.errors
        
        for error in all_errors:
            if error.category == ErrorCategory.NETWORK:
                options.enable_web_retrieval = False
                options.fallback_to_cached = True
            
            elif error.category == ErrorCategory.RESOURCE:
                options.max_retries = 1
                options.timeout_seconds = 15
                options.enable_advanced_generation = False
            
            elif error.category == ErrorCategory.EXTERNAL_API:
                options.fallback_to_simple_response = True
            
            elif error.severity == ErrorSeverity.CRITICAL:
                # For critical errors, use minimal processing
                options.enable_web_retrieval = False
                options.enable_image_processing = False
                options.enable_context_retrieval = False
                options.fallback_to_simple_response = True
        
        return options
    
    def _generate_recommendations(self, text_validation: ValidationResult,
                                image_validation: ValidationResult,
                                errors: List[ErrorDetails]) -> List[str]:
        """Generate recommendations based on validation results."""
        recommendations = []
        
        # Text-specific recommendations
        if not text_validation.is_valid:
            recommendations.extend([
                "Provide a clear, descriptive question or search term",
                "Avoid special characters and formatting in your query"
            ])
        
        # Image-specific recommendations
        if not image_validation.is_valid:
            recommendations.extend([
                "Use supported image formats (JPEG, PNG, WebP, GIF)",
                "Ensure images are not corrupted and are reasonably sized"
            ])
        
        # Error-specific recommendations
        error_categories = {error.category for error in errors}
        
        if ErrorCategory.NETWORK in error_categories:
            recommendations.append("Check your internet connection and try again")
        
        if ErrorCategory.RESOURCE in error_categories:
            recommendations.append("Try with a simpler query or smaller images")
        
        if ErrorCategory.EXTERNAL_API in error_categories:
            recommendations.append("The service may be temporarily unavailable - try again later")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics for monitoring."""
        stats = self.validation_stats.copy()
        
        # Calculate success rate
        total = stats['total_validations']
        if total > 0:
            stats['success_rate'] = stats['successful_validations'] / total
            stats['failure_rate'] = stats['failed_validations'] / total
        else:
            stats['success_rate'] = 0.0
            stats['failure_rate'] = 0.0
        
        return stats
    
    def reset_statistics(self):
        """Reset validation statistics."""
        self.validation_stats = {
            'total_validations': 0,
            'successful_validations': 0,
            'failed_validations': 0,
            'warnings_issued': 0,
            'errors_by_category': {}
        }
        
        self.logger.info(
            "Validation statistics reset",
            component="validation_manager",
            category=LogCategory.SYSTEM
        )


# Global validation manager instance
validation_manager = ValidationManager()


# Decorator for automatic validation and error handling
def validate_and_handle_errors(component: str):
    """Decorator to add automatic validation and error handling to functions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_details, fallback_strategy = validation_manager.handle_processing_error(
                    component, e, {'function': func.__name__, 'args': len(args), 'kwargs': len(kwargs)}
                )
                
                # If there's a fallback strategy, you might want to apply it here
                # For now, we'll re-raise the exception with additional context
                enhanced_logger.error(
                    f"Function {func.__name__} failed in {component}",
                    component=component,
                    category=LogCategory.ERROR_HANDLING,
                    error=e,
                    metadata={'error_details': error_details.to_dict(), 'fallback_strategy': fallback_strategy}
                )
                
                raise
        
        return wrapper
    return decorator
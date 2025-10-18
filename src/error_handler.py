"""
Comprehensive Error Handling and Validation System for the multimodal RAG pipeline.
Provides graceful degradation, input validation, and user-friendly error messages.
"""

import logging
import traceback
import re
from typing import Dict, Any, List, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from PIL import Image
import requests
from pathlib import Path

from config.settings import settings

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    NETWORK = "network"
    PROCESSING = "processing"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    EXTERNAL_API = "external_api"
    SYSTEM = "system"


@dataclass
class ErrorDetails:
    """Detailed error information."""
    error_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    user_message: str
    suggestions: List[str]
    technical_details: str
    timestamp: str
    component: str
    recoverable: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/API responses."""
        return {
            "error_id": self.error_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "user_message": self.user_message,
            "suggestions": self.suggestions,
            "technical_details": self.technical_details,
            "timestamp": self.timestamp,
            "component": self.component,
            "recoverable": self.recoverable
        }


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    errors: List[ErrorDetails]
    warnings: List[str]
    sanitized_input: Any = None


class InputValidator:
    """Validates user inputs with comprehensive error reporting."""
    
    def __init__(self):
        self.max_text_length = settings.MAX_TEXT_LENGTH
        self.supported_image_formats = settings.SUPPORTED_IMAGE_FORMATS
        self.max_image_size = settings.MAX_IMAGE_SIZE
        
        # Patterns for detecting potentially problematic input
        self.suspicious_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',  # JavaScript URLs
            r'data:.*base64',  # Base64 data URLs (potential for large payloads)
            r'file://',  # File URLs
        ]
    
    def validate_text_query(self, text: str) -> ValidationResult:
        """
        Validate text query input.
        
        Args:
            text: User's text query
            
        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        
        try:
            # Check if text is provided
            if not text or not isinstance(text, str):
                errors.append(ErrorDetails(
                    error_id="TEXT_001",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.HIGH,
                    message="No text query provided",
                    user_message="Please provide a text query to search for information.",
                    suggestions=[
                        "Enter a descriptive question or search term",
                        "Try asking about a specific topic you're interested in"
                    ],
                    technical_details="Text input is None or not a string",
                    timestamp=datetime.now().isoformat(),
                    component="InputValidator"
                ))
                return ValidationResult(False, errors, warnings)
            
            # Check text length
            text_stripped = text.strip()
            if len(text_stripped) == 0:
                errors.append(ErrorDetails(
                    error_id="TEXT_002",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.HIGH,
                    message="Empty text query",
                    user_message="Your query appears to be empty. Please provide a meaningful question or search term.",
                    suggestions=[
                        "Enter at least a few words describing what you're looking for",
                        "Be specific about the information you need"
                    ],
                    technical_details="Text input is empty after stripping whitespace",
                    timestamp=datetime.now().isoformat(),
                    component="InputValidator"
                ))
                return ValidationResult(False, errors, warnings)
            
            if len(text_stripped) < 3:
                errors.append(ErrorDetails(
                    error_id="TEXT_003",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.MEDIUM,
                    message="Text query too short",
                    user_message="Your query is very short. Please provide more details for better results.",
                    suggestions=[
                        "Add more descriptive words to your query",
                        "Include context about what you're trying to find"
                    ],
                    technical_details=f"Text length: {len(text_stripped)} characters",
                    timestamp=datetime.now().isoformat(),
                    component="InputValidator"
                ))
            
            if len(text) > self.max_text_length:
                warnings.append(f"Query will be truncated to {self.max_text_length} characters")
                text = text[:self.max_text_length]
            
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    errors.append(ErrorDetails(
                        error_id="TEXT_004",
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.HIGH,
                        message="Potentially unsafe content detected",
                        user_message="Your query contains content that cannot be processed for security reasons.",
                        suggestions=[
                            "Remove any HTML, JavaScript, or special formatting",
                            "Use plain text for your query"
                        ],
                        technical_details=f"Matched suspicious pattern: {pattern}",
                        timestamp=datetime.now().isoformat(),
                        component="InputValidator"
                    ))
            
            # Check for reasonable content
            if len(text_stripped.split()) > 100:
                warnings.append("Very long query detected - consider breaking into smaller, more focused questions")
            
            # Sanitize text
            sanitized_text = self._sanitize_text(text_stripped)
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                sanitized_input=sanitized_text
            )
            
        except Exception as e:
            logger.error(f"Text validation failed: {e}")
            errors.append(ErrorDetails(
                error_id="TEXT_999",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message="Text validation system error",
                user_message="An unexpected error occurred while processing your query. Please try again.",
                suggestions=["Try rephrasing your query", "Contact support if the problem persists"],
                technical_details=str(e),
                timestamp=datetime.now().isoformat(),
                component="InputValidator"
            ))
            
            return ValidationResult(False, errors, warnings)
    
    def validate_image_input(self, image_input: Union[str, Image.Image, bytes, None]) -> ValidationResult:
        """
        Validate image input.
        
        Args:
            image_input: Image file path, PIL Image, bytes, or None
            
        Returns:
            ValidationResult with validation status and details
        """
        errors = []
        warnings = []
        
        try:
            if image_input is None:
                return ValidationResult(True, [], [], None)  # No image is valid
            
            processed_image = None
            
            # Handle different input types
            if isinstance(image_input, str):
                # File path validation
                if not self._validate_image_path(image_input):
                    errors.append(ErrorDetails(
                        error_id="IMG_001",
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.HIGH,
                        message="Invalid image file path",
                        user_message="The image file path is invalid or the file doesn't exist.",
                        suggestions=[
                            "Check that the file path is correct",
                            "Ensure the image file exists and is accessible",
                            "Try using a different image format (JPEG, PNG, WebP, GIF)"
                        ],
                        technical_details=f"File path: {image_input}",
                        timestamp=datetime.now().isoformat(),
                        component="InputValidator"
                    ))
                    return ValidationResult(False, errors, warnings)
                
                try:
                    processed_image = Image.open(image_input)
                except Exception as e:
                    errors.append(ErrorDetails(
                        error_id="IMG_002",
                        category=ErrorCategory.PROCESSING,
                        severity=ErrorSeverity.HIGH,
                        message="Cannot open image file",
                        user_message="The image file cannot be opened. It may be corrupted or in an unsupported format.",
                        suggestions=[
                            "Try a different image file",
                            "Ensure the image is in a supported format (JPEG, PNG, WebP, GIF)",
                            "Check if the file is corrupted"
                        ],
                        technical_details=f"PIL Error: {str(e)}",
                        timestamp=datetime.now().isoformat(),
                        component="InputValidator"
                    ))
                    return ValidationResult(False, errors, warnings)
            
            elif isinstance(image_input, bytes):
                # Validate bytes input
                if len(image_input) == 0:
                    errors.append(ErrorDetails(
                        error_id="IMG_003",
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.HIGH,
                        message="Empty image data",
                        user_message="The image data is empty.",
                        suggestions=["Provide valid image data", "Check the image upload process"],
                        technical_details="Image bytes length: 0",
                        timestamp=datetime.now().isoformat(),
                        component="InputValidator"
                    ))
                    return ValidationResult(False, errors, warnings)
                
                if len(image_input) > 10 * 1024 * 1024:  # 10MB limit
                    errors.append(ErrorDetails(
                        error_id="IMG_004",
                        category=ErrorCategory.VALIDATION,
                        severity=ErrorSeverity.MEDIUM,
                        message="Image file too large",
                        user_message="The image file is too large. Please use an image smaller than 10MB.",
                        suggestions=[
                            "Compress the image to reduce file size",
                            "Use a lower resolution image",
                            "Convert to a more efficient format like JPEG"
                        ],
                        technical_details=f"Image size: {len(image_input)} bytes",
                        timestamp=datetime.now().isoformat(),
                        component="InputValidator"
                    ))
                    return ValidationResult(False, errors, warnings)
                
                try:
                    from io import BytesIO
                    processed_image = Image.open(BytesIO(image_input))
                except Exception as e:
                    errors.append(ErrorDetails(
                        error_id="IMG_005",
                        category=ErrorCategory.PROCESSING,
                        severity=ErrorSeverity.HIGH,
                        message="Cannot process image bytes",
                        user_message="The image data cannot be processed. It may be corrupted or in an unsupported format.",
                        suggestions=[
                            "Try uploading the image again",
                            "Use a different image format",
                            "Check if the image file is corrupted"
                        ],
                        technical_details=f"PIL Error: {str(e)}",
                        timestamp=datetime.now().isoformat(),
                        component="InputValidator"
                    ))
                    return ValidationResult(False, errors, warnings)
            
            elif isinstance(image_input, Image.Image):
                processed_image = image_input
            
            else:
                errors.append(ErrorDetails(
                    error_id="IMG_006",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.HIGH,
                    message="Unsupported image input type",
                    user_message="The image input type is not supported.",
                    suggestions=[
                        "Provide image as file path, PIL Image, or bytes",
                        "Check the image upload method"
                    ],
                    technical_details=f"Input type: {type(image_input)}",
                    timestamp=datetime.now().isoformat(),
                    component="InputValidator"
                ))
                return ValidationResult(False, errors, warnings)
            
            # Validate processed image
            if processed_image:
                image_validation = self._validate_image_properties(processed_image)
                errors.extend(image_validation.errors)
                warnings.extend(image_validation.warnings)
                
                if image_validation.is_valid:
                    processed_image = image_validation.sanitized_input
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                sanitized_input=processed_image
            )
            
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            errors.append(ErrorDetails(
                error_id="IMG_999",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message="Image validation system error",
                user_message="An unexpected error occurred while processing your image. Please try again.",
                suggestions=["Try a different image", "Contact support if the problem persists"],
                technical_details=str(e),
                timestamp=datetime.now().isoformat(),
                component="InputValidator"
            ))
            
            return ValidationResult(False, errors, warnings)
    
    def _validate_image_path(self, path: str) -> bool:
        """Validate image file path."""
        try:
            path_obj = Path(path)
            return path_obj.exists() and path_obj.is_file()
        except:
            return False
    
    def _validate_image_properties(self, image: Image.Image) -> ValidationResult:
        """Validate image properties like format, size, etc."""
        errors = []
        warnings = []
        
        try:
            # Check format (only if format is available)
            if image.format and image.format not in self.supported_image_formats:
                errors.append(ErrorDetails(
                    error_id="IMG_007",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.MEDIUM,
                    message="Unsupported image format",
                    user_message=f"The image format '{image.format}' is not supported. Please use JPEG, PNG, WebP, or GIF.",
                    suggestions=[
                        "Convert the image to JPEG or PNG format",
                        "Use an image editor to change the format"
                    ],
                    technical_details=f"Image format: {image.format}",
                    timestamp=datetime.now().isoformat(),
                    component="InputValidator"
                ))
            
            # Check dimensions
            width, height = image.size
            
            if width < 32 or height < 32:
                errors.append(ErrorDetails(
                    error_id="IMG_008",
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.MEDIUM,
                    message="Image too small",
                    user_message="The image is too small to process effectively. Please use an image at least 32x32 pixels.",
                    suggestions=[
                        "Use a higher resolution image",
                        "Ensure the image contains clear, visible content"
                    ],
                    technical_details=f"Image size: {width}x{height}",
                    timestamp=datetime.now().isoformat(),
                    component="InputValidator"
                ))
            
            if width > 4000 or height > 4000:
                warnings.append(f"Large image ({width}x{height}) will be resized for processing")
            
            # Check mode
            if image.mode not in ['RGB', 'RGBA', 'L']:
                warnings.append(f"Image mode '{image.mode}' will be converted to RGB")
                image = image.convert('RGB')
            
            # Sanitize image (resize if needed)
            if width > self.max_image_size[0] or height > self.max_image_size[1]:
                from PIL import ImageOps
                image = ImageOps.fit(image, self.max_image_size, Image.Resampling.LANCZOS)
                warnings.append(f"Image resized to {self.max_image_size[0]}x{self.max_image_size[1]}")
            
            return ValidationResult(
                is_valid=len(errors) == 0,
                errors=errors,
                warnings=warnings,
                sanitized_input=image
            )
            
        except Exception as e:
            logger.error(f"Image property validation failed: {e}")
            errors.append(ErrorDetails(
                error_id="IMG_998",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message="Image property validation error",
                user_message="An error occurred while validating the image properties.",
                suggestions=["Try a different image", "Contact support if the problem persists"],
                technical_details=str(e),
                timestamp=datetime.now().isoformat(),
                component="InputValidator"
            ))
            
            return ValidationResult(False, errors, warnings)
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text input by removing potentially harmful content."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove JavaScript
        text = re.sub(r'javascript:[^;]*;?', '', text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text


class ComponentErrorHandler:
    """Handles errors from individual pipeline components with graceful degradation."""
    
    def __init__(self):
        self.component_status = {}
        self.fallback_strategies = {
            'web_retriever': self._web_retriever_fallback,
            'content_processor': self._content_processor_fallback,
            'vector_db': self._vector_db_fallback,
            'response_generator': self._response_generator_fallback
        }
    
    def handle_component_error(self, component: str, error: Exception, context: Dict[str, Any] = None) -> ErrorDetails:
        """
        Handle error from a specific component and determine fallback strategy.
        
        Args:
            component: Name of the component that failed
            error: The exception that occurred
            context: Additional context about the error
            
        Returns:
            ErrorDetails with error information and recovery suggestions
        """
        try:
            # Update component status
            self.component_status[component] = {
                'status': 'error',
                'last_error': str(error),
                'timestamp': datetime.now().isoformat()
            }
            
            # Determine error category and severity
            category, severity = self._classify_error(error)
            
            # Generate error details
            error_details = ErrorDetails(
                error_id=f"{component.upper()}_ERR_{int(datetime.now().timestamp())}",
                category=category,
                severity=severity,
                message=f"{component} component error: {str(error)}",
                user_message=self._generate_user_message(component, error),
                suggestions=self._generate_suggestions(component, error),
                technical_details=f"Component: {component}, Error: {str(error)}, Context: {context}",
                timestamp=datetime.now().isoformat(),
                component=component,
                recoverable=component in self.fallback_strategies
            )
            
            # Log the error
            logger.error(f"Component error in {component}: {error}")
            logger.debug(f"Error context: {context}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            
            return error_details
            
        except Exception as e:
            logger.error(f"Error handler failed: {e}")
            return ErrorDetails(
                error_id="ERR_HANDLER_FAIL",
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message="Error handling system failure",
                user_message="A critical system error occurred. Please try again later.",
                suggestions=["Contact system administrator"],
                technical_details=str(e),
                timestamp=datetime.now().isoformat(),
                component="ErrorHandler",
                recoverable=False
            )
    
    def _classify_error(self, error: Exception) -> Tuple[ErrorCategory, ErrorSeverity]:
        """Classify error by type to determine category and severity."""
        error_type = type(error).__name__
        error_message = str(error).lower()
        
        # Network-related errors
        if isinstance(error, (requests.RequestException, ConnectionError, TimeoutError)):
            return ErrorCategory.NETWORK, ErrorSeverity.MEDIUM
        
        # Resource-related errors
        if 'memory' in error_message or 'disk' in error_message or isinstance(error, MemoryError):
            return ErrorCategory.RESOURCE, ErrorSeverity.HIGH
        
        # API-related errors
        if 'api' in error_message or 'openai' in error_message or 'rate limit' in error_message:
            return ErrorCategory.EXTERNAL_API, ErrorSeverity.MEDIUM
        
        # Configuration errors
        if 'config' in error_message or isinstance(error, (KeyError, AttributeError)):
            return ErrorCategory.CONFIGURATION, ErrorSeverity.HIGH
        
        # Processing errors
        if isinstance(error, (ValueError, TypeError)):
            return ErrorCategory.PROCESSING, ErrorSeverity.MEDIUM
        
        # Default to system error
        return ErrorCategory.SYSTEM, ErrorSeverity.HIGH
    
    def _generate_user_message(self, component: str, error: Exception) -> str:
        """Generate user-friendly error message."""
        component_messages = {
            'web_retriever': "We're having trouble accessing web content right now.",
            'content_processor': "There was an issue processing the content.",
            'vector_db': "We're experiencing database connectivity issues.",
            'response_generator': "There was a problem generating your response."
        }
        
        base_message = component_messages.get(component, "A system component encountered an error.")
        
        # Add specific context based on error type
        if isinstance(error, (requests.RequestException, ConnectionError)):
            return f"{base_message} This might be due to network connectivity issues."
        elif isinstance(error, TimeoutError):
            return f"{base_message} The operation timed out - please try again."
        elif 'rate limit' in str(error).lower():
            return f"{base_message} We've hit a rate limit - please wait a moment and try again."
        
        return base_message
    
    def _generate_suggestions(self, component: str, error: Exception) -> List[str]:
        """Generate helpful suggestions for error recovery."""
        suggestions = []
        
        # Component-specific suggestions
        if component == 'web_retriever':
            suggestions.extend([
                "Check your internet connection",
                "Try again in a few moments",
                "The system will attempt to use cached information if available"
            ])
        elif component == 'content_processor':
            suggestions.extend([
                "Try with a simpler query",
                "If using images, try a different image format",
                "Reduce the complexity of your request"
            ])
        elif component == 'vector_db':
            suggestions.extend([
                "The system will try to continue without stored context",
                "Try restarting the application if problems persist"
            ])
        elif component == 'response_generator':
            suggestions.extend([
                "Try rephrasing your question",
                "Make your query more specific",
                "Check if the API service is available"
            ])
        
        # Error-type specific suggestions
        if isinstance(error, TimeoutError):
            suggestions.append("Try breaking your request into smaller parts")
        elif 'memory' in str(error).lower():
            suggestions.append("Try with a smaller or simpler request")
        elif 'rate limit' in str(error).lower():
            suggestions.append("Wait a few minutes before trying again")
        
        return suggestions
    
    def _web_retriever_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback strategy for web retriever failures."""
        return {
            'strategy': 'use_cached_only',
            'message': 'Using cached information only',
            'web_retrieval_disabled': True
        }
    
    def _content_processor_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback strategy for content processor failures."""
        return {
            'strategy': 'text_only_mode',
            'message': 'Processing text only, images disabled',
            'image_processing_disabled': True
        }
    
    def _vector_db_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback strategy for vector database failures."""
        return {
            'strategy': 'no_context_retrieval',
            'message': 'Using general knowledge only',
            'context_retrieval_disabled': True
        }
    
    def _response_generator_fallback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback strategy for response generator failures."""
        return {
            'strategy': 'simple_response',
            'message': 'Providing basic response format',
            'advanced_generation_disabled': True
        }
    
    def get_component_status(self) -> Dict[str, Any]:
        """Get status of all components."""
        return self.component_status.copy()


# Global instances
input_validator = InputValidator()
component_error_handler = ComponentErrorHandler()
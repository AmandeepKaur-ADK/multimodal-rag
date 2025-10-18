"""
Enhanced Logging System for the multimodal RAG pipeline.
Provides structured logging, error tracking, and comprehensive debugging support.
"""

import logging
import logging.handlers
import json
import traceback
import sys
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
import threading
import time

from config.settings import settings


class LogLevel(Enum):
    """Custom log levels for the RAG pipeline."""
    TRACE = 5
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogCategory(Enum):
    """Log categories for better organization."""
    SYSTEM = "system"
    PIPELINE = "pipeline"
    WEB_RETRIEVAL = "web_retrieval"
    CONTENT_PROCESSING = "content_processing"
    VECTOR_DB = "vector_db"
    RESPONSE_GENERATION = "response_generation"
    USER_INTERACTION = "user_interaction"
    PERFORMANCE = "performance"
    SECURITY = "security"
    ERROR_HANDLING = "error_handling"


@dataclass
class LogEntry:
    """Structured log entry."""
    timestamp: str
    level: str
    category: str
    component: str
    message: str
    request_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    execution_time_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    stack_trace: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON."""
        # Extract custom fields from record
        log_entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            category=getattr(record, 'category', LogCategory.SYSTEM.value),
            component=getattr(record, 'component', record.name),
            message=record.getMessage(),
            request_id=getattr(record, 'request_id', None),
            user_id=getattr(record, 'user_id', None),
            session_id=getattr(record, 'session_id', None),
            execution_time_ms=getattr(record, 'execution_time_ms', None),
            metadata=getattr(record, 'metadata', None),
            stack_trace=self.formatException(record.exc_info) if record.exc_info else None
        )
        
        return log_entry.to_json()


class PerformanceLogger:
    """Logger for performance metrics and timing."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._timers: Dict[str, float] = {}
        self._lock = threading.Lock()
    
    def start_timer(self, operation_id: str):
        """Start timing an operation."""
        with self._lock:
            self._timers[operation_id] = time.time()
    
    def end_timer(self, operation_id: str, component: str, category: LogCategory = LogCategory.PERFORMANCE) -> float:
        """End timing and log the duration."""
        with self._lock:
            start_time = self._timers.pop(operation_id, None)
            
        if start_time is None:
            self.logger.warning(f"Timer not found for operation: {operation_id}")
            return 0.0
        
        duration_ms = (time.time() - start_time) * 1000
        
        self.logger.info(
            f"Operation completed: {operation_id}",
            extra={
                'category': category.value,
                'component': component,
                'execution_time_ms': duration_ms,
                'metadata': {'operation_id': operation_id}
            }
        )
        
        return duration_ms
    
    def log_performance_metric(self, metric_name: str, value: float, unit: str, 
                             component: str, metadata: Dict[str, Any] = None):
        """Log a performance metric."""
        self.logger.info(
            f"Performance metric: {metric_name} = {value} {unit}",
            extra={
                'category': LogCategory.PERFORMANCE.value,
                'component': component,
                'metadata': {
                    'metric_name': metric_name,
                    'value': value,
                    'unit': unit,
                    **(metadata or {})
                }
            }
        )


class ErrorTracker:
    """Tracks and analyzes error patterns."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.error_counts: Dict[str, int] = {}
        self.error_history: List[Dict[str, Any]] = []
        self.max_history = 1000
        self._lock = threading.Lock()
    
    def log_error(self, error: Exception, component: str, category: LogCategory,
                  request_id: str = None, metadata: Dict[str, Any] = None):
        """Log an error with tracking."""
        error_type = type(error).__name__
        error_message = str(error)
        
        with self._lock:
            # Update error counts
            error_key = f"{component}:{error_type}"
            self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
            
            # Add to history
            error_record = {
                'timestamp': datetime.now().isoformat(),
                'component': component,
                'error_type': error_type,
                'error_message': error_message,
                'request_id': request_id,
                'count': self.error_counts[error_key],
                'metadata': metadata
            }
            
            self.error_history.append(error_record)
            
            # Limit history size
            if len(self.error_history) > self.max_history:
                self.error_history = self.error_history[-self.max_history:]
        
        # Log the error
        self.logger.error(
            f"Error in {component}: {error_message}",
            exc_info=True,
            extra={
                'category': category.value,
                'component': component,
                'request_id': request_id,
                'metadata': {
                    'error_type': error_type,
                    'error_count': self.error_counts[error_key],
                    **(metadata or {})
                }
            }
        )
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period."""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        
        with self._lock:
            recent_errors = [
                error for error in self.error_history
                if datetime.fromisoformat(error['timestamp']).timestamp() > cutoff_time
            ]
            
            # Count by component and type
            component_counts = {}
            type_counts = {}
            
            for error in recent_errors:
                component = error['component']
                error_type = error['error_type']
                
                component_counts[component] = component_counts.get(component, 0) + 1
                type_counts[error_type] = type_counts.get(error_type, 0) + 1
            
            return {
                'total_errors': len(recent_errors),
                'unique_components': len(component_counts),
                'unique_error_types': len(type_counts),
                'errors_by_component': component_counts,
                'errors_by_type': type_counts,
                'recent_errors': recent_errors[-10:],  # Last 10 errors
                'time_period_hours': hours
            }


class EnhancedLogger:
    """
    Enhanced logging system with structured logging, performance tracking,
    and error analysis capabilities.
    """
    
    def __init__(self, name: str = "multimodal_rag"):
        """
        Initialize enhanced logger.
        
        Args:
            name: Logger name
        """
        self.name = name
        self.logger = logging.getLogger(name)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_logging()
        
        # Initialize sub-components
        self.performance = PerformanceLogger(self.logger)
        self.error_tracker = ErrorTracker(self.logger)
        
        # Request context
        self._request_context = threading.local()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        # Set log level
        log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # Create formatters
        json_formatter = StructuredFormatter()
        
        # Console formatter (human-readable)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # File handler with rotation
        log_file = Path(settings.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(json_formatter)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)
        console_handler.setLevel(log_level)
        
        # Error file handler (errors only)
        error_file = log_file.parent / "errors.log"
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3
        )
        error_handler.setFormatter(json_formatter)
        error_handler.setLevel(logging.ERROR)
        
        # Add handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(error_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def set_request_context(self, request_id: str, user_id: str = None, session_id: str = None):
        """Set context for the current request/session."""
        self._request_context.request_id = request_id
        self._request_context.user_id = user_id
        self._request_context.session_id = session_id
    
    def clear_request_context(self):
        """Clear the current request context."""
        for attr in ['request_id', 'user_id', 'session_id']:
            if hasattr(self._request_context, attr):
                delattr(self._request_context, attr)
    
    def _get_extra_fields(self, component: str, category: LogCategory, 
                         metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get extra fields for log record."""
        extra = {
            'component': component,
            'category': category.value
        }
        
        # Add request context if available
        if hasattr(self._request_context, 'request_id'):
            extra['request_id'] = self._request_context.request_id
        if hasattr(self._request_context, 'user_id'):
            extra['user_id'] = self._request_context.user_id
        if hasattr(self._request_context, 'session_id'):
            extra['session_id'] = self._request_context.session_id
        
        # Add metadata
        if metadata:
            extra['metadata'] = metadata
        
        return extra
    
    def trace(self, message: str, component: str, category: LogCategory = LogCategory.SYSTEM,
              metadata: Dict[str, Any] = None):
        """Log trace level message."""
        extra = self._get_extra_fields(component, category, metadata)
        self.logger.log(LogLevel.TRACE.value, message, extra=extra)
    
    def debug(self, message: str, component: str, category: LogCategory = LogCategory.SYSTEM,
              metadata: Dict[str, Any] = None):
        """Log debug level message."""
        extra = self._get_extra_fields(component, category, metadata)
        self.logger.debug(message, extra=extra)
    
    def info(self, message: str, component: str, category: LogCategory = LogCategory.SYSTEM,
             metadata: Dict[str, Any] = None):
        """Log info level message."""
        extra = self._get_extra_fields(component, category, metadata)
        self.logger.info(message, extra=extra)
    
    def warning(self, message: str, component: str, category: LogCategory = LogCategory.SYSTEM,
                metadata: Dict[str, Any] = None):
        """Log warning level message."""
        extra = self._get_extra_fields(component, category, metadata)
        self.logger.warning(message, extra=extra)
    
    def error(self, message: str, component: str, category: LogCategory = LogCategory.ERROR_HANDLING,
              error: Exception = None, metadata: Dict[str, Any] = None):
        """Log error level message."""
        extra = self._get_extra_fields(component, category, metadata)
        
        if error:
            # Track the error
            request_id = getattr(self._request_context, 'request_id', None)
            self.error_tracker.log_error(error, component, category, request_id, metadata)
        else:
            self.logger.error(message, extra=extra)
    
    def critical(self, message: str, component: str, category: LogCategory = LogCategory.SYSTEM,
                 error: Exception = None, metadata: Dict[str, Any] = None):
        """Log critical level message."""
        extra = self._get_extra_fields(component, category, metadata)
        
        if error:
            # Track the error
            request_id = getattr(self._request_context, 'request_id', None)
            self.error_tracker.log_error(error, component, category, request_id, metadata)
        else:
            self.logger.critical(message, extra=extra)
    
    def log_user_action(self, action: str, user_id: str = None, metadata: Dict[str, Any] = None):
        """Log user action for audit trail."""
        self.info(
            f"User action: {action}",
            component="user_interface",
            category=LogCategory.USER_INTERACTION,
            metadata={
                'action': action,
                'user_id': user_id or getattr(self._request_context, 'user_id', 'anonymous'),
                **(metadata or {})
            }
        )
    
    def log_security_event(self, event: str, severity: str = "medium", 
                          metadata: Dict[str, Any] = None):
        """Log security-related event."""
        log_method = self.warning if severity == "medium" else self.error
        
        log_method(
            f"Security event: {event}",
            component="security",
            category=LogCategory.SECURITY,
            metadata={
                'event': event,
                'severity': severity,
                **(metadata or {})
            }
        )
    
    def get_logs_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of logs for the specified time period."""
        error_summary = self.error_tracker.get_error_summary(hours)
        
        return {
            'time_period_hours': hours,
            'error_summary': error_summary,
            'logger_name': self.name,
            'log_level': self.logger.level,
            'handlers_count': len(self.logger.handlers)
        }


# Global enhanced logger instance
enhanced_logger = EnhancedLogger()


# Context manager for request logging
class RequestLoggingContext:
    """Context manager for request-scoped logging."""
    
    def __init__(self, request_id: str, user_id: str = None, session_id: str = None):
        self.request_id = request_id
        self.user_id = user_id
        self.session_id = session_id
    
    def __enter__(self):
        enhanced_logger.set_request_context(self.request_id, self.user_id, self.session_id)
        enhanced_logger.info(
            f"Request started: {self.request_id}",
            component="request_handler",
            category=LogCategory.PIPELINE
        )
        return enhanced_logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            enhanced_logger.error(
                f"Request failed: {self.request_id}",
                component="request_handler",
                category=LogCategory.ERROR_HANDLING,
                error=exc_val
            )
        else:
            enhanced_logger.info(
                f"Request completed: {self.request_id}",
                component="request_handler",
                category=LogCategory.PIPELINE
            )
        
        enhanced_logger.clear_request_context()


# Decorator for automatic function logging
def log_function_call(component: str, category: LogCategory = LogCategory.SYSTEM):
    """Decorator to automatically log function calls with timing."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"
            operation_id = f"{func_name}_{int(time.time() * 1000)}"
            
            enhanced_logger.debug(
                f"Function called: {func_name}",
                component=component,
                category=category,
                metadata={'function': func_name, 'args_count': len(args), 'kwargs_count': len(kwargs)}
            )
            
            enhanced_logger.performance.start_timer(operation_id)
            
            try:
                result = func(*args, **kwargs)
                
                duration = enhanced_logger.performance.end_timer(operation_id, component, category)
                
                enhanced_logger.debug(
                    f"Function completed: {func_name}",
                    component=component,
                    category=category,
                    metadata={'function': func_name, 'duration_ms': duration}
                )
                
                return result
                
            except Exception as e:
                enhanced_logger.error(
                    f"Function failed: {func_name}",
                    component=component,
                    category=LogCategory.ERROR_HANDLING,
                    error=e,
                    metadata={'function': func_name}
                )
                raise
        
        return wrapper
    return decorator
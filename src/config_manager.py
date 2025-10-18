"""
Configuration Manager for the multimodal RAG pipeline.
Provides dynamic configuration management, validation, and administration features.
"""

import json
import os
import time
import threading
from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
from pathlib import Path

from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class RetrievalConfig:
    """Configuration for web retrieval parameters."""
    max_retrieval_time: int = 30
    max_concurrent_requests: int = 5
    request_timeout: int = 10
    min_delay_between_requests: float = 1.0
    max_retries: int = 3
    retry_delay: float = 2.0
    
    def validate(self) -> List[str]:
        """Validate configuration values."""
        errors = []
        if self.max_retrieval_time <= 0:
            errors.append("max_retrieval_time must be positive")
        if self.max_concurrent_requests <= 0:
            errors.append("max_concurrent_requests must be positive")
        if self.request_timeout <= 0:
            errors.append("request_timeout must be positive")
        if self.min_delay_between_requests < 0:
            errors.append("min_delay_between_requests cannot be negative")
        return errors


@dataclass
class DomainConfig:
    """Configuration for domain management."""
    allowed_domains: List[str]
    blocked_domains: List[str]
    auto_block_failed_domains: bool = True
    domain_failure_threshold: int = 3
    
    def is_domain_allowed(self, domain: str) -> bool:
        """Check if a domain is allowed."""
        domain = domain.lower().strip()
        
        # Check blocked domains first
        for blocked in self.blocked_domains:
            if blocked.strip().lower() in domain:
                return False
        
        # Check allowed domains if configured
        if self.allowed_domains:
            for allowed in self.allowed_domains:
                if allowed.strip().lower() in domain:
                    return True
            return False
        
        return True


@dataclass
class ResourceConfig:
    """Configuration for resource management."""
    max_memory_usage_mb: int = 1024
    max_vector_db_size_mb: int = 2048
    cleanup_interval_hours: int = 24
    max_cached_embeddings: int = 10000
    enable_auto_cleanup: bool = True
    
    def validate(self) -> List[str]:
        """Validate configuration values."""
        errors = []
        if self.max_memory_usage_mb <= 0:
            errors.append("max_memory_usage_mb must be positive")
        if self.max_vector_db_size_mb <= 0:
            errors.append("max_vector_db_size_mb must be positive")
        return errors


@dataclass
class PerformanceConfig:
    """Configuration for performance monitoring and auto-adjustment."""
    enable_auto_adjustment: bool = True
    performance_check_interval: int = 300  # seconds
    slow_response_threshold: float = 10.0  # seconds
    failure_rate_threshold: float = 0.2  # 20%
    adjustment_factor: float = 0.8  # Reduce limits by 20% when performance degrades
    
    def validate(self) -> List[str]:
        """Validate configuration values."""
        errors = []
        if self.performance_check_interval <= 0:
            errors.append("performance_check_interval must be positive")
        if self.slow_response_threshold <= 0:
            errors.append("slow_response_threshold must be positive")
        if not 0 <= self.failure_rate_threshold <= 1:
            errors.append("failure_rate_threshold must be between 0 and 1")
        return errors


@dataclass
class SystemConfig:
    """Complete system configuration."""
    retrieval: RetrievalConfig
    domains: DomainConfig
    resources: ResourceConfig
    performance: PerformanceConfig
    last_updated: str
    version: str = "1.0"
    
    def validate(self) -> List[str]:
        """Validate all configuration sections."""
        errors = []
        errors.extend(self.retrieval.validate())
        errors.extend(self.resources.validate())
        errors.extend(self.performance.validate())
        return errors


class ConfigManager:
    """
    Manages system configuration with dynamic updates, validation, and persistence.
    """
    
    def __init__(self, config_file: str = "config/system_config.json"):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        self._config: SystemConfig = None
        self._config_lock = threading.RLock()
        self._change_callbacks: List[Callable[[SystemConfig], None]] = []
        self._domain_failure_counts: Dict[str, int] = {}
        self._performance_history: List[Dict[str, Any]] = []
        
        # Load or create default configuration
        self.load_config()
        
        # Start performance monitoring if enabled
        if self._config.performance.enable_auto_adjustment:
            self._start_performance_monitoring()
    
    def load_config(self) -> SystemConfig:
        """Load configuration from file or create default."""
        with self._config_lock:
            try:
                if self.config_file.exists():
                    with open(self.config_file, 'r') as f:
                        config_data = json.load(f)
                    
                    # Convert to SystemConfig object
                    self._config = self._dict_to_config(config_data)
                    logger.info(f"Loaded configuration from {self.config_file}")
                else:
                    # Create default configuration
                    self._config = self._create_default_config()
                    self.save_config()
                    logger.info("Created default configuration")
                
                # Validate configuration
                errors = self._config.validate()
                if errors:
                    logger.warning(f"Configuration validation errors: {errors}")
                
                return self._config
                
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                self._config = self._create_default_config()
                return self._config
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        with self._config_lock:
            try:
                self._config.last_updated = datetime.now().isoformat()
                
                config_dict = asdict(self._config)
                
                with open(self.config_file, 'w') as f:
                    json.dump(config_dict, f, indent=2)
                
                logger.info(f"Saved configuration to {self.config_file}")
                
                # Notify callbacks
                for callback in self._change_callbacks:
                    try:
                        callback(self._config)
                    except Exception as e:
                        logger.error(f"Configuration callback failed: {e}")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to save configuration: {e}")
                return False
    
    def get_config(self) -> SystemConfig:
        """Get current configuration."""
        with self._config_lock:
            return self._config
    
    def update_retrieval_config(self, **kwargs) -> bool:
        """Update retrieval configuration parameters."""
        with self._config_lock:
            try:
                # Update retrieval config
                for key, value in kwargs.items():
                    if hasattr(self._config.retrieval, key):
                        setattr(self._config.retrieval, key, value)
                    else:
                        logger.warning(f"Unknown retrieval config parameter: {key}")
                
                # Validate
                errors = self._config.retrieval.validate()
                if errors:
                    logger.error(f"Invalid retrieval configuration: {errors}")
                    return False
                
                return self.save_config()
                
            except Exception as e:
                logger.error(f"Failed to update retrieval config: {e}")
                return False
    
    def update_domain_config(self, 
                           allowed_domains: List[str] = None,
                           blocked_domains: List[str] = None,
                           **kwargs) -> bool:
        """Update domain configuration."""
        with self._config_lock:
            try:
                if allowed_domains is not None:
                    self._config.domains.allowed_domains = allowed_domains
                
                if blocked_domains is not None:
                    self._config.domains.blocked_domains = blocked_domains
                
                # Update other domain config parameters
                for key, value in kwargs.items():
                    if hasattr(self._config.domains, key):
                        setattr(self._config.domains, key, value)
                
                return self.save_config()
                
            except Exception as e:
                logger.error(f"Failed to update domain config: {e}")
                return False
    
    def add_blocked_domain(self, domain: str) -> bool:
        """Add a domain to the blocked list."""
        with self._config_lock:
            if domain not in self._config.domains.blocked_domains:
                self._config.domains.blocked_domains.append(domain)
                logger.info(f"Added blocked domain: {domain}")
                return self.save_config()
            return True
    
    def remove_blocked_domain(self, domain: str) -> bool:
        """Remove a domain from the blocked list."""
        with self._config_lock:
            if domain in self._config.domains.blocked_domains:
                self._config.domains.blocked_domains.remove(domain)
                logger.info(f"Removed blocked domain: {domain}")
                return self.save_config()
            return True
    
    def record_domain_failure(self, domain: str):
        """Record a failure for a domain and auto-block if threshold reached."""
        with self._config_lock:
            self._domain_failure_counts[domain] = self._domain_failure_counts.get(domain, 0) + 1
            
            if (self._config.domains.auto_block_failed_domains and 
                self._domain_failure_counts[domain] >= self._config.domains.domain_failure_threshold):
                
                if domain not in self._config.domains.blocked_domains:
                    self.add_blocked_domain(domain)
                    logger.warning(f"Auto-blocked domain due to failures: {domain}")
    
    def update_resource_config(self, **kwargs) -> bool:
        """Update resource configuration parameters."""
        with self._config_lock:
            try:
                for key, value in kwargs.items():
                    if hasattr(self._config.resources, key):
                        setattr(self._config.resources, key, value)
                
                errors = self._config.resources.validate()
                if errors:
                    logger.error(f"Invalid resource configuration: {errors}")
                    return False
                
                return self.save_config()
                
            except Exception as e:
                logger.error(f"Failed to update resource config: {e}")
                return False
    
    def update_performance_config(self, **kwargs) -> bool:
        """Update performance configuration parameters."""
        with self._config_lock:
            try:
                for key, value in kwargs.items():
                    if hasattr(self._config.performance, key):
                        setattr(self._config.performance, key, value)
                
                errors = self._config.performance.validate()
                if errors:
                    logger.error(f"Invalid performance configuration: {errors}")
                    return False
                
                return self.save_config()
                
            except Exception as e:
                logger.error(f"Failed to update performance config: {e}")
                return False
    
    def register_change_callback(self, callback: Callable[[SystemConfig], None]):
        """Register a callback to be called when configuration changes."""
        self._change_callbacks.append(callback)
    
    def record_performance_metrics(self, metrics: Dict[str, Any]):
        """Record performance metrics for monitoring."""
        with self._config_lock:
            metrics['timestamp'] = time.time()
            self._performance_history.append(metrics)
            
            # Keep only recent history
            max_history = 1000
            if len(self._performance_history) > max_history:
                self._performance_history = self._performance_history[-max_history:]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary and recommendations."""
        with self._config_lock:
            if not self._performance_history:
                return {"status": "no_data"}
            
            recent_metrics = self._performance_history[-100:]  # Last 100 records
            
            # Calculate averages
            avg_response_time = sum(m.get('total_time', 0) for m in recent_metrics) / len(recent_metrics)
            failure_rate = sum(1 for m in recent_metrics if not m.get('success', True)) / len(recent_metrics)
            
            # Determine status
            status = "healthy"
            recommendations = []
            
            if avg_response_time > self._config.performance.slow_response_threshold:
                status = "slow"
                recommendations.append("Consider reducing max_concurrent_requests or max_retrieval_time")
            
            if failure_rate > self._config.performance.failure_rate_threshold:
                status = "degraded" if status == "healthy" else "critical"
                recommendations.append("High failure rate detected - check network connectivity and domain configuration")
            
            return {
                "status": status,
                "avg_response_time": avg_response_time,
                "failure_rate": failure_rate,
                "total_requests": len(self._performance_history),
                "recommendations": recommendations,
                "domain_failures": dict(self._domain_failure_counts)
            }
    
    def _create_default_config(self) -> SystemConfig:
        """Create default system configuration."""
        return SystemConfig(
            retrieval=RetrievalConfig(
                max_retrieval_time=settings.MAX_RETRIEVAL_TIME,
                max_concurrent_requests=settings.MAX_CONCURRENT_REQUESTS,
                request_timeout=settings.REQUEST_TIMEOUT
            ),
            domains=DomainConfig(
                allowed_domains=settings.ALLOWED_DOMAINS,
                blocked_domains=settings.BLOCKED_DOMAINS
            ),
            resources=ResourceConfig(),
            performance=PerformanceConfig(),
            last_updated=datetime.now().isoformat()
        )
    
    def _dict_to_config(self, config_dict: Dict[str, Any]) -> SystemConfig:
        """Convert dictionary to SystemConfig object."""
        return SystemConfig(
            retrieval=RetrievalConfig(**config_dict.get('retrieval', {})),
            domains=DomainConfig(**config_dict.get('domains', {})),
            resources=ResourceConfig(**config_dict.get('resources', {})),
            performance=PerformanceConfig(**config_dict.get('performance', {})),
            last_updated=config_dict.get('last_updated', datetime.now().isoformat()),
            version=config_dict.get('version', '1.0')
        )
    
    def _start_performance_monitoring(self):
        """Start background performance monitoring and auto-adjustment."""
        def monitor():
            while True:
                try:
                    time.sleep(self._config.performance.performance_check_interval)
                    
                    summary = self.get_performance_summary()
                    
                    if summary.get('status') in ['slow', 'degraded', 'critical']:
                        self._auto_adjust_performance()
                        
                except Exception as e:
                    logger.error(f"Performance monitoring error: {e}")
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        logger.info("Started performance monitoring thread")
    
    def _auto_adjust_performance(self):
        """Automatically adjust configuration based on performance."""
        with self._config_lock:
            try:
                summary = self.get_performance_summary()
                
                if summary.get('status') in ['slow', 'degraded']:
                    # Reduce concurrent requests and retrieval time
                    factor = self._config.performance.adjustment_factor
                    
                    new_concurrent = max(1, int(self._config.retrieval.max_concurrent_requests * factor))
                    new_retrieval_time = max(10, int(self._config.retrieval.max_retrieval_time * factor))
                    
                    self.update_retrieval_config(
                        max_concurrent_requests=new_concurrent,
                        max_retrieval_time=new_retrieval_time
                    )
                    
                    logger.info(f"Auto-adjusted performance: concurrent={new_concurrent}, retrieval_time={new_retrieval_time}")
                
            except Exception as e:
                logger.error(f"Auto-adjustment failed: {e}")


# Global configuration manager instance
config_manager = ConfigManager()
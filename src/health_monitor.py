"""
System Health Monitoring for the multimodal RAG pipeline.
Provides comprehensive health checks, status reporting, and system diagnostics.
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
import psutil
import requests
from pathlib import Path

from config.settings import settings
from src.config_manager import config_manager
from src.resource_manager import resource_manager

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """System health status levels."""
    HEALTHY = "healthy"
    WARNING = "warning"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass
class ComponentHealth:
    """Health status of an individual component."""
    name: str
    status: HealthStatus
    message: str
    last_check: str
    response_time_ms: Optional[float] = None
    error_count: int = 0
    success_rate: float = 1.0
    details: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['status'] = self.status.value
        return result


@dataclass
class SystemHealth:
    """Overall system health status."""
    overall_status: HealthStatus
    components: Dict[str, ComponentHealth]
    performance_metrics: Dict[str, Any]
    resource_usage: Dict[str, Any]
    alerts: List[str]
    recommendations: List[str]
    last_updated: str
    uptime_seconds: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "overall_status": self.overall_status.value,
            "components": {name: comp.to_dict() for name, comp in self.components.items()},
            "performance_metrics": self.performance_metrics,
            "resource_usage": self.resource_usage,
            "alerts": self.alerts,
            "recommendations": self.recommendations,
            "last_updated": self.last_updated,
            "uptime_seconds": self.uptime_seconds
        }


class HealthChecker:
    """Performs health checks on individual components."""
    
    def __init__(self):
        self.check_timeout = 5.0  # seconds
        
    def check_web_retriever(self) -> ComponentHealth:
        """Check web retriever component health."""
        start_time = time.time()
        
        try:
            # Test basic connectivity
            response = requests.get(
                "https://httpbin.org/status/200", 
                timeout=self.check_timeout
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                status = HealthStatus.HEALTHY if response_time < 2000 else HealthStatus.WARNING
                message = f"Web connectivity OK (response time: {response_time:.0f}ms)"
            else:
                status = HealthStatus.DEGRADED
                message = f"Unexpected response code: {response.status_code}"
            
            return ComponentHealth(
                name="web_retriever",
                status=status,
                message=message,
                last_check=datetime.now().isoformat(),
                response_time_ms=response_time,
                details={
                    "connectivity_test": "passed",
                    "response_code": response.status_code
                }
            )
            
        except requests.exceptions.Timeout:
            return ComponentHealth(
                name="web_retriever",
                status=HealthStatus.DEGRADED,
                message="Network connectivity timeout",
                last_check=datetime.now().isoformat(),
                response_time_ms=self.check_timeout * 1000,
                details={"connectivity_test": "timeout"}
            )
            
        except Exception as e:
            return ComponentHealth(
                name="web_retriever",
                status=HealthStatus.CRITICAL,
                message=f"Network connectivity failed: {str(e)}",
                last_check=datetime.now().isoformat(),
                details={"connectivity_test": "failed", "error": str(e)}
            )
    
    def check_content_processor(self) -> ComponentHealth:
        """Check content processor component health."""
        start_time = time.time()
        
        try:
            # Test text processing
            from src.content_processor import ContentProcessor
            processor = ContentProcessor()
            
            # Simple test
            test_text = "This is a test for content processing health check."
            embedding = processor.generate_text_embedding(test_text)
            
            response_time = (time.time() - start_time) * 1000
            
            if embedding is not None:
                status = HealthStatus.HEALTHY
                message = f"Content processing OK (response time: {response_time:.0f}ms)"
            else:
                status = HealthStatus.DEGRADED
                message = "Content processing returned null result"
            
            return ComponentHealth(
                name="content_processor",
                status=status,
                message=message,
                last_check=datetime.now().isoformat(),
                response_time_ms=response_time,
                details={
                    "text_processing": "passed" if embedding else "failed",
                    "embedding_dimension": len(embedding.vector) if embedding else 0
                }
            )
            
        except Exception as e:
            return ComponentHealth(
                name="content_processor",
                status=HealthStatus.CRITICAL,
                message=f"Content processor failed: {str(e)}",
                last_check=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )
    
    def check_vector_db(self) -> ComponentHealth:
        """Check vector database component health."""
        start_time = time.time()
        
        try:
            from src.vector_db import VectorDB
            
            # Test database connection
            db = VectorDB()
            stats = db.get_collection_stats()
            
            response_time = (time.time() - start_time) * 1000
            
            if "error" not in stats:
                status = HealthStatus.HEALTHY
                message = f"Vector DB OK ({stats.get('total_embeddings', 0)} embeddings)"
            else:
                status = HealthStatus.DEGRADED
                message = f"Vector DB error: {stats['error']}"
            
            return ComponentHealth(
                name="vector_db",
                status=status,
                message=message,
                last_check=datetime.now().isoformat(),
                response_time_ms=response_time,
                details=stats
            )
            
        except Exception as e:
            return ComponentHealth(
                name="vector_db",
                status=HealthStatus.CRITICAL,
                message=f"Vector DB failed: {str(e)}",
                last_check=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )
    
    def check_response_generator(self) -> ComponentHealth:
        """Check response generator component health."""
        start_time = time.time()
        
        try:
            # Check if OpenAI API key is configured
            if not settings.OPENAI_API_KEY:
                return ComponentHealth(
                    name="response_generator",
                    status=HealthStatus.CRITICAL,
                    message="OpenAI API key not configured",
                    last_check=datetime.now().isoformat(),
                    details={"api_key_configured": False}
                )
            
            # Test API connectivity (simple request)
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            
            # Make a minimal API call to test connectivity
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            
            response_time = (time.time() - start_time) * 1000
            
            if response and response.choices:
                status = HealthStatus.HEALTHY
                message = f"Response generator OK (response time: {response_time:.0f}ms)"
            else:
                status = HealthStatus.DEGRADED
                message = "API responded but with unexpected format"
            
            return ComponentHealth(
                name="response_generator",
                status=status,
                message=message,
                last_check=datetime.now().isoformat(),
                response_time_ms=response_time,
                details={
                    "api_key_configured": True,
                    "api_test": "passed"
                }
            )
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "rate limit" in error_msg:
                status = HealthStatus.WARNING
                message = "API rate limit reached"
            elif "api key" in error_msg or "authentication" in error_msg:
                status = HealthStatus.CRITICAL
                message = "API authentication failed"
            else:
                status = HealthStatus.DEGRADED
                message = f"Response generator error: {str(e)}"
            
            return ComponentHealth(
                name="response_generator",
                status=status,
                message=message,
                last_check=datetime.now().isoformat(),
                response_time_ms=(time.time() - start_time) * 1000,
                details={"error": str(e)}
            )


class SystemHealthMonitor:
    """
    Comprehensive system health monitoring with periodic checks,
    alerting, and performance tracking.
    """
    
    def __init__(self, check_interval: int = 300):  # 5 minutes default
        """
        Initialize health monitor.
        
        Args:
            check_interval: Interval between health checks in seconds
        """
        self.check_interval = check_interval
        self.health_checker = HealthChecker()
        self.start_time = time.time()
        
        # Health history for trend analysis
        self.health_history: List[SystemHealth] = []
        self.max_history = 100
        
        # Monitoring state
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Alert callbacks
        self.alert_callbacks: List[Callable[[SystemHealth], None]] = []
        
        # Current health status
        self._current_health: Optional[SystemHealth] = None
        self._health_lock = threading.RLock()
    
    def start_monitoring(self):
        """Start continuous health monitoring."""
        if self.monitoring_active:
            logger.warning("Health monitoring already active")
            return
        
        self.monitoring_active = True
        
        def monitor():
            logger.info("Started health monitoring")
            
            while self.monitoring_active:
                try:
                    # Perform health check
                    health = self.check_system_health()
                    
                    # Store current health
                    with self._health_lock:
                        self._current_health = health
                        self.health_history.append(health)
                        
                        # Limit history size
                        if len(self.health_history) > self.max_history:
                            self.health_history = self.health_history[-self.max_history:]
                    
                    # Trigger alerts if needed
                    self._check_alerts(health)
                    
                    # Log health status
                    logger.info(f"System health: {health.overall_status.value}")
                    
                    if health.alerts:
                        logger.warning(f"Health alerts: {health.alerts}")
                    
                    time.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f"Health monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        self.monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self.monitoring_thread.start()
    
    def stop_monitoring(self):
        """Stop health monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        logger.info("Stopped health monitoring")
    
    def check_system_health(self) -> SystemHealth:
        """
        Perform comprehensive system health check.
        
        Returns:
            SystemHealth object with complete system status
        """
        logger.debug("Performing system health check")
        
        # Check individual components
        components = {}
        
        try:
            components['web_retriever'] = self.health_checker.check_web_retriever()
        except Exception as e:
            logger.error(f"Web retriever health check failed: {e}")
            components['web_retriever'] = ComponentHealth(
                name="web_retriever",
                status=HealthStatus.UNKNOWN,
                message=f"Health check failed: {str(e)}",
                last_check=datetime.now().isoformat()
            )
        
        try:
            components['content_processor'] = self.health_checker.check_content_processor()
        except Exception as e:
            logger.error(f"Content processor health check failed: {e}")
            components['content_processor'] = ComponentHealth(
                name="content_processor",
                status=HealthStatus.UNKNOWN,
                message=f"Health check failed: {str(e)}",
                last_check=datetime.now().isoformat()
            )
        
        try:
            components['vector_db'] = self.health_checker.check_vector_db()
        except Exception as e:
            logger.error(f"Vector DB health check failed: {e}")
            components['vector_db'] = ComponentHealth(
                name="vector_db",
                status=HealthStatus.UNKNOWN,
                message=f"Health check failed: {str(e)}",
                last_check=datetime.now().isoformat()
            )
        
        try:
            components['response_generator'] = self.health_checker.check_response_generator()
        except Exception as e:
            logger.error(f"Response generator health check failed: {e}")
            components['response_generator'] = ComponentHealth(
                name="response_generator",
                status=HealthStatus.UNKNOWN,
                message=f"Health check failed: {str(e)}",
                last_check=datetime.now().isoformat()
            )
        
        # Get performance metrics
        performance_metrics = self._get_performance_metrics()
        
        # Get resource usage
        resource_usage = self._get_resource_usage()
        
        # Determine overall status
        overall_status = self._determine_overall_status(components, resource_usage)
        
        # Generate alerts and recommendations
        alerts, recommendations = self._generate_alerts_and_recommendations(
            components, resource_usage, performance_metrics
        )
        
        # Calculate uptime
        uptime = time.time() - self.start_time
        
        return SystemHealth(
            overall_status=overall_status,
            components=components,
            performance_metrics=performance_metrics,
            resource_usage=resource_usage,
            alerts=alerts,
            recommendations=recommendations,
            last_updated=datetime.now().isoformat(),
            uptime_seconds=uptime
        )
    
    def get_current_health(self) -> Optional[SystemHealth]:
        """Get the most recent health check result."""
        with self._health_lock:
            return self._current_health
    
    def get_health_history(self, hours: int = 24) -> List[SystemHealth]:
        """
        Get health history for the specified time period.
        
        Args:
            hours: Number of hours of history to return
            
        Returns:
            List of SystemHealth objects
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._health_lock:
            filtered_history = []
            for health in self.health_history:
                try:
                    health_time = datetime.fromisoformat(health.last_updated.replace('Z', '+00:00'))
                    if health_time >= cutoff_time:
                        filtered_history.append(health)
                except:
                    # Include if we can't parse the timestamp
                    filtered_history.append(health)
            
            return filtered_history
    
    def register_alert_callback(self, callback: Callable[[SystemHealth], None]):
        """Register a callback to be called when alerts are triggered."""
        self.alert_callbacks.append(callback)
    
    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics from config manager."""
        try:
            return config_manager.get_performance_summary()
        except Exception as e:
            logger.error(f"Failed to get performance metrics: {e}")
            return {"error": str(e)}
    
    def _get_resource_usage(self) -> Dict[str, Any]:
        """Get resource usage from resource manager."""
        try:
            return resource_manager.get_resource_stats()
        except Exception as e:
            logger.error(f"Failed to get resource usage: {e}")
            return {"error": str(e)}
    
    def _determine_overall_status(self, components: Dict[str, ComponentHealth], 
                                resource_usage: Dict[str, Any]) -> HealthStatus:
        """Determine overall system health status."""
        # Count component statuses
        status_counts = {}
        for component in components.values():
            status = component.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Check for critical issues
        if status_counts.get(HealthStatus.CRITICAL, 0) > 0:
            return HealthStatus.CRITICAL
        
        # Check resource pressure
        if resource_usage.get("health", {}).get("memory_pressure", False):
            return HealthStatus.DEGRADED
        
        # Check for degraded components
        if status_counts.get(HealthStatus.DEGRADED, 0) > 1:
            return HealthStatus.DEGRADED
        elif status_counts.get(HealthStatus.DEGRADED, 0) > 0:
            return HealthStatus.WARNING
        
        # Check for warnings
        if status_counts.get(HealthStatus.WARNING, 0) > 0:
            return HealthStatus.WARNING
        
        # All healthy
        return HealthStatus.HEALTHY
    
    def _generate_alerts_and_recommendations(self, components: Dict[str, ComponentHealth],
                                           resource_usage: Dict[str, Any],
                                           performance_metrics: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """Generate alerts and recommendations based on system status."""
        alerts = []
        recommendations = []
        
        # Component alerts
        for name, component in components.items():
            if component.status == HealthStatus.CRITICAL:
                alerts.append(f"CRITICAL: {name} is not functioning - {component.message}")
                recommendations.append(f"Investigate {name} component immediately")
            elif component.status == HealthStatus.DEGRADED:
                alerts.append(f"DEGRADED: {name} performance issues - {component.message}")
                recommendations.append(f"Monitor {name} component closely")
        
        # Resource alerts
        health_info = resource_usage.get("health", {})
        if health_info.get("memory_pressure", False):
            alerts.append("HIGH: Memory usage above threshold")
            recommendations.append("Consider reducing concurrent requests or clearing cache")
        
        if health_info.get("high_cpu", False):
            alerts.append("HIGH: CPU usage above 80%")
            recommendations.append("Monitor system load and consider scaling")
        
        if health_info.get("disk_pressure", False):
            alerts.append("HIGH: Disk usage above threshold")
            recommendations.append("Clean up old data or increase storage capacity")
        
        # Performance alerts
        perf_status = performance_metrics.get("status", "unknown")
        if perf_status == "degraded":
            alerts.append("PERFORMANCE: System response time degraded")
            recommendations.append("Check network connectivity and reduce load")
        elif perf_status == "critical":
            alerts.append("CRITICAL: System performance severely degraded")
            recommendations.append("Immediate intervention required - check all components")
        
        return alerts, recommendations
    
    def _check_alerts(self, health: SystemHealth):
        """Check if alerts should be triggered and call callbacks."""
        if health.alerts:
            for callback in self.alert_callbacks:
                try:
                    callback(health)
                except Exception as e:
                    logger.error(f"Alert callback failed: {e}")


# Global health monitor instance
health_monitor = SystemHealthMonitor()
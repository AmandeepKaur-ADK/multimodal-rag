"""
Resource Manager for the multimodal RAG pipeline.
Handles concurrent request limiting, memory management, and resource monitoring.
"""

import asyncio
import threading
import time
import psutil
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from pathlib import Path

from src.config_manager import config_manager

logger = logging.getLogger(__name__)


@dataclass
class ResourceUsage:
    """Current resource usage statistics."""
    memory_usage_mb: float
    cpu_usage_percent: float
    disk_usage_mb: float
    active_requests: int
    total_requests: int
    timestamp: str


@dataclass
class RequestContext:
    """Context for tracking individual requests."""
    request_id: str
    start_time: float
    request_type: str
    status: str = "active"
    memory_start: float = 0.0


class ConcurrencyLimiter:
    """Manages concurrent request limits with semaphore-based control."""
    
    def __init__(self, max_concurrent: int = 5):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.sync_semaphore = threading.Semaphore(max_concurrent)
        self.active_requests: Dict[str, RequestContext] = {}
        self.request_lock = threading.Lock()
        
    def update_limit(self, new_limit: int):
        """Update the concurrent request limit."""
        if new_limit != self.max_concurrent:
            self.max_concurrent = new_limit
            # Note: asyncio.Semaphore doesn't support dynamic limit changes
            # We'll need to recreate the semaphore
            self.semaphore = asyncio.Semaphore(new_limit)
            self.sync_semaphore = threading.Semaphore(new_limit)
            logger.info(f"Updated concurrent request limit to {new_limit}")
    
    async def acquire_async(self, request_id: str, request_type: str = "unknown") -> RequestContext:
        """Acquire a slot for async request."""
        await self.semaphore.acquire()
        
        context = RequestContext(
            request_id=request_id,
            start_time=time.time(),
            request_type=request_type,
            memory_start=psutil.Process().memory_info().rss / 1024 / 1024
        )
        
        with self.request_lock:
            self.active_requests[request_id] = context
        
        logger.debug(f"Acquired async slot for request {request_id}")
        return context
    
    def acquire_sync(self, request_id: str, request_type: str = "unknown") -> RequestContext:
        """Acquire a slot for synchronous request."""
        self.sync_semaphore.acquire()
        
        context = RequestContext(
            request_id=request_id,
            start_time=time.time(),
            request_type=request_type,
            memory_start=psutil.Process().memory_info().rss / 1024 / 1024
        )
        
        with self.request_lock:
            self.active_requests[request_id] = context
        
        logger.debug(f"Acquired sync slot for request {request_id}")
        return context
    
    def release_async(self, request_id: str):
        """Release an async request slot."""
        with self.request_lock:
            if request_id in self.active_requests:
                context = self.active_requests[request_id]
                context.status = "completed"
                del self.active_requests[request_id]
        
        self.semaphore.release()
        logger.debug(f"Released async slot for request {request_id}")
    
    def release_sync(self, request_id: str):
        """Release a synchronous request slot."""
        with self.request_lock:
            if request_id in self.active_requests:
                context = self.active_requests[request_id]
                context.status = "completed"
                del self.active_requests[request_id]
        
        self.sync_semaphore.release()
        logger.debug(f"Released sync slot for request {request_id}")
    
    def get_active_requests(self) -> List[RequestContext]:
        """Get list of currently active requests."""
        with self.request_lock:
            return list(self.active_requests.values())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get concurrency statistics."""
        with self.request_lock:
            active_count = len(self.active_requests)
            request_types = {}
            
            for context in self.active_requests.values():
                request_types[context.request_type] = request_types.get(context.request_type, 0) + 1
            
            return {
                "max_concurrent": self.max_concurrent,
                "active_requests": active_count,
                "available_slots": self.max_concurrent - active_count,
                "request_types": request_types
            }


class MemoryManager:
    """Manages memory usage and cleanup."""
    
    def __init__(self):
        self.cleanup_callbacks: List[callable] = []
        self.memory_threshold_mb = 1024  # Default 1GB
        self.last_cleanup = time.time()
        self.cleanup_interval = 3600  # 1 hour
        
    def register_cleanup_callback(self, callback: callable):
        """Register a callback for memory cleanup."""
        self.cleanup_callbacks.append(callback)
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except Exception as e:
            logger.error(f"Failed to get memory usage: {e}")
            return 0.0
    
    def check_memory_pressure(self) -> bool:
        """Check if memory usage is above threshold."""
        current_usage = self.get_memory_usage()
        config = config_manager.get_config()
        threshold = config.resources.max_memory_usage_mb
        
        return current_usage > threshold
    
    def cleanup_if_needed(self, force: bool = False) -> bool:
        """Perform cleanup if memory pressure is high or forced."""
        current_time = time.time()
        
        if not force and current_time - self.last_cleanup < self.cleanup_interval:
            return False
        
        if force or self.check_memory_pressure():
            logger.info("Performing memory cleanup...")
            
            cleaned = False
            for callback in self.cleanup_callbacks:
                try:
                    callback()
                    cleaned = True
                except Exception as e:
                    logger.error(f"Cleanup callback failed: {e}")
            
            self.last_cleanup = current_time
            
            if cleaned:
                logger.info(f"Memory cleanup completed. Current usage: {self.get_memory_usage():.1f} MB")
            
            return cleaned
        
        return False


class ResourceManager:
    """
    Main resource manager that coordinates concurrency limiting,
    memory management, and resource monitoring.
    """
    
    def __init__(self):
        """Initialize resource manager."""
        config = config_manager.get_config()
        
        self.concurrency_limiter = ConcurrencyLimiter(
            max_concurrent=config.retrieval.max_concurrent_requests
        )
        self.memory_manager = MemoryManager()
        
        self.resource_history: List[ResourceUsage] = []
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Register for configuration changes
        config_manager.register_change_callback(self._on_config_change)
        
        # Start resource monitoring
        self.start_monitoring()
    
    def _on_config_change(self, new_config):
        """Handle configuration changes."""
        try:
            # Update concurrency limits
            self.concurrency_limiter.update_limit(
                new_config.retrieval.max_concurrent_requests
            )
            
            # Update memory threshold
            self.memory_manager.memory_threshold_mb = new_config.resources.max_memory_usage_mb
            
            logger.info("Updated resource manager configuration")
            
        except Exception as e:
            logger.error(f"Failed to update resource manager config: {e}")
    
    async def acquire_request_slot_async(self, request_id: str, request_type: str = "web_retrieval") -> RequestContext:
        """Acquire a request slot asynchronously."""
        # Check memory pressure before acquiring
        if self.memory_manager.check_memory_pressure():
            self.memory_manager.cleanup_if_needed(force=True)
        
        return await self.concurrency_limiter.acquire_async(request_id, request_type)
    
    def acquire_request_slot_sync(self, request_id: str, request_type: str = "web_retrieval") -> RequestContext:
        """Acquire a request slot synchronously."""
        # Check memory pressure before acquiring
        if self.memory_manager.check_memory_pressure():
            self.memory_manager.cleanup_if_needed(force=True)
        
        return self.concurrency_limiter.acquire_sync(request_id, request_type)
    
    def release_request_slot_async(self, request_id: str):
        """Release an async request slot."""
        self.concurrency_limiter.release_async(request_id)
    
    def release_request_slot_sync(self, request_id: str):
        """Release a sync request slot."""
        self.concurrency_limiter.release_sync(request_id)
    
    def register_cleanup_callback(self, callback: callable):
        """Register a callback for memory cleanup."""
        self.memory_manager.register_cleanup_callback(callback)
    
    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage statistics."""
        try:
            process = psutil.Process()
            memory_info = process.memory_info()
            
            # Get disk usage for vector database
            config = config_manager.get_config()
            vector_db_path = Path(config.resources.max_vector_db_size_mb if hasattr(config.resources, 'vector_db_path') else './data/vector_db')
            
            disk_usage = 0.0
            if vector_db_path.exists():
                disk_usage = sum(f.stat().st_size for f in vector_db_path.rglob('*') if f.is_file()) / 1024 / 1024
            
            active_requests = len(self.concurrency_limiter.get_active_requests())
            
            return ResourceUsage(
                memory_usage_mb=memory_info.rss / 1024 / 1024,
                cpu_usage_percent=process.cpu_percent(),
                disk_usage_mb=disk_usage,
                active_requests=active_requests,
                total_requests=len(self.resource_history),
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to get resource usage: {e}")
            return ResourceUsage(
                memory_usage_mb=0.0,
                cpu_usage_percent=0.0,
                disk_usage_mb=0.0,
                active_requests=0,
                total_requests=0,
                timestamp=datetime.now().isoformat()
            )
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """Get comprehensive resource statistics."""
        current_usage = self.get_resource_usage()
        concurrency_stats = self.concurrency_limiter.get_stats()
        
        # Calculate averages from recent history
        recent_history = self.resource_history[-100:] if self.resource_history else []
        
        avg_memory = sum(r.memory_usage_mb for r in recent_history) / len(recent_history) if recent_history else 0
        avg_cpu = sum(r.cpu_usage_percent for r in recent_history) / len(recent_history) if recent_history else 0
        
        config = config_manager.get_config()
        
        return {
            "current": {
                "memory_usage_mb": current_usage.memory_usage_mb,
                "cpu_usage_percent": current_usage.cpu_usage_percent,
                "disk_usage_mb": current_usage.disk_usage_mb,
                "active_requests": current_usage.active_requests
            },
            "averages": {
                "memory_usage_mb": avg_memory,
                "cpu_usage_percent": avg_cpu
            },
            "limits": {
                "max_memory_mb": config.resources.max_memory_usage_mb,
                "max_concurrent_requests": config.retrieval.max_concurrent_requests,
                "max_vector_db_mb": config.resources.max_vector_db_size_mb
            },
            "concurrency": concurrency_stats,
            "health": {
                "memory_pressure": current_usage.memory_usage_mb > config.resources.max_memory_usage_mb,
                "high_cpu": current_usage.cpu_usage_percent > 80,
                "disk_pressure": current_usage.disk_usage_mb > config.resources.max_vector_db_size_mb
            }
        }
    
    def start_monitoring(self):
        """Start resource monitoring thread."""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        
        def monitor():
            while self.monitoring_active:
                try:
                    # Record resource usage
                    usage = self.get_resource_usage()
                    self.resource_history.append(usage)
                    
                    # Keep only recent history
                    if len(self.resource_history) > 1000:
                        self.resource_history = self.resource_history[-1000:]
                    
                    # Check for cleanup needs
                    config = config_manager.get_config()
                    if config.resources.enable_auto_cleanup:
                        self.memory_manager.cleanup_if_needed()
                    
                    # Record performance metrics for config manager
                    config_manager.record_performance_metrics({
                        'memory_usage_mb': usage.memory_usage_mb,
                        'cpu_usage_percent': usage.cpu_usage_percent,
                        'active_requests': usage.active_requests
                    })
                    
                    time.sleep(30)  # Monitor every 30 seconds
                    
                except Exception as e:
                    logger.error(f"Resource monitoring error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        self.monitoring_thread = threading.Thread(target=monitor, daemon=True)
        self.monitoring_thread.start()
        logger.info("Started resource monitoring")
    
    def stop_monitoring(self):
        """Stop resource monitoring."""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logger.info("Stopped resource monitoring")
    
    def force_cleanup(self) -> Dict[str, Any]:
        """Force immediate cleanup and return results."""
        logger.info("Forcing resource cleanup...")
        
        before_usage = self.get_resource_usage()
        cleanup_performed = self.memory_manager.cleanup_if_needed(force=True)
        after_usage = self.get_resource_usage()
        
        return {
            "cleanup_performed": cleanup_performed,
            "before": {
                "memory_mb": before_usage.memory_usage_mb,
                "disk_mb": before_usage.disk_usage_mb
            },
            "after": {
                "memory_mb": after_usage.memory_usage_mb,
                "disk_mb": after_usage.disk_usage_mb
            },
            "savings": {
                "memory_mb": before_usage.memory_usage_mb - after_usage.memory_usage_mb,
                "disk_mb": before_usage.disk_usage_mb - after_usage.disk_usage_mb
            }
        }


# Global resource manager instance
resource_manager = ResourceManager()
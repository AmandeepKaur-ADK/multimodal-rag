"""
Admin Interface for the multimodal RAG pipeline.
Provides web-based administration and monitoring capabilities.
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from flask import Flask, request, jsonify, render_template_string
import logging
from pathlib import Path

from src.config_manager import config_manager, SystemConfig
from src.resource_manager import resource_manager

logger = logging.getLogger(__name__)


class AdminInterface:
    """
    Web-based admin interface for system configuration and monitoring.
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080):
        """
        Initialize admin interface.
        
        Args:
            host: Host to bind to
            port: Port to listen on
        """
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.app.secret_key = "rag_admin_interface_secret_key"
        
        # Setup routes
        self._setup_routes()
        
        logger.info(f"Admin interface initialized on {host}:{port}")
    
    def _setup_routes(self):
        """Setup Flask routes for the admin interface."""
        
        @self.app.route('/')
        def dashboard():
            """Main dashboard page."""
            return render_template_string(DASHBOARD_TEMPLATE)
        
        @self.app.route('/admin')
        def admin_dashboard():
            """Admin dashboard page."""
            return render_template_string(DASHBOARD_TEMPLATE)
        
        @self.app.route('/api/status')
        def get_status():
            """Get system status and health."""
            try:
                config = config_manager.get_config()
                resource_stats = resource_manager.get_resource_stats()
                performance_summary = config_manager.get_performance_summary()
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "system_health": self._get_system_health(),
                        "resource_stats": resource_stats,
                        "performance_summary": performance_summary,
                        "config_version": config.version,
                        "last_updated": config.last_updated
                    }
                })
                
            except Exception as e:
                logger.error(f"Failed to get system status: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/config')
        def get_config():
            """Get current system configuration."""
            try:
                config = config_manager.get_config()
                return jsonify({
                    "status": "success",
                    "data": {
                        "retrieval": config.retrieval.__dict__,
                        "domains": config.domains.__dict__,
                        "resources": config.resources.__dict__,
                        "performance": config.performance.__dict__,
                        "last_updated": config.last_updated,
                        "version": config.version
                    }
                })
                
            except Exception as e:
                logger.error(f"Failed to get configuration: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/config/retrieval', methods=['POST'])
        def update_retrieval_config():
            """Update retrieval configuration."""
            try:
                data = request.get_json()
                
                success = config_manager.update_retrieval_config(**data)
                
                if success:
                    return jsonify({
                        "status": "success",
                        "message": "Retrieval configuration updated successfully"
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": "Failed to update retrieval configuration"
                    }), 400
                    
            except Exception as e:
                logger.error(f"Failed to update retrieval config: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/config/domains', methods=['POST'])
        def update_domain_config():
            """Update domain configuration."""
            try:
                data = request.get_json()
                
                success = config_manager.update_domain_config(**data)
                
                if success:
                    return jsonify({
                        "status": "success",
                        "message": "Domain configuration updated successfully"
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": "Failed to update domain configuration"
                    }), 400
                    
            except Exception as e:
                logger.error(f"Failed to update domain config: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/config/resources', methods=['POST'])
        def update_resource_config():
            """Update resource configuration."""
            try:
                data = request.get_json()
                
                success = config_manager.update_resource_config(**data)
                
                if success:
                    return jsonify({
                        "status": "success",
                        "message": "Resource configuration updated successfully"
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": "Failed to update resource configuration"
                    }), 400
                    
            except Exception as e:
                logger.error(f"Failed to update resource config: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/config/performance', methods=['POST'])
        def update_performance_config():
            """Update performance configuration."""
            try:
                data = request.get_json()
                
                success = config_manager.update_performance_config(**data)
                
                if success:
                    return jsonify({
                        "status": "success",
                        "message": "Performance configuration updated successfully"
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": "Failed to update performance configuration"
                    }), 400
                    
            except Exception as e:
                logger.error(f"Failed to update performance config: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/domains/block', methods=['POST'])
        def block_domain():
            """Block a domain."""
            try:
                data = request.get_json()
                domain = data.get('domain')
                
                if not domain:
                    return jsonify({"status": "error", "message": "Domain is required"}), 400
                
                success = config_manager.add_blocked_domain(domain)
                
                if success:
                    return jsonify({
                        "status": "success",
                        "message": f"Domain {domain} blocked successfully"
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": "Failed to block domain"
                    }), 400
                    
            except Exception as e:
                logger.error(f"Failed to block domain: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/domains/unblock', methods=['POST'])
        def unblock_domain():
            """Unblock a domain."""
            try:
                data = request.get_json()
                domain = data.get('domain')
                
                if not domain:
                    return jsonify({"status": "error", "message": "Domain is required"}), 400
                
                success = config_manager.remove_blocked_domain(domain)
                
                if success:
                    return jsonify({
                        "status": "success",
                        "message": f"Domain {domain} unblocked successfully"
                    })
                else:
                    return jsonify({
                        "status": "error",
                        "message": "Failed to unblock domain"
                    }), 400
                    
            except Exception as e:
                logger.error(f"Failed to unblock domain: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/resources/cleanup', methods=['POST'])
        def force_cleanup():
            """Force resource cleanup."""
            try:
                cleanup_results = resource_manager.force_cleanup()
                
                return jsonify({
                    "status": "success",
                    "message": "Resource cleanup completed",
                    "data": cleanup_results
                })
                
            except Exception as e:
                logger.error(f"Failed to force cleanup: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/monitoring/performance')
        def get_performance_history():
            """Get performance monitoring history."""
            try:
                # Get recent performance data
                performance_summary = config_manager.get_performance_summary()
                resource_stats = resource_manager.get_resource_stats()
                
                return jsonify({
                    "status": "success",
                    "data": {
                        "performance_summary": performance_summary,
                        "resource_stats": resource_stats,
                        "timestamp": datetime.now().isoformat()
                    }
                })
                
            except Exception as e:
                logger.error(f"Failed to get performance history: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
        
        @self.app.route('/api/system/health')
        def get_system_health():
            """Get detailed system health information."""
            try:
                health_info = self._get_system_health()
                
                return jsonify({
                    "status": "success",
                    "data": health_info
                })
                
            except Exception as e:
                logger.error(f"Failed to get system health: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health information."""
        try:
            config = config_manager.get_config()
            resource_stats = resource_manager.get_resource_stats()
            performance_summary = config_manager.get_performance_summary()
            
            # Determine overall health status
            health_issues = []
            overall_status = "healthy"
            
            # Check resource health
            if resource_stats["health"]["memory_pressure"]:
                health_issues.append("High memory usage")
                overall_status = "warning"
            
            if resource_stats["health"]["high_cpu"]:
                health_issues.append("High CPU usage")
                overall_status = "warning"
            
            if resource_stats["health"]["disk_pressure"]:
                health_issues.append("High disk usage")
                overall_status = "warning"
            
            # Check performance health
            if performance_summary.get("status") in ["degraded", "critical"]:
                health_issues.append(f"Performance {performance_summary.get('status')}")
                overall_status = "critical" if performance_summary.get("status") == "critical" else "warning"
            
            # Check configuration validation
            config_errors = config.validate()
            if config_errors:
                health_issues.extend(config_errors)
                overall_status = "critical"
            
            return {
                "overall_status": overall_status,
                "health_issues": health_issues,
                "components": {
                    "configuration": {
                        "status": "healthy" if not config_errors else "error",
                        "errors": config_errors
                    },
                    "resources": {
                        "status": "healthy" if not any(resource_stats["health"].values()) else "warning",
                        "details": resource_stats["health"]
                    },
                    "performance": {
                        "status": performance_summary.get("status", "unknown"),
                        "details": performance_summary
                    }
                },
                "uptime": time.time(),  # Simplified uptime
                "last_check": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                "overall_status": "error",
                "health_issues": [f"Health check failed: {str(e)}"],
                "components": {},
                "last_check": datetime.now().isoformat()
            }
    
    def run(self, debug: bool = False):
        """Run the admin interface server."""
        try:
            logger.info(f"Starting admin interface on http://{self.host}:{self.port}")
            self.app.run(host=self.host, port=self.port, debug=debug)
        except Exception as e:
            logger.error(f"Failed to start admin interface: {e}")
            raise


# HTML template for the dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>RAG Pipeline Admin</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
        .card { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .status-healthy { color: #27ae60; }
        .status-warning { color: #f39c12; }
        .status-critical { color: #e74c3c; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .form-group { margin-bottom: 15px; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-group input, .form-group select { width: 100%; padding: 8px; border: 1px solid #ddd; border-radius: 4px; }
        .btn { background: #3498db; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        .btn:hover { background: #2980b9; }
        .btn-danger { background: #e74c3c; }
        .btn-danger:hover { background: #c0392b; }
        .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; }
        .metric { text-align: center; padding: 10px; background: #ecf0f1; border-radius: 4px; }
        .metric-value { font-size: 24px; font-weight: bold; color: #2c3e50; }
        .metric-label { font-size: 12px; color: #7f8c8d; }
        #status { margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>RAG Pipeline Administration</h1>
            <p>System Configuration and Monitoring</p>
        </div>
        
        <div id="status" class="card">
            <h2>System Status</h2>
            <div id="system-health">Loading...</div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>Resource Monitoring</h3>
                <div id="resource-metrics" class="metrics">
                    <div class="metric">
                        <div class="metric-value" id="memory-usage">--</div>
                        <div class="metric-label">Memory (MB)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="cpu-usage">--</div>
                        <div class="metric-label">CPU (%)</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="active-requests">--</div>
                        <div class="metric-label">Active Requests</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value" id="disk-usage">--</div>
                        <div class="metric-label">Disk (MB)</div>
                    </div>
                </div>
                <button class="btn btn-danger" onclick="forceCleanup()">Force Cleanup</button>
            </div>
            
            <div class="card">
                <h3>Retrieval Configuration</h3>
                <form id="retrieval-form">
                    <div class="form-group">
                        <label>Max Retrieval Time (seconds)</label>
                        <input type="number" id="max-retrieval-time" min="1" max="300">
                    </div>
                    <div class="form-group">
                        <label>Max Concurrent Requests</label>
                        <input type="number" id="max-concurrent-requests" min="1" max="20">
                    </div>
                    <div class="form-group">
                        <label>Request Timeout (seconds)</label>
                        <input type="number" id="request-timeout" min="1" max="60">
                    </div>
                    <button type="submit" class="btn">Update Retrieval Config</button>
                </form>
            </div>
            
            <div class="card">
                <h3>Domain Management</h3>
                <div class="form-group">
                    <label>Blocked Domains</label>
                    <div id="blocked-domains"></div>
                </div>
                <div class="form-group">
                    <label>Add Blocked Domain</label>
                    <input type="text" id="new-blocked-domain" placeholder="example.com">
                    <button class="btn" onclick="blockDomain()">Block Domain</button>
                </div>
            </div>
        </div>
    </div>

    <script>
        // Auto-refresh data every 30 seconds
        setInterval(loadData, 30000);
        loadData();
        
        async function loadData() {
            try {
                const [statusResponse, configResponse] = await Promise.all([
                    fetch('/api/status'),
                    fetch('/api/config')
                ]);
                
                const statusData = await statusResponse.json();
                const configData = await configResponse.json();
                
                updateSystemHealth(statusData.data.system_health);
                updateResourceMetrics(statusData.data.resource_stats);
                updateConfigForm(configData.data);
                
            } catch (error) {
                console.error('Failed to load data:', error);
            }
        }
        
        function updateSystemHealth(health) {
            const statusDiv = document.getElementById('system-health');
            const statusClass = `status-${health.overall_status}`;
            
            statusDiv.innerHTML = `
                <div class="${statusClass}">
                    <strong>Status: ${health.overall_status.toUpperCase()}</strong>
                </div>
                ${health.health_issues.length > 0 ? 
                    '<ul>' + health.health_issues.map(issue => `<li>${issue}</li>`).join('') + '</ul>' : 
                    '<p>All systems operational</p>'
                }
            `;
        }
        
        function updateResourceMetrics(stats) {
            document.getElementById('memory-usage').textContent = Math.round(stats.current.memory_usage_mb);
            document.getElementById('cpu-usage').textContent = Math.round(stats.current.cpu_usage_percent);
            document.getElementById('active-requests').textContent = stats.current.active_requests;
            document.getElementById('disk-usage').textContent = Math.round(stats.current.disk_usage_mb);
        }
        
        function updateConfigForm(config) {
            document.getElementById('max-retrieval-time').value = config.retrieval.max_retrieval_time;
            document.getElementById('max-concurrent-requests').value = config.retrieval.max_concurrent_requests;
            document.getElementById('request-timeout').value = config.retrieval.request_timeout;
            
            const blockedDomainsDiv = document.getElementById('blocked-domains');
            blockedDomainsDiv.innerHTML = config.domains.blocked_domains.map(domain => 
                `<span style="background: #e74c3c; color: white; padding: 2px 8px; border-radius: 4px; margin: 2px; display: inline-block;">
                    ${domain} <button onclick="unblockDomain('${domain}')" style="background: none; border: none; color: white; cursor: pointer;">×</button>
                </span>`
            ).join('');
        }
        
        document.getElementById('retrieval-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const data = {
                max_retrieval_time: parseInt(document.getElementById('max-retrieval-time').value),
                max_concurrent_requests: parseInt(document.getElementById('max-concurrent-requests').value),
                request_timeout: parseInt(document.getElementById('request-timeout').value)
            };
            
            try {
                const response = await fetch('/api/config/retrieval', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                alert(result.message);
                
                if (result.status === 'success') {
                    loadData();
                }
            } catch (error) {
                alert('Failed to update configuration: ' + error.message);
            }
        });
        
        async function blockDomain() {
            const domain = document.getElementById('new-blocked-domain').value.trim();
            if (!domain) return;
            
            try {
                const response = await fetch('/api/domains/block', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ domain })
                });
                
                const result = await response.json();
                alert(result.message);
                
                if (result.status === 'success') {
                    document.getElementById('new-blocked-domain').value = '';
                    loadData();
                }
            } catch (error) {
                alert('Failed to block domain: ' + error.message);
            }
        }
        
        async function unblockDomain(domain) {
            try {
                const response = await fetch('/api/domains/unblock', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ domain })
                });
                
                const result = await response.json();
                alert(result.message);
                
                if (result.status === 'success') {
                    loadData();
                }
            } catch (error) {
                alert('Failed to unblock domain: ' + error.message);
            }
        }
        
        async function forceCleanup() {
            try {
                const response = await fetch('/api/resources/cleanup', { method: 'POST' });
                const result = await response.json();
                
                alert(`Cleanup completed. Memory saved: ${Math.round(result.data.savings.memory_mb)} MB`);
                loadData();
            } catch (error) {
                alert('Failed to perform cleanup: ' + error.message);
            }
        }
    </script>
</body>
</html>
"""


# Factory function to create admin interface
def create_admin_interface(host: str = "127.0.0.1", port: int = 8080) -> AdminInterface:
    """
    Create an admin interface instance.
    
    Args:
        host: Host to bind to
        port: Port to listen on
        
    Returns:
        AdminInterface instance
    """
    return AdminInterface(host=host, port=port)
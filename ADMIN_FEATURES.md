# RAG Pipeline Administration Features

This document describes the comprehensive administration and configuration features implemented for the multimodal RAG pipeline.

## Overview

The administration system provides:
- **Dynamic Configuration Management**: Real-time parameter adjustment without restarts
- **Resource Management**: Concurrent request limiting and memory monitoring
- **Performance Monitoring**: Automatic performance tracking and optimization
- **Domain Management**: Whitelist/blacklist functionality with auto-blocking
- **Web Admin Interface**: Browser-based administration dashboard
- **CLI Administration**: Command-line tools for system management

## Components

### 1. Configuration Manager (`src/config_manager.py`)

Manages all system configuration with dynamic updates and validation.

#### Features:
- **Real-time Configuration Updates**: Changes applied immediately without restart
- **Configuration Validation**: Ensures all parameters are valid before applying
- **Persistent Storage**: Configuration saved to JSON file with versioning
- **Change Callbacks**: Notify components when configuration changes
- **Performance Metrics**: Track system performance for auto-adjustment
- **Domain Failure Tracking**: Automatically block failing domains

#### Configuration Sections:
- **Retrieval Config**: Web scraping parameters and timeouts
- **Domain Config**: Whitelist/blacklist management
- **Resource Config**: Memory and disk usage limits
- **Performance Config**: Auto-adjustment settings

#### Usage Example:
```python
from src.config_manager import config_manager

# Update retrieval settings
config_manager.update_retrieval_config(
    max_retrieval_time=45,
    max_concurrent_requests=8
)

# Block a domain
config_manager.add_blocked_domain("spam-site.com")

# Get performance summary
summary = config_manager.get_performance_summary()
```

### 2. Resource Manager (`src/resource_manager.py`)

Handles concurrent request limiting, memory management, and resource monitoring.

#### Features:
- **Concurrency Limiting**: Semaphore-based request slot management
- **Memory Monitoring**: Real-time memory usage tracking
- **Automatic Cleanup**: Memory pressure detection and cleanup
- **Resource Statistics**: Comprehensive resource usage metrics
- **Background Monitoring**: Continuous resource monitoring thread

#### Key Classes:
- **ConcurrencyLimiter**: Manages concurrent request slots
- **MemoryManager**: Handles memory monitoring and cleanup
- **ResourceManager**: Main coordinator for all resource management

#### Usage Example:
```python
from src.resource_manager import resource_manager

# Acquire request slot
context = resource_manager.acquire_request_slot_sync("req_123", "web_retrieval")

try:
    # Perform work
    pass
finally:
    # Always release slot
    resource_manager.release_request_slot_sync("req_123")

# Get resource statistics
stats = resource_manager.get_resource_stats()
```

### 3. Admin Interface (`src/admin_interface.py`)

Web-based administration dashboard with REST API.

#### Features:
- **Real-time Dashboard**: Live system status and metrics
- **Configuration Management**: Update settings through web UI
- **Domain Management**: Block/unblock domains with one click
- **Resource Monitoring**: Visual resource usage displays
- **Performance Charts**: Historical performance data
- **System Health**: Overall system status indicators

#### API Endpoints:
- `GET /api/status` - System status and health
- `GET /api/config` - Current configuration
- `POST /api/config/{section}` - Update configuration section
- `POST /api/domains/block` - Block a domain
- `POST /api/domains/unblock` - Unblock a domain
- `POST /api/resources/cleanup` - Force resource cleanup
- `GET /api/monitoring/performance` - Performance history

#### Starting the Web Interface:
```bash
# Using main.py
python main.py --admin --port 8080

# Using CLI tool
python -m src.admin_cli web --host 127.0.0.1 --port 8080

# Programmatically
from src.admin_interface import create_admin_interface
admin = create_admin_interface(host="127.0.0.1", port=8080)
admin.run()
```

### 4. Admin CLI (`src/admin_cli.py`)

Command-line administration tool for system management.

#### Available Commands:

**System Status:**
```bash
python -m src.admin_cli status                    # Show system status
python -m src.admin_cli status --json            # JSON format output
```

**Configuration Management:**
```bash
python -m src.admin_cli config show              # Show all configuration
python -m src.admin_cli config show --section retrieval  # Show specific section
python -m src.admin_cli config update --section retrieval --key max_retrieval_time --value 45
```

**Domain Management:**
```bash
python -m src.admin_cli domains list             # List all domains
python -m src.admin_cli domains block example.com    # Block a domain
python -m src.admin_cli domains unblock example.com  # Unblock a domain
```

**Resource Management:**
```bash
python -m src.admin_cli resources stats          # Show resource statistics
python -m src.admin_cli resources cleanup        # Force cleanup
```

**Performance Monitoring:**
```bash
python -m src.admin_cli performance summary      # Performance summary
```

**Web Interface:**
```bash
python -m src.admin_cli web                      # Start web interface
python -m src.admin_cli web --port 9000         # Custom port
python -m src.admin_cli web --debug             # Debug mode
```

## Integration with RAG Pipeline

The administration features are fully integrated with the RAG pipeline:

### 1. Configuration Integration
- Pipeline components automatically use current configuration
- Configuration changes are applied immediately via callbacks
- No restart required for most configuration changes

### 2. Resource Management Integration
- Web retriever uses resource manager for concurrent request limiting
- Pipeline registers cleanup callbacks for memory management
- Automatic resource monitoring during pipeline operations

### 3. Performance Monitoring Integration
- Pipeline automatically records performance metrics
- Metrics used for auto-adjustment of configuration parameters
- Health monitoring provides pipeline status information

## Configuration File Structure

The system uses a JSON configuration file (`config/system_config.json`):

```json
{
  "retrieval": {
    "max_retrieval_time": 30,
    "max_concurrent_requests": 5,
    "request_timeout": 10,
    "min_delay_between_requests": 1.0,
    "max_retries": 3,
    "retry_delay": 2.0
  },
  "domains": {
    "allowed_domains": [],
    "blocked_domains": ["spam-site.com"],
    "auto_block_failed_domains": true,
    "domain_failure_threshold": 3
  },
  "resources": {
    "max_memory_usage_mb": 1024,
    "max_vector_db_size_mb": 2048,
    "cleanup_interval_hours": 24,
    "max_cached_embeddings": 10000,
    "enable_auto_cleanup": true
  },
  "performance": {
    "enable_auto_adjustment": true,
    "performance_check_interval": 300,
    "slow_response_threshold": 10.0,
    "failure_rate_threshold": 0.2,
    "adjustment_factor": 0.8
  },
  "last_updated": "2024-01-01T00:00:00",
  "version": "1.0"
}
```

## Auto-Adjustment Features

### Performance-Based Auto-Adjustment
- Monitors response times and failure rates
- Automatically reduces concurrent requests when performance degrades
- Adjusts retrieval timeouts based on network conditions
- Provides recommendations for manual optimization

### Domain Auto-Blocking
- Tracks failures per domain
- Automatically blocks domains that exceed failure threshold
- Prevents wasted resources on unreliable sources
- Manual override available through admin interface

### Memory Management
- Monitors memory usage continuously
- Triggers cleanup when memory pressure detected
- Configurable memory thresholds and cleanup intervals
- Automatic vector database optimization

## Security Considerations

### Access Control
- Admin interface binds to localhost by default
- No authentication implemented (suitable for local development)
- For production: add authentication middleware
- Consider firewall rules for network access

### Configuration Security
- Configuration file should have appropriate file permissions
- Sensitive settings (API keys) remain in environment variables
- Configuration changes are logged for audit trail

## Monitoring and Alerting

### Health Checks
- Overall system health status (healthy/warning/critical)
- Component-level health monitoring
- Resource usage thresholds
- Performance degradation detection

### Metrics Collection
- Response time statistics
- Success/failure rates
- Resource usage trends
- Domain performance tracking

### Alerting (Future Enhancement)
- Email/SMS notifications for critical issues
- Webhook integration for external monitoring systems
- Custom alert thresholds and conditions

## Troubleshooting

### Common Issues

**High Memory Usage:**
```bash
# Check current usage
python -m src.admin_cli resources stats

# Force cleanup
python -m src.admin_cli resources cleanup

# Adjust memory limits
python -m src.admin_cli config update --section resources --key max_memory_usage_mb --value 2048
```

**Slow Performance:**
```bash
# Check performance summary
python -m src.admin_cli performance summary

# Reduce concurrent requests
python -m src.admin_cli config update --section retrieval --key max_concurrent_requests --value 3

# Reduce retrieval timeout
python -m src.admin_cli config update --section retrieval --key max_retrieval_time --value 20
```

**Domain Issues:**
```bash
# List blocked domains
python -m src.admin_cli domains list

# Unblock a domain
python -m src.admin_cli domains unblock problematic-domain.com

# Disable auto-blocking
python -m src.admin_cli config update --section domains --key auto_block_failed_domains --value false
```

## Examples and Demos

### Basic Usage Example
See `examples/admin_example.py` for a comprehensive demonstration of all administration features.

### Validation Script
Run `python validate_admin_features.py` to test basic functionality without external dependencies.

### Integration Example
```python
from src.rag_pipeline import create_rag_pipeline
from src.config_manager import config_manager

# Create pipeline with admin features
pipeline = create_rag_pipeline()

# Update configuration on the fly
config_manager.update_retrieval_config(max_concurrent_requests=10)

# Process queries - pipeline automatically uses new settings
result = pipeline.process_query("What is AI?")

# Monitor performance
health = pipeline.get_pipeline_health()
print(f"Pipeline status: {health['status']}")
```

## Future Enhancements

### Planned Features
- **Authentication System**: User management and role-based access
- **Advanced Monitoring**: Grafana/Prometheus integration
- **Distributed Configuration**: Support for multiple pipeline instances
- **A/B Testing**: Configuration variant testing
- **Backup/Restore**: Configuration and data backup functionality

### API Extensions
- **Webhook Support**: External system notifications
- **Bulk Operations**: Batch configuration updates
- **Export/Import**: Configuration sharing between environments
- **Audit Logging**: Detailed change tracking and history

## Dependencies

The administration features require these additional packages:
- `psutil>=5.9.0` - System resource monitoring
- `flask>=2.3.0` - Web admin interface

Install with:
```bash
pip install psutil flask
```

Or use the updated requirements.txt:
```bash
pip install -r requirements.txt
```

## Conclusion

The administration features provide comprehensive management capabilities for the RAG pipeline, enabling:
- Real-time configuration management without restarts
- Proactive resource monitoring and optimization
- Automated performance tuning and problem detection
- User-friendly interfaces for both web and command-line administration

These features make the RAG pipeline production-ready with enterprise-grade administration capabilities.
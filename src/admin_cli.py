"""
Command-line administration tool for the multimodal RAG pipeline.
Provides CLI access to configuration and monitoring features.
"""

import argparse
import json
import sys
from typing import Dict, Any
import logging

from src.config_manager import config_manager
from src.resource_manager import resource_manager
from src.admin_interface import create_admin_interface

logger = logging.getLogger(__name__)


class AdminCLI:
    """Command-line interface for RAG pipeline administration."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser for CLI commands."""
        parser = argparse.ArgumentParser(
            description="RAG Pipeline Administration Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Status command
        status_parser = subparsers.add_parser('status', help='Show system status')
        status_parser.add_argument('--json', action='store_true', help='Output in JSON format')
        
        # Config commands
        config_parser = subparsers.add_parser('config', help='Configuration management')
        config_subparsers = config_parser.add_subparsers(dest='config_action')
        
        # Config show
        config_show = config_subparsers.add_parser('show', help='Show current configuration')
        config_show.add_argument('--section', choices=['retrieval', 'domains', 'resources', 'performance'], 
                                help='Show specific section only')
        
        # Config update
        config_update = config_subparsers.add_parser('update', help='Update configuration')
        config_update.add_argument('--section', required=True, 
                                  choices=['retrieval', 'domains', 'resources', 'performance'],
                                  help='Configuration section to update')
        config_update.add_argument('--key', required=True, help='Configuration key')
        config_update.add_argument('--value', required=True, help='New value')
        
        # Domain commands
        domain_parser = subparsers.add_parser('domains', help='Domain management')
        domain_subparsers = domain_parser.add_subparsers(dest='domain_action')
        
        # Block domain
        block_domain = domain_subparsers.add_parser('block', help='Block a domain')
        block_domain.add_argument('domain', help='Domain to block')
        
        # Unblock domain
        unblock_domain = domain_subparsers.add_parser('unblock', help='Unblock a domain')
        unblock_domain.add_argument('domain', help='Domain to unblock')
        
        # List domains
        list_domains = domain_subparsers.add_parser('list', help='List blocked/allowed domains')
        
        # Resources commands
        resources_parser = subparsers.add_parser('resources', help='Resource management')
        resources_subparsers = resources_parser.add_subparsers(dest='resource_action')
        
        # Resource stats
        resource_stats = resources_subparsers.add_parser('stats', help='Show resource statistics')
        
        # Force cleanup
        force_cleanup = resources_subparsers.add_parser('cleanup', help='Force resource cleanup')
        
        # Performance commands
        perf_parser = subparsers.add_parser('performance', help='Performance monitoring')
        perf_subparsers = perf_parser.add_subparsers(dest='perf_action')
        
        # Performance summary
        perf_summary = perf_subparsers.add_parser('summary', help='Show performance summary')
        
        # Web interface command
        web_parser = subparsers.add_parser('web', help='Start web admin interface')
        web_parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
        web_parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
        web_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
        
        return parser
    
    def run(self, args=None):
        """Run the CLI with given arguments."""
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return
        
        try:
            if parsed_args.command == 'status':
                self._handle_status(parsed_args)
            elif parsed_args.command == 'config':
                self._handle_config(parsed_args)
            elif parsed_args.command == 'domains':
                self._handle_domains(parsed_args)
            elif parsed_args.command == 'resources':
                self._handle_resources(parsed_args)
            elif parsed_args.command == 'performance':
                self._handle_performance(parsed_args)
            elif parsed_args.command == 'web':
                self._handle_web_interface(parsed_args)
            else:
                print(f"Unknown command: {parsed_args.command}")
                
        except Exception as e:
            print(f"Error: {e}")
            logger.error(f"CLI command failed: {e}")
            sys.exit(1)
    
    def _handle_status(self, args):
        """Handle status command."""
        try:
            config = config_manager.get_config()
            resource_stats = resource_manager.get_resource_stats()
            performance_summary = config_manager.get_performance_summary()
            
            status_data = {
                "system_health": self._get_system_health(),
                "resource_stats": resource_stats,
                "performance_summary": performance_summary,
                "config_version": config.version,
                "last_updated": config.last_updated
            }
            
            if args.json:
                print(json.dumps(status_data, indent=2))
            else:
                self._print_status_human(status_data)
                
        except Exception as e:
            print(f"Failed to get system status: {e}")
    
    def _handle_config(self, args):
        """Handle config commands."""
        if args.config_action == 'show':
            config = config_manager.get_config()
            
            if args.section:
                section_data = getattr(config, args.section).__dict__
                print(json.dumps(section_data, indent=2))
            else:
                config_data = {
                    "retrieval": config.retrieval.__dict__,
                    "domains": config.domains.__dict__,
                    "resources": config.resources.__dict__,
                    "performance": config.performance.__dict__
                }
                print(json.dumps(config_data, indent=2))
                
        elif args.config_action == 'update':
            # Convert value to appropriate type
            value = self._convert_value(args.value)
            
            if args.section == 'retrieval':
                success = config_manager.update_retrieval_config(**{args.key: value})
            elif args.section == 'domains':
                success = config_manager.update_domain_config(**{args.key: value})
            elif args.section == 'resources':
                success = config_manager.update_resource_config(**{args.key: value})
            elif args.section == 'performance':
                success = config_manager.update_performance_config(**{args.key: value})
            else:
                print(f"Unknown section: {args.section}")
                return
            
            if success:
                print(f"Successfully updated {args.section}.{args.key} = {value}")
            else:
                print(f"Failed to update {args.section}.{args.key}")
    
    def _handle_domains(self, args):
        """Handle domain commands."""
        if args.domain_action == 'block':
            success = config_manager.add_blocked_domain(args.domain)
            if success:
                print(f"Successfully blocked domain: {args.domain}")
            else:
                print(f"Failed to block domain: {args.domain}")
                
        elif args.domain_action == 'unblock':
            success = config_manager.remove_blocked_domain(args.domain)
            if success:
                print(f"Successfully unblocked domain: {args.domain}")
            else:
                print(f"Failed to unblock domain: {args.domain}")
                
        elif args.domain_action == 'list':
            config = config_manager.get_config()
            
            print("Blocked domains:")
            for domain in config.domains.blocked_domains:
                print(f"  - {domain}")
            
            print("\\nAllowed domains:")
            if config.domains.allowed_domains:
                for domain in config.domains.allowed_domains:
                    print(f"  - {domain}")
            else:
                print("  (All domains allowed except blocked ones)")
    
    def _handle_resources(self, args):
        """Handle resource commands."""
        if args.resource_action == 'stats':
            stats = resource_manager.get_resource_stats()
            print(json.dumps(stats, indent=2))
            
        elif args.resource_action == 'cleanup':
            print("Performing resource cleanup...")
            cleanup_results = resource_manager.force_cleanup()
            
            print(f"Cleanup completed:")
            print(f"  Memory saved: {cleanup_results['savings']['memory_mb']:.1f} MB")
            print(f"  Disk saved: {cleanup_results['savings']['disk_mb']:.1f} MB")
    
    def _handle_performance(self, args):
        """Handle performance commands."""
        if args.perf_action == 'summary':
            summary = config_manager.get_performance_summary()
            print(json.dumps(summary, indent=2))
    
    def _handle_web_interface(self, args):
        """Handle web interface command."""
        print(f"Starting web admin interface on http://{args.host}:{args.port}")
        print("Press Ctrl+C to stop")
        
        admin_interface = create_admin_interface(host=args.host, port=args.port)
        admin_interface.run(debug=args.debug)
    
    def _get_system_health(self) -> Dict[str, Any]:
        """Get system health information."""
        try:
            config = config_manager.get_config()
            resource_stats = resource_manager.get_resource_stats()
            performance_summary = config_manager.get_performance_summary()
            
            health_issues = []
            overall_status = "healthy"
            
            # Check resource health
            if resource_stats["health"]["memory_pressure"]:
                health_issues.append("High memory usage")
                overall_status = "warning"
            
            if resource_stats["health"]["high_cpu"]:
                health_issues.append("High CPU usage")
                overall_status = "warning"
            
            # Check performance health
            if performance_summary.get("status") in ["degraded", "critical"]:
                health_issues.append(f"Performance {performance_summary.get('status')}")
                overall_status = "critical" if performance_summary.get("status") == "critical" else "warning"
            
            return {
                "overall_status": overall_status,
                "health_issues": health_issues,
                "components": {
                    "configuration": "healthy",
                    "resources": "healthy" if not any(resource_stats["health"].values()) else "warning",
                    "performance": performance_summary.get("status", "unknown")
                }
            }
            
        except Exception as e:
            return {
                "overall_status": "error",
                "health_issues": [f"Health check failed: {str(e)}"],
                "components": {}
            }
    
    def _print_status_human(self, status_data):
        """Print status in human-readable format."""
        health = status_data["system_health"]
        
        print("=== RAG Pipeline System Status ===")
        print(f"Overall Status: {health['overall_status'].upper()}")
        
        if health["health_issues"]:
            print("\\nHealth Issues:")
            for issue in health["health_issues"]:
                print(f"  - {issue}")
        
        print("\\nComponent Status:")
        for component, status in health["components"].items():
            print(f"  {component}: {status}")
        
        # Resource stats
        resources = status_data["resource_stats"]["current"]
        print(f"\\nResource Usage:")
        print(f"  Memory: {resources['memory_usage_mb']:.1f} MB")
        print(f"  CPU: {resources['cpu_usage_percent']:.1f}%")
        print(f"  Active Requests: {resources['active_requests']}")
        print(f"  Disk Usage: {resources['disk_usage_mb']:.1f} MB")
        
        # Performance summary
        perf = status_data["performance_summary"]
        if perf.get("status") != "no_data":
            print(f"\\nPerformance:")
            print(f"  Status: {perf.get('status', 'unknown')}")
            print(f"  Avg Response Time: {perf.get('avg_response_time', 0):.2f}s")
            print(f"  Failure Rate: {perf.get('failure_rate', 0):.1%}")
    
    def _convert_value(self, value_str: str):
        """Convert string value to appropriate type."""
        # Try to convert to int
        try:
            return int(value_str)
        except ValueError:
            pass
        
        # Try to convert to float
        try:
            return float(value_str)
        except ValueError:
            pass
        
        # Try to convert to boolean
        if value_str.lower() in ('true', 'false'):
            return value_str.lower() == 'true'
        
        # Try to convert to list (comma-separated)
        if ',' in value_str:
            return [item.strip() for item in value_str.split(',')]
        
        # Return as string
        return value_str


def main():
    """Main entry point for CLI."""
    cli = AdminCLI()
    cli.run()


if __name__ == '__main__':
    main()
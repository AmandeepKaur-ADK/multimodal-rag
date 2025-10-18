"""
Robots.txt checker utility for respecting website crawling policies.
"""
import requests
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class RobotsChecker:
    """Utility to check robots.txt compliance."""
    
    def __init__(self):
        self.robots_cache: Dict[str, Optional[RobotFileParser]] = {}
        self.user_agent = "RAGBot"
    
    def can_fetch(self, url: str) -> bool:
        """
        Check if we can fetch the given URL according to robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            True if allowed to fetch, False otherwise
        """
        try:
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Get robots.txt for this domain
            robots_parser = self._get_robots_parser(domain)
            
            if robots_parser is None:
                # If we can't get robots.txt, assume it's allowed
                return True
            
            # Check if we can fetch this URL
            return robots_parser.can_fetch(self.user_agent, url)
            
        except Exception as e:
            logger.warning(f"Error checking robots.txt for {url}: {e}")
            # If there's an error, err on the side of caution but allow
            return True
    
    def _get_robots_parser(self, domain: str) -> Optional[RobotFileParser]:
        """Get robots.txt parser for a domain, with caching."""
        
        if domain in self.robots_cache:
            return self.robots_cache[domain]
        
        try:
            robots_url = urljoin(domain, '/robots.txt')
            
            # Create parser
            parser = RobotFileParser()
            parser.set_url(robots_url)
            
            # Try to read robots.txt
            parser.read()
            
            # Cache the result
            self.robots_cache[domain] = parser
            logger.debug(f"Loaded robots.txt for {domain}")
            
            return parser
            
        except Exception as e:
            logger.debug(f"Could not load robots.txt for {domain}: {e}")
            # Cache None to avoid repeated attempts
            self.robots_cache[domain] = None
            return None
    
    def get_crawl_delay(self, url: str) -> Optional[float]:
        """
        Get the crawl delay specified in robots.txt.
        
        Args:
            url: URL to check
            
        Returns:
            Crawl delay in seconds, or None if not specified
        """
        try:
            parsed_url = urlparse(url)
            domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            robots_parser = self._get_robots_parser(domain)
            
            if robots_parser is None:
                return None
            
            return robots_parser.crawl_delay(self.user_agent)
            
        except Exception as e:
            logger.warning(f"Error getting crawl delay for {url}: {e}")
            return None
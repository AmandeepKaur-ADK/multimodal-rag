"""
Web Retriever component for the multimodal RAG pipeline.
Handles web search and content scraping functionality.
"""
import asyncio
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup
import logging
from config.settings import settings
from .search_utils import get_search_urls
from .robots_checker import RobotsChecker
from .config_manager import config_manager
from .resource_manager import resource_manager

# Set up logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

@dataclass
class WebContent:
    """Container for scraped web content."""
    url: str
    title: str
    text_content: str
    image_urls: List[str]
    timestamp: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class ContentPair:
    """Container for text and image content from a single source."""
    text: str
    images: List[str]
    metadata: Dict[str, str]

class WebRetriever:
    """
    Web retrieval component that searches and scrapes websites for content.
    Implements rate limiting, error handling, and domain management.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.last_request_time = {}  # Domain -> timestamp for rate limiting
        self.robots_checker = RobotsChecker()
        
        # Get initial configuration
        self.config = config_manager.get_config()
        
        # Register for configuration updates
        config_manager.register_change_callback(self._on_config_change)
    
    def _on_config_change(self, new_config):
        """Handle configuration changes."""
        self.config = new_config
        logger.info("Web retriever configuration updated")
        
    def search_and_scrape(self, query: str, max_results: int = 5) -> List[WebContent]:
        """
        Search for relevant URLs and scrape their content.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            
        Returns:
            List of WebContent objects with scraped data
        """
        request_id = f"search_{int(time.time() * 1000)}"
        logger.info(f"Starting web retrieval for query: {query} (request_id: {request_id})")
        
        # Acquire resource slot for concurrent request limiting
        request_context = resource_manager.acquire_request_slot_sync(request_id, "web_retrieval")
        
        try:
            # Get current configuration
            config = self.config
            
            # Get search URLs (simplified approach using DuckDuckGo)
            search_urls = self._get_search_urls(query, max_results)
            
            # Scrape content from URLs
            results = []
            start_time = time.time()
            
            for url in search_urls:
                # Check time limit using current config
                if time.time() - start_time > config.retrieval.max_retrieval_time:
                    logger.warning(f"Retrieval time limit reached ({config.retrieval.max_retrieval_time}s)")
                    break
                    
                # Check domain restrictions using config manager
                if not config.domains.is_domain_allowed(urlparse(url).netloc):
                    logger.info(f"Skipping blocked domain: {url}")
                    continue
                    
                # Check robots.txt compliance
                if not self.robots_checker.can_fetch(url):
                    logger.info(f"Skipping URL blocked by robots.txt: {url}")
                    continue
                    
                # Scrape content
                content = self.extract_text_and_images(url)
                if content:
                    results.append(content)
                else:
                    # Record domain failure for auto-blocking
                    domain = urlparse(url).netloc
                    config_manager.record_domain_failure(domain)
                    
            logger.info(f"Retrieved {len(results)} successful results")
            return results
            
        finally:
            # Always release the resource slot
            resource_manager.release_request_slot_sync(request_id)
    
    def extract_text_and_images(self, url: str) -> Optional[WebContent]:
        """
        Extract text and image content from a single URL.
        
        Args:
            url: URL to scrape
            
        Returns:
            WebContent object or None if scraping failed
        """
        try:
            # Rate limiting
            self._apply_rate_limit(url)
            
            # Make request using current config timeout
            logger.debug(f"Scraping URL: {url}")
            response = self.session.get(
                url, 
                timeout=self.config.retrieval.request_timeout,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Parse content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else "No title"
            
            # Extract text content
            text_content = self._extract_text_content(soup)
            
            # Extract image URLs
            image_urls = self._extract_image_urls(soup, url)
            
            return WebContent(
                url=url,
                title=title,
                text_content=text_content,
                image_urls=image_urls,
                timestamp=time.time(),
                success=True
            )
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return WebContent(
                url=url,
                title="",
                text_content="",
                image_urls=[],
                timestamp=time.time(),
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            logger.error(f"Unexpected error scraping {url}: {str(e)}")
            return WebContent(
                url=url,
                title="",
                text_content="",
                image_urls=[],
                timestamp=time.time(),
                success=False,
                error_message=str(e)
            )
    
    def _get_search_urls(self, query: str, max_results: int) -> List[str]:
        """
        Get search URLs using DuckDuckGo API and fallback sources.
        """
        try:
            return get_search_urls(query, max_results)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Fallback to basic URLs
            search_terms = query.replace(' ', '+')
            return [
                f"https://en.wikipedia.org/wiki/Special:Search?search={search_terms}",
                f"https://simple.wikipedia.org/wiki/Special:Search?search={search_terms}",
            ][:max_results]
    
    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract clean text content from HTML."""
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        # Get text from main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup
        
        # Extract text
        text = main_content.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit text length
        if len(text) > settings.MAX_TEXT_LENGTH:
            text = text[:settings.MAX_TEXT_LENGTH] + "..."
            
        return text
    
    def _extract_image_urls(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract image URLs from HTML."""
        image_urls = []
        
        # Find all img tags
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if src:
                # Convert relative URLs to absolute
                full_url = urljoin(base_url, src)
                
                # Basic filtering for relevant images
                if self._is_valid_image_url(full_url):
                    image_urls.append(full_url)
        
        return image_urls[:10]  # Limit number of images
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Check if URL points to a valid image."""
        try:
            parsed = urlparse(url)
            path = parsed.path.lower()
            
            # Check file extension
            valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg']
            if any(path.endswith(ext) for ext in valid_extensions):
                return True
                
            # Check if it's not obviously an icon or small image
            if any(keyword in path for keyword in ['icon', 'logo', 'avatar', 'thumb']):
                return False
                
            return True
        except:
            return False
    
    def _apply_rate_limit(self, url: str):
        """Apply rate limiting per domain, respecting robots.txt crawl delay."""
        domain = urlparse(url).netloc
        
        # Check for robots.txt crawl delay
        robots_delay = self.robots_checker.get_crawl_delay(url)
        min_delay = self.config.retrieval.min_delay_between_requests
        delay = max(min_delay, robots_delay or 0)
        
        if domain in self.last_request_time:
            time_since_last = time.time() - self.last_request_time[domain]
            if time_since_last < delay:
                sleep_time = delay - time_since_last
                logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
                time.sleep(sleep_time)
        
        self.last_request_time[domain] = time.time()
    
    def _is_domain_allowed(self, url: str) -> bool:
        """Check if domain is allowed based on whitelist/blacklist."""
        try:
            domain = urlparse(url).netloc.lower()
            return self.config.domains.is_domain_allowed(domain)
        except:
            return False
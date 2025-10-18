"""
Search utilities for web retrieval.
Provides simple search functionality using DuckDuckGo and other sources.
"""
import requests
import json
from typing import List, Dict
from urllib.parse import quote_plus
import logging

logger = logging.getLogger(__name__)

class SimpleSearcher:
    """Simple web searcher using publicly available APIs."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def search_duckduckgo(self, query: str, max_results: int = 5) -> List[str]:
        """
        Search using DuckDuckGo instant answer API.
        Returns list of URLs.
        """
        try:
            # Use DuckDuckGo's instant answer API
            encoded_query = quote_plus(query)
            url = f"https://api.duckduckgo.com/?q={encoded_query}&format=json&no_html=1&skip_disambig=1"
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            urls = []
            
            # Extract URLs from different sections
            if 'RelatedTopics' in data:
                for topic in data['RelatedTopics'][:max_results]:
                    if isinstance(topic, dict) and 'FirstURL' in topic:
                        urls.append(topic['FirstURL'])
            
            # If we don't have enough results, add some fallback URLs
            if len(urls) < max_results:
                fallback_urls = self._get_fallback_urls(query, max_results - len(urls))
                urls.extend(fallback_urls)
            
            return urls[:max_results]
            
        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {e}")
            return self._get_fallback_urls(query, max_results)
    
    def _get_fallback_urls(self, query: str, max_results: int) -> List[str]:
        """Get fallback URLs when search APIs fail."""
        search_terms = quote_plus(query)
        
        fallback_urls = [
            f"https://en.wikipedia.org/wiki/Special:Search?search={search_terms}",
            f"https://www.britannica.com/search?query={search_terms}",
            f"https://simple.wikipedia.org/wiki/Special:Search?search={search_terms}",
        ]
        
        return fallback_urls[:max_results]

def get_search_urls(query: str, max_results: int = 5) -> List[str]:
    """
    Main function to get search URLs for a query.
    
    Args:
        query: Search query string
        max_results: Maximum number of URLs to return
        
    Returns:
        List of URLs to scrape
    """
    searcher = SimpleSearcher()
    return searcher.search_duckduckgo(query, max_results)
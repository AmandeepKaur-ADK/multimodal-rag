#!/usr/bin/env python3
"""
Simple CLI tool to test the Web Retriever component.
Usage: python test_retriever.py "your search query"
"""
import sys
import os
from src.web_retriever import WebRetriever

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_retriever.py \"your search query\"")
        print("Example: python test_retriever.py \"artificial intelligence\"")
        return
    
    query = " ".join(sys.argv[1:])
    
    print(f"Testing Web Retriever with query: '{query}'")
    print("=" * 50)
    
    # Initialize retriever
    retriever = WebRetriever()
    
    # Perform search and scraping
    results = retriever.search_and_scrape(query, max_results=3)
    
    # Display results
    print(f"\nResults: {len(results)} pages scraped")
    print("-" * 30)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   Success: {'✓' if result.success else '✗'}")
        
        if result.success:
            print(f"   Text: {len(result.text_content)} chars")
            print(f"   Images: {len(result.image_urls)} found")
            
            # Show preview
            preview = result.text_content[:150].replace('\n', ' ')
            print(f"   Preview: {preview}...")
            
        else:
            print(f"   Error: {result.error_message}")

if __name__ == "__main__":
    main()
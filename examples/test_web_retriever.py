"""
Example script to test the Web Retriever component.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.web_retriever import WebRetriever
import json

def test_web_retriever():
    """Test the web retriever with a sample query."""
    
    print("Testing Web Retriever Component")
    print("=" * 40)
    
    # Initialize retriever
    retriever = WebRetriever()
    
    # Test query
    query = "artificial intelligence recent developments"
    print(f"Query: {query}")
    print()
    
    # Perform search and scraping
    print("Searching and scraping...")
    results = retriever.search_and_scrape(query, max_results=3)
    
    # Display results
    print(f"\nFound {len(results)} results:")
    print("-" * 40)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.title}")
        print(f"   URL: {result.url}")
        print(f"   Success: {result.success}")
        
        if result.success:
            print(f"   Text length: {len(result.text_content)} characters")
            print(f"   Images found: {len(result.image_urls)}")
            print(f"   Preview: {result.text_content[:200]}...")
            
            if result.image_urls:
                print(f"   Sample images:")
                for img_url in result.image_urls[:3]:
                    print(f"     - {img_url}")
        else:
            print(f"   Error: {result.error_message}")
    
    print("\n" + "=" * 40)
    print("Test completed!")

if __name__ == "__main__":
    test_web_retriever()
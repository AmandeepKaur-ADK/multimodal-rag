"""
Example API client for the multimodal RAG pipeline web interface.
Demonstrates programmatic access to the RAG pipeline through REST API.
"""

import requests
import json
import time
from typing import Dict, Any, List, Optional
from pathlib import Path


class RAGPipelineClient:
    """
    Client for interacting with the RAG Pipeline REST API.
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8080"):
        """
        Initialize the API client.
        
        Args:
            base_url: Base URL of the RAG pipeline web interface
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'RAG-Pipeline-Client/1.0'
        })
    
    def submit_query(self, query: str, image_paths: List[str] = None) -> Dict[str, Any]:
        """
        Submit a query to the RAG pipeline.
        
        Args:
            query: Text query to process
            image_paths: Optional list of image file paths to upload
            
        Returns:
            Dictionary with response data
        """
        url = f"{self.base_url}/api/query"
        
        # Prepare form data
        data = {'query': query}
        files = []
        
        # Add image files if provided
        if image_paths:
            for image_path in image_paths:
                path = Path(image_path)
                if path.exists() and path.is_file():
                    files.append(('images', (path.name, open(path, 'rb'), 'image/jpeg')))
                else:
                    print(f"Warning: Image file not found: {image_path}")
        
        try:
            response = self.session.post(url, data=data, files=files)
            
            # Close file handles
            for _, file_tuple in files:
                if len(file_tuple) > 2:
                    file_tuple[1].close()
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
    
    def get_pipeline_health(self) -> Dict[str, Any]:
        """
        Get RAG pipeline health status.
        
        Returns:
            Dictionary with health information
        """
        url = f"{self.base_url}/api/pipeline/health"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get system status and configuration.
        
        Returns:
            Dictionary with system status
        """
        url = f"{self.base_url}/api/status"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
    
    def clear_pipeline_data(self) -> Dict[str, Any]:
        """
        Clear pipeline vector database.
        
        Returns:
            Dictionary with operation result
        """
        url = f"{self.base_url}/api/pipeline/clear"
        
        try:
            response = self.session.post(url)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }
    
    def validate_query(self, query: str, image_paths: List[str] = None) -> Dict[str, Any]:
        """
        Validate query before submission.
        
        Args:
            query: Text query to validate
            image_paths: Optional list of image file paths
            
        Returns:
            Dictionary with validation result
        """
        url = f"{self.base_url}/api/query/validate"
        
        # Prepare form data
        data = {'query': query}
        files = []
        
        # Add image files if provided
        if image_paths:
            for image_path in image_paths:
                path = Path(image_path)
                if path.exists() and path.is_file():
                    files.append(('images', (path.name, open(path, 'rb'), 'image/jpeg')))
        
        try:
            response = self.session.post(url, data=data, files=files)
            
            # Close file handles
            for _, file_tuple in files:
                if len(file_tuple) > 2:
                    file_tuple[1].close()
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "message": f"Request failed: {str(e)}"
            }


def main():
    """
    Example usage of the RAG Pipeline API client.
    """
    print("=== RAG Pipeline API Client Example ===\n")
    
    # Initialize client
    client = RAGPipelineClient()
    
    # Check system health
    print("1. Checking system health...")
    health = client.get_pipeline_health()
    if health.get("status") == "success":
        health_data = health.get("data", {})
        print(f"   Pipeline Status: {health_data.get('status', 'unknown')}")
        print(f"   Success Rate: {health_data.get('success_rate', 0):.1%}")
        print(f"   Average Response Time: {health_data.get('average_response_time', 0):.2f}s")
    else:
        print(f"   Error: {health.get('message', 'Unknown error')}")
    
    print()
    
    # Example queries
    example_queries = [
        "What are the latest developments in artificial intelligence?",
        "How does renewable energy impact climate change?",
        "What are the current trends in machine learning research?"
    ]
    
    print("2. Processing example queries...")
    
    for i, query in enumerate(example_queries, 1):
        print(f"\n   Query {i}: {query}")
        print("   " + "-" * 50)
        
        # Validate query first
        validation = client.validate_query(query)
        if validation.get("status") == "success":
            val_data = validation.get("data", {})
            if val_data.get("issues"):
                print(f"   Validation Issues: {', '.join(val_data['issues'])}")
            if val_data.get("suggestions"):
                print(f"   Suggestions: {', '.join(val_data['suggestions'])}")
        
        start_time = time.time()
        result = client.submit_query(query)
        processing_time = time.time() - start_time
        
        if result.get("status") == "success":
            data = result.get("data", {})
            
            print(f"   Answer: {data.get('answer', 'No answer')[:200]}...")
            print(f"   Confidence: {data.get('confidence', 0):.1%}")
            print(f"   Sources: {len(data.get('sources', []))}")
            print(f"   Processing Time: {processing_time:.2f}s")
            
            # Show retrieval summary
            retrieval_summary = data.get('retrieval_summary', {})
            if retrieval_summary:
                print(f"   Retrieval: {retrieval_summary.get('successful_retrievals', 0)}/{retrieval_summary.get('total_sources_attempted', 0)} successful")
                if retrieval_summary.get('failed_retrievals', 0) > 0:
                    print(f"   Failed retrievals: {retrieval_summary['failed_retrievals']}")
            
            # Show top sources
            sources = data.get('sources', [])
            if sources:
                print("   Top Sources:")
                for j, source in enumerate(sources[:2], 1):
                    print(f"     {j}. {source.get('title', 'Untitled')} ({source.get('relevance_score', 0):.1%})")
            
            # Show query suggestions if no sources found
            suggestions = data.get('query_suggestions', [])
            if suggestions:
                print("   Query Suggestions:")
                for suggestion in suggestions[:2]:
                    print(f"     • {suggestion}")
        else:
            print(f"   Error: {result.get('message', 'Unknown error')}")
        
        # Small delay between queries
        if i < len(example_queries):
            time.sleep(2)
    
    print("\n3. Getting system status...")
    status = client.get_system_status()
    if status.get("status") == "success":
        data = status.get("data", {})
        resource_stats = data.get("resource_stats", {}).get("current", {})
        
        print(f"   Memory Usage: {resource_stats.get('memory_usage_mb', 0):.1f} MB")
        print(f"   CPU Usage: {resource_stats.get('cpu_usage_percent', 0):.1f}%")
        print(f"   Active Requests: {resource_stats.get('active_requests', 0)}")
    else:
        print(f"   Error: {status.get('message', 'Unknown error')}")
    
    print("\n=== Example completed ===")


def example_with_images():
    """
    Example of submitting a query with images.
    """
    print("=== Image Query Example ===\n")
    
    client = RAGPipelineClient()
    
    # Example query with image (you would need to provide actual image paths)
    query = "What can you tell me about this image?"
    image_paths = []  # Add actual image paths here: ["path/to/image1.jpg", "path/to/image2.png"]
    
    if not image_paths:
        print("No image paths provided. Skipping image example.")
        print("To test with images, add image file paths to the image_paths list.")
        return
    
    print(f"Query: {query}")
    print(f"Images: {len(image_paths)}")
    
    result = client.submit_query(query, image_paths)
    
    if result.get("status") == "success":
        data = result.get("data", {})
        print(f"Answer: {data.get('answer', 'No answer')}")
        print(f"Confidence: {data.get('confidence', 0):.1%}")
        print(f"Sources: {len(data.get('sources', []))}")
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")


if __name__ == "__main__":
    try:
        main()
        print("\n" + "="*50)
        example_with_images()
    except KeyboardInterrupt:
        print("\n\nExample interrupted by user")
    except Exception as e:
        print(f"\nExample failed: {e}")
"""
Example usage of the RAG Pipeline orchestrator.
Demonstrates how to process queries and handle responses.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rag_pipeline import RAGPipeline, create_rag_pipeline
import logging

# Configure logging for the example
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Main example function demonstrating RAG pipeline usage."""
    
    print("=== RAG Pipeline Example ===\n")
    
    try:
        # Create RAG pipeline instance
        print("1. Initializing RAG Pipeline...")
        pipeline = create_rag_pipeline(
            vector_db_path="./data/example_vector_db",
            enable_web_retrieval=True  # Set to False to disable web retrieval
        )
        print("✓ Pipeline initialized successfully\n")
        
        # Example queries
        example_queries = [
            "What are the latest developments in artificial intelligence?",
            "How does machine learning work?",
            "What is the current state of renewable energy technology?"
        ]
        
        # Process each query
        for i, query in enumerate(example_queries, 1):
            print(f"{i}. Processing query: '{query}'")
            print("-" * 50)
            
            # Process the query through the pipeline
            result = pipeline.process_query(
                text=query,
                max_results=3,  # Limit to 3 search results
                enable_fallback=True
            )
            
            # Display results
            if result.success:
                print("✓ Query processed successfully")
                print(f"Response: {result.response.answer[:200]}...")
                print(f"Confidence: {result.response.confidence_score:.2f}")
                print(f"Sources used: {len(result.response.sources)}")
                print(f"Processing time: {result.pipeline_stats['total_time']:.2f}s")
                
                # Show source information
                if result.response.sources:
                    print("\nSources:")
                    for j, source in enumerate(result.response.sources[:2], 1):
                        print(f"  {j}. {source['url']} (relevance: {source['relevance_score']:.2f})")
                
            else:
                print("✗ Query processing failed")
                print(f"Error: {result.error_message}")
                if result.response:
                    print(f"Fallback response: {result.response.answer[:100]}...")
            
            print("\n" + "="*60 + "\n")
        
        # Show pipeline health
        print("Pipeline Health Status:")
        health = pipeline.get_pipeline_health()
        print(f"Status: {health.get('status', 'unknown')}")
        print(f"Success rate: {health.get('success_rate', 0):.2%}")
        print(f"Average response time: {health.get('average_response_time', 0):.2f}s")
        print(f"Total queries processed: {health.get('total_queries_processed', 0)}")
        
        # Clean up
        pipeline.close()
        print("\n✓ Pipeline closed successfully")
        
    except Exception as e:
        logger.error(f"Example failed: {e}")
        print(f"✗ Example failed: {e}")

def example_with_images():
    """Example demonstrating multimodal query processing with images."""
    
    print("\n=== Multimodal Query Example ===\n")
    
    try:
        # Create pipeline
        pipeline = create_rag_pipeline(enable_web_retrieval=False)  # Use existing data only
        
        # Example with text and image description
        query_text = "What can you tell me about this image?"
        
        # Note: In a real scenario, you would provide actual image files
        # For this example, we'll just use text
        result = pipeline.process_query(
            text=query_text,
            images=[],  # Would contain image paths or PIL Image objects
            enable_fallback=True
        )
        
        print(f"Query: {query_text}")
        print(f"Response: {result.response.answer}")
        print(f"Success: {result.success}")
        
        pipeline.close()
        
    except Exception as e:
        logger.error(f"Multimodal example failed: {e}")
        print(f"✗ Multimodal example failed: {e}")

if __name__ == "__main__":
    main()
    example_with_images()
"""
Example usage of the VectorDB component for the multimodal RAG pipeline.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.vector_db import VectorDB, EmbeddingData
import numpy as np


def main():
    """Demonstrate VectorDB functionality."""
    print("VectorDB Example - Multimodal RAG Pipeline")
    print("=" * 50)
    
    # Initialize vector database
    print("1. Initializing VectorDB...")
    vector_db = VectorDB(db_path="./data/example_vector_db", collection_name="example_collection")
    
    # Create some sample embeddings (normally these would come from your embedding models)
    print("\n2. Creating sample embeddings...")
    
    # Text embedding example
    text_embedding = EmbeddingData(
        embedding=np.random.rand(384).tolist(),  # Typical sentence-transformer size
        content="This is a sample text about artificial intelligence and machine learning.",
        source_url="https://example.com/ai-article",
        content_type="text",
        metadata={"topic": "AI", "author": "John Doe"}
    )
    
    # Image embedding example
    image_embedding = EmbeddingData(
        embedding=np.random.rand(384).tolist(),
        content="Image showing a neural network diagram with multiple layers",
        source_url="https://example.com/neural-network-image.jpg",
        content_type="image",
        metadata={"topic": "AI", "image_type": "diagram"}
    )
    
    # Combined multimodal embedding example
    combined_embedding = EmbeddingData(
        embedding=np.random.rand(384).tolist(),
        content="Article about deep learning with accompanying visualization charts",
        source_url="https://example.com/deep-learning-article",
        content_type="combined",
        metadata={"topic": "Deep Learning", "has_images": True}
    )
    
    # Store embeddings
    print("\n3. Storing embeddings...")
    text_id = vector_db.store(text_embedding)
    image_id = vector_db.store(image_embedding)
    combined_id = vector_db.store(combined_embedding)
    
    print(f"   Stored text embedding: {text_id}")
    print(f"   Stored image embedding: {image_id}")
    print(f"   Stored combined embedding: {combined_id}")
    
    # Get collection statistics
    print("\n4. Collection statistics:")
    stats = vector_db.get_collection_stats()
    print(f"   Total embeddings: {stats['total_embeddings']}")
    print(f"   Collection name: {stats['collection_name']}")
    print(f"   Database path: {stats['db_path']}")
    
    # Perform similarity search
    print("\n5. Performing similarity search...")
    
    # Search with a query similar to the text embedding
    query_embedding = np.random.rand(384).tolist()
    results = vector_db.search(query_embedding, top_k=3)
    
    print(f"   Found {len(results)} similar results:")
    for i, result in enumerate(results, 1):
        print(f"   {i}. Content: {result.content[:60]}...")
        print(f"      Source: {result.source_url}")
        print(f"      Type: {result.content_type}")
        print(f"      Similarity: {result.similarity_score:.3f}")
        print()
    
    # Search with content type filter
    print("6. Searching with content type filter (text only)...")
    text_results = vector_db.search(query_embedding, top_k=5, content_type_filter="text")
    print(f"   Found {len(text_results)} text results")
    
    # Search with content type filter
    print("\n7. Searching with content type filter (image only)...")
    image_results = vector_db.search(query_embedding, top_k=5, content_type_filter="image")
    print(f"   Found {len(image_results)} image results")
    
    # Demonstrate deletion by source
    print("\n8. Demonstrating deletion by source...")
    deleted_count = vector_db.delete_by_source("https://example.com/ai-article")
    print(f"   Deleted {deleted_count} embeddings from AI article source")
    
    # Final statistics
    final_stats = vector_db.get_collection_stats()
    print(f"\n9. Final statistics:")
    print(f"   Total embeddings: {final_stats['total_embeddings']}")
    
    # Close database
    vector_db.close()
    print("\n10. Database closed successfully!")
    
    print("\nVectorDB example completed successfully!")


if __name__ == "__main__":
    main()
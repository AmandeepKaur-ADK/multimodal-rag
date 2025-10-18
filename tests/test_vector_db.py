"""
Tests for the VectorDB component.
"""

import os
import tempfile
import shutil
import pytest
from src.vector_db import VectorDB, EmbeddingData, SearchResult


class TestVectorDB:
    """Test cases for VectorDB functionality."""
    
    def setup_method(self):
        """Set up test environment with temporary database."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_db")
        self.vector_db = VectorDB(db_path=self.db_path, collection_name="test_collection")
    
    def teardown_method(self):
        """Clean up test environment."""
        self.vector_db.close()
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_store_and_search_embedding(self):
        """Test storing and searching embeddings."""
        # Create test embedding data
        embedding_data = EmbeddingData(
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],
            content="Test content about AI and machine learning",
            source_url="https://example.com/ai-article",
            content_type="text",
            metadata={"topic": "AI"}
        )
        
        # Store the embedding
        doc_id = self.vector_db.store(embedding_data)
        assert doc_id is not None
        assert isinstance(doc_id, str)
        
        # Search for similar content
        query_embedding = [0.1, 0.2, 0.3, 0.4, 0.5]  # Exact match
        results = self.vector_db.search(query_embedding, top_k=1)
        
        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].content == "Test content about AI and machine learning"
        assert results[0].source_url == "https://example.com/ai-article"
        assert results[0].content_type == "text"
        assert results[0].similarity_score > 0.9  # Should be very high for exact match
    
    def test_multiple_embeddings_and_ranking(self):
        """Test storing multiple embeddings and similarity ranking."""
        # Store multiple embeddings
        embeddings = [
            EmbeddingData([0.1, 0.2, 0.3], "AI content", "https://ai.com", "text"),
            EmbeddingData([0.9, 0.8, 0.7], "Sports content", "https://sports.com", "text"),
            EmbeddingData([0.2, 0.3, 0.4], "Similar AI content", "https://ai2.com", "text")
        ]
        
        for emb_data in embeddings:
            self.vector_db.store(emb_data)
        
        # Search with query similar to first embedding
        query_embedding = [0.1, 0.2, 0.3]
        results = self.vector_db.search(query_embedding, top_k=3)
        
        assert len(results) == 3
        # First result should be most similar (exact match)
        assert results[0].content == "AI content"
        assert results[0].similarity_score >= results[1].similarity_score
    
    def test_content_type_filtering(self):
        """Test filtering search results by content type."""
        # Store embeddings of different types
        text_embedding = EmbeddingData([0.1, 0.2], "Text content", "https://text.com", "text")
        image_embedding = EmbeddingData([0.1, 0.2], "Image description", "https://img.com", "image")
        
        self.vector_db.store(text_embedding)
        self.vector_db.store(image_embedding)
        
        # Search with text filter
        results = self.vector_db.search([0.1, 0.2], top_k=5, content_type_filter="text")
        assert len(results) == 1
        assert results[0].content_type == "text"
        
        # Search with image filter
        results = self.vector_db.search([0.1, 0.2], top_k=5, content_type_filter="image")
        assert len(results) == 1
        assert results[0].content_type == "image"
    
    def test_collection_stats(self):
        """Test getting collection statistics."""
        # Initially empty
        stats = self.vector_db.get_collection_stats()
        assert stats["total_embeddings"] == 0
        
        # Add some embeddings
        for i in range(3):
            embedding_data = EmbeddingData(
                [0.1 * i, 0.2 * i], f"Content {i}", f"https://example{i}.com", "text"
            )
            self.vector_db.store(embedding_data)
        
        stats = self.vector_db.get_collection_stats()
        assert stats["total_embeddings"] == 3
        assert stats["collection_name"] == "test_collection"
    
    def test_delete_by_source(self):
        """Test deleting embeddings by source URL."""
        # Store embeddings from different sources
        embedding1 = EmbeddingData([0.1, 0.2], "Content 1", "https://source1.com", "text")
        embedding2 = EmbeddingData([0.3, 0.4], "Content 2", "https://source2.com", "text")
        embedding3 = EmbeddingData([0.5, 0.6], "Content 3", "https://source1.com", "text")
        
        self.vector_db.store(embedding1)
        self.vector_db.store(embedding2)
        self.vector_db.store(embedding3)
        
        # Delete embeddings from source1
        deleted_count = self.vector_db.delete_by_source("https://source1.com")
        assert deleted_count == 2
        
        # Verify only source2 embedding remains
        stats = self.vector_db.get_collection_stats()
        assert stats["total_embeddings"] == 1
    
    def test_persistence(self):
        """Test database persistence across instances."""
        # Store an embedding
        embedding_data = EmbeddingData(
            [0.1, 0.2, 0.3], "Persistent content", "https://persist.com", "text"
        )
        doc_id = self.vector_db.store(embedding_data)
        
        # Close and recreate database
        self.vector_db.close()
        new_vector_db = VectorDB(db_path=self.db_path, collection_name="test_collection")
        
        # Verify data persisted
        stats = new_vector_db.get_collection_stats()
        assert stats["total_embeddings"] == 1
        
        # Search should still work
        results = new_vector_db.search([0.1, 0.2, 0.3], top_k=1)
        assert len(results) == 1
        assert results[0].content == "Persistent content"
        
        new_vector_db.close()


if __name__ == "__main__":
    pytest.main([__file__])
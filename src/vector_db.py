"""
Vector Database component for the multimodal RAG pipeline.
Handles embedding storage, retrieval, and similarity search using ChromaDB.
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import chromadb
from chromadb.config import Settings
import numpy as np


@dataclass
class SearchResult:
    """Represents a search result from the vector database."""
    content: str
    source_url: str
    similarity_score: float
    content_type: str
    timestamp: str
    metadata: Dict[str, Any]


@dataclass
class EmbeddingData:
    """Represents embedding data to be stored in the vector database."""
    embedding: List[float]
    content: str
    source_url: str
    content_type: str  # "text", "image", or "combined"
    metadata: Optional[Dict[str, Any]] = None


class VectorDB:
    """
    Vector database component using ChromaDB for embedding storage and similarity search.
    
    Handles storage of multimodal embeddings with metadata and provides
    similarity search functionality with configurable parameters.
    """
    
    def __init__(self, db_path: str = "./data/vector_db", collection_name: str = "multimodal_rag"):
        """
        Initialize the vector database.
        
        Args:
            db_path: Path to store the ChromaDB database
            collection_name: Name of the collection to store embeddings
        """
        self.db_path = db_path
        self.collection_name = collection_name
        self.logger = logging.getLogger(__name__)
        
        # Ensure database directory exists
        os.makedirs(db_path, exist_ok=True)
        
        # Initialize ChromaDB client
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize ChromaDB client and collection."""
        try:
            # Create ChromaDB client with persistent storage
            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Multimodal RAG embeddings"}
            )
            
            self.logger.info(f"Initialized ChromaDB at {self.db_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def store(self, embedding_data: EmbeddingData) -> str:
        """
        Store an embedding with metadata in the vector database.
        
        Args:
            embedding_data: EmbeddingData object containing embedding and metadata
            
        Returns:
            str: Unique ID of the stored embedding
            
        Raises:
            Exception: If storage fails
        """
        try:
            # Generate unique ID based on content hash and timestamp
            timestamp = datetime.now().isoformat()
            doc_id = f"{hash(embedding_data.content)}_{timestamp.replace(':', '-')}"
            
            # Prepare metadata
            metadata = {
                "source_url": embedding_data.source_url,
                "content_type": embedding_data.content_type,
                "timestamp": timestamp,
                **(embedding_data.metadata or {})
            }
            
            # Store in ChromaDB
            self.collection.add(
                embeddings=[embedding_data.embedding],
                documents=[embedding_data.content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            self.logger.info(f"Stored embedding with ID: {doc_id}")
            return doc_id
            
        except Exception as e:
            self.logger.error(f"Failed to store embedding: {e}")
            raise
    
    def search(self, query_embedding: List[float], top_k: int = 5, 
               content_type_filter: Optional[str] = None) -> List[SearchResult]:
        """
        Search for similar embeddings in the vector database.
        
        Args:
            query_embedding: Query embedding vector
            top_k: Number of top results to return
            content_type_filter: Optional filter by content type
            
        Returns:
            List[SearchResult]: List of similar content with similarity scores
            
        Raises:
            Exception: If search fails
        """
        try:
            # Prepare where clause for filtering
            where_clause = {}
            if content_type_filter:
                where_clause["content_type"] = content_type_filter
            
            # Perform similarity search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_clause if where_clause else None
            )
            
            # Convert results to SearchResult objects
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    # Calculate similarity score (ChromaDB returns distances, convert to similarity)
                    distance = results['distances'][0][i] if results['distances'] else 0
                    similarity_score = 1.0 / (1.0 + distance)  # Convert distance to similarity
                    
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    
                    search_result = SearchResult(
                        content=results['documents'][0][i],
                        source_url=metadata.get('source_url', ''),
                        similarity_score=similarity_score,
                        content_type=metadata.get('content_type', ''),
                        timestamp=metadata.get('timestamp', ''),
                        metadata=metadata
                    )
                    search_results.append(search_result)
            
            self.logger.info(f"Found {len(search_results)} similar results")
            return search_results
            
        except Exception as e:
            self.logger.error(f"Failed to search embeddings: {e}")
            raise
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector database collection.
        
        Returns:
            Dict containing collection statistics
        """
        try:
            count = self.collection.count()
            return {
                "total_embeddings": count,
                "collection_name": self.collection_name,
                "db_path": self.db_path
            }
        except Exception as e:
            self.logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    def delete_by_source(self, source_url: str) -> int:
        """
        Delete all embeddings from a specific source URL.
        
        Args:
            source_url: Source URL to delete embeddings for
            
        Returns:
            int: Number of embeddings deleted
        """
        try:
            # Get all documents with the specified source URL
            results = self.collection.get(
                where={"source_url": source_url}
            )
            
            if results['ids']:
                # Delete the documents
                self.collection.delete(ids=results['ids'])
                deleted_count = len(results['ids'])
                self.logger.info(f"Deleted {deleted_count} embeddings from {source_url}")
                return deleted_count
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Failed to delete embeddings: {e}")
            raise
    
    def clear_collection(self) -> None:
        """
        Clear all embeddings from the collection.
        
        Warning: This will delete all stored embeddings!
        """
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Multimodal RAG embeddings"}
            )
            self.logger.info("Cleared all embeddings from collection")
            
        except Exception as e:
            self.logger.error(f"Failed to clear collection: {e}")
            raise
    
    def close(self) -> None:
        """Close the database connection."""
        try:
            # ChromaDB handles persistence automatically
            self.logger.info("Vector database connection closed")
        except Exception as e:
            self.logger.error(f"Error closing database: {e}")


# Utility functions for common operations
def create_vector_db(db_path: str = "./data/vector_db", 
                    collection_name: str = "multimodal_rag") -> VectorDB:
    """
    Factory function to create a VectorDB instance.
    
    Args:
        db_path: Path to store the database
        collection_name: Name of the collection
        
    Returns:
        VectorDB: Initialized vector database instance
    """
    return VectorDB(db_path=db_path, collection_name=collection_name)
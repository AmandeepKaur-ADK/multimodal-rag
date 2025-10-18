"""
Configuration settings for the multimodal RAG pipeline.
"""
import os
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Main configuration class for the RAG pipeline."""
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    
    # Web Retrieval Settings
    MAX_RETRIEVAL_TIME: int = int(os.getenv("MAX_RETRIEVAL_TIME", "30"))  # seconds
    MAX_CONCURRENT_REQUESTS: int = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", "10"))  # seconds
    
    # Domain Management
    ALLOWED_DOMAINS: List[str] = os.getenv("ALLOWED_DOMAINS", "").split(",") if os.getenv("ALLOWED_DOMAINS") else []
    BLOCKED_DOMAINS: List[str] = os.getenv("BLOCKED_DOMAINS", "").split(",") if os.getenv("BLOCKED_DOMAINS") else []
    
    # Vector Database Settings
    VECTOR_DB_PATH: str = os.getenv("VECTOR_DB_PATH", "./data/vector_db")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "384"))
    TOP_K_RESULTS: int = int(os.getenv("TOP_K_RESULTS", "5"))
    
    # Content Processing Settings
    MAX_IMAGE_SIZE: tuple = (800, 600)  # width, height
    SUPPORTED_IMAGE_FORMATS: List[str] = ["JPEG", "PNG", "WebP", "GIF"]
    MAX_TEXT_LENGTH: int = int(os.getenv("MAX_TEXT_LENGTH", "10000"))
    
    # Response Generation Settings
    MAX_RESPONSE_LENGTH: int = int(os.getenv("MAX_RESPONSE_LENGTH", "1000"))
    TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
    
    # Logging Settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/rag_pipeline.log")

# Global settings instance
settings = Settings()
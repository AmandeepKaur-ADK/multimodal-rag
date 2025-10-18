"""
Content Processor component for the multimodal RAG pipeline.
Handles text cleaning, image processing, and embedding generation.
"""
import re
import logging
from typing import List, Optional, Tuple, Union
from dataclasses import dataclass
from PIL import Image, ImageOps
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel
from bs4 import BeautifulSoup
import io
import base64

from config.settings import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

@dataclass
class TextEmbedding:
    """Text embedding with metadata."""
    vector: np.ndarray
    content: str
    content_type: str = "text"

@dataclass
class ImageEmbedding:
    """Image embedding with metadata."""
    vector: np.ndarray
    content: str  # image description or path
    content_type: str = "image"

@dataclass
class CombinedEmbedding:
    """Combined multimodal embedding."""
    vector: np.ndarray
    text_content: str
    image_content: str
    content_type: str = "multimodal"

class ContentProcessor:
    """
    Processes text and images for the multimodal RAG pipeline.
    
    Handles:
    - Text cleaning and normalization
    - Image processing and validation
    - Embedding generation for text and images
    - Multimodal embedding combination
    """
    
    def __init__(self):
        """Initialize the content processor with required models."""
        logger.info("Initializing ContentProcessor...")
        
        # Initialize text embedding model
        try:
            self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Text embedding model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load text embedding model: {e}")
            raise
        
        # Initialize CLIP model for image embeddings
        try:
            self.clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
            self.clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            logger.info("CLIP model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load CLIP model: {e}")
            raise
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text content that may contain HTML, extra whitespace, etc.
            
        Returns:
            Cleaned and normalized text
        """
        if not text or not isinstance(text, str):
            return ""
        
        # Remove HTML tags using BeautifulSoup
        soup = BeautifulSoup(text, 'html.parser')
        text = soup.get_text()
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)  # Replace multiple whitespace with single space
        text = re.sub(r'\n+', '\n', text)  # Replace multiple newlines with single newline
        
        # Remove extra punctuation and special characters
        text = re.sub(r'[^\w\s\.\,\!\?\;\:\-\(\)]', '', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Truncate if too long
        if len(text) > settings.MAX_TEXT_LENGTH:
            text = text[:settings.MAX_TEXT_LENGTH] + "..."
            logger.warning(f"Text truncated to {settings.MAX_TEXT_LENGTH} characters")
        
        return text
    
    def validate_image(self, image: Image.Image) -> bool:
        """
        Validate image format and properties.
        
        Args:
            image: PIL Image object
            
        Returns:
            True if image is valid, False otherwise
        """
        try:
            # Check if image format is supported
            if image.format not in settings.SUPPORTED_IMAGE_FORMATS:
                logger.warning(f"Unsupported image format: {image.format}")
                return False
            
            # Check image size (not too small or too large)
            width, height = image.size
            if width < 32 or height < 32:
                logger.warning(f"Image too small: {width}x{height}")
                return False
            
            if width > 4000 or height > 4000:
                logger.warning(f"Image too large: {width}x{height}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Image validation failed: {e}")
            return False
    
    def process_image(self, image_input: Union[str, Image.Image, bytes]) -> Optional[Image.Image]:
        """
        Process and normalize image for embedding generation.
        
        Args:
            image_input: Image file path, PIL Image, or image bytes
            
        Returns:
            Processed PIL Image or None if processing fails
        """
        try:
            # Handle different input types
            if isinstance(image_input, str):
                # File path
                image = Image.open(image_input)
            elif isinstance(image_input, bytes):
                # Image bytes
                image = Image.open(io.BytesIO(image_input))
            elif isinstance(image_input, Image.Image):
                # Already a PIL Image
                image = image_input
            else:
                logger.error(f"Unsupported image input type: {type(image_input)}")
                return None
            
            # Validate image
            if not self.validate_image(image):
                return None
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize image to standard size while maintaining aspect ratio
            image = ImageOps.fit(
                image, 
                settings.MAX_IMAGE_SIZE, 
                Image.Resampling.LANCZOS
            )
            
            logger.debug(f"Image processed successfully: {image.size}")
            return image
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return None 
   
    def generate_text_embedding(self, text: str) -> Optional[TextEmbedding]:
        """
        Generate embedding for text content.
        
        Args:
            text: Clean text content
            
        Returns:
            TextEmbedding object or None if generation fails
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for embedding generation")
                return None
            
            # Clean the text first
            cleaned_text = self.clean_text(text)
            
            if not cleaned_text:
                logger.warning("Text became empty after cleaning")
                return None
            
            # Generate embedding using sentence-transformers
            embedding_vector = self.text_model.encode(cleaned_text)
            
            # Normalize the embedding vector
            embedding_vector = embedding_vector / np.linalg.norm(embedding_vector)
            
            logger.debug(f"Generated text embedding with shape: {embedding_vector.shape}")
            
            return TextEmbedding(
                vector=embedding_vector,
                content=cleaned_text,
                content_type="text"
            )
            
        except Exception as e:
            logger.error(f"Text embedding generation failed: {e}")
            return None
    
    def generate_image_embedding(self, image: Image.Image, description: str = "") -> Optional[ImageEmbedding]:
        """
        Generate embedding for image content using CLIP.
        
        Args:
            image: Processed PIL Image
            description: Optional text description of the image
            
        Returns:
            ImageEmbedding object or None if generation fails
        """
        try:
            if image is None:
                logger.warning("No image provided for embedding generation")
                return None
            
            # Process image with CLIP processor
            inputs = self.clip_processor(images=image, return_tensors="pt")
            
            # Generate image embedding
            with torch.no_grad():
                image_features = self.clip_model.get_image_features(**inputs)
                
            # Convert to numpy and normalize
            embedding_vector = image_features.numpy().flatten()
            embedding_vector = embedding_vector / np.linalg.norm(embedding_vector)
            
            # Use description or generate a simple one
            content_description = description if description else f"Image {image.size[0]}x{image.size[1]}"
            
            logger.debug(f"Generated image embedding with shape: {embedding_vector.shape}")
            
            return ImageEmbedding(
                vector=embedding_vector,
                content=content_description,
                content_type="image"
            )
            
        except Exception as e:
            logger.error(f"Image embedding generation failed: {e}")
            return None
    
    def combine_embeddings(self, text_embedding: Optional[TextEmbedding], 
                          image_embedding: Optional[ImageEmbedding]) -> Optional[CombinedEmbedding]:
        """
        Combine text and image embeddings into a multimodal embedding.
        
        Args:
            text_embedding: Text embedding object
            image_embedding: Image embedding object
            
        Returns:
            CombinedEmbedding object or None if combination fails
        """
        try:
            if text_embedding is None and image_embedding is None:
                logger.warning("No embeddings provided for combination")
                return None
            
            # Handle cases where only one modality is available
            if text_embedding is None:
                logger.info("Only image embedding available, using as combined")
                return CombinedEmbedding(
                    vector=image_embedding.vector,
                    text_content="",
                    image_content=image_embedding.content,
                    content_type="multimodal"
                )
            
            if image_embedding is None:
                logger.info("Only text embedding available, using as combined")
                return CombinedEmbedding(
                    vector=text_embedding.vector,
                    text_content=text_embedding.content,
                    image_content="",
                    content_type="multimodal"
                )
            
            # Combine both embeddings
            # Simple approach: concatenate and normalize
            combined_vector = np.concatenate([text_embedding.vector, image_embedding.vector])
            combined_vector = combined_vector / np.linalg.norm(combined_vector)
            
            logger.debug(f"Combined embedding shape: {combined_vector.shape}")
            
            return CombinedEmbedding(
                vector=combined_vector,
                text_content=text_embedding.content,
                image_content=image_embedding.content,
                content_type="multimodal"
            )
            
        except Exception as e:
            logger.error(f"Embedding combination failed: {e}")
            return None
    
    def process_multimodal_content(self, text: str = "", 
                                 image_input: Union[str, Image.Image, bytes, None] = None) -> Optional[CombinedEmbedding]:
        """
        Process both text and image content to create a multimodal embedding.
        
        Args:
            text: Text content to process
            image_input: Image content (file path, PIL Image, or bytes)
            
        Returns:
            CombinedEmbedding object or None if processing fails
        """
        try:
            text_embedding = None
            image_embedding = None
            
            # Process text if provided
            if text and text.strip():
                text_embedding = self.generate_text_embedding(text)
                if text_embedding is None:
                    logger.warning("Failed to generate text embedding")
            
            # Process image if provided
            if image_input is not None:
                processed_image = self.process_image(image_input)
                if processed_image is not None:
                    image_embedding = self.generate_image_embedding(processed_image)
                    if image_embedding is None:
                        logger.warning("Failed to generate image embedding")
            
            # Combine embeddings
            combined_embedding = self.combine_embeddings(text_embedding, image_embedding)
            
            if combined_embedding is None:
                logger.error("Failed to create any embeddings from provided content")
                return None
            
            logger.info("Successfully processed multimodal content")
            return combined_embedding
            
        except Exception as e:
            logger.error(f"Multimodal content processing failed: {e}")
            return None
    
    def batch_process_text(self, texts: List[str]) -> List[TextEmbedding]:
        """
        Process multiple text items in batch for efficiency.
        
        Args:
            texts: List of text strings to process
            
        Returns:
            List of TextEmbedding objects (may contain None for failed items)
        """
        results = []
        
        try:
            # Clean all texts first
            cleaned_texts = [self.clean_text(text) for text in texts]
            
            # Filter out empty texts but keep track of indices
            valid_texts = []
            valid_indices = []
            
            for i, text in enumerate(cleaned_texts):
                if text and text.strip():
                    valid_texts.append(text)
                    valid_indices.append(i)
            
            if not valid_texts:
                logger.warning("No valid texts to process in batch")
                return [None] * len(texts)
            
            # Generate embeddings in batch
            embedding_vectors = self.text_model.encode(valid_texts)
            
            # Normalize embeddings
            embedding_vectors = embedding_vectors / np.linalg.norm(embedding_vectors, axis=1, keepdims=True)
            
            # Create result list with proper indexing
            results = [None] * len(texts)
            
            for i, (vector, text) in enumerate(zip(embedding_vectors, valid_texts)):
                original_index = valid_indices[i]
                results[original_index] = TextEmbedding(
                    vector=vector,
                    content=text,
                    content_type="text"
                )
            
            logger.info(f"Batch processed {len(valid_texts)} texts successfully")
            
        except Exception as e:
            logger.error(f"Batch text processing failed: {e}")
            results = [None] * len(texts)
        
        return results
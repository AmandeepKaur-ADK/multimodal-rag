"""
Tests for the ContentProcessor component.
"""
import pytest
import numpy as np
from PIL import Image
import io
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from content_processor import ContentProcessor, TextEmbedding, ImageEmbedding, CombinedEmbedding

class TestContentProcessor:
    """Test cases for ContentProcessor class."""
    
    @pytest.fixture
    def processor(self):
        """Create a ContentProcessor instance for testing."""
        return ContentProcessor()
    
    @pytest.fixture
    def sample_image(self):
        """Create a sample image for testing."""
        # Create a simple RGB image
        image = Image.new('RGB', (100, 100), color='red')
        return image
    
    def test_clean_text_basic(self, processor):
        """Test basic text cleaning functionality."""
        html_text = "<p>Hello <b>world</b>!</p>\n\n  Extra   spaces  "
        cleaned = processor.clean_text(html_text)
        
        assert cleaned == "Hello world! Extra spaces"
        assert "<p>" not in cleaned
        assert "<b>" not in cleaned
    
    def test_clean_text_empty(self, processor):
        """Test text cleaning with empty input."""
        assert processor.clean_text("") == ""
        assert processor.clean_text(None) == ""
        assert processor.clean_text("   ") == ""
    
    def test_validate_image_valid(self, processor, sample_image):
        """Test image validation with valid image."""
        # Set format for validation
        sample_image.format = 'JPEG'
        assert processor.validate_image(sample_image) == True
    
    def test_validate_image_invalid_format(self, processor, sample_image):
        """Test image validation with invalid format."""
        sample_image.format = 'INVALID'
        assert processor.validate_image(sample_image) == False
    
    def test_process_image_pil(self, processor, sample_image):
        """Test image processing with PIL Image input."""
        sample_image.format = 'JPEG'
        processed = processor.process_image(sample_image)
        
        assert processed is not None
        assert processed.mode == 'RGB'
        assert processed.size[0] <= 800  # Should be resized
        assert processed.size[1] <= 600
    
    def test_generate_text_embedding(self, processor):
        """Test text embedding generation."""
        text = "This is a test sentence for embedding generation."
        embedding = processor.generate_text_embedding(text)
        
        assert embedding is not None
        assert isinstance(embedding, TextEmbedding)
        assert embedding.vector is not None
        assert len(embedding.vector.shape) == 1  # Should be 1D vector
        assert embedding.content_type == "text"
        assert embedding.content == text  # Should be cleaned but same content
    
    def test_generate_image_embedding(self, processor, sample_image):
        """Test image embedding generation."""
        sample_image.format = 'JPEG'
        embedding = processor.generate_image_embedding(sample_image)
        
        assert embedding is not None
        assert isinstance(embedding, ImageEmbedding)
        assert embedding.vector is not None
        assert len(embedding.vector.shape) == 1  # Should be 1D vector
        assert embedding.content_type == "image"
    
    def test_combine_embeddings_both(self, processor):
        """Test combining both text and image embeddings."""
        # Create mock embeddings
        text_emb = TextEmbedding(
            vector=np.array([1.0, 0.0, 0.0]),
            content="test text"
        )
        image_emb = ImageEmbedding(
            vector=np.array([0.0, 1.0, 0.0]),
            content="test image"
        )
        
        combined = processor.combine_embeddings(text_emb, image_emb)
        
        assert combined is not None
        assert isinstance(combined, CombinedEmbedding)
        assert combined.content_type == "multimodal"
        assert len(combined.vector) == 6  # Concatenated vectors
        assert combined.text_content == "test text"
        assert combined.image_content == "test image"
    
    def test_combine_embeddings_text_only(self, processor):
        """Test combining with only text embedding."""
        text_emb = TextEmbedding(
            vector=np.array([1.0, 0.0, 0.0]),
            content="test text"
        )
        
        combined = processor.combine_embeddings(text_emb, None)
        
        assert combined is not None
        assert combined.content_type == "multimodal"
        assert combined.text_content == "test text"
        assert combined.image_content == ""
    
    def test_process_multimodal_content_text_only(self, processor):
        """Test processing multimodal content with text only."""
        text = "This is a test sentence."
        
        result = processor.process_multimodal_content(text=text)
        
        assert result is not None
        assert isinstance(result, CombinedEmbedding)
        assert result.text_content == text
        assert result.image_content == ""
    
    def test_batch_process_text(self, processor):
        """Test batch processing of multiple texts."""
        texts = [
            "First test sentence.",
            "Second test sentence.",
            "",  # Empty text
            "Third test sentence."
        ]
        
        results = processor.batch_process_text(texts)
        
        assert len(results) == 4
        assert results[0] is not None  # First text
        assert results[1] is not None  # Second text
        assert results[2] is None      # Empty text
        assert results[3] is not None  # Third text
        
        # Check that valid results are TextEmbedding objects
        for i, result in enumerate(results):
            if result is not None:
                assert isinstance(result, TextEmbedding)
                assert result.content == texts[i]

if __name__ == "__main__":
    # Simple test runner
    processor = ContentProcessor()
    print("ContentProcessor initialized successfully!")
    
    # Test text cleaning
    test_text = "<p>Hello <b>world</b>!</p>\n\n  Extra   spaces  "
    cleaned = processor.clean_text(test_text)
    print(f"Cleaned text: '{cleaned}'")
    
    # Test text embedding
    embedding = processor.generate_text_embedding("Test sentence for embedding.")
    if embedding:
        print(f"Text embedding shape: {embedding.vector.shape}")
    
    print("Basic tests completed!")
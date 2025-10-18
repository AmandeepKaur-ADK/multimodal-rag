"""
Tests for the Response Generator component.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os

from src.response_generator import ResponseGenerator, GeneratedResponse, SourceCitation, create_response_generator
from src.vector_db import SearchResult


class TestResponseGenerator:
    """Test cases for ResponseGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        # Mock OpenAI API key for testing
        self.test_api_key = "test-api-key"
        
        # Create mock search results
        self.mock_search_results = [
            SearchResult(
                content="Artificial intelligence is rapidly advancing in 2024.",
                source_url="https://example.com/ai-news",
                similarity_score=0.9,
                content_type="text",
                timestamp="2024-01-15T10:30:00",
                metadata={"title": "AI News"}
            ),
            SearchResult(
                content="Machine learning models are becoming more efficient.",
                source_url="https://example.com/ml-research",
                similarity_score=0.8,
                content_type="text",
                timestamp="2024-01-14T15:20:00",
                metadata={"title": "ML Research"}
            )
        ]
    
    @patch('src.response_generator.OpenAI')
    def test_initialization_success(self, mock_openai):
        """Test successful initialization of ResponseGenerator."""
        mock_client = Mock()
        mock_openai.return_value = mock_client
        
        generator = ResponseGenerator(api_key=self.test_api_key)
        
        assert generator.api_key == self.test_api_key
        assert generator.client == mock_client
        mock_openai.assert_called_once_with(api_key=self.test_api_key)
    
    def test_initialization_no_api_key(self):
        """Test initialization fails without API key."""
        with patch('src.response_generator.settings') as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            
            with pytest.raises(ValueError, match="OpenAI API key is required"):
                ResponseGenerator()
    
    def test_build_context(self):
        """Test context building from search results."""
        with patch('src.response_generator.OpenAI'):
            generator = ResponseGenerator(api_key=self.test_api_key)
            
            context, citations = generator.build_context(self.mock_search_results, "test query")
            
            # Check context contains source information
            assert "Source 1:" in context
            assert "Source 2:" in context
            assert "https://example.com/ai-news" in context
            assert "https://example.com/ml-research" in context
            
            # Check citations
            assert len(citations) == 2
            assert citations[0].url == "https://example.com/ai-news"
            assert citations[0].relevance_score == 0.9
            assert citations[1].url == "https://example.com/ml-research"
            assert citations[1].relevance_score == 0.8
    
    def test_build_context_empty_results(self):
        """Test context building with empty search results."""
        with patch('src.response_generator.OpenAI'):
            generator = ResponseGenerator(api_key=self.test_api_key)
            
            context, citations = generator.build_context([], "test query")
            
            assert context == ""
            assert citations == []
    
    @patch('src.response_generator.OpenAI')
    def test_generate_answer_success(self, mock_openai):
        """Test successful answer generation."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test answer with [Source 1] citation."
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        generator = ResponseGenerator(api_key=self.test_api_key)
        
        context = "Test context"
        citations = [SourceCitation("http://test.com", "2024-01-01", "text", 0.9, "excerpt")]
        
        answer = generator.generate_answer("test query", context, citations)
        
        assert answer == "This is a test answer with [Source 1] citation."
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('src.response_generator.OpenAI')
    def test_generate_answer_api_error(self, mock_openai):
        """Test answer generation with API error."""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        generator = ResponseGenerator(api_key=self.test_api_key)
        
        answer = generator.generate_answer("test query", "context", [])
        
        assert "error while generating a response" in answer.lower()
    
    def test_add_citations(self):
        """Test adding citations to answer."""
        with patch('src.response_generator.OpenAI'):
            generator = ResponseGenerator(api_key=self.test_api_key)
            
            answer = "This is a test answer."
            citations = [
                SourceCitation("http://test1.com", "2024-01-01T10:00:00", "text", 0.9, "excerpt1"),
                SourceCitation("http://test2.com", "2024-01-02T11:00:00", "image", 0.8, "excerpt2")
            ]
            
            result = generator.add_citations(answer, citations)
            
            assert "This is a test answer." in result
            assert "**Sources:**" in result
            assert "http://test1.com" in result
            assert "http://test2.com" in result
            assert "text content" in result
            assert "image content" in result
    
    def test_add_citations_empty(self):
        """Test adding citations with empty citation list."""
        with patch('src.response_generator.OpenAI'):
            generator = ResponseGenerator(api_key=self.test_api_key)
            
            answer = "This is a test answer."
            result = generator.add_citations(answer, [])
            
            assert result == answer  # Should return unchanged
    
    def test_validate_response_good(self):
        """Test response validation with good response."""
        with patch('src.response_generator.OpenAI'):
            generator = ResponseGenerator(api_key=self.test_api_key)
            
            response = "This is a comprehensive answer with [Source 1] and [Source 2] citations that provides detailed information."
            citations = [
                SourceCitation("http://test1.com", "2024-01-01", "text", 0.9, "excerpt1"),
                SourceCitation("http://test2.com", "2024-01-02", "text", 0.8, "excerpt2")
            ]
            
            passed, confidence, issues = generator.validate_response(response, "test query", citations)
            
            assert passed is True
            assert confidence > 0.5
            assert len(issues) == 0
    
    def test_validate_response_too_short(self):
        """Test response validation with too short response."""
        with patch('src.response_generator.OpenAI'):
            generator = ResponseGenerator(api_key=self.test_api_key)
            
            response = "Short answer."
            citations = []
            
            passed, confidence, issues = generator.validate_response(response, "test query", citations)
            
            assert passed is False
            assert "Response too short" in issues
    
    def test_validate_response_no_citations(self):
        """Test response validation with no citations."""
        with patch('src.response_generator.OpenAI'):
            generator = ResponseGenerator(api_key=self.test_api_key)
            
            response = "This is a longer response that doesn't have any source citations in it at all."
            citations = [SourceCitation("http://test.com", "2024-01-01", "text", 0.9, "excerpt")]
            
            passed, confidence, issues = generator.validate_response(response, "test query", citations)
            
            assert passed is False
            assert "No source citations found in response" in issues
    
    @patch('src.response_generator.OpenAI')
    def test_generate_response_complete_flow(self, mock_openai):
        """Test complete response generation flow."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Based on recent developments, AI is advancing rapidly [Source 1]. Machine learning is also improving [Source 2]."
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        generator = ResponseGenerator(api_key=self.test_api_key)
        
        result = generator.generate_response("What's new in AI?", self.mock_search_results)
        
        assert isinstance(result, GeneratedResponse)
        assert len(result.answer) > 0
        assert len(result.sources) == 2
        assert result.confidence_score > 0
        assert "**Sources:**" in result.answer
    
    @patch('src.response_generator.OpenAI')
    def test_generate_fallback_response(self, mock_openai):
        """Test fallback response generation."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Based on general knowledge, AI is a field of computer science."
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        generator = ResponseGenerator(api_key=self.test_api_key)
        
        result = generator.generate_fallback_response("What is AI?", "No web sources available")
        
        assert isinstance(result, GeneratedResponse)
        assert "No web sources available" in result.answer
        assert "general knowledge" in result.answer.lower()
        assert len(result.sources) == 0
        assert result.confidence_score == 0.5
    
    def test_create_response_generator_factory(self):
        """Test factory function for creating ResponseGenerator."""
        with patch('src.response_generator.OpenAI'):
            generator = create_response_generator(api_key=self.test_api_key)
            
            assert isinstance(generator, ResponseGenerator)
            assert generator.api_key == self.test_api_key


if __name__ == "__main__":
    pytest.main([__file__])
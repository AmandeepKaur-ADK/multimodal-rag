"""
Tests for the web interface functionality.
"""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import io

from src.web_interface import WebInterface, create_web_interface
from src.rag_pipeline import PipelineResult, UserQuery, GeneratedResponse


class TestWebInterface:
    """Test cases for the web interface."""
    
    @pytest.fixture
    def mock_pipeline(self):
        """Create a mock RAG pipeline."""
        pipeline = Mock()
        
        # Mock successful response
        mock_response = GeneratedResponse(
            answer="This is a test answer with relevant information.",
            sources=[
                {
                    "url": "https://example.com/article1",
                    "title": "Test Article 1",
                    "relevance_score": 0.85,
                    "timestamp": "2024-01-01T12:00:00",
                    "content": "This is test content from the first article."
                },
                {
                    "url": "https://example.com/article2", 
                    "title": "Test Article 2",
                    "relevance_score": 0.72,
                    "timestamp": "2024-01-01T11:00:00",
                    "content": "This is test content from the second article."
                }
            ],
            confidence_score=0.78,
            generation_time="2024-01-01T12:00:00",
            context_used=["context1", "context2"],
            validation_passed=True
        )
        
        mock_result = PipelineResult(
            query=UserQuery(text="test query"),
            response=mock_response,
            retrieval_stats={"sources_successful": 2, "sources_failed": 0},
            processing_stats={"embeddings_created": 2, "embeddings_stored": 2},
            pipeline_stats={"total_time": 1.5, "retrieval_time": 0.5},
            success=True
        )
        
        pipeline.process_query.return_value = mock_result
        pipeline.get_pipeline_health.return_value = {
            "status": "healthy",
            "success_rate": 0.95,
            "average_response_time": 1.2
        }
        
        return pipeline
    
    @pytest.fixture
    def web_interface(self, mock_pipeline):
        """Create a web interface instance with mocked pipeline."""
        with tempfile.TemporaryDirectory() as temp_dir:
            interface = WebInterface(host="127.0.0.1", port=8080, upload_folder=temp_dir)
            interface.pipeline = mock_pipeline
            interface.app.config['TESTING'] = True
            yield interface
    
    def test_web_interface_initialization(self):
        """Test web interface initialization."""
        with tempfile.TemporaryDirectory() as temp_dir:
            interface = WebInterface(upload_folder=temp_dir)
            
            assert interface.host == "127.0.0.1"
            assert interface.port == 8080
            assert interface.upload_folder == Path(temp_dir)
            assert interface.allowed_extensions == {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    def test_allowed_file_validation(self, web_interface):
        """Test file extension validation."""
        assert web_interface._allowed_file("test.jpg") == True
        assert web_interface._allowed_file("test.png") == True
        assert web_interface._allowed_file("test.gif") == True
        assert web_interface._allowed_file("test.webp") == True
        assert web_interface._allowed_file("test.txt") == False
        assert web_interface._allowed_file("test.pdf") == False
        assert web_interface._allowed_file("test") == False
    
    def test_main_dashboard_route(self, web_interface):
        """Test main dashboard route."""
        with web_interface.app.test_client() as client:
            response = client.get('/')
            
            assert response.status_code == 200
            assert b"Multimodal RAG Pipeline" in response.data
            assert b"Query Interface" in response.data
            assert b"System Administration" in response.data
    
    def test_query_interface_route(self, web_interface):
        """Test query interface route."""
        with web_interface.app.test_client() as client:
            response = client.get('/query')
            
            assert response.status_code == 200
            assert b"Ask Questions" in response.data
            assert b"Your Question" in response.data
            assert b"Upload Images" in response.data
    
    def test_process_query_text_only(self, web_interface):
        """Test processing text-only query."""
        with web_interface.app.test_client() as client:
            response = client.post('/api/query', data={
                'query': 'What is artificial intelligence?'
            })
            
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'answer' in data['data']
            assert 'sources' in data['data']
            assert 'confidence' in data['data']
            assert data['data']['answer'] == "This is a test answer with relevant information."
            assert len(data['data']['sources']) == 2
    
    def test_process_query_with_image(self, web_interface):
        """Test processing query with image upload."""
        # Create a test image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='PNG')
        img_bytes.seek(0)
        
        with web_interface.app.test_client() as client:
            response = client.post('/api/query', 
                data={
                    'query': 'What is in this image?',
                    'images': (img_bytes, 'test.png')
                },
                content_type='multipart/form-data'
            )
            
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'answer' in data['data']
    
    def test_process_query_empty_text(self, web_interface):
        """Test processing query with empty text."""
        with web_interface.app.test_client() as client:
            response = client.post('/api/query', data={
                'query': ''
            })
            
            assert response.status_code == 400
            
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'required' in data['message'].lower()
    
    def test_process_query_invalid_image(self, web_interface):
        """Test processing query with invalid image file."""
        # Create a text file disguised as image
        text_content = b"This is not an image"
        
        with web_interface.app.test_client() as client:
            response = client.post('/api/query',
                data={
                    'query': 'Test query',
                    'images': (io.BytesIO(text_content), 'fake.jpg')
                },
                content_type='multipart/form-data'
            )
            
            # Should still process the text query even if image is invalid
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
    
    def test_pipeline_health_endpoint(self, web_interface):
        """Test pipeline health endpoint."""
        with web_interface.app.test_client() as client:
            response = client.get('/api/pipeline/health')
            
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'status' in data['data']
            assert data['data']['status'] == 'healthy'
    
    def test_pipeline_health_no_pipeline(self, web_interface):
        """Test pipeline health endpoint when pipeline is not available."""
        web_interface.pipeline = None
        
        with web_interface.app.test_client() as client:
            response = client.get('/api/pipeline/health')
            
            assert response.status_code == 503
            
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'not initialized' in data['message'].lower()
    
    def test_clear_pipeline_data(self, web_interface):
        """Test clearing pipeline data."""
        with web_interface.app.test_client() as client:
            response = client.post('/api/pipeline/clear')
            
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'cleared' in data['message'].lower()
            
            # Verify the pipeline method was called
            web_interface.pipeline.clear_vector_database.assert_called_once()
    
    def test_query_status_endpoint(self, web_interface):
        """Test query status endpoint."""
        with web_interface.app.test_client() as client:
            response = client.get('/api/query/status/test-query-id')
            
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert data['data']['query_id'] == 'test-query-id'
            assert data['data']['status'] == 'completed'
    
    def test_format_sources(self, web_interface):
        """Test source formatting for display."""
        sources = [
            {
                "url": "https://example.com/long-article",
                "title": "Long Article Title",
                "relevance_score": 0.85,
                "timestamp": "2024-01-01T12:00:00",
                "content": "This is a very long content that should be truncated because it exceeds the 200 character limit that we have set for content previews in the web interface. This additional text makes it longer than 200 characters so it will be truncated with ellipsis."
            },
            {
                "url": "https://example.com/short",
                "title": "Short",
                "relevance_score": 0.72,
                "content": "Short content"
            }
        ]
        
        formatted = web_interface._format_sources(sources)
        
        assert len(formatted) == 2
        assert formatted[0]['url'] == "https://example.com/long-article"
        assert formatted[0]['title'] == "Long Article Title"
        assert formatted[0]['relevance_score'] == 0.85
        assert len(formatted[0]['content_preview']) <= 203  # 200 + "..."
        assert formatted[0]['content_preview'].endswith("...")
        
        assert formatted[1]['content_preview'] == "Short content"
        assert not formatted[1]['content_preview'].endswith("...")
    
    def test_create_web_interface_factory(self):
        """Test web interface factory function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            interface = create_web_interface(
                host="0.0.0.0", 
                port=9000, 
                upload_folder=temp_dir
            )
            
            assert interface.host == "0.0.0.0"
            assert interface.port == 9000
            assert interface.upload_folder == Path(temp_dir)
    
    @patch('src.web_interface.create_rag_pipeline')
    def test_pipeline_initialization_failure(self, mock_create_pipeline):
        """Test handling of pipeline initialization failure."""
        mock_create_pipeline.side_effect = Exception("Pipeline init failed")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            interface = WebInterface(upload_folder=temp_dir)
            
            # Pipeline should be None when initialization fails
            assert interface.pipeline is None
    
    def test_process_query_no_pipeline(self, web_interface):
        """Test processing query when pipeline is not available."""
        web_interface.pipeline = None
        
        with web_interface.app.test_client() as client:
            response = client.post('/api/query', data={
                'query': 'Test query'
            })
            
            assert response.status_code == 503
            
            data = json.loads(response.data)
            assert data['status'] == 'error'
            assert 'not available' in data['message'].lower()
    
    def test_query_validation_endpoint(self, web_interface):
        """Test query validation endpoint."""
        with web_interface.app.test_client() as client:
            # Test valid query
            response = client.post('/api/query/validate', data={
                'query': 'What are the latest developments in AI?'
            })
            
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert data['data']['valid'] == True
            
            # Test empty query
            response = client.post('/api/query/validate', data={
                'query': ''
            })
            
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert data['data']['valid'] == False
            assert len(data['data']['issues']) > 0
    
    def test_create_retrieval_summary(self, web_interface):
        """Test retrieval summary creation."""
        mock_result = Mock()
        mock_result.retrieval_stats = {
            'sources_attempted': 5,
            'sources_successful': 3,
            'sources_failed': 2,
            'search_terms': ['AI', 'machine learning'],
            'domains_consulted': ['example.com', 'test.org'],
            'retrieval_time': 1.5,
            'search_strategy': 'web_search'
        }
        
        summary = web_interface._create_retrieval_summary(mock_result)
        
        assert summary['total_sources_attempted'] == 5
        assert summary['successful_retrievals'] == 3
        assert summary['failed_retrievals'] == 2
        assert summary['search_terms_used'] == ['AI', 'machine learning']
        assert summary['domains_consulted'] == ['example.com', 'test.org']
        assert summary['strategy_used'] == 'web_search'
    
    def test_generate_query_suggestions(self, web_interface):
        """Test query suggestion generation."""
        # Test short query
        suggestions = web_interface._generate_query_suggestions("AI")
        assert any("more specific keywords" in s for s in suggestions)
        
        # Test query without question mark
        suggestions = web_interface._generate_query_suggestions("Tell me about AI")
        assert any("specific question" in s for s in suggestions)
        
        # Test query without time keywords
        suggestions = web_interface._generate_query_suggestions("What is artificial intelligence")
        assert any("latest" in s or "recent" in s for s in suggestions)
    
    def test_enhanced_query_response_format(self, web_interface):
        """Test enhanced query response with retrieval summary and suggestions."""
        # Mock a result with no sources to trigger suggestions
        mock_response = GeneratedResponse(
            answer="I don't have current information about this topic.",
            sources=[],
            confidence_score=0.3,
            generation_time="2024-01-01T12:00:00",
            context_used=[],
            validation_passed=True
        )
        
        mock_result = PipelineResult(
            query=UserQuery(text="obscure topic query"),
            response=mock_response,
            retrieval_stats={
                "sources_successful": 0, 
                "sources_failed": 3,
                "sources_attempted": 3,
                "search_strategy": "web_search"
            },
            processing_stats={"embeddings_created": 0},
            pipeline_stats={"total_time": 1.0},
            success=True
        )
        
        web_interface.pipeline.process_query.return_value = mock_result
        
        with web_interface.app.test_client() as client:
            response = client.post('/api/query', data={
                'query': 'obscure topic query'
            })
            
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['status'] == 'success'
            assert 'retrieval_summary' in data['data']
            assert 'query_suggestions' in data['data']
            assert len(data['data']['query_suggestions']) > 0
            assert data['data']['retrieval_summary']['failed_retrievals'] == 3


if __name__ == "__main__":
    pytest.main([__file__])
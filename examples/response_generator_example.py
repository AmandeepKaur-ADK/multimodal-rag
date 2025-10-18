"""
Example usage of the Response Generator component.
Demonstrates how to generate responses with context and citations.
"""

import os
import sys
from datetime import datetime

# Add project root to path for imports
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(project_root)

from src.response_generator import ResponseGenerator, create_response_generator
from src.vector_db import SearchResult


def create_mock_search_results():
    """Create mock search results for demonstration."""
    return [
        SearchResult(
            content="Artificial Intelligence has seen remarkable advances in 2024, particularly in large language models and multimodal AI systems. Companies like OpenAI, Google, and Anthropic have released more capable models.",
            source_url="https://techcrunch.com/ai-advances-2024",
            similarity_score=0.92,
            content_type="text",
            timestamp="2024-01-15T10:30:00",
            metadata={"title": "AI Advances in 2024", "author": "Tech Reporter"}
        ),
        SearchResult(
            content="Machine learning models are becoming more efficient and require less computational power. New techniques like model compression and quantization are making AI more accessible.",
            source_url="https://arxiv.org/ml-efficiency-2024",
            similarity_score=0.87,
            content_type="text", 
            timestamp="2024-01-14T15:20:00",
            metadata={"title": "Efficient ML Models", "type": "research_paper"}
        ),
        SearchResult(
            content="Computer vision has improved significantly with new transformer-based architectures. Image recognition accuracy has reached new benchmarks across multiple datasets.",
            source_url="https://papers.nips.cc/vision-transformers",
            similarity_score=0.83,
            content_type="text",
            timestamp="2024-01-12T09:15:00",
            metadata={"title": "Vision Transformers", "conference": "NeurIPS"}
        )
    ]


def demonstrate_response_generation():
    """Demonstrate the response generation process."""
    print("=== Response Generator Example ===\n")
    
    # Note: This example uses a mock API key for demonstration
    # In real usage, you would use a valid OpenAI API key
    try:
        # Create response generator (this will fail without a real API key)
        generator = create_response_generator(api_key="demo-key-for-testing")
        print("✓ Response Generator initialized")
    except Exception as e:
        print(f"✗ Failed to initialize (expected without real API key): {e}")
        print("This example shows the structure without making actual API calls.\n")
        
        # Create generator for demonstration of other methods
        generator = ResponseGenerator.__new__(ResponseGenerator)
        generator.api_key = "demo-key"
        generator.max_response_length = 1000
        generator.temperature = 0.7
        generator.min_response_length = 50
        generator.max_context_sources = 10
        generator.min_confidence_threshold = 0.3
    
    # Create mock search results
    search_results = create_mock_search_results()
    print(f"Created {len(search_results)} mock search results")
    
    # Demonstrate context building
    print("\n--- Context Building ---")
    context, citations = generator.build_context(search_results, "What are the latest AI developments?")
    
    print(f"Built context from {len(citations)} sources:")
    for i, citation in enumerate(citations, 1):
        print(f"  {i}. {citation.url} (relevance: {citation.relevance_score:.2f})")
    
    print(f"\nContext preview (first 200 chars):")
    print(f"{context[:200]}...")
    
    # Demonstrate citation formatting
    print("\n--- Citation Formatting ---")
    sample_answer = "Based on recent research, AI has advanced significantly [Source 1]. Machine learning efficiency has improved [Source 2], and computer vision has reached new benchmarks [Source 3]."
    
    answer_with_citations = generator.add_citations(sample_answer, citations)
    print("Sample answer with citations:")
    print(answer_with_citations)
    
    # Demonstrate response validation
    print("\n--- Response Validation ---")
    validation_passed, confidence_score, issues = generator.validate_response(
        answer_with_citations, "What are the latest AI developments?", citations
    )
    
    print(f"Validation passed: {validation_passed}")
    print(f"Confidence score: {confidence_score:.3f}")
    if issues:
        print(f"Issues found: {issues}")
    else:
        print("No validation issues found")
    
    # Show what a complete response would look like
    print("\n--- Complete Response Structure ---")
    
    # Mock a complete response (without actual API call)
    from src.response_generator import GeneratedResponse
    
    mock_response = GeneratedResponse(
        answer=answer_with_citations,
        sources=[
            {
                "url": citation.url,
                "timestamp": citation.timestamp,
                "content_type": citation.content_type,
                "relevance_score": citation.relevance_score,
                "excerpt": citation.excerpt
            }
            for citation in citations
        ],
        confidence_score=confidence_score,
        generation_time=datetime.now().isoformat(),
        context_used=[result.content[:100] + "..." for result in search_results],
        validation_passed=validation_passed
    )
    
    print("Complete response structure:")
    print(f"  Answer length: {len(mock_response.answer)} characters")
    print(f"  Number of sources: {len(mock_response.sources)}")
    print(f"  Confidence score: {mock_response.confidence_score:.3f}")
    print(f"  Validation passed: {mock_response.validation_passed}")
    print(f"  Generation time: {mock_response.generation_time}")


def demonstrate_error_handling():
    """Demonstrate error handling scenarios."""
    print("\n=== Error Handling Examples ===\n")
    
    # Create generator for demonstration
    generator = ResponseGenerator.__new__(ResponseGenerator)
    generator.api_key = "demo-key"
    generator.max_response_length = 1000
    generator.temperature = 0.7
    generator.min_response_length = 50
    generator.max_context_sources = 10
    generator.min_confidence_threshold = 0.3
    
    # Test with empty search results
    print("--- Empty Search Results ---")
    context, citations = generator.build_context([], "test query")
    print(f"Context: '{context}'")
    print(f"Citations: {len(citations)}")
    
    # Test validation with poor response
    print("\n--- Poor Response Validation ---")
    poor_response = "I don't know."
    validation_passed, confidence_score, issues = generator.validate_response(
        poor_response, "test query", []
    )
    print(f"Validation passed: {validation_passed}")
    print(f"Confidence score: {confidence_score:.3f}")
    print(f"Issues: {issues}")
    
    # Test validation with good response
    print("\n--- Good Response Validation ---")
    good_response = "Based on the latest research [Source 1], artificial intelligence has made significant progress in natural language processing and computer vision. The improvements in model efficiency [Source 2] have made these technologies more accessible to developers and researchers worldwide."
    
    mock_citations = [
        SearchResult(
            content="AI research progress",
            source_url="https://example.com/ai-research",
            similarity_score=0.9,
            content_type="text",
            timestamp="2024-01-15T10:00:00",
            metadata={}
        )
    ]
    
    _, good_citations = generator.build_context(mock_citations, "AI progress")
    
    validation_passed, confidence_score, issues = generator.validate_response(
        good_response, "AI progress", good_citations
    )
    print(f"Validation passed: {validation_passed}")
    print(f"Confidence score: {confidence_score:.3f}")
    print(f"Issues: {issues}")


if __name__ == "__main__":
    demonstrate_response_generation()
    demonstrate_error_handling()
    
    print("\n=== Example Complete ===")
    print("The Response Generator component provides:")
    print("✓ Context building from search results")
    print("✓ OpenAI API integration for answer generation")
    print("✓ Automatic source citation formatting")
    print("✓ Response quality validation")
    print("✓ Error handling and fallback responses")
    print("✓ Comprehensive logging and monitoring")
"""
Response Generator component for the multimodal RAG pipeline.
Handles answer generation using retrieved context and OpenAI API integration.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import re
import openai
from openai import OpenAI

from config.settings import settings
from src.vector_db import SearchResult

# Configure logging
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)


@dataclass
class GeneratedResponse:
    """Represents a generated response with metadata."""
    answer: str
    sources: List[Dict[str, Any]]
    confidence_score: float
    generation_time: str
    context_used: List[str]
    validation_passed: bool


@dataclass
class SourceCitation:
    """Represents a source citation."""
    url: str
    timestamp: str
    content_type: str
    relevance_score: float
    excerpt: str


class ResponseGenerator:
    """
    Generates responses using retrieved context and OpenAI API.
    
    Handles:
    - Context building from retrieved similar content
    - Response generation using language models
    - Source citation formatting
    - Response validation and quality checks
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the response generator.
        
        Args:
            api_key: OpenAI API key (uses settings if not provided)
        """
        logger.info("Initializing ResponseGenerator...")
        
        # Set up OpenAI client
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            logger.error("OpenAI API key not provided")
            raise ValueError("OpenAI API key is required")
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
        
        # Response generation settings
        self.max_response_length = settings.MAX_RESPONSE_LENGTH
        self.temperature = settings.TEMPERATURE
        
        # Quality validation thresholds
        self.min_response_length = 50
        self.max_context_sources = 10
        self.min_confidence_threshold = 0.3
    
    def build_context(self, search_results: List[SearchResult], query: str) -> Tuple[str, List[SourceCitation]]:
        """
        Build context string from search results for response generation.
        
        Args:
            search_results: List of search results from vector database
            query: Original user query for relevance filtering
            
        Returns:
            Tuple of (context_string, source_citations)
        """
        try:
            if not search_results:
                logger.warning("No search results provided for context building")
                return "", []
            
            # Sort results by similarity score (highest first)
            sorted_results = sorted(search_results, key=lambda x: x.similarity_score, reverse=True)
            
            # Limit number of sources to prevent context overflow
            limited_results = sorted_results[:self.max_context_sources]
            
            context_parts = []
            source_citations = []
            
            for i, result in enumerate(limited_results, 1):
                # Create excerpt from content (first 200 characters)
                excerpt = result.content[:200] + "..." if len(result.content) > 200 else result.content
                
                # Build context entry
                context_entry = f"""
Source {i}:
URL: {result.source_url}
Content Type: {result.content_type}
Timestamp: {result.timestamp}
Content: {result.content}
Relevance Score: {result.similarity_score:.3f}
---
"""
                context_parts.append(context_entry)
                
                # Create source citation
                citation = SourceCitation(
                    url=result.source_url,
                    timestamp=result.timestamp,
                    content_type=result.content_type,
                    relevance_score=result.similarity_score,
                    excerpt=excerpt
                )
                source_citations.append(citation)
            
            context_string = "\n".join(context_parts)
            
            logger.info(f"Built context from {len(limited_results)} sources")
            return context_string, source_citations
            
        except Exception as e:
            logger.error(f"Context building failed: {e}")
            return "", []
    
    def generate_answer(self, query: str, context: str, source_citations: List[SourceCitation]) -> str:
        """
        Generate answer using OpenAI API with retrieved context.
        
        Args:
            query: User's original query
            context: Built context from search results
            source_citations: List of source citations
            
        Returns:
            Generated answer string
        """
        try:
            # Build system prompt
            system_prompt = """You are a helpful AI assistant that answers questions using provided context from web sources. 

Instructions:
1. Use the provided context to answer the user's question accurately
2. If the context doesn't contain enough information, say so clearly
3. Always cite your sources using the format [Source X] where X is the source number
4. Prioritize more recent and relevant sources
5. Be concise but comprehensive
6. If sources contradict each other, mention the discrepancy
7. Focus on factual information from the sources"""
            
            # Build user prompt with context
            user_prompt = f"""Question: {query}

Context from retrieved sources:
{context}

Please answer the question based on the provided context. Remember to cite sources using [Source X] format."""
            
            # Generate response using OpenAI
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=self.max_response_length,
                temperature=self.temperature,
                top_p=0.9,
                frequency_penalty=0.1,
                presence_penalty=0.1
            )
            
            answer = response.choices[0].message.content.strip()
            
            logger.info("Successfully generated answer using OpenAI API")
            return answer
            
        except Exception as e:
            logger.error(f"Answer generation failed: {e}")
            # Fallback response
            return f"I apologize, but I encountered an error while generating a response: {str(e)}"
    
    def add_citations(self, answer: str, source_citations: List[SourceCitation]) -> str:
        """
        Add formatted source citations to the generated answer.
        
        Args:
            answer: Generated answer text
            source_citations: List of source citations
            
        Returns:
            Answer with formatted citations appended
        """
        try:
            if not source_citations:
                return answer
            
            # Add citations section
            citations_text = "\n\n**Sources:**\n"
            
            for i, citation in enumerate(source_citations, 1):
                # Format timestamp for display
                try:
                    timestamp_obj = datetime.fromisoformat(citation.timestamp.replace('Z', '+00:00'))
                    formatted_time = timestamp_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_time = citation.timestamp
                
                citation_entry = f"{i}. [{citation.url}]({citation.url}) - {citation.content_type} content (Retrieved: {formatted_time})\n"
                citations_text += citation_entry
            
            return answer + citations_text
            
        except Exception as e:
            logger.error(f"Citation formatting failed: {e}")
            return answer  # Return answer without citations if formatting fails
    
    def validate_response(self, response: str, query: str, source_citations: List[SourceCitation]) -> Tuple[bool, float, List[str]]:
        """
        Validate the quality of the generated response.
        
        Args:
            response: Generated response text
            query: Original user query
            source_citations: Source citations used
            
        Returns:
            Tuple of (validation_passed, confidence_score, validation_issues)
        """
        validation_issues = []
        confidence_factors = []
        
        try:
            # Check response length
            if len(response.strip()) < self.min_response_length:
                validation_issues.append("Response too short")
                confidence_factors.append(0.2)
            else:
                confidence_factors.append(0.8)
            
            # Check if response contains source citations
            citation_pattern = r'\[Source \d+\]'
            citations_found = len(re.findall(citation_pattern, response))
            
            if citations_found == 0:
                validation_issues.append("No source citations found in response")
                confidence_factors.append(0.3)
            elif citations_found > len(source_citations):
                validation_issues.append("More citations referenced than sources available")
                confidence_factors.append(0.5)
            else:
                confidence_factors.append(0.9)
            
            # Check for generic/unhelpful responses
            generic_phrases = [
                "i don't know", "i'm not sure", "i cannot", "i can't help",
                "no information", "not enough information", "unable to"
            ]
            
            response_lower = response.lower()
            generic_count = sum(1 for phrase in generic_phrases if phrase in response_lower)
            
            if generic_count > 2:
                validation_issues.append("Response appears too generic or unhelpful")
                confidence_factors.append(0.4)
            else:
                confidence_factors.append(0.8)
            
            # Check source relevance
            if source_citations:
                avg_relevance = sum(c.relevance_score for c in source_citations) / len(source_citations)
                if avg_relevance < self.min_confidence_threshold:
                    validation_issues.append("Low relevance of source materials")
                    confidence_factors.append(0.5)
                else:
                    confidence_factors.append(min(avg_relevance, 1.0))
            
            # Calculate overall confidence score
            confidence_score = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
            
            # Determine if validation passed
            validation_passed = len(validation_issues) == 0 and confidence_score >= self.min_confidence_threshold
            
            logger.info(f"Response validation: passed={validation_passed}, confidence={confidence_score:.3f}")
            
            return validation_passed, confidence_score, validation_issues
            
        except Exception as e:
            logger.error(f"Response validation failed: {e}")
            return False, 0.0, [f"Validation error: {str(e)}"]
    
    def generate_response(self, query: str, search_results: List[SearchResult]) -> GeneratedResponse:
        """
        Main method to generate a complete response with citations and validation.
        
        Args:
            query: User's original query
            search_results: List of search results from vector database
            
        Returns:
            GeneratedResponse object with answer, sources, and metadata
        """
        generation_start = datetime.now()
        
        try:
            logger.info(f"Generating response for query: {query[:100]}...")
            
            # Build context from search results
            context, source_citations = self.build_context(search_results, query)
            
            # Generate answer
            answer = self.generate_answer(query, context, source_citations)
            
            # Add formatted citations
            answer_with_citations = self.add_citations(answer, source_citations)
            
            # Validate response
            validation_passed, confidence_score, validation_issues = self.validate_response(
                answer_with_citations, query, source_citations
            )
            
            # Prepare source information for response
            sources = []
            for citation in source_citations:
                source_info = {
                    "url": citation.url,
                    "timestamp": citation.timestamp,
                    "content_type": citation.content_type,
                    "relevance_score": citation.relevance_score,
                    "excerpt": citation.excerpt
                }
                sources.append(source_info)
            
            # Create response object
            response = GeneratedResponse(
                answer=answer_with_citations,
                sources=sources,
                confidence_score=confidence_score,
                generation_time=generation_start.isoformat(),
                context_used=[result.content[:100] + "..." for result in search_results[:5]],
                validation_passed=validation_passed
            )
            
            # Log validation issues if any
            if validation_issues:
                logger.warning(f"Response validation issues: {validation_issues}")
            
            logger.info(f"Response generated successfully (confidence: {confidence_score:.3f})")
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            
            # Return error response
            return GeneratedResponse(
                answer=f"I apologize, but I encountered an error while processing your request: {str(e)}",
                sources=[],
                confidence_score=0.0,
                generation_time=generation_start.isoformat(),
                context_used=[],
                validation_passed=False
            )
    
    def generate_fallback_response(self, query: str, error_message: str = "") -> GeneratedResponse:
        """
        Generate a fallback response when no context is available.
        
        Args:
            query: User's original query
            error_message: Optional error message to include
            
        Returns:
            GeneratedResponse object with fallback answer
        """
        try:
            fallback_prompt = f"""Please provide a helpful general answer to this question: {query}

Note: No current web sources were available, so please provide general knowledge while clearly stating that the information may not be current."""
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant. Provide general knowledge answers but clearly indicate when information may not be current."},
                    {"role": "user", "content": fallback_prompt}
                ],
                max_tokens=self.max_response_length,
                temperature=self.temperature
            )
            
            answer = response.choices[0].message.content.strip()
            
            if error_message:
                answer = f"**Note:** {error_message}\n\n{answer}"
            
            answer += "\n\n**Note:** This response is based on general knowledge and may not include the most current information."
            
            return GeneratedResponse(
                answer=answer,
                sources=[],
                confidence_score=0.5,  # Lower confidence for fallback
                generation_time=datetime.now().isoformat(),
                context_used=[],
                validation_passed=True
            )
            
        except Exception as e:
            logger.error(f"Fallback response generation failed: {e}")
            
            return GeneratedResponse(
                answer="I apologize, but I'm unable to process your request at this time. Please try again later.",
                sources=[],
                confidence_score=0.0,
                generation_time=datetime.now().isoformat(),
                context_used=[],
                validation_passed=False
            )


# Utility function for easy response generation
def create_response_generator(api_key: Optional[str] = None) -> ResponseGenerator:
    """
    Factory function to create a ResponseGenerator instance.
    
    Args:
        api_key: OpenAI API key (uses settings if not provided)
        
    Returns:
        ResponseGenerator: Initialized response generator instance
    """
    return ResponseGenerator(api_key=api_key)
"""
Free Response Generator using Hugging Face transformers.
No API keys required - uses local models.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import re

try:
    from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from src.vector_db import SearchResult

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
    model_used: str = "free_model"


class FreeResponseGenerator:
    """
    Response generator using free Hugging Face models.
    No API keys required - runs locally.
    """
    
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        """
        Initialize the free response generator.
        
        Args:
            model_name: Hugging Face model to use
        """
        logger.info("Initializing Free Response Generator...")
        
        self.model_name = model_name
        self.generator = None
        self.tokenizer = None
        
        # Try to load the model
        self._load_model()
        
        # Fallback templates if model loading fails
        self.fallback_templates = {
            "general": "Based on the available information, {query} can be understood as follows: {context_summary}",
            "no_context": "I understand you're asking about '{query}'. While I don't have specific current information, this is generally a topic that involves multiple aspects and considerations.",
            "error": "I apologize, but I'm having difficulty processing your request about '{query}'. Please try rephrasing your question."
        }
    
    def _load_model(self):
        """Load the Hugging Face model."""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Transformers library not available. Using template-based responses.")
            return
        
        try:
            logger.info(f"Loading model: {self.model_name}")
            
            # Try different free models in order of preference
            models_to_try = [
                "microsoft/DialoGPT-small",  # Smaller, faster
                "gpt2",  # Classic GPT-2
                "distilgpt2",  # Distilled version, faster
            ]
            
            for model in models_to_try:
                try:
                    logger.info(f"Attempting to load {model}...")
                    
                    # Load tokenizer and model
                    self.tokenizer = AutoTokenizer.from_pretrained(model)
                    
                    # Add padding token if it doesn't exist
                    if self.tokenizer.pad_token is None:
                        self.tokenizer.pad_token = self.tokenizer.eos_token
                    
                    # Create text generation pipeline
                    self.generator = pipeline(
                        "text-generation",
                        model=model,
                        tokenizer=self.tokenizer,
                        max_length=200,
                        num_return_sequences=1,
                        temperature=0.7,
                        do_sample=True,
                        pad_token_id=self.tokenizer.eos_token_id
                    )
                    
                    self.model_name = model
                    logger.info(f"Successfully loaded {model}")
                    return
                    
                except Exception as e:
                    logger.warning(f"Failed to load {model}: {e}")
                    continue
            
            logger.warning("Could not load any Hugging Face models. Using template responses.")
            
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            logger.info("Falling back to template-based responses")
    
    def generate_response(self, query: str, search_results: List[SearchResult]) -> GeneratedResponse:
        """
        Generate response using free models or templates.
        
        Args:
            query: User's query
            search_results: Retrieved search results
            
        Returns:
            GeneratedResponse object
        """
        start_time = datetime.now()
        
        try:
            # Build context from search results
            context = self._build_context(search_results)
            
            # Generate response
            if self.generator and TRANSFORMERS_AVAILABLE:
                answer = self._generate_with_model(query, context)
                model_used = self.model_name
            else:
                answer = self._generate_with_template(query, context, search_results)
                model_used = "template_based"
            
            # Add source citations
            answer_with_citations = self._add_citations(answer, search_results)
            
            # Prepare source information
            sources = []
            for result in search_results[:5]:  # Limit to top 5
                sources.append({
                    "url": result.source_url,
                    "content_type": result.content_type,
                    "similarity_score": result.similarity_score,
                    "excerpt": result.content[:200] + "..." if len(result.content) > 200 else result.content
                })
            
            # Calculate confidence based on available context
            confidence = self._calculate_confidence(search_results, answer)
            
            return GeneratedResponse(
                answer=answer_with_citations,
                sources=sources,
                confidence_score=confidence,
                generation_time=start_time.isoformat(),
                context_used=[r.content[:100] + "..." for r in search_results[:3]],
                validation_passed=True,
                model_used=model_used
            )
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            
            # Return error response
            return GeneratedResponse(
                answer=f"I apologize, but I encountered an error while generating a response to your question about '{query}'. Please try rephrasing your question or try again later.",
                sources=[],
                confidence_score=0.0,
                generation_time=start_time.isoformat(),
                context_used=[],
                validation_passed=False,
                model_used="error_fallback"
            )
    
    def _generate_with_model(self, query: str, context: str) -> str:
        """Generate response using the loaded Hugging Face model."""
        try:
            # Create prompt
            if context:
                prompt = f"Question: {query}\nContext: {context[:500]}\nAnswer:"
            else:
                prompt = f"Question: {query}\nAnswer:"
            
            # Generate response
            outputs = self.generator(
                prompt,
                max_length=len(prompt.split()) + 50,  # Add 50 tokens for response
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Extract the generated text
            generated_text = outputs[0]['generated_text']
            
            # Extract just the answer part
            if "Answer:" in generated_text:
                answer = generated_text.split("Answer:")[-1].strip()
            else:
                answer = generated_text[len(prompt):].strip()
            
            # Clean up the answer
            answer = self._clean_generated_text(answer)
            
            # Ensure minimum quality
            if len(answer) < 10 or not answer:
                return self._generate_with_template(query, context, [])
            
            return answer
            
        except Exception as e:
            logger.error(f"Model generation failed: {e}")
            return self._generate_with_template(query, context, [])
    
    def _generate_with_template(self, query: str, context: str, search_results: List[SearchResult]) -> str:
        """Generate response using templates when model is not available."""
        
        if search_results and context:
            # Use context-based template
            context_summary = self._summarize_context(context)
            return self.fallback_templates["general"].format(
                query=query,
                context_summary=context_summary
            )
        else:
            # Use general template
            return self.fallback_templates["no_context"].format(query=query)
    
    def _build_context(self, search_results: List[SearchResult]) -> str:
        """Build context string from search results."""
        if not search_results:
            return ""
        
        context_parts = []
        for result in search_results[:3]:  # Use top 3 results
            if result.content:
                # Take first 200 characters of each result
                excerpt = result.content[:200].strip()
                if excerpt:
                    context_parts.append(excerpt)
        
        return " ".join(context_parts)
    
    def _summarize_context(self, context: str) -> str:
        """Create a simple summary of the context."""
        if not context:
            return "various relevant information and perspectives"
        
        # Simple extractive summary - take first and last sentences
        sentences = re.split(r'[.!?]+', context)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) == 0:
            return "relevant information from multiple sources"
        elif len(sentences) == 1:
            return sentences[0]
        elif len(sentences) <= 3:
            return ". ".join(sentences)
        else:
            # Take first and last sentences
            return f"{sentences[0]}. {sentences[-1]}"
    
    def _clean_generated_text(self, text: str) -> str:
        """Clean up generated text."""
        # Remove common artifacts
        text = re.sub(r'\n+', ' ', text)  # Replace newlines with spaces
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        text = text.strip()
        
        # Remove incomplete sentences at the end
        sentences = re.split(r'[.!?]+', text)
        if len(sentences) > 1 and len(sentences[-1].strip()) < 10:
            text = '.'.join(sentences[:-1]) + '.'
        
        return text
    
    def _add_citations(self, answer: str, search_results: List[SearchResult]) -> str:
        """Add source citations to the answer."""
        if not search_results:
            return answer
        
        # Add citations section
        citations = "\n\n**Sources:**\n"
        for i, result in enumerate(search_results[:3], 1):
            citations += f"{i}. {result.source_url} (Similarity: {result.similarity_score:.2f})\n"
        
        return answer + citations
    
    def _calculate_confidence(self, search_results: List[SearchResult], answer: str) -> float:
        """Calculate confidence score based on available information."""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on search results
        if search_results:
            avg_similarity = sum(r.similarity_score for r in search_results) / len(search_results)
            confidence += avg_similarity * 0.3
        
        # Increase confidence based on answer length and quality
        if len(answer) > 50:
            confidence += 0.1
        
        if len(answer) > 100:
            confidence += 0.1
        
        # Cap at 1.0
        return min(confidence, 1.0)
    
    def generate_fallback_response(self, query: str, error_message: str = "") -> GeneratedResponse:
        """Generate a fallback response when main generation fails."""
        
        fallback_answer = f"I understand you're asking about '{query}'. "
        
        if error_message:
            fallback_answer += f"I encountered an issue ({error_message}), but I can provide some general guidance. "
        
        fallback_answer += "This topic typically involves multiple aspects and considerations. For the most accurate and up-to-date information, I'd recommend consulting authoritative sources or experts in this field."
        
        return GeneratedResponse(
            answer=fallback_answer,
            sources=[],
            confidence_score=0.3,
            generation_time=datetime.now().isoformat(),
            context_used=[],
            validation_passed=True,
            model_used="fallback_template"
        )


# Factory function
def create_free_response_generator(model_name: str = "microsoft/DialoGPT-small") -> FreeResponseGenerator:
    """
    Create a free response generator instance.
    
    Args:
        model_name: Hugging Face model to use
        
    Returns:
        FreeResponseGenerator instance
    """
    return FreeResponseGenerator(model_name=model_name)
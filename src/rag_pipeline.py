"""
Main RAG Pipeline orchestrator for the multimodal RAG system.
Coordinates all components and implements the main pipeline flow with comprehensive
error handling, validation, and graceful degradation.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
from PIL import Image
import asyncio
import traceback

from config.settings import settings
from src.web_retriever import WebRetriever, WebContent
from src.content_processor import ContentProcessor, CombinedEmbedding
from src.vector_db import VectorDB, EmbeddingData, SearchResult
from src.response_generator import ResponseGenerator, GeneratedResponse
from src.config_manager import config_manager
from src.resource_manager import resource_manager

# Import enhanced error handling and validation
from src.validation_manager import validation_manager, ValidationReport, ProcessingOptions
from src.enhanced_logger import enhanced_logger, LogCategory, RequestLoggingContext
from src.health_monitor import health_monitor
from src.error_handler import ErrorSeverity, ErrorCategory

# Configure basic logging (enhanced logging is handled separately)
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class UserQuery:
    """Represents a user query with text and optional images."""
    text: str
    images: List[Union[str, Image.Image]] = None
    query_id: str = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.images is None:
            self.images = []
        if self.query_id is None:
            self.query_id = f"query_{int(time.time() * 1000)}"
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class PipelineResult:
    """Represents the complete result from the RAG pipeline."""
    query: UserQuery
    response: GeneratedResponse
    retrieval_stats: Dict[str, Any]
    processing_stats: Dict[str, Any]
    pipeline_stats: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    validation_report: Optional[ValidationReport] = None
    fallback_strategies_used: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.fallback_strategies_used is None:
            self.fallback_strategies_used = []
        if self.warnings is None:
            self.warnings = []


@dataclass
class PipelineStats:
    """Statistics for monitoring pipeline performance."""
    total_time: float
    retrieval_time: float
    processing_time: float
    generation_time: float
    sources_retrieved: int
    embeddings_created: int
    similar_results_found: int
    success: bool


class RAGPipeline:
    """
    Main orchestrator for the multimodal RAG pipeline.
    
    Coordinates web retrieval, content processing, vector storage/search,
    and response generation to provide comprehensive answers to user queries.
    """
    
    def __init__(self, 
                 vector_db_path: str = None,
                 openai_api_key: str = None,
                 enable_web_retrieval: bool = True):
        """
        Initialize the RAG pipeline with all components.
        
        Args:
            vector_db_path: Path for vector database storage
            openai_api_key: OpenAI API key for response generation
            enable_web_retrieval: Whether to enable live web retrieval
        """
        logger.info("Initializing RAG Pipeline...")
        
        self.enable_web_retrieval = enable_web_retrieval
        self.pipeline_stats = []
        
        # Get configuration
        self.config = config_manager.get_config()
        
        # Register cleanup callback with resource manager
        resource_manager.register_cleanup_callback(self._cleanup_resources)
        
        try:
            # Initialize components
            self._initialize_components(vector_db_path, openai_api_key)
            logger.info("RAG Pipeline initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG Pipeline: {e}")
            raise
    
    def _initialize_components(self, vector_db_path: str, openai_api_key: str):
        """Initialize all pipeline components."""
        
        # Initialize Web Retriever
        if self.enable_web_retrieval:
            try:
                self.web_retriever = WebRetriever()
                logger.info("Web Retriever initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Web Retriever: {e}")
                self.web_retriever = None
                self.enable_web_retrieval = False
        else:
            self.web_retriever = None
        
        # Initialize Content Processor
        try:
            self.content_processor = ContentProcessor()
            logger.info("Content Processor initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Content Processor: {e}")
            raise
        
        # Initialize Vector Database
        try:
            db_path = vector_db_path or settings.VECTOR_DB_PATH
            self.vector_db = VectorDB(db_path=db_path)
            logger.info("Vector Database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Vector Database: {e}")
            raise
        
        # Initialize Response Generator
        try:
            api_key = openai_api_key or settings.OPENAI_API_KEY
            self.response_generator = ResponseGenerator(api_key=api_key)
            logger.info("Response Generator initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Response Generator: {e}")
            raise
    
    def process_query(self, 
                     text: str, 
                     images: List[Union[str, Image.Image]] = None,
                     max_results: int = None,
                     enable_fallback: bool = True,
                     request_id: str = None) -> PipelineResult:
        """
        Main method to process a user query through the complete RAG pipeline
        with comprehensive validation, error handling, and graceful degradation.
        
        Args:
            text: User's text query
            images: Optional list of images (file paths or PIL Images)
            max_results: Maximum number of search results to retrieve
            enable_fallback: Whether to use fallback response if retrieval fails
            request_id: Optional request ID for tracking
            
        Returns:
            PipelineResult with response, validation report, and statistics
        """
        start_time = time.time()
        
        # Generate request ID if not provided
        if request_id is None:
            request_id = f"req_{int(time.time() * 1000)}"
        
        # Use request logging context
        with RequestLoggingContext(request_id) as req_logger:
            
            # Step 0: System readiness check
            is_ready, system_warnings, critical_issues = validation_manager.check_system_readiness()
            
            if not is_ready:
                error_message = f"System not ready: {'; '.join(critical_issues)}"
                req_logger.error(
                    error_message,
                    component="rag_pipeline",
                    category=LogCategory.SYSTEM
                )
                
                return PipelineResult(
                    query=UserQuery(text=text, images=images or []),
                    response=GeneratedResponse(
                        answer="The system is currently unavailable. Please try again later.",
                        sources=[],
                        confidence_score=0.0,
                        generation_time=datetime.now().isoformat(),
                        context_used=[],
                        validation_passed=False
                    ),
                    retrieval_stats={},
                    processing_stats={},
                    pipeline_stats={"total_time": time.time() - start_time, "error": error_message},
                    success=False,
                    error_message=error_message,
                    warnings=system_warnings
                )
            
            # Step 1: Comprehensive input validation
            req_logger.info(
                f"Processing query: {text[:100]}...",
                component="rag_pipeline",
                category=LogCategory.PIPELINE,
                metadata={"text_length": len(text), "image_count": len(images or [])}
            )
            
            validation_report = validation_manager.validate_user_input(text, images, request_id)
            
            if not validation_report.is_valid:
                error_message = validation_report.get_user_message()
                req_logger.warning(
                    f"Input validation failed: {error_message}",
                    component="rag_pipeline",
                    category=LogCategory.USER_INTERACTION
                )
                
                return PipelineResult(
                    query=UserQuery(text=text, images=images or []),
                    response=GeneratedResponse(
                        answer=error_message,
                        sources=[],
                        confidence_score=0.0,
                        generation_time=datetime.now().isoformat(),
                        context_used=[],
                        validation_passed=False
                    ),
                    retrieval_stats={},
                    processing_stats={},
                    pipeline_stats={"total_time": time.time() - start_time, "validation_failed": True},
                    success=False,
                    error_message=error_message,
                    validation_report=validation_report
                )
            
            # Create user query object with sanitized input
            user_query = UserQuery(
                text=validation_report.text_validation.sanitized_input or text,
                images=images or []
            )
            
            # Get processing options from validation
            processing_options = validation_report.processing_options
            fallback_strategies_used = []
            
            req_logger.info(
                f"Input validation passed with options: web_retrieval={processing_options.enable_web_retrieval}, "
                f"image_processing={processing_options.enable_image_processing}",
                component="rag_pipeline",
                category=LogCategory.USER_INTERACTION
            )
            
            try:
                # Step 2: Retrieve relevant content from web (with error handling)
                retrieval_start = time.time()
                web_contents, retrieval_stats = self._retrieve_content_with_fallback(
                    user_query, max_results, processing_options, fallback_strategies_used
                )
                retrieval_time = time.time() - retrieval_start
            
                # Step 3: Process content and create embeddings (with error handling)
                processing_start = time.time()
                embeddings, processing_stats = self._process_content_with_fallback(
                    web_contents, user_query, processing_options, fallback_strategies_used
                )
                processing_time = time.time() - processing_start
            
                # Step 4: Search for similar content in vector database (with error handling)
                search_start = time.time()
                query_embedding, similar_results = self._search_with_fallback(
                    user_query, max_results, processing_options, fallback_strategies_used
                )
                search_time = time.time() - search_start
            
                # Step 5: Generate response using retrieved context (with error handling)
                generation_start = time.time()
                response = self._generate_response_with_fallback(
                    user_query, similar_results, processing_options, fallback_strategies_used
                )
                generation_time = time.time() - generation_start
            
                total_time = time.time() - start_time
                
                # Create pipeline statistics
                pipeline_stats = {
                    "total_time": total_time,
                    "retrieval_time": retrieval_time,
                    "processing_time": processing_time,
                    "search_time": search_time,
                    "generation_time": generation_time,
                    "query_id": user_query.query_id,
                    "timestamp": datetime.now().isoformat(),
                    "fallback_strategies_used": fallback_strategies_used,
                    "validation_warnings": len(validation_report.warnings)
                }
            
                # Store statistics for monitoring
                self._record_pipeline_stats(pipeline_stats, retrieval_stats, processing_stats, True)
                
                # Record performance metrics for config manager
                config_manager.record_performance_metrics({
                    'total_time': total_time,
                    'retrieval_time': retrieval_time,
                    'processing_time': processing_time,
                    'generation_time': generation_time,
                    'success': True,
                    'sources_retrieved': retrieval_stats.get("sources_successful", 0),
                    'fallback_strategies_count': len(fallback_strategies_used)
                })
                
                req_logger.info(
                    f"Query processed successfully in {total_time:.2f}s",
                    component="rag_pipeline",
                    category=LogCategory.PIPELINE,
                    metadata={
                        "total_time": total_time,
                        "fallback_strategies": fallback_strategies_used,
                        "validation_warnings": len(validation_report.warnings)
                    }
                )
                
                return PipelineResult(
                    query=user_query,
                    response=response,
                    retrieval_stats=retrieval_stats,
                    processing_stats=processing_stats,
                    pipeline_stats=pipeline_stats,
                    success=True,
                    validation_report=validation_report,
                    fallback_strategies_used=fallback_strategies_used,
                    warnings=validation_report.warnings + system_warnings
                )
            
            except Exception as e:
                total_time = time.time() - start_time
                
                # Handle the error with comprehensive error handling
                error_details, fallback_strategy = validation_manager.handle_processing_error(
                    "rag_pipeline", e, {"query_id": user_query.query_id, "total_time": total_time}
                )
                
                error_message = error_details.user_message
                
                req_logger.error(
                    f"Pipeline processing failed: {error_details.message}",
                    component="rag_pipeline",
                    category=LogCategory.ERROR_HANDLING,
                    error=e,
                    metadata={"error_details": error_details.to_dict()}
                )
                
                # Try to generate fallback response
                fallback_response = None
                if enable_fallback:
                    try:
                        fallback_response = self.response_generator.generate_fallback_response(
                            user_query.text, error_message
                        )
                        fallback_strategies_used.append("fallback_response")
                        req_logger.info(
                            "Generated fallback response",
                            component="rag_pipeline",
                            category=LogCategory.ERROR_HANDLING
                        )
                    except Exception as fallback_error:
                        req_logger.error(
                            "Fallback response generation failed",
                            component="rag_pipeline",
                            category=LogCategory.ERROR_HANDLING,
                            error=fallback_error
                        )
                
                # Record failed pipeline stats
                pipeline_stats = {
                    "total_time": total_time,
                    "error": error_details.message,
                    "error_category": error_details.category.value,
                    "error_severity": error_details.severity.value,
                    "query_id": user_query.query_id,
                    "timestamp": datetime.now().isoformat(),
                    "fallback_strategies_used": fallback_strategies_used
                }
                self._record_pipeline_stats(pipeline_stats, {}, {}, False)
                
                # Record performance metrics for config manager
                config_manager.record_performance_metrics({
                    'total_time': total_time,
                    'success': False,
                    'error': error_details.message,
                    'error_category': error_details.category.value
                })
                
                return PipelineResult(
                    query=user_query,
                    response=fallback_response,
                    retrieval_stats={},
                    processing_stats={},
                    pipeline_stats=pipeline_stats,
                    success=False,
                    error_message=error_message,
                    validation_report=validation_report,
                    fallback_strategies_used=fallback_strategies_used,
                    warnings=validation_report.warnings if validation_report else []
                )
    
    def _retrieve_content(self, user_query: UserQuery, max_results: int = None) -> Tuple[List[WebContent], Dict[str, Any]]:
        """
        Retrieve relevant content from web sources.
        
        Args:
            user_query: User query object
            max_results: Maximum number of results to retrieve
            
        Returns:
            Tuple of (web_contents, retrieval_stats)
        """
        retrieval_stats = {
            "enabled": self.enable_web_retrieval,
            "sources_attempted": 0,
            "sources_successful": 0,
            "sources_failed": 0,
            "total_content_length": 0,
            "total_images_found": 0
        }
        
        if not self.enable_web_retrieval or not self.web_retriever:
            logger.info("Web retrieval disabled, skipping content retrieval")
            return [], retrieval_stats
        
        try:
            max_results = max_results or self.config.retrieval.max_concurrent_requests
            
            logger.info(f"Retrieving web content for query: {user_query.text}")
            web_contents = self.web_retriever.search_and_scrape(user_query.text, max_results)
            
            # Calculate statistics
            retrieval_stats["sources_attempted"] = max_results
            retrieval_stats["sources_successful"] = sum(1 for content in web_contents if content.success)
            retrieval_stats["sources_failed"] = sum(1 for content in web_contents if not content.success)
            retrieval_stats["total_content_length"] = sum(len(content.text_content) for content in web_contents)
            retrieval_stats["total_images_found"] = sum(len(content.image_urls) for content in web_contents)
            
            logger.info(f"Retrieved {len(web_contents)} web sources")
            return web_contents, retrieval_stats
            
        except Exception as e:
            logger.error(f"Content retrieval failed: {e}")
            retrieval_stats["error"] = str(e)
            return [], retrieval_stats
    
    def _process_content(self, web_contents: List[WebContent], user_query: UserQuery) -> Tuple[List[CombinedEmbedding], Dict[str, Any]]:
        """
        Process retrieved content and user query to create embeddings.
        
        Args:
            web_contents: List of retrieved web content
            user_query: User query object
            
        Returns:
            Tuple of (embeddings, processing_stats)
        """
        processing_stats = {
            "web_contents_processed": 0,
            "embeddings_created": 0,
            "embeddings_stored": 0,
            "text_processing_errors": 0,
            "image_processing_errors": 0
        }
        
        embeddings = []
        
        try:
            # Process web content
            for content in web_contents:
                if not content.success:
                    continue
                
                try:
                    # Process text content
                    embedding = self.content_processor.process_multimodal_content(
                        text=content.text_content,
                        image_input=None  # For now, just process text
                    )
                    
                    if embedding:
                        embeddings.append(embedding)
                        
                        # Store embedding in vector database
                        embedding_data = EmbeddingData(
                            embedding=embedding.vector.tolist(),
                            content=embedding.text_content,
                            source_url=content.url,
                            content_type=embedding.content_type,
                            metadata={
                                "title": content.title,
                                "timestamp": content.timestamp,
                                "query_id": user_query.query_id
                            }
                        )
                        
                        self.vector_db.store(embedding_data)
                        processing_stats["embeddings_stored"] += 1
                        
                    processing_stats["embeddings_created"] += 1
                    processing_stats["web_contents_processed"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to process content from {content.url}: {e}")
                    processing_stats["text_processing_errors"] += 1
            
            logger.info(f"Processed {processing_stats['web_contents_processed']} web contents, created {processing_stats['embeddings_created']} embeddings")
            return embeddings, processing_stats
            
        except Exception as e:
            logger.error(f"Content processing failed: {e}")
            processing_stats["error"] = str(e)
            return embeddings, processing_stats
    
    def _create_query_embedding(self, user_query: UserQuery) -> Optional[CombinedEmbedding]:
        """
        Create embedding for the user query (text + images).
        
        Args:
            user_query: User query object
            
        Returns:
            Combined embedding for the query or None if creation fails
        """
        try:
            # Process user's query with text and images
            query_embedding = self.content_processor.process_multimodal_content(
                text=user_query.text,
                image_input=user_query.images[0] if user_query.images else None
            )
            
            if query_embedding:
                logger.debug("Created query embedding successfully")
            else:
                logger.warning("Failed to create query embedding")
            
            return query_embedding
            
        except Exception as e:
            logger.error(f"Query embedding creation failed: {e}")
            return None
    
    def _search_similar_content(self, query_embedding: Optional[CombinedEmbedding], max_results: int = None) -> List[SearchResult]:
        """
        Search for similar content in the vector database.
        
        Args:
            query_embedding: Query embedding to search with
            max_results: Maximum number of results to return
            
        Returns:
            List of similar search results
        """
        if not query_embedding:
            logger.warning("No query embedding available for similarity search")
            return []
        
        try:
            max_results = max_results or self.config.retrieval.max_concurrent_requests
            
            similar_results = self.vector_db.search(
                query_embedding=query_embedding.vector.tolist(),
                top_k=max_results
            )
            
            logger.info(f"Found {len(similar_results)} similar results")
            return similar_results
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return []
    
    def _generate_response(self, user_query: UserQuery, similar_results: List[SearchResult], enable_fallback: bool = True) -> GeneratedResponse:
        """
        Generate final response using retrieved context.
        
        Args:
            user_query: User query object
            similar_results: List of similar search results
            enable_fallback: Whether to use fallback if no results
            
        Returns:
            Generated response object
        """
        try:
            if similar_results:
                # Generate response with context
                response = self.response_generator.generate_response(user_query.text, similar_results)
                logger.info("Generated response with retrieved context")
            elif enable_fallback:
                # Generate fallback response
                response = self.response_generator.generate_fallback_response(
                    user_query.text, 
                    "No relevant sources found in current database"
                )
                logger.info("Generated fallback response")
            else:
                # Return empty response
                response = GeneratedResponse(
                    answer="I couldn't find relevant information to answer your question.",
                    sources=[],
                    confidence_score=0.0,
                    generation_time=datetime.now().isoformat(),
                    context_used=[],
                    validation_passed=False
                )
                logger.info("Generated empty response (fallback disabled)")
            
            return response
            
        except Exception as e:
            logger.error(f"Response generation failed: {e}")
            
            # Return error response
            return GeneratedResponse(
                answer=f"I encountered an error while generating a response: {str(e)}",
                sources=[],
                confidence_score=0.0,
                generation_time=datetime.now().isoformat(),
                context_used=[],
                validation_passed=False
            )
    
    def _record_pipeline_stats(self, pipeline_stats: Dict[str, Any], 
                              retrieval_stats: Dict[str, Any], 
                              processing_stats: Dict[str, Any], 
                              success: bool):
        """Record pipeline statistics for monitoring."""
        try:
            stats_record = PipelineStats(
                total_time=pipeline_stats.get("total_time", 0),
                retrieval_time=pipeline_stats.get("retrieval_time", 0),
                processing_time=pipeline_stats.get("processing_time", 0),
                generation_time=pipeline_stats.get("generation_time", 0),
                sources_retrieved=retrieval_stats.get("sources_successful", 0),
                embeddings_created=processing_stats.get("embeddings_created", 0),
                similar_results_found=0,  # Will be updated in search phase
                success=success
            )
            
            self.pipeline_stats.append(stats_record)
            
            # Keep only last 100 records to prevent memory issues
            if len(self.pipeline_stats) > 100:
                self.pipeline_stats = self.pipeline_stats[-100:]
                
        except Exception as e:
            logger.error(f"Failed to record pipeline stats: {e}")
    
    def get_pipeline_health(self) -> Dict[str, Any]:
        """
        Get current pipeline health and performance statistics.
        
        Returns:
            Dictionary with health metrics
        """
        try:
            if not self.pipeline_stats:
                return {"status": "no_data", "message": "No pipeline statistics available"}
            
            recent_stats = self.pipeline_stats[-10:]  # Last 10 queries
            
            # Calculate averages
            avg_total_time = sum(s.total_time for s in recent_stats) / len(recent_stats)
            avg_retrieval_time = sum(s.retrieval_time for s in recent_stats) / len(recent_stats)
            avg_processing_time = sum(s.processing_time for s in recent_stats) / len(recent_stats)
            avg_generation_time = sum(s.generation_time for s in recent_stats) / len(recent_stats)
            
            success_rate = sum(1 for s in recent_stats if s.success) / len(recent_stats)
            
            # Get component health
            vector_db_stats = self.vector_db.get_collection_stats()
            
            health_status = {
                "status": "healthy" if success_rate > 0.8 else "degraded" if success_rate > 0.5 else "unhealthy",
                "success_rate": success_rate,
                "average_response_time": avg_total_time,
                "component_times": {
                    "retrieval": avg_retrieval_time,
                    "processing": avg_processing_time,
                    "generation": avg_generation_time
                },
                "vector_db": vector_db_stats,
                "web_retrieval_enabled": self.enable_web_retrieval,
                "total_queries_processed": len(self.pipeline_stats)
            }
            
            return health_status
            
        except Exception as e:
            logger.error(f"Failed to get pipeline health: {e}")
            return {"status": "error", "message": str(e)}
    
    def clear_vector_database(self):
        """Clear all stored embeddings from the vector database."""
        try:
            self.vector_db.clear_collection()
            logger.info("Vector database cleared successfully")
        except Exception as e:
            logger.error(f"Failed to clear vector database: {e}")
            raise
    
    def _cleanup_resources(self):
        """Clean up pipeline resources for memory management."""
        try:
            # Clear old pipeline statistics
            if len(self.pipeline_stats) > 50:
                self.pipeline_stats = self.pipeline_stats[-50:]
            
            # Trigger vector database cleanup if available
            if hasattr(self, 'vector_db') and hasattr(self.vector_db, 'cleanup'):
                self.vector_db.cleanup()
            
            logger.info("Pipeline resources cleaned up")
            
        except Exception as e:
            logger.error(f"Error during resource cleanup: {e}")
    
    def _retrieve_content_with_fallback(self, user_query: UserQuery, max_results: int, 
                                       processing_options: ProcessingOptions, 
                                       fallback_strategies_used: List[str]) -> Tuple[List[WebContent], Dict[str, Any]]:
        """Retrieve content with error handling and fallback strategies."""
        if not processing_options.enable_web_retrieval:
            enhanced_logger.info(
                "Web retrieval disabled by processing options",
                component="rag_pipeline",
                category=LogCategory.WEB_RETRIEVAL
            )
            fallback_strategies_used.append("web_retrieval_disabled")
            return [], {"enabled": False, "reason": "disabled_by_validation"}
        
        try:
            return self._retrieve_content(user_query, max_results)
        except Exception as e:
            enhanced_logger.error(
                "Web retrieval failed, using fallback",
                component="rag_pipeline",
                category=LogCategory.WEB_RETRIEVAL,
                error=e
            )
            fallback_strategies_used.append("web_retrieval_fallback")
            return [], {"enabled": True, "error": str(e), "fallback_used": True}
    
    def _process_content_with_fallback(self, web_contents: List[WebContent], user_query: UserQuery,
                                      processing_options: ProcessingOptions,
                                      fallback_strategies_used: List[str]) -> Tuple[List[CombinedEmbedding], Dict[str, Any]]:
        """Process content with error handling and fallback strategies."""
        try:
            # If image processing is disabled, modify the query
            if not processing_options.enable_image_processing and user_query.images:
                enhanced_logger.info(
                    "Image processing disabled, processing text only",
                    component="rag_pipeline",
                    category=LogCategory.CONTENT_PROCESSING
                )
                fallback_strategies_used.append("text_only_processing")
                # Create a new query without images
                text_only_query = UserQuery(text=user_query.text, images=[])
                return self._process_content(web_contents, text_only_query)
            
            return self._process_content(web_contents, user_query)
            
        except Exception as e:
            enhanced_logger.error(
                "Content processing failed, using minimal processing",
                component="rag_pipeline",
                category=LogCategory.CONTENT_PROCESSING,
                error=e
            )
            fallback_strategies_used.append("minimal_content_processing")
            
            # Minimal fallback: just return empty embeddings
            return [], {"error": str(e), "fallback_used": True}
    
    def _search_with_fallback(self, user_query: UserQuery, max_results: int,
                             processing_options: ProcessingOptions,
                             fallback_strategies_used: List[str]) -> Tuple[Optional[CombinedEmbedding], List[SearchResult]]:
        """Search with error handling and fallback strategies."""
        if not processing_options.enable_context_retrieval:
            enhanced_logger.info(
                "Context retrieval disabled by processing options",
                component="rag_pipeline",
                category=LogCategory.VECTOR_DB
            )
            fallback_strategies_used.append("context_retrieval_disabled")
            return None, []
        
        try:
            query_embedding = self._create_query_embedding(user_query)
            similar_results = self._search_similar_content(query_embedding, max_results)
            return query_embedding, similar_results
            
        except Exception as e:
            enhanced_logger.error(
                "Vector search failed, proceeding without context",
                component="rag_pipeline",
                category=LogCategory.VECTOR_DB,
                error=e
            )
            fallback_strategies_used.append("vector_search_fallback")
            return None, []
    
    def _generate_response_with_fallback(self, user_query: UserQuery, similar_results: List[SearchResult],
                                        processing_options: ProcessingOptions,
                                        fallback_strategies_used: List[str]) -> GeneratedResponse:
        """Generate response with error handling and fallback strategies."""
        try:
            if similar_results:
                # Generate response with context
                response = self.response_generator.generate_response(user_query.text, similar_results)
                enhanced_logger.info(
                    "Generated response with retrieved context",
                    component="rag_pipeline",
                    category=LogCategory.RESPONSE_GENERATION
                )
                return response
            elif processing_options.fallback_to_simple_response:
                # Generate fallback response
                response = self.response_generator.generate_fallback_response(
                    user_query.text, 
                    "No relevant sources found in current database"
                )
                fallback_strategies_used.append("simple_response_fallback")
                enhanced_logger.info(
                    "Generated fallback response",
                    component="rag_pipeline",
                    category=LogCategory.RESPONSE_GENERATION
                )
                return response
            else:
                # Return minimal response
                fallback_strategies_used.append("minimal_response")
                return GeneratedResponse(
                    answer="I couldn't find relevant information to answer your question.",
                    sources=[],
                    confidence_score=0.0,
                    generation_time=datetime.now().isoformat(),
                    context_used=[],
                    validation_passed=False
                )
            
        except Exception as e:
            enhanced_logger.error(
                "Response generation failed, using error response",
                component="rag_pipeline",
                category=LogCategory.RESPONSE_GENERATION,
                error=e
            )
            fallback_strategies_used.append("error_response")
            
            # Return error response
            return GeneratedResponse(
                answer=f"I encountered an error while generating a response. Please try rephrasing your question.",
                sources=[],
                confidence_score=0.0,
                generation_time=datetime.now().isoformat(),
                context_used=[],
                validation_passed=False
            )
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status including health, validation stats, and pipeline metrics.
        
        Returns:
            Dictionary with complete system status information
        """
        try:
            # Get pipeline health
            pipeline_health = self.get_pipeline_health()
            
            # Get validation statistics
            validation_stats = validation_manager.get_validation_statistics()
            
            # Get system health
            system_health = health_monitor.get_current_health()
            
            # Get resource usage
            resource_stats = resource_manager.get_resource_stats()
            
            # Get configuration status
            config = config_manager.get_config()
            
            return {
                "timestamp": datetime.now().isoformat(),
                "pipeline_health": pipeline_health,
                "validation_statistics": validation_stats,
                "system_health": system_health.to_dict() if system_health else None,
                "resource_usage": resource_stats,
                "configuration": {
                    "web_retrieval_enabled": self.enable_web_retrieval,
                    "max_concurrent_requests": config.retrieval.max_concurrent_requests,
                    "max_retrieval_time": config.retrieval.max_retrieval_time
                },
                "component_status": component_error_handler.get_component_status()
            }
            
        except Exception as e:
            enhanced_logger.error(
                "Failed to get system status",
                component="rag_pipeline",
                category=LogCategory.SYSTEM,
                error=e
            )
            
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def close(self):
        """Clean up pipeline resources."""
        try:
            if hasattr(self, 'vector_db'):
                self.vector_db.close()
            enhanced_logger.info(
                "RAG Pipeline closed successfully",
                component="rag_pipeline",
                category=LogCategory.SYSTEM
            )
        except Exception as e:
            enhanced_logger.error(
                "Error closing pipeline",
                component="rag_pipeline",
                category=LogCategory.ERROR_HANDLING,
                error=e
            )


# Utility function for easy pipeline creation
def create_rag_pipeline(vector_db_path: str = None, 
                       openai_api_key: str = None,
                       enable_web_retrieval: bool = True) -> RAGPipeline:
    """
    Factory function to create a RAG Pipeline instance.
    
    Args:
        vector_db_path: Path for vector database storage
        openai_api_key: OpenAI API key for response generation
        enable_web_retrieval: Whether to enable live web retrieval
        
    Returns:
        RAGPipeline: Initialized pipeline instance
    """
    return RAGPipeline(
        vector_db_path=vector_db_path,
        openai_api_key=openai_api_key,
        enable_web_retrieval=enable_web_retrieval
    )
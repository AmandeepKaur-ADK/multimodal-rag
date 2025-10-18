"""
Free Web Interface for the RAG Pipeline using Streamlit.
Uses Hugging Face models - NO OpenAI API key required!
"""

import sys
import os
import time
from datetime import datetime

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False

from src.free_rag_pipeline import create_free_rag_pipeline
from src.validation_manager import validation_manager


def main():
    """Main Streamlit application."""
    
    if not STREAMLIT_AVAILABLE:
        print("❌ Streamlit not installed. Install with: pip install streamlit")
        print("💡 Or run the command line demo: python examples/free_rag_demo.py")
        return
    
    # Page configuration
    st.set_page_config(
        page_title="Free RAG Pipeline",
        page_icon="🆓",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Title and description
    st.title("🆓 Free RAG Pipeline")
    st.markdown("### Powered by Hugging Face Models - No API Keys Required!")
    
    # Sidebar configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Model selection
        model_options = {
            "microsoft/DialoGPT-small": "Fast & Lightweight",
            "gpt2": "Classic GPT-2",
            "distilgpt2": "Distilled GPT-2 (Faster)"
        }
        
        selected_model = st.selectbox(
            "Choose Model:",
            options=list(model_options.keys()),
            format_func=lambda x: f"{x.split('/')[-1]} - {model_options[x]}",
            index=0
        )
        
        # Other options
        enable_web_retrieval = st.checkbox("Enable Web Retrieval", value=False, 
                                         help="Enable to search the web for current information")
        
        max_results = st.slider("Max Results", min_value=1, max_value=10, value=3)
        
        # System status
        st.header("📊 System Status")
        
        # Check system readiness
        is_ready, warnings, critical_issues = validation_manager.check_system_readiness()
        
        if is_ready:
            st.success("✅ System Ready")
        else:
            st.error("❌ System Issues")
            for issue in critical_issues[:2]:
                st.error(f"• {issue}")
        
        if warnings:
            for warning in warnings[:2]:
                st.warning(f"⚠️ {warning}")
    
    # Initialize pipeline
    @st.cache_resource
    def get_pipeline(model_name, web_retrieval):
        """Initialize and cache the pipeline."""
        with st.spinner(f"Loading {model_name}..."):
            return create_free_rag_pipeline(
                model_name=model_name,
                enable_web_retrieval=web_retrieval
            )
    
    try:
        pipeline = get_pipeline(selected_model, enable_web_retrieval)
        
        # Main interface
        st.header("💬 Ask Your Question")
        
        # Query input
        query = st.text_area(
            "Enter your question:",
            placeholder="What is artificial intelligence?",
            height=100
        )
        
        # Image upload (optional)
        uploaded_file = st.file_uploader(
            "Upload an image (optional):",
            type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
            help="Upload an image to ask questions about it"
        )
        
        # Process button
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            process_button = st.button("🚀 Process Query", type="primary", use_container_width=True)
        
        # Process query
        if process_button and query.strip():
            
            # Prepare images
            images = []
            if uploaded_file is not None:
                try:
                    from PIL import Image
                    image = Image.open(uploaded_file)
                    images = [image]
                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")
            
            # Show processing status
            with st.spinner("🔄 Processing your query..."):
                start_time = time.time()
                
                # Process the query
                result = pipeline.process_query(
                    text=query,
                    images=images,
                    max_results=max_results,
                    request_id=f"web_{int(time.time())}"
                )
                
                processing_time = time.time() - start_time
            
            # Display results
            st.header("📝 Results")
            
            if result.success:
                # Success case
                st.success(f"✅ Query processed successfully in {processing_time:.2f}s")
                
                # Answer
                st.subheader("💡 Answer")
                st.write(result.response.answer)
                
                # Metadata
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("🎯 Confidence", f"{result.response.confidence_score:.2%}")
                
                with col2:
                    st.metric("🤖 Model", result.response.model_used.split('/')[-1])
                
                with col3:
                    st.metric("⏱️ Time", f"{processing_time:.2f}s")
                
                # Sources (if any)
                if result.response.sources:
                    st.subheader("📚 Sources")
                    for i, source in enumerate(result.response.sources, 1):
                        with st.expander(f"Source {i}: {source.get('url', 'Unknown')}"):
                            st.write(f"**Type:** {source.get('content_type', 'Unknown')}")
                            st.write(f"**Similarity:** {source.get('similarity_score', 0):.2%}")
                            st.write(f"**Excerpt:** {source.get('excerpt', 'No excerpt available')}")
                
                # Warnings and fallbacks
                if result.warnings:
                    st.subheader("⚠️ Warnings")
                    for warning in result.warnings:
                        st.warning(warning)
                
                if result.fallback_strategies_used:
                    st.subheader("🔄 Fallback Strategies Used")
                    for strategy in result.fallback_strategies_used:
                        st.info(f"• {strategy.replace('_', ' ').title()}")
                
                # Detailed stats (expandable)
                with st.expander("📊 Detailed Statistics"):
                    st.json({
                        "Pipeline Stats": result.pipeline_stats,
                        "Retrieval Stats": result.retrieval_stats,
                        "Processing Stats": result.processing_stats
                    })
            
            else:
                # Error case
                st.error(f"❌ Query processing failed")
                st.error(f"**Error:** {result.error_message}")
                
                # Validation details
                if result.validation_report and not result.validation_report.is_valid:
                    st.subheader("📋 Validation Issues")
                    
                    for error in result.validation_report.errors:
                        st.error(f"**{error.error_id}:** {error.user_message}")
                    
                    if result.validation_report.recommendations:
                        st.subheader("💡 Suggestions")
                        for rec in result.validation_report.recommendations:
                            st.info(f"• {rec}")
        
        elif process_button and not query.strip():
            st.warning("⚠️ Please enter a question to process.")
        
        # Example queries
        st.header("💡 Example Queries")
        
        example_queries = [
            "What is artificial intelligence?",
            "How does machine learning work?",
            "Explain neural networks in simple terms",
            "What are the benefits of renewable energy?",
            "How do computers process information?"
        ]
        
        cols = st.columns(len(example_queries))
        
        for i, example in enumerate(example_queries):
            with cols[i]:
                if st.button(f"📝 {example[:20]}...", key=f"example_{i}"):
                    st.rerun()
        
        # Footer
        st.markdown("---")
        st.markdown(
            """
            <div style='text-align: center; color: #666;'>
                🆓 <strong>Free RAG Pipeline</strong> - No API keys required!<br>
                Powered by Hugging Face 🤗 | Built with Streamlit ⚡
            </div>
            """,
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.error(f"❌ Failed to initialize pipeline: {str(e)}")
        st.info("💡 Try running: python examples/free_rag_demo.py")


if __name__ == "__main__":
    if STREAMLIT_AVAILABLE:
        main()
    else:
        print("❌ Streamlit not installed.")
        print("📦 Install with: pip install streamlit")
        print("🚀 Then run: streamlit run examples/free_web_demo.py")
        print("💡 Or use the command line demo: python examples/free_rag_demo.py")
# Multimodal RAG Pipeline - Execution Guide

This guide shows you how to set up and run the multimodal RAG pipeline project.

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Clone or navigate to the project directory
cd multimodal-rag-demo

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
copy .env.example .env

# Edit .env file with your settings
# Required: Add your OpenAI API key
```

**Important**: Edit the `.env` file and add your OpenAI API key:
```
OPENAI_API_KEY=your-actual-openai-api-key-here
```

### 3. Create Required Directories

```bash
# Create data and log directories
mkdir data\vector_db
mkdir logs
```

### 4. Run the Pipeline

```bash
# Run the main pipeline
python main.py
```

## 📋 Detailed Setup Steps

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (get one at https://platform.openai.com/api-keys)
- Internet connection for web retrieval

### Installation

1. **Install Python Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

   This installs:
   - `openai` - For response generation
   - `requests` - For web scraping
   - `beautifulsoup4` - For HTML parsing
   - `sentence-transformers` - For text embeddings
   - `chromadb` - For vector database
   - `pillow` - For image processing
   - `transformers` - For multimodal embeddings
   - `pytest` - For testing

2. **Environment Configuration**
   
   Copy `.env.example` to `.env`:
   ```bash
   copy .env.example .env
   ```
   
   Edit `.env` with your settings:
   ```env
   # Required
   OPENAI_API_KEY=sk-your-openai-api-key-here
   
   # Optional (defaults provided)
   MAX_RETRIEVAL_TIME=30
   MAX_CONCURRENT_REQUESTS=5
   REQUEST_TIMEOUT=10
   VECTOR_DB_PATH=./data/vector_db
   TOP_K_RESULTS=5
   MAX_RESPONSE_LENGTH=1000
   TEMPERATURE=0.7
   LOG_LEVEL=INFO
   ```

## 🎯 Running Different Components

### 1. Full Pipeline (Recommended)

```bash
python main.py
```

This runs the complete interactive pipeline where you can:
- Ask questions and get AI-generated responses
- Automatically retrieve web content
- Store and search embeddings
- Get responses with source citations

### 2. Individual Component Examples

#### Vector Database Example
```bash
python examples/vector_db_example.py
```

#### Content Processor Example
```bash
python examples/content_processor_example.py
```

#### Response Generator Example
```bash
python examples/response_generator_example.py
```

### 3. Running Tests

```bash
# Run all tests
python -m pytest

# Run specific component tests
python -m pytest tests/test_vector_db.py
python -m pytest tests/test_content_processor.py
python -m pytest tests/test_response_generator.py

# Run with verbose output
python -m pytest -v
```

## 💡 Usage Examples

### Interactive Mode

When you run `python main.py`, you'll get an interactive prompt:

```
💬 Your question: What are the latest developments in AI?

🔄 Processing: What are the latest developments in AI?
----------------------------------------

📝 Answer:
Based on recent web sources, artificial intelligence has seen significant advances in 2024 [Source 1]. Key developments include improvements in large language models, better multimodal capabilities, and more efficient training methods [Source 2].

**Sources:**
1. [https://example.com/ai-news](https://example.com/ai-news) - text content (Retrieved: 2024-01-15 10:30)
2. [https://example.com/ml-research](https://example.com/ml-research) - text content (Retrieved: 2024-01-14 15:20)

📈 Metadata:
  • Confidence: 0.85
  • Sources used: 2
  • Content retrieved: 3
```

### Programmatic Usage

```python
from main import MultimodalRAGPipeline

# Initialize pipeline
pipeline = MultimodalRAGPipeline()

# Process a query
result = pipeline.process_query("How does renewable energy work?")

print(result['answer'])
print(f"Confidence: {result['confidence']}")
print(f"Sources: {len(result['sources'])}")
```

### Using Specific URLs

```python
# Process query with specific URLs
urls = [
    "https://example.com/renewable-energy",
    "https://example.com/solar-power"
]

result = pipeline.process_query(
    "How does solar energy work?", 
    urls=urls
)
```

## 🔧 Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | None |
| `MAX_RETRIEVAL_TIME` | Max time for web retrieval (seconds) | 30 |
| `MAX_CONCURRENT_REQUESTS` | Concurrent web requests | 5 |
| `REQUEST_TIMEOUT` | Request timeout (seconds) | 10 |
| `VECTOR_DB_PATH` | Vector database storage path | ./data/vector_db |
| `EMBEDDING_DIMENSION` | Embedding vector dimension | 384 |
| `TOP_K_RESULTS` | Number of search results | 5 |
| `MAX_TEXT_LENGTH` | Max text length to process | 10000 |
| `MAX_RESPONSE_LENGTH` | Max response length | 1000 |
| `TEMPERATURE` | AI response creativity (0-1) | 0.7 |
| `LOG_LEVEL` | Logging level | INFO |

### Domain Filtering

```env
# Allow only specific domains (comma-separated)
ALLOWED_DOMAINS=wikipedia.org,arxiv.org,github.com

# Block specific domains (comma-separated)
BLOCKED_DOMAINS=spam-site.com,malicious-site.org
```

## 🐛 Troubleshooting

### Common Issues

1. **"OpenAI API key not set"**
   - Make sure you've copied `.env.example` to `.env`
   - Add your actual OpenAI API key to the `.env` file

2. **"Module not found" errors**
   - Make sure you've installed dependencies: `pip install -r requirements.txt`
   - Activate your virtual environment if using one

3. **"Permission denied" or file errors**
   - Make sure the `data/vector_db` and `logs` directories exist
   - Check file permissions in the project directory

4. **Web retrieval fails**
   - Check your internet connection
   - Some websites may block automated requests
   - Try with different URLs or queries

5. **Low response quality**
   - Increase `TOP_K_RESULTS` to use more sources
   - Adjust `TEMPERATURE` (lower = more focused, higher = more creative)
   - Check that relevant content was actually retrieved

### Debug Mode

Enable debug logging:
```env
LOG_LEVEL=DEBUG
```

This will show detailed information about:
- Web retrieval process
- Content processing steps
- Embedding generation
- Vector database operations
- Response generation

### Performance Tips

1. **Faster startup**: The first run downloads ML models, subsequent runs are faster
2. **Better results**: Use specific, focused queries
3. **Resource usage**: Adjust `MAX_CONCURRENT_REQUESTS` based on your system
4. **Storage**: Vector database grows over time, clear it periodically if needed

## 📊 Monitoring

### Pipeline Statistics

```python
pipeline = MultimodalRAGPipeline()
stats = pipeline.get_stats()
print(stats)
```

### Logs

Check the log file for detailed execution information:
```bash
# View recent logs
tail -f logs/rag_pipeline.log

# Search for errors
grep ERROR logs/rag_pipeline.log
```

## 🔄 Next Steps

1. **Customize for your use case**: Modify the pipeline components
2. **Add new data sources**: Extend the web retriever
3. **Improve embeddings**: Experiment with different models
4. **Scale up**: Add caching, async processing, or API endpoints
5. **Deploy**: Package as a web service or desktop application

## 📚 Component Documentation

- **Web Retriever**: Fetches content from URLs and search results
- **Content Processor**: Handles text/image processing and embedding generation
- **Vector Database**: Stores and searches embeddings using ChromaDB
- **Response Generator**: Creates AI responses with source citations

Each component can be used independently or as part of the full pipeline.
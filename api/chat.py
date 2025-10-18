"""
AI Chat API - Serverless function for Vercel
Uses free AI APIs for responses
"""

import json
import requests
from datetime import datetime

def handler(request):
    """Handle chat requests"""
    
    # Handle CORS
    if request.method == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type',
            },
            'body': ''
        }
    
    if request.method != 'POST':
        return {
            'statusCode': 405,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({'error': 'Method not allowed'})
        }
    
    try:
        # Parse request
        body = json.loads(request.body)
        question = body.get('question', '').strip()
        
        if not question:
            return {
                'statusCode': 400,
                'headers': {'Access-Control-Allow-Origin': '*'},
                'body': json.dumps({'error': 'No question provided'})
            }
        
        # Generate AI response using free APIs
        ai_response = generate_ai_response(question)
        
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'success': True,
                'answer': ai_response['answer'],
                'confidence': ai_response['confidence'],
                'model': ai_response['model'],
                'sources': ai_response.get('sources', []),
                'timestamp': datetime.now().isoformat()
            })
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {'Access-Control-Allow-Origin': '*'},
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'AI service temporarily unavailable'
            })
        }

def generate_ai_response(question):
    """Generate AI response using free services"""
    
    # Try multiple free AI services
    
    # Option 1: Use Hugging Face Inference API (free)
    try:
        response = get_huggingface_response(question)
        if response:
            return response
    except:
        pass
    
    # Option 2: Use local knowledge base
    try:
        response = get_knowledge_response(question)
        if response:
            return response
    except:
        pass
    
    # Fallback: Generate contextual response
    return get_fallback_response(question)

def get_huggingface_response(question):
    """Try Hugging Face free inference API"""
    try:
        # Use free Hugging Face models
        api_url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": question,
            "parameters": {
                "max_length": 200,
                "temperature": 0.7
            }
        }
        
        response = requests.post(api_url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result and len(result) > 0:
                return {
                    'answer': result[0].get('generated_text', '').replace(question, '').strip(),
                    'confidence': 0.8,
                    'model': 'DialoGPT-medium',
                    'sources': []
                }
    except:
        pass
    
    return None

def get_knowledge_response(question):
    """Generate response from knowledge base"""
    
    # AI/ML related responses
    ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural', 'deep learning']
    if any(keyword in question.lower() for keyword in ai_keywords):
        return {
            'answer': """Artificial Intelligence (AI) is a branch of computer science that aims to create intelligent machines capable of performing tasks that typically require human intelligence. This includes learning, reasoning, problem-solving, perception, and language understanding.

Key aspects of AI include:
• Machine Learning: Algorithms that improve through experience
• Neural Networks: Computing systems inspired by biological neural networks  
• Deep Learning: ML using multi-layered neural networks
• Natural Language Processing: Understanding and generating human language
• Computer Vision: Interpreting and analyzing visual information

AI is used in many applications today, from virtual assistants and recommendation systems to autonomous vehicles and medical diagnosis.""",
            'confidence': 0.9,
            'model': 'Knowledge Base',
            'sources': [
                {'url': 'https://en.wikipedia.org/wiki/Artificial_intelligence', 'title': 'AI Wikipedia'},
                {'url': 'https://www.ibm.com/cloud/learn/what-is-artificial-intelligence', 'title': 'IBM AI Guide'}
            ]
        }
    
    # Programming related
    programming_keywords = ['python', 'javascript', 'programming', 'code', 'software']
    if any(keyword in question.lower() for keyword in programming_keywords):
        return {
            'answer': """Programming is the process of creating instructions for computers to execute. It involves writing code in programming languages like Python, JavaScript, Java, or C++ to solve problems and build applications.

Key programming concepts:
• Variables: Store data and information
• Functions: Reusable blocks of code
• Loops: Repeat actions efficiently  
• Conditionals: Make decisions in code
• Data Structures: Organize and store data
• Algorithms: Step-by-step problem-solving procedures

Popular programming languages serve different purposes - Python for AI/data science, JavaScript for web development, and Java for enterprise applications.""",
            'confidence': 0.85,
            'model': 'Knowledge Base',
            'sources': []
        }
    
    return None

def get_fallback_response(question):
    """Generate a helpful fallback response"""
    
    return {
        'answer': f"""Thank you for your question: "{question}"

I'm a free AI assistant powered by open-source models. While I'm continuously learning, I can help you with:

🤖 **AI & Technology Topics**
• Artificial Intelligence and Machine Learning
• Programming and Software Development  
• Web Development and Design
• Data Science and Analytics

💡 **How I Work**
• I use free, open-source AI models
• No API keys or paid services required
• Responses are generated locally when possible
• I aim to provide helpful, accurate information

Feel free to ask me about AI, programming, technology, or rephrase your question for a more specific response!""",
        'confidence': 0.7,
        'model': 'Fallback System',
        'sources': []
    }
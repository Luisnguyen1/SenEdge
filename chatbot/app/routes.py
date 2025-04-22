from flask import Blueprint, render_template, request, jsonify
from datetime import datetime
from app.models.rag_model import RAGChatbot
import time
import os

# Create blueprints
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

# Initialize RAG Chatbot (lazy loading)
chatbot = None

def get_chatbot():
    global chatbot
    if chatbot is None:
        print("Initializing RAG Chatbot...")
        chatbot = RAGChatbot()
    return chatbot

@main_bp.route('/')
def index():
    current_time = datetime.now().strftime("%H:%M")
    return render_template('index.html', current_time=current_time)

@api_bp.route('/chat', methods=['POST'])
def chat():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    query = data.get('query', '')
    
    if not query:
        return jsonify({"error": "Query is required"}), 400
    
    start_time = time.time()
    
    # Get RAG Chatbot instance and process query
    rag = get_chatbot()
    response = rag.get_response(query)
    
    processing_time = time.time() - start_time
    
    return jsonify({
        "query": query,
        "response": response,
        "success": True,
        "processing_time_ms": round(processing_time * 1000)
    })

@api_bp.route('/health', methods=['GET'])
def health_check():
    # Check if Gemini API key is set
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    gemini_available = bool(gemini_api_key)
    
    # Check if MongoDB is connected
    rag = get_chatbot()
    mongodb_connected = rag.mongo_connected
    model_initialized = rag.model_initialized
    
    return jsonify({
        "status": "ok",
        "services": {
            "mongodb": "connected" if mongodb_connected else "disconnected",
            "embedding_model": "initialized" if model_initialized else "not_initialized",
            "gemini": "available" if gemini_available else "not_available"
        }
    })

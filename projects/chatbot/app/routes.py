from flask import Blueprint, render_template, request, jsonify, send_file
from datetime import datetime
from app.models.rag_model import RAGChatbot
import time
import os
import json
from werkzeug.utils import secure_filename
import tempfile
import uuid

# Create blueprints
main_bp = Blueprint('main', __name__)
api_bp = Blueprint('api', __name__)

# Initialize RAG Chatbot (lazy loading)
chatbot = None

# File upload configuration
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'jpg', 'jpeg', 'png', 'gif'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    try:
        # Handle both JSON and form data (for file uploads)
        if request.is_json:
            data = request.get_json()
            query = data.get('query', '')
            style = data.get('style', 'friendly')
            length = data.get('length', 'medium')
            language = data.get('language', 'vi')
            files = []
        else:
            # Handle form data with files
            query = request.form.get('query', '')
            style = request.form.get('style', 'friendly')
            length = request.form.get('length', 'medium')
            language = request.form.get('language', 'vi')
            files = []
            
            # Process uploaded files
            for key in request.files:
                if key.startswith('file_'):
                    file = request.files[key]
                    if file and file.filename and allowed_file(file.filename):
                        if len(file.read()) <= MAX_FILE_SIZE:
                            file.seek(0)  # Reset file pointer
                            files.append({
                                'filename': secure_filename(file.filename),
                                'content': file.read(),
                                'content_type': file.content_type
                            })
                        else:
                            return jsonify({
                                "error": f"File {file.filename} is too large (max 10MB)",
                                "success": False
                            }), 400
        
        if not query and not files:
            return jsonify({
                "error": "Query or files are required",
                "success": False
            }), 400
        
        start_time = time.time()
        
        # Get RAG Chatbot instance
        rag = get_chatbot()
        
        # Process files if any
        file_context = ""
        if files:
            file_context = process_uploaded_files(files)
            if file_context:
                query = f"Based on the uploaded files:\n{file_context}\n\nUser question: {query}" if query else f"Please analyze these uploaded files:\n{file_context}"
        
        # Customize prompt based on style and length
        customized_query = customize_prompt(query, style, length, language)
        
        # Get response from RAG model
        response_data = rag.get_response(customized_query)
        
        # Handle both old format (string) and new format (dict)
        if isinstance(response_data, dict):
            response = response_data.get("response", "")
            navigation = response_data.get("navigation")
            product_images = response_data.get("product_images", [])
        else:
            # Backward compatibility - old format returns string
            response = response_data
            navigation = None
            product_images = []
        
        processing_time = time.time() - start_time
        
        # Generate quick replies based on response
        quick_replies = generate_quick_replies(response, language)
        
        result = {
            "query": query,
            "response": response,
            "success": True,
            "processing_time_ms": round(processing_time * 1000),
            "quick_replies": quick_replies,
            "files_processed": len(files)
        }
        
        # Add navigation info if available
        if navigation:
            result["navigation"] = navigation
            
        # Add product images if available
        if product_images:
            result["product_images"] = product_images
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "success": False,
            "details": str(e) if os.getenv('DEBUG') else None
        }), 500

def process_uploaded_files(files):
    """Process uploaded files and extract text content"""
    file_contents = []
    
    for file_data in files:
        filename = file_data['filename']
        content = file_data['content']
        content_type = file_data['content_type']
        
        try:
            if content_type.startswith('text/'):
                # Text files
                text_content = content.decode('utf-8')
                file_contents.append(f"File: {filename}\nContent:\n{text_content}")
            elif content_type.startswith('image/'):
                # For images, just note that an image was uploaded
                file_contents.append(f"Image file: {filename} (Image analysis not yet implemented)")
            else:
                file_contents.append(f"File: {filename} (Content type: {content_type})")
        except Exception as e:
            file_contents.append(f"File: {filename} (Error reading file: {str(e)})")
    
    return "\n\n".join(file_contents)

def customize_prompt(query, style, length, language):
    """Customize the prompt based on user preferences"""
    style_prompts = {
        'friendly': 'Please respond in a friendly and conversational tone.',
        'professional': 'Please respond in a professional and formal tone.',
        'casual': 'Please respond in a casual and relaxed tone.',
        'technical': 'Please respond with technical details and precision.'
    }
    
    length_prompts = {
        'short': 'Keep your response brief and to the point.',
        'medium': 'Provide a balanced response with adequate detail.',
        'detailed': 'Provide a comprehensive and detailed response.'
    }
    
    language_prompts = {
        'vi': 'Please respond in Vietnamese.',
        'en': 'Please respond in English.'
    }
    
    customizations = []
    if style in style_prompts:
        customizations.append(style_prompts[style])
    if length in length_prompts:
        customizations.append(length_prompts[length])
    if language in language_prompts:
        customizations.append(language_prompts[language])
    
    if customizations:
        customization_text = " ".join(customizations)
        return f"{customization_text}\n\nUser question: {query}"
    
    return query

def generate_quick_replies(response, language='vi'):
    """Generate contextual quick reply suggestions"""
    if language == 'vi':
        quick_replies = ['Tiếp tục', 'Giải thích thêm', 'Ví dụ khác', 'Tóm tắt']
    else:
        quick_replies = ['Continue', 'Explain more', 'Another example', 'Summarize']
    
    # Add contextual replies based on response content
    if 'code' in response.lower() or '```' in response:
        if language == 'vi':
            quick_replies.extend(['Chạy thử code', 'Giải thích code'])
        else:
            quick_replies.extend(['Test the code', 'Explain the code'])
    
    return quick_replies[:4]  # Limit to 4 quick replies

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

@api_bp.route('/sessions', methods=['GET'])
def get_sessions():
    """Get user chat sessions"""
    # In a real app, this would be user-specific and stored in database
    return jsonify({
        "sessions": [],
        "success": True
    })

@api_bp.route('/sessions', methods=['POST'])
def create_session():
    """Create a new chat session"""
    data = request.get_json()
    session_id = str(uuid.uuid4())
    
    return jsonify({
        "session_id": session_id,
        "success": True
    })

@api_bp.route('/export/<format>', methods=['POST'])
def export_chat(format):
    """Export chat history in different formats"""
    try:
        data = request.get_json()
        messages = data.get('messages', [])
        
        if format == 'txt':
            content = "\n\n".join([
                f"[{msg.get('timestamp', '')}] {msg.get('sender', '').title()}: {msg.get('text', '')}"
                for msg in messages
            ])
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
            temp_file.write(content)
            temp_file.close()
            
            return send_file(
                temp_file.name,
                as_attachment=True,
                download_name=f'chat-export-{datetime.now().strftime("%Y%m%d-%H%M%S")}.txt',
                mimetype='text/plain'
            )
        
        elif format == 'json':
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8')
            json.dump({
                'export_date': datetime.now().isoformat(),
                'messages': messages
            }, temp_file, ensure_ascii=False, indent=2)
            temp_file.close()
            
            return send_file(
                temp_file.name,
                as_attachment=True,
                download_name=f'chat-export-{datetime.now().strftime("%Y%m%d-%H%M%S")}.json',
                mimetype='application/json'
            )
        
        else:
            return jsonify({
                "error": "Unsupported export format",
                "success": False
            }), 400
            
    except Exception as e:
        return jsonify({
            "error": "Export failed",
            "success": False,
            "details": str(e)
        }), 500

@api_bp.route('/analytics', methods=['GET'])
def get_analytics():
    """Get chat analytics and statistics"""
    return jsonify({
        "total_conversations": 0,
        "total_messages": 0,
        "avg_response_time": 0,
        "popular_topics": [],
        "success": True
    })

@api_bp.route('/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback"""
    data = request.get_json()
    feedback = data.get('feedback', '')
    rating = data.get('rating', 0)
    
    # In a real app, store this feedback in database
    print(f"Feedback received: {feedback}, Rating: {rating}")
    
    return jsonify({
        "message": "Feedback submitted successfully",
        "success": True
    })

@api_bp.route('/suggestions', methods=['GET'])
def get_suggestions():
    """Get suggested prompts based on context"""
    category = request.args.get('category', 'general')
    language = request.args.get('language', 'vi')
    
    suggestions_db = {
        'vi': {
            'general': [
                'Giải thích về trí tuệ nhân tạo',
                'Viết một bài thơ về mùa xuân',
                'Tạo danh sách công việc hàng ngày',
                'Phân tích xu hướng công nghệ 2024'
            ],
            'code': [
                'Viết hàm Python để sắp xếp mảng',
                'Tạo API REST với Flask',
                'Debugging JavaScript code',
                'Tối ưu hiệu suất SQL query'
            ],
            'translate': [
                'Dịch đoạn văn này sang tiếng Anh',
                'Giải thích cách dùng từ này',
                'Tìm từ đồng nghĩa',
                'Kiểm tra ngữ pháp'
            ]
        },
        'en': {
            'general': [
                'Explain artificial intelligence',
                'Write a poem about spring',
                'Create a daily todo list',
                'Analyze tech trends 2024'
            ],
            'code': [
                'Write Python function to sort array',
                'Create REST API with Flask',
                'Debug JavaScript code',
                'Optimize SQL query performance'
            ],
            'translate': [
                'Translate this text to Vietnamese',
                'Explain word usage',
                'Find synonyms',
                'Check grammar'
            ]
        }
    }
    
    suggestions = suggestions_db.get(language, {}).get(category, [])
    
    return jsonify({
        "suggestions": suggestions,
        "success": True
    })

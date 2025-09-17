#!/usr/bin/env python3
"""
Professional Dashboard for Chat Bot, Indoor Navigation, and Security System
Built with Flask and Three.js for real-time monitoring and analytics
"""

from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_from_directory
from flask_cors import CORS
from datetime import datetime, timedelta
import random
import logging
from typing import Dict, Any, List
import sqlite3
import functools
import os
import base64
from werkzeug.utils import secure_filename

# Firebase imports
import firebase_admin
from firebase_admin import credentials, messaging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
app.config['DATABASE'] = 'dashboard.db'
app.config['USERNAME'] = 'sgteam'
app.config['PASSWORD'] = 'quyetthang'

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=12)

# Upload configuration
app.config['UPLOAD_FOLDER'] = 'uploads/navigation'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Create upload directory if not exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize Firebase Admin SDK
try:
    # Load Firebase service account from JSON file
    firebase_config_path = 'iot-challenge-2025.json'
    if os.path.exists(firebase_config_path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(firebase_config_path)
            firebase_admin.initialize_app(cred)
            logger.info("✅ Firebase Admin SDK initialized successfully")
            firebase_initialized = True
        else:
            firebase_initialized = True
            logger.info("🔄 Firebase Admin SDK already initialized")
    else:
        logger.error("❌ Firebase config file not found: iot-challenge-2025.json")
        firebase_initialized = False
        
except Exception as e:
    logger.error(f"❌ Error initializing Firebase: {e}")
    firebase_initialized = False

class DatabaseManager:
    """Handles all database operations"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Chat bot metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chatbot_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    active_users INTEGER,
                    conversations INTEGER,
                    avg_response_time REAL,
                    intent_accuracy REAL,
                    sentiment_score REAL
                )
            ''')
            
            # Indoor navigation metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS navigation_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    navigation_requests INTEGER,
                    accuracy REAL,
                    completion_rate REAL,
                    avg_duration REAL
                )
            ''')
            
            # Security metrics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS security_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    alerts_count INTEGER,
                    access_attempts INTEGER,
                    breach_detections INTEGER,
                    camera_status REAL
                )
            ''')
            
            # Glass break events
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS glass_break_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    device_id TEXT,
                    location TEXT,
                    severity TEXT,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            # FCM Tokens table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS fcm_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    token TEXT UNIQUE NOT NULL,
                    user_agent TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Navigation images table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS navigation_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    location TEXT,
                    image_path TEXT NOT NULL,
                    image_name TEXT NOT NULL,
                    image_size INTEGER,
                    processed_data TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active'
                )
            ''')
            
            conn.commit()
    
    def insert_metric(self, table: str, data: Dict[str, Any]):
        """Insert metric data into specified table"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            columns = ', '.join(data.keys())
            placeholders = ', '.join(['?' for _ in data])
            query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
            cursor.execute(query, list(data.values()))
            conn.commit()
    
    def get_recent_metrics(self, table: str, hours: int = 24) -> List[Dict]:
        """Get recent metrics from specified table"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            query = f"""
                SELECT * FROM {table}
                WHERE timestamp >= datetime('now', '-{hours} hours')
                ORDER BY timestamp DESC
            """
            return [dict(row) for row in cursor.execute(query).fetchall()]

# Initialize database manager
db_manager = DatabaseManager(app.config['DATABASE'])

def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(view):
    """Decorator to ensure user is logged in before accessing views"""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return view(**kwargs)
    return wrapped_view

class MetricsGenerator:
    """Generates realistic sample data for dashboard"""
    
    @staticmethod
    def generate_chatbot_metrics() -> Dict[str, Any]:
        return {
            'active_users': random.randint(50, 200),
            'conversations': random.randint(100, 500),
            'avg_response_time': round(random.uniform(0.5, 3.0), 2),
            'intent_accuracy': round(random.uniform(0.85, 0.98), 3),
            'sentiment_score': round(random.uniform(0.6, 0.9), 2)
        }
    
    @staticmethod
    def generate_navigation_metrics() -> Dict[str, Any]:
        return {
            'navigation_requests': random.randint(20, 100),
            'accuracy': round(random.uniform(0.88, 0.99), 3),
            'completion_rate': round(random.uniform(0.82, 0.96), 3),
            'avg_duration': round(random.uniform(30, 180), 1)
        }
    
    @staticmethod
    def generate_security_metrics() -> Dict[str, Any]:
        return {
            'alerts_count': random.randint(0, 15),
            'access_attempts': random.randint(50, 300),
            'breach_detections': random.randint(0, 3),
            'camera_status': round(random.uniform(0.95, 1.0), 3)
        }

# Authentication Routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    error = None
    
    if 'logged_in' in session:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == app.config['USERNAME'] and password == app.config['PASSWORD']:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password'
    
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('login'))

# Routes
@app.route('/')
@login_required
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@app.route('/test')
def test_page():
    """Test page for push notifications"""
    return render_template('test.html')

# Firebase FCM Routes
@app.route('/save-token', methods=['POST'])
def save_token():
    """Save FCM token to database (following test folder approach)"""
    try:
        data = request.get_json()
        token = data.get('token')
        user_agent = request.headers.get('User-Agent', '')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            
            # Check if token already exists
            cursor.execute('SELECT id FROM fcm_tokens WHERE token = ?', (token,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing token
                cursor.execute('''
                    UPDATE fcm_tokens 
                    SET is_active = 1, updated_at = CURRENT_TIMESTAMP, user_agent = ?
                    WHERE token = ?
                ''', (user_agent, token))
            else:
                # Insert new token
                cursor.execute('''
                    INSERT INTO fcm_tokens (token, user_agent) 
                    VALUES (?, ?)
                ''', (token, user_agent))
            
            conn.commit()
        
        logger.info(f"🔑 FCM token saved: {token[:20]}...")
        return jsonify({'message': 'Token saved successfully'}), 200
        
    except Exception as e:
        logger.error(f"❌ Error saving token: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/register-fcm-token', methods=['POST'])
@login_required
def register_fcm_token():
    """Register FCM token from client"""
    try:
        data = request.get_json()
        token = data.get('token')
        user_agent = request.headers.get('User-Agent', '')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            
            # Check if token already exists
            cursor.execute('SELECT id FROM fcm_tokens WHERE token = ?', (token,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing token
                cursor.execute('''
                    UPDATE fcm_tokens 
                    SET is_active = 1, updated_at = CURRENT_TIMESTAMP, user_agent = ?
                    WHERE token = ?
                ''', (user_agent, token))
                is_new = False
            else:
                # Insert new token
                cursor.execute('''
                    INSERT INTO fcm_tokens (token, user_agent) 
                    VALUES (?, ?)
                ''', (token, user_agent))
                is_new = True
            
            conn.commit()
            
            # Get total active tokens
            cursor.execute('SELECT COUNT(*) FROM fcm_tokens WHERE is_active = 1')
            total_tokens = cursor.fetchone()[0]
        
        logger.info(f"🔑 FCM token {'registered' if is_new else 'updated'}: {token[:20]}...")
        
        return jsonify({
            'message': 'Token registered successfully',
            'total_tokens': total_tokens,
            'token_preview': token[:20] + '...',
            'is_new': is_new
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error registering FCM token: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/send-notification', methods=['POST'])
def send_notification():
    """Send push notification to a specific device (following test folder approach)"""
    try:
        data = request.get_json()
        token = data.get('token')
        title = data.get('title', 'Notification')
        body = data.get('body', 'Notification content')
        link = data.get('link', '/')
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        if not firebase_initialized:
            return jsonify({'error': 'Firebase not initialized'}), 500
        
        # Create FCM message
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            webpush=messaging.WebpushConfig(
                fcm_options=messaging.WebpushFCMOptions(
                    link=link
                ),
                notification=messaging.WebpushNotification(
                    title=title,
                    body=body,
                    icon='/static/icon.png',
                    badge='/static/badge.png'
                )
            ),
            token=token
        )
        
        # Send message
        response = messaging.send(message)
        logger.info(f"📨 Single notification sent: {response}")
        
        return jsonify({
            'message': 'Notification sent successfully',
            'response': response
        }), 200
        
    except messaging.UnregisteredError:
        # Token không hợp lệ, deactivate trong database
        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE fcm_tokens SET is_active = 0 WHERE token = ?', (token,))
            conn.commit()
        return jsonify({'error': 'Token is invalid and has been deactivated'}), 400
    except Exception as e:
        logger.error(f"❌ Error sending notification: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/send-multicast', methods=['POST'])
def send_multicast():
    """Send push notification to all registered devices (using loop to send to each token)"""
    try:
        data = request.get_json()
        title = data.get('title', 'Notification')
        body = data.get('body', 'Notification content for all devices')
        link = data.get('link', 'https://dashboard-sgteam.onrender.com/login')
        
        if not firebase_initialized:
            return jsonify({'error': 'Firebase not initialized'}), 500
        
        # Get all active tokens
        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT token FROM fcm_tokens WHERE is_active = 1')
            tokens = [row[0] for row in cursor.fetchall()]
        
        if not tokens:
            return jsonify({'error': 'No active tokens found'}), 400
        
        # Duyệt vòng lặp để gửi từng token
        success_count = 0
        failure_count = 0
        failed_tokens = []
        
        for token in tokens:
            try:
                # Tạo tin nhắn FCM cho từng token
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    webpush=messaging.WebpushConfig(
                        fcm_options=messaging.WebpushFCMOptions(
                            link=link
                        ),
                        notification=messaging.WebpushNotification(
                            title=title,
                            body=body,
                            icon='/static/icon.png',
                            badge='/static/badge.png'
                        )
                    ),
                    token=token
                )
                
                # Gửi tin nhắn
                response = messaging.send(message)
                success_count += 1
                logger.info(f"📨 Notification sent to token {token[:20]}...: {response}")
                
            except messaging.UnregisteredError:
                # Token không hợp lệ
                failed_tokens.append(token)
                failure_count += 1
                logger.warning(f"❌ Invalid token: {token[:20]}...")
            except Exception as e:
                failed_tokens.append(token)
                failure_count += 1
                logger.error(f"❌ Error sending to token {token[:20]}...: {e}")
        
        # Deactivate token không hợp lệ
        if failed_tokens:
            with sqlite3.connect(app.config['DATABASE']) as conn:
                cursor = conn.cursor()
                for failed_token in failed_tokens:
                    cursor.execute('UPDATE fcm_tokens SET is_active = 0 WHERE token = ?', (failed_token,))
                conn.commit()
        
        logger.info(f"📨 Notification sent to all tokens: {success_count} success, {failure_count} failures")
        
        return jsonify({
            'message': 'Notifications sent to all tokens',
            'success_count': success_count,
            'failure_count': failure_count,
            'total_tokens': len(tokens)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error sending notifications: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/send-data-message', methods=['POST'])
def send_data_message():
    """Gửi data message (không hiển thị notification UI) (theo cách folder test)"""
    try:
        data = request.get_json()
        token = data.get('token')
        custom_data = data.get('data', {})
        
        if not token:
            return jsonify({'error': 'Token is required'}), 400
        
        if not firebase_initialized:
            return jsonify({'error': 'Firebase not initialized'}), 500
        
        # Tạo data message
        message = messaging.Message(
            data=custom_data,
            token=token
        )
        
        response = messaging.send(message)
        logger.info(f"📨 Data message sent: {response}")
        
        return jsonify({
            'message': 'Data message sent successfully',
            'response': response
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error sending data message: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/tokens')
def list_tokens():
    """Hiển thị danh sách token đã đăng ký (theo cách folder test)"""
    try:
        with sqlite3.connect(app.config['DATABASE']) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, token, user_agent, created_at 
                FROM fcm_tokens 
                WHERE is_active = 1 
                ORDER BY created_at DESC
            ''')
            tokens = cursor.fetchall()
        
        return jsonify({
            'tokens': [{
                'id': token['id'],
                'token': token['token'][:50] + '...',  # Chỉ hiển thị 50 ký tự đầu
                'user_agent': token['user_agent'],
                'created_at': token['created_at']
            } for token in tokens],
            'count': len(tokens)
        })
        
    except Exception as e:
        logger.error(f"❌ Error listing tokens: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/fcm-tokens/status')
@login_required
def fcm_tokens_status():
    """Get FCM tokens status"""
    try:
        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM fcm_tokens WHERE is_active = 1')
            tokens_count = cursor.fetchone()[0]
        
        return jsonify({
            'tokens_count': tokens_count,
            'firebase_initialized': firebase_initialized,
            'notification_system_status': 'active' if firebase_initialized else 'inactive',
            'message': f'{tokens_count} active tokens registered'
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error getting FCM status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/test-firebase', methods=['POST'])
@login_required
def test_firebase_notification():
    """Send test Firebase notification (sử dụng vòng lặp gửi từng token)"""
    try:
        if not firebase_initialized:
            return jsonify({'error': 'Firebase not initialized'}), 500
        
        data = request.get_json()
        title = data.get('title', 'Test Notification')
        body = data.get('body', 'This is a test notification from SGTeam Dashboard')
        link = data.get('link', 'https://manhteky123-iot-challenge-2025.hf.space')
        
        # Get all active tokens
        with sqlite3.connect(app.config['DATABASE']) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT token FROM fcm_tokens WHERE is_active = 1')
            tokens = [row[0] for row in cursor.fetchall()]
        
        if not tokens:
            return jsonify({'error': 'No active tokens found'}), 400
        
        # Duyệt vòng lặp để gửi từng token
        success_count = 0
        failure_count = 0
        failed_tokens = []
        
        for token in tokens:
            try:
                # Tạo tin nhắn FCM cho từng token
                message = messaging.Message(
                    notification=messaging.Notification(
                        title=title,
                        body=body
                    ),
                    webpush=messaging.WebpushConfig(
                        fcm_options=messaging.WebpushFCMOptions(
                            link=link
                        ),
                        notification=messaging.WebpushNotification(
                            title=title,
                            body=body,
                            icon='/static/icon.png',
                            badge='/static/badge.png'
                        )
                    ),
                    token=token
                )
                
                # Gửi tin nhắn
                response = messaging.send(message)
                success_count += 1
                logger.info(f"📨 Test notification sent to token {token[:20]}...: {response}")
                
            except messaging.UnregisteredError:
                # Token không hợp lệ
                failed_tokens.append(token)
                failure_count += 1
                logger.warning(f"❌ Invalid token: {token[:20]}...")
            except Exception as e:
                failed_tokens.append(token)
                failure_count += 1
                logger.error(f"❌ Error sending test notification to token {token[:20]}...: {e}")
        
        # Deactivate failed tokens
        if failed_tokens:
            with sqlite3.connect(app.config['DATABASE']) as conn:
                cursor = conn.cursor()
                for failed_token in failed_tokens:
                    cursor.execute('UPDATE fcm_tokens SET is_active = 0 WHERE token = ?', (failed_token,))
                conn.commit()
        
        logger.info(f"📨 Test notification sent: {success_count} success, {failure_count} failures")
        
        return jsonify({
            'message': 'Test notification sent successfully',
            'success_count': success_count,
            'failure_count': failure_count,
            'total_tokens': len(tokens)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error sending test notification: {e}")
        return jsonify({'error': str(e)}), 500



@app.route('/api/chatbot/metrics')
@login_required
def chatbot_metrics():
    """Get chatbot metrics"""
    try:
        recent_data = db_manager.get_recent_metrics('chatbot_metrics', 24)
        if not recent_data:
            # Generate sample data if no data exists
            sample_data = MetricsGenerator.generate_chatbot_metrics()
            db_manager.insert_metric('chatbot_metrics', sample_data)
            recent_data = db_manager.get_recent_metrics('chatbot_metrics', 24)
        
        return jsonify({
            'status': 'success',
            'data': recent_data[:50],  # Limit to last 50 records
            'summary': {
                'total_conversations': sum(item['conversations'] for item in recent_data),
                'avg_response_time': round(sum(item['avg_response_time'] for item in recent_data) / len(recent_data), 2),
                'avg_accuracy': round(sum(item['intent_accuracy'] for item in recent_data) / len(recent_data), 3)
            }
        })
    except Exception as e:
        logger.error(f"Error fetching chatbot metrics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/navigation/metrics')
@login_required
def navigation_metrics():
    """Get indoor navigation metrics"""
    try:
        recent_data = db_manager.get_recent_metrics('navigation_metrics', 24)
        if not recent_data:
            sample_data = MetricsGenerator.generate_navigation_metrics()
            db_manager.insert_metric('navigation_metrics', sample_data)
            recent_data = db_manager.get_recent_metrics('navigation_metrics', 24)
        
        return jsonify({
            'status': 'success',
            'data': recent_data[:50],
            'summary': {
                'total_requests': sum(item['navigation_requests'] for item in recent_data),
                'avg_accuracy': round(sum(item['accuracy'] for item in recent_data) / len(recent_data), 3),
                'avg_completion_rate': round(sum(item['completion_rate'] for item in recent_data) / len(recent_data), 3)
            }
        })
    except Exception as e:
        logger.error(f"Error fetching navigation metrics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/navigation/upload-image', methods=['POST'])
def upload_navigation_image():
    """API để nhận hình ảnh đã xử lý từ ESP32 cam"""
    try:
        # Check if request contains file or base64 data
        if 'file' in request.files:
            # Handle file upload
            file = request.files['file']
            device_id = request.form.get('device_id', 'unknown')
            location = request.form.get('location', '')
            processed_data = request.form.get('processed_data', '')
            
            if file.filename == '':
                return jsonify({
                    'status': 'error',
                    'message': 'No file selected',
                    'code': 'NO_FILE'
                }), 400
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to filename to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_id}_{timestamp}_{filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                file.save(filepath)
                file_size = os.path.getsize(filepath)
                
        elif request.is_json:
            # Handle base64 image data
            data = request.get_json()
            
            if not data or 'image_data' not in data:
                return jsonify({
                    'status': 'error',
                    'message': 'No image data provided',
                    'code': 'NO_IMAGE_DATA'
                }), 400
            
            device_id = data.get('device_id', 'unknown')
            location = data.get('location', '')
            processed_data = data.get('processed_data', '')
            image_data = data.get('image_data')
            image_format = data.get('format', 'jpg')
            
            # Decode base64 image
            try:
                # Remove data URL prefix if present
                if image_data.startswith('data:image/'):
                    image_data = image_data.split(',')[1]
                
                image_bytes = base64.b64decode(image_data)
                
                # Create filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{device_id}_{timestamp}.{image_format}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                
                file_size = len(image_bytes)
                
            except Exception as decode_error:
                logger.error(f"Error decoding base64 image: {decode_error}")
                return jsonify({
                    'status': 'error',
                    'message': 'Invalid base64 image data',
                    'code': 'INVALID_IMAGE_DATA'
                }), 400
        else:
            return jsonify({
                'status': 'error',
                'message': 'No image data provided. Use file upload or JSON with base64 data.',
                'code': 'NO_DATA'
            }), 400
        
        # Save image info to database
        image_data = {
            'device_id': device_id,
            'location': location,
            'image_path': filepath,
            'image_name': filename,
            'image_size': file_size,
            'processed_data': processed_data
        }
        
        db_manager.insert_metric('navigation_images', image_data)
        
        logger.info(f"📸 Navigation image uploaded: {filename} from device {device_id}")
        
        return jsonify({
            'status': 'success',
            'message': 'Image uploaded successfully',
            'data': {
                'filename': filename,
                'device_id': device_id,
                'location': location,
                'size': file_size,
                'timestamp': datetime.now().isoformat()
            }
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error uploading navigation image: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Error processing image upload',
            'code': 'UPLOAD_ERROR'
        }), 500

@app.route('/api/navigation/images')
@login_required
def get_navigation_images():
    """API để lấy danh sách hình ảnh navigation cho dashboard"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 20, type=int)
        device_id = request.args.get('device_id')
        hours = request.args.get('hours', 24, type=int)
        
        with sqlite3.connect(app.config['DATABASE']) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build query
            query = """
                SELECT id, device_id, location, image_path, image_name, 
                       image_size, processed_data, timestamp, status
                FROM navigation_images
                WHERE timestamp >= datetime('now', '-{} hours')
            """.format(hours)
            
            params = []
            
            if device_id:
                query += " AND device_id = ?"
                params.append(device_id)
            
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            images = [dict(row) for row in cursor.execute(query, params).fetchall()]
        
        # Convert images to base64 for display
        images_data = []
        for img in images:
            try:
                # Read image file and convert to base64
                if os.path.exists(img['image_path']):
                    with open(img['image_path'], 'rb') as f:
                        image_bytes = f.read()
                        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                        
                        # Get file extension for MIME type
                        file_ext = img['image_name'].split('.')[-1].lower()
                        mime_type = f"image/{file_ext}" if file_ext in ['jpg', 'jpeg'] else f"image/{file_ext}"
                        
                        images_data.append({
                            'id': img['id'],
                            'device_id': img['device_id'],
                            'location': img['location'],
                            'image_name': img['image_name'],
                            'image_size': img['image_size'],
                            'processed_data': img['processed_data'],
                            'timestamp': img['timestamp'],
                            'status': img['status'],
                            'image_data': f"data:{mime_type};base64,{image_base64}"
                        })
                else:
                    # File not found, mark as missing
                    images_data.append({
                        'id': img['id'],
                        'device_id': img['device_id'],
                        'location': img['location'],
                        'image_name': img['image_name'],
                        'image_size': img['image_size'],
                        'processed_data': img['processed_data'],
                        'timestamp': img['timestamp'],
                        'status': 'file_missing',
                        'image_data': None
                    })
            except Exception as img_error:
                logger.error(f"Error processing image {img['image_name']}: {img_error}")
                continue
        
        return jsonify({
            'status': 'success',
            'data': images_data,
            'count': len(images_data),
            'total_images': len(images)
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error fetching navigation images: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching images',
            'code': 'FETCH_ERROR'
        }), 500

@app.route('/api/navigation/images/<int:image_id>')
@login_required
def get_navigation_image(image_id):
    """API để lấy một hình ảnh cụ thể theo ID"""
    try:
        with sqlite3.connect(app.config['DATABASE']) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, device_id, location, image_path, image_name, 
                       image_size, processed_data, timestamp, status
                FROM navigation_images
                WHERE id = ?
            """, (image_id,))
            
            img = cursor.fetchone()
            
            if not img:
                return jsonify({
                    'status': 'error',
                    'message': 'Image not found',
                    'code': 'NOT_FOUND'
                }), 404
        
        img_dict = dict(img)
        
        # Read and encode image
        if os.path.exists(img_dict['image_path']):
            with open(img_dict['image_path'], 'rb') as f:
                image_bytes = f.read()
                image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                
                # Get file extension for MIME type
                file_ext = img_dict['image_name'].split('.')[-1].lower()
                mime_type = f"image/{file_ext}" if file_ext in ['jpg', 'jpeg'] else f"image/{file_ext}"
                
                img_dict['image_data'] = f"data:{mime_type};base64,{image_base64}"
        else:
            img_dict['status'] = 'file_missing'
            img_dict['image_data'] = None
        
        return jsonify({
            'status': 'success',
            'data': img_dict
        }), 200
        
    except Exception as e:
        logger.error(f"❌ Error fetching navigation image {image_id}: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Error fetching image',
            'code': 'FETCH_ERROR'
        }), 500

@app.route('/api/security/metrics')
@login_required
def security_metrics():
    """Get security system metrics"""
    try:
        recent_data = db_manager.get_recent_metrics('security_metrics', 24)
        if not recent_data:
            sample_data = MetricsGenerator.generate_security_metrics()
            db_manager.insert_metric('security_metrics', sample_data)
            recent_data = db_manager.get_recent_metrics('security_metrics', 24)
        
        return jsonify({
            'status': 'success',
            'data': recent_data[:50],
            'summary': {
                'total_alerts': sum(item['alerts_count'] for item in recent_data),
                'total_access_attempts': sum(item['access_attempts'] for item in recent_data),
                'avg_camera_status': round(sum(item['camera_status'] for item in recent_data) / len(recent_data), 3)
            }
        })
    except Exception as e:
        logger.error(f"Error fetching security metrics: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/security/glass-break', methods=['POST'])
def glass_break_alert():
    """
    Optimized endpoint to receive and process glass break alerts from edge devices
    Also sends Firebase push notifications to all active tokens
    """
    try:
        data = request.get_json()
        
        # Validate request data
        if not data:
            return jsonify({
                'status': 'error', 
                'message': 'No JSON data provided',
                'code': 'MISSING_DATA'
            }), 400
        
        # Validate required fields
        required_fields = ['device_id', 'location', 'severity']
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        
        if missing_fields:
            return jsonify({
                'status': 'error',
                'message': f'Missing required fields: {", ".join(missing_fields)}',
                'code': 'MISSING_FIELDS',
                'required_fields': required_fields
            }), 400
        
        # Validate severity level
        valid_severities = ['low', 'medium', 'high', 'critical']
        severity = data['severity'].lower()
        if severity not in valid_severities:
            return jsonify({
                'status': 'error',
                'message': f'Invalid severity level. Must be one of: {", ".join(valid_severities)}',
                'code': 'INVALID_SEVERITY'
            }), 400
        
        # Prepare event data for database
        event_data = {
            'device_id': data['device_id'].strip(),
            'location': data['location'].strip(),
            'severity': severity,
            'status': data.get('status', 'active').strip()
        }
        
        # Insert glass break event into database
        db_manager.insert_metric('glass_break_events', event_data)
        
        # Send Firebase push notification if Firebase is initialized
        notification_sent = False
        if firebase_initialized:
            try:
                # Get all active tokens
                with sqlite3.connect(app.config['DATABASE']) as conn:
                    cursor = conn.cursor()
                    cursor.execute('SELECT token FROM fcm_tokens WHERE is_active = 1')
                    tokens = [row[0] for row in cursor.fetchall()]
                
                logger.info(f"🔑 Found {len(tokens)} active FCM tokens for glass break alert")
                
                if tokens:
                    # Create glass break alert message
                    severity_emoji = {
                        'low': '🟡',
                        'medium': '🟠', 
                        'high': '🔴',
                        'critical': '🚨'
                    }
                    
                    title = f"{severity_emoji.get(severity, '🚨')} Glass Break Alert - {severity.upper()}"
                    body = f"Location: {event_data['location']}\nDevice: {event_data['device_id']}"
                    link = "https://manhteky123-iot-challenge-2025.hf.space"
                    
                    # Duyệt vòng lặp để gửi từng token
                    success_count = 0
                    failure_count = 0
                    failed_tokens = []
                    
                    for token in tokens:
                        try:
                            # Tạo tin nhắn FCM cho từng token
                            message = messaging.Message(
                                notification=messaging.Notification(
                                    title=title,
                                    body=body
                                ),
                                webpush=messaging.WebpushConfig(
                                    fcm_options=messaging.WebpushFCMOptions(
                                        link=link
                                    ),
                                    notification=messaging.WebpushNotification(
                                        title=title,
                                        body=body,
                                        icon='/static/icon.png',
                                        badge='/static/badge.png'
                                    )
                                ),
                                token=token
                            )
                            
                            # Gửi tin nhắn
                            response = messaging.send(message)
                            success_count += 1
                            
                        except messaging.UnregisteredError:
                            # Token không hợp lệ
                            failed_tokens.append(token)
                            failure_count += 1
                        except Exception as token_error:
                            failed_tokens.append(token)
                            failure_count += 1
                            logger.error(f"❌ Error sending glass break alert to token: {token_error}")
                    
                    notification_sent = success_count > 0
                    
                    logger.info(f"🔔 Glass break notification sent: {success_count} success, {failure_count} failures")
                    
                    # Handle failed tokens
                    if failed_tokens:
                        with sqlite3.connect(app.config['DATABASE']) as conn:
                            cursor = conn.cursor()
                            for failed_token in failed_tokens:
                                cursor.execute('UPDATE fcm_tokens SET is_active = 0 WHERE token = ?', (failed_token,))
                            conn.commit()
                else:
                    logger.warning("⚠️ No active FCM tokens found for glass break alert")
                
            except Exception as notification_error:
                logger.error(f"❌ Error sending glass break notification: {notification_error}")
        else:
            logger.warning("⚠️ Firebase not initialized - cannot send glass break notification")
        
        # Log the event
        logger.info(f"🚨 Glass break alert processed: {event_data['location']} "
                   f"(Device: {event_data['device_id']}, Severity: {event_data['severity']}, "
                   f"Notification sent: {notification_sent})")
        
        # Prepare response
        response_data = {
            'status': 'success',
            'message': 'Glass break alert received and processed successfully',
            'notification_sent': notification_sent,
            'event': {
                'device_id': event_data['device_id'],
                'location': event_data['location'],
                'severity': event_data['severity'],
                'status': event_data['status'],
                'timestamp': datetime.now().isoformat()
            }
        }
        
        return jsonify(response_data), 200
        
    except ValueError as ve:
        logger.error(f"❌ Glass break alert validation error: {ve}")
        return jsonify({
            'status': 'error',
            'message': f'Data validation error: {str(ve)}',
            'code': 'VALIDATION_ERROR'
        }), 400
        
    except Exception as e:
        logger.error(f"❌ Error processing glass break alert: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error while processing alert',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/security/glass-break/events')
@login_required
def get_glass_break_events():
    """Get recent glass break events"""
    try:
        recent_events = db_manager.get_recent_metrics('glass_break_events', 168)  # Last 7 days
        return jsonify({
            'status': 'success',
            'data': recent_events
        })
    except Exception as e:
        logger.error(f"Error fetching glass break events: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/dashboard/overview')
@login_required
def dashboard_overview():
    """Get overview data for all systems"""
    try:
        # Get latest metrics from each system
        chatbot_data = db_manager.get_recent_metrics('chatbot_metrics', 1)
        navigation_data = db_manager.get_recent_metrics('navigation_metrics', 1)
        security_data = db_manager.get_recent_metrics('security_metrics', 1)
        glass_break_events = db_manager.get_recent_metrics('glass_break_events', 24)
        
        overview = {
            'systems_status': {
                'chatbot': 'online' if chatbot_data else 'offline',
                'navigation': 'online' if navigation_data else 'offline',
                'security': 'online' if security_data else 'offline'
            },
            'current_metrics': {
                'active_users': chatbot_data[0]['active_users'] if chatbot_data else 0,
                'navigation_requests': navigation_data[0]['navigation_requests'] if navigation_data else 0,
                'security_alerts': security_data[0]['alerts_count'] if security_data else 0,
                'glass_break_alerts': len([e for e in glass_break_events if e['status'] == 'active'])
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'data': overview
        })
        
    except Exception as e:
        logger.error(f"Error fetching dashboard overview: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Service worker for Firebase
@app.route('/firebase-messaging-sw.js')
def firebase_sw():
    """Serve Firebase messaging service worker"""
    return send_from_directory('static', 'firebase-messaging-sw.js', mimetype='application/javascript')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

if __name__ == '__main__':
    # Generate some initial sample data
    for _ in range(10):
        db_manager.insert_metric('chatbot_metrics', MetricsGenerator.generate_chatbot_metrics())
        db_manager.insert_metric('navigation_metrics', MetricsGenerator.generate_navigation_metrics())
        db_manager.insert_metric('security_metrics', MetricsGenerator.generate_security_metrics())
    
    logger.info("🚀 SGTeam Dashboard starting...")
    logger.info(f"🔔 Firebase notifications: {'✅ Enabled' if firebase_initialized else '❌ Disabled'}")
    
    # Get port from environment variable (for Hugging Face Spaces compatibility)
    import os
    port = int(os.environ.get('PORT', 7860))
    
    app.run(debug=False, host='0.0.0.0', port=port)
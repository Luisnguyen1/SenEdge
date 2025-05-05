from flask import Flask, render_template, request, jsonify, send_file
from flask_socketio import SocketIO
import json
import os
from datetime import datetime
import logging
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'iotchallenge2025'
socketio = SocketIO(app)

# Create directory for storing detection images
UPLOAD_FOLDER = 'detections'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# In-memory storage for sensor data
sensor_data = {
    'temperature': 25.0,
    'humidity': 60.0,
    'pressure': 1013.25,
    'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# Store person detections
person_detections = []

# Store device status
device_status = {}

# Store logs in memory
request_logs = []

# Store camera images
camera_images = []

# Route for the home page
@app.route('/')
def index():
    return render_template('dashboard.html', 
                          sensor_data=sensor_data, 
                          detections=person_detections,
                          device_status=device_status)

# API endpoint to update sensor data
@app.route('/api/update_sensor', methods=['POST'])
def update_sensor():
    global sensor_data
    try:
        data = request.get_json()
        
        # Log the incoming request
        log_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'endpoint': '/api/update_sensor',
            'method': 'POST',
            'data': data,
            'client_ip': request.remote_addr
        }
        request_logs.append(log_entry)
        
        # Update sensor data if values are provided
        if 'temperature' in data:
            sensor_data['temperature'] = float(data['temperature'])
        if 'humidity' in data:
            sensor_data['humidity'] = float(data['humidity'])
        if 'pressure' in data:
            sensor_data['pressure'] = float(data['pressure'])
            
        sensor_data['last_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Notify connected clients about the update
        socketio.emit('sensor_update', sensor_data)
        socketio.emit('new_log', log_entry)
        
        logger.info(f"Sensor data updated: {sensor_data}")
        
        return jsonify({'status': 'success', 'message': 'Sensor data updated'})
    
    except Exception as e:
        error_message = f"Error updating sensor data: {str(e)}"
        logger.error(error_message)
        return jsonify({'status': 'error', 'message': error_message}), 400

# API endpoint to get current sensor data
@app.route('/api/sensor_data', methods=['GET'])
def get_sensor_data():
    log_entry = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'endpoint': '/api/sensor_data',
        'method': 'GET',
        'client_ip': request.remote_addr
    }
    request_logs.append(log_entry)
    socketio.emit('new_log', log_entry)
    
    return jsonify(sensor_data)

# API endpoint to update device status
@app.route('/api/device-status', methods=['POST'])
def device_status_update():
    try:
        data = request.get_json()
        
        device_id = data.get('device_id', 'unknown')
        
        # Update device status
        device_status[device_id] = {
            'status': data.get('status', 'unknown'),
            'ip': data.get('ip', 'unknown'),
            'mac': data.get('mac', 'unknown'),
            'rssi': data.get('rssi', 0),
            'free_heap': data.get('free_heap', 0),
            'psram': data.get('psram', 0),
            'last_seen': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Log the status update
        log_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'endpoint': '/api/device-status',
            'method': 'POST',
            'device_id': device_id,
            'status': data.get('status', 'unknown'),
            'client_ip': request.remote_addr
        }
        request_logs.append(log_entry)
        
        # Notify connected clients
        socketio.emit('device_status', device_status)
        socketio.emit('new_log', log_entry)
        
        logger.info(f"Device status updated: {device_id} is {data.get('status', 'unknown')}")
        
        return jsonify({
            'status': 'success', 
            'message': 'Device status updated', 
            'device_id': device_id
        })
        
    except Exception as e:
        error_message = f"Error updating device status: {str(e)}"
        logger.error(error_message)
        return jsonify({'status': 'error', 'message': error_message}), 400

# API endpoint for person detection
@app.route('/api/person-detection', methods=['POST'])
def person_detection():
    try:
        # Get the image data from the request
        if not request.data:
            return jsonify({'status': 'error', 'message': 'No image data received'}), 400

        # Create a timestamp for the detection
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save the image
        image_filename = f'detection_{timestamp}.jpg'
        image_path = os.path.join(UPLOAD_FOLDER, image_filename)
        
        with open(image_path, 'wb') as f:
            f.write(request.data)
        
        # Create detection entry
        detection = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'image_path': image_path,
            'client_ip': request.remote_addr
        }
        
        person_detections.append(detection)
        
        # Create log entry
        log_entry = {
            'timestamp': detection['timestamp'],
            'endpoint': '/api/person-detection',
            'method': 'POST',
            'client_ip': request.remote_addr,
            'image': image_filename
        }
        request_logs.append(log_entry)
        
        # Notify connected clients
        socketio.emit('person_detected', detection)
        socketio.emit('new_log', log_entry)
        
        logger.info(f"Person detected and image saved: {image_path}")
        
        return jsonify({
            'status': 'success', 
            'message': 'Person detection recorded',
            'detection': detection
        })
        
    except Exception as e:
        error_message = f"Error processing person detection: {str(e)}"
        logger.error(error_message)
        return jsonify({'status': 'error', 'message': error_message}), 400

# API endpoint to get detection image
@app.route('/api/detections/<filename>')
def get_detection(filename):
    try:
        # Validate filename to avoid security issues
        if '..' in filename or filename.startswith('/'):
            return jsonify({'status': 'error', 'message': 'Invalid filename'}), 400
            
        # Try to send the file
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if os.path.exists(file_path):
            return send_file(file_path)
        else:
            return jsonify({'status': 'error', 'message': 'Image not found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# API endpoint to get all detections
@app.route('/api/detections', methods=['GET'])
def get_detections():
    return jsonify(person_detections)

# API endpoint for camera images from ESP32 CAM
@app.route('/api/camera-image', methods=['POST'])
def camera_image():
    try:
        # Get the image data from the request
        if not request.data:
            return jsonify({'status': 'error', 'message': 'No image data received'}), 400

        # Create a timestamp for the image
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save the image
        image_filename = f'camera_{timestamp}.jpg'
        image_path = os.path.join(UPLOAD_FOLDER, image_filename)
        
        with open(image_path, 'wb') as f:
            f.write(request.data)
        
        # Get device info if available in headers
        device_id = request.headers.get('X-Device-ID', 'unknown')
        
        # Create image entry
        image = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'image_path': image_path,
            'client_ip': request.remote_addr,
            'device_id': device_id
        }
        
        camera_images.append(image)
          # Create log entry
        log_entry = {
            'timestamp': image['timestamp'],
            'endpoint': '/api/camera-image',
            'method': 'POST',
            'client_ip': request.remote_addr,
            'device_id': device_id,
            'image': image_filename
        }
        request_logs.append(log_entry)
        
        # Notify connected clients
        socketio.emit('new_camera_image', image)
        socketio.emit('new_log', log_entry)
        
        logger.info(f"Camera image received and saved: {image_path} from device {device_id}")
        
        return jsonify({
            'status': 'success', 
            'message': 'Camera image saved successfully',
            'image': image
        })
        
    except Exception as e:
        error_message = f"Error processing camera image: {str(e)}"
        logger.error(error_message)
        return jsonify({'status': 'error', 'message': error_message}), 400

# API endpoint to get all camera images
@app.route('/api/camera-images', methods=['GET'])
def get_camera_images():
    return jsonify(camera_images)
    
# API endpoint to get combined image data (both camera and person detection images)
@app.route('/api/images', methods=['GET'])
def get_all_images():
    all_images = person_detections + camera_images
    # Sort by timestamp, newest first
    all_images.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify(all_images)

# API endpoint to get logs
@app.route('/api/logs', methods=['GET'])
def get_logs():
    return jsonify(request_logs)

if __name__ == '__main__':
    # # Create directories for templates and static files if they don't exist
    # os.makedirs('templates', exist_ok=True)
    # os.makedirs('static/css', exist_ok=True)
    # os.makedirs('static/js', exist_ok=True)
    
    logger.info("Starting IoT Challenge 2025 server on port 7860...")
    socketio.run(app, host='0.0.0.0', port=7860, debug=True, allow_unsafe_werkzeug=True)

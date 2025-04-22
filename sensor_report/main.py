from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import json
import os
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'iotchallenge2025'
socketio = SocketIO(app)

# In-memory storage for sensor data
sensor_data = {
    'temperature': 25.0,
    'humidity': 60.0,
    'pressure': 1013.25,
    'last_updated': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

# Store logs in memory
request_logs = []

# Route for the home page
@app.route('/')
def index():
    return render_template('dashboard.html', sensor_data=sensor_data)

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

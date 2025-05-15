from flask import Flask, request, render_template, jsonify
import math
import threading
import time
import os

app = Flask(__name__)

# In a real app, beacon positions would be stored in a database
# For simplicity, we'll hardcode them here
beacons = {
    "beacon1": {"x": 0, "y": 0},    # Position of beacon 1
    "beacon2": {"x": 10, "y": 0},   # Position of beacon 2
    "beacon3": {"x": 5, "y": 8},    # Position of beacon 3
}

# State variables
current_user_hotspot = None
rssi_values = {}
user_position = {"x": None, "y": None}
scanning_active = False

def distance_from_rssi(rssi):
    # RSSI to distance conversion (adjust parameters as needed)
    tx_power = -45  # RSSI at 1 meter
    n = 2.5         # Path loss exponent (2-4 typically)
    
    if rssi == 0:
        return -1
    
    ratio = rssi / tx_power
    if ratio < 1.0:
        return pow(ratio, 10)
    else:
        distance = pow(10, (tx_power - rssi) / (10 * n))
        return distance

def trilateration():
    global rssi_values, user_position
    
    # Need at least 3 beacons with RSSI values for trilateration
    if len(rssi_values) < 3:
        return
    
    # Convert RSSI to distances
    distances = {}
    for beacon_id, rssi in rssi_values.items():
        if beacon_id in beacons:
            distances[beacon_id] = distance_from_rssi(rssi)
    
    # Simple trilateration algorithm (can be improved)
    # Using first 3 beacons with valid distances
    valid_beacons = [(bid, beacons[bid], dist) for bid, dist in distances.items() 
                    if bid in beacons and dist > 0]
    
    if len(valid_beacons) >= 3:
        # Extract 3 beacons for trilateration
        b1, p1, r1 = valid_beacons[0]
        b2, p2, r2 = valid_beacons[1]
        b3, p3, r3 = valid_beacons[2]
        
        # Calculate intersection of three circles
        # This is a simplified approach and could be improved
        A = 2 * (p2["x"] - p1["x"])
        B = 2 * (p2["y"] - p1["y"])
        C = r1**2 - r2**2 - p1["x"]**2 + p2["x"]**2 - p1["y"]**2 + p2["y"]**2
        D = 2 * (p3["x"] - p2["x"])
        E = 2 * (p3["y"] - p2["y"])
        F = r2**2 - r3**2 - p2["x"]**2 + p3["x"]**2 - p2["y"]**2 + p3["y"]**2
        
        # Solve the system of equations
        try:
            x = (C*E - F*B) / (E*A - B*D)
            y = (C*D - A*F) / (B*D - A*E)
            user_position = {"x": x, "y": y}
        except:
            # Fallback if the equations are unsolvable
            # Average of beacon positions weighted by inverse distance
            total_weight = sum(1/d for _, _, d in valid_beacons)
            x = sum(p["x"] * (1/d) / total_weight for _, p, d in valid_beacons)
            y = sum(p["y"] * (1/d) / total_weight for _, p, d in valid_beacons)
            user_position = {"x": x, "y": y}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/navigation')
def navigation():
    # Check if it's a mobile device (simple user agent check)
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent or 'ipad' in user_agent
    
    if is_mobile:
        return render_template('mobile_map.html')
    else:
        return render_template('indoor_navigation.html')

@app.route('/mobile-map')
def mobile_map():
    # Direct access to mobile map view
    return render_template('mobile_map.html')

@app.route('/set_hotspot', methods=['POST'])
def set_hotspot():
    global current_user_hotspot, scanning_active, rssi_values
    
    data = request.get_json()
    current_user_hotspot = data.get('hotspot_name')
    
    # Reset previous data
    rssi_values = {}
    user_position = {"x": None, "y": None}
    
    # Activate scanning
    scanning_active = True
    
    return jsonify({"status": "OK", "message": f"Scanning for hotspot: {current_user_hotspot}"})

@app.route('/get_target_hotspot', methods=['GET'])
def get_target_hotspot():
    beacon_id = request.args.get('beacon_id')
    if scanning_active and current_user_hotspot:
        return jsonify({
            "scan_active": True,
            "hotspot_name": current_user_hotspot
        })
    else:
        return jsonify({
            "scan_active": False
        })

@app.route('/rssi', methods=['POST'])
def receive_rssi():
    global rssi_values
    
    if not scanning_active:
        return 'Scanning not active', 200
        
    data = request.get_json()
    beacon_id = data.get('beacon_id')
    rssi = data.get('rssi')
    
    print(f"Received from {beacon_id}: RSSI = {rssi} for hotspot {current_user_hotspot}")
    
    rssi_values[beacon_id] = rssi
    
    # Try to calculate position with current data
    trilateration()
    
    return 'OK', 200

@app.route('/get_position', methods=['GET'])
def get_position():
    return jsonify({
        "position": user_position,
        "beacons": beacons,
        "rssi_values": rssi_values
    })

# Make sure the templates and static directories exist
os.makedirs('templates', exist_ok=True)
os.makedirs('static/js', exist_ok=True)

# Add link to navigation page in index.html
@app.context_processor
def inject_navigation_link():
    return {
        'nav_links': [
            {'url': '/', 'text': 'Basic View'},
            {'url': '/navigation', 'text': 'Advanced Navigation'}
        ]
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

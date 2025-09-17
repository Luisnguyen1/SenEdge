from flask import Flask, request, jsonify, render_template
from flask_socketio import SocketIO, emit
import json
from datetime import datetime
import math
import threading
import time

# Try to import BeaconManager, continue without it if not available
try:
    from BLE_Becons import BeaconManager  # Import BeaconManager
    BEACON_MANAGER_AVAILABLE = True
except ImportError:
    print("⚠️ BLE_Becons module not available. Continuing without BLE functionality.")
    BeaconManager = None
    BEACON_MANAGER_AVAILABLE = False

# Try to import GlassBreakService, continue without it if not available
try:
    from glass_break_service import GlassBreakService
    GLASS_BREAK_SERVICE_AVAILABLE = True
except ImportError:
    print("⚠️ Glass Break Service module not available. Continuing without glass break detection.")
    GlassBreakService = None
    GLASS_BREAK_SERVICE_AVAILABLE = False

app = Flask(__name__)
app.config['SECRET_KEY'] = 'indoor_navigation_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Thread lock for thread-safe access to beacon data
beacon_lock = threading.Lock()

# Store beacon data in memory
beacon_data = []

# Store current beacon RSSI values (latest from each beacon)
current_beacon_rssi = {}

# Store current user position
current_user_position = {
    "x": 9,  # Default position
    "y": 9,
    "last_beacon": None,
    "last_update": None,
    "distance_to_beacon": None,
    "admin_controlled": False  # Flag to indicate if position is admin controlled
}

# Store crowded areas information
crowded_areas = {
    # Format: "area_id": {
    #     "position": [x, y],
    #     "size": [width, height], 
    #     "crowd_level": 0-5 (0=empty, 5=very crowded),
    #     "people_count": int,
    #     "last_update": timestamp,
    #     "description": "Area description"
    # }
}

# Thread lock for crowded areas data
crowded_areas_lock = threading.Lock()

# Store checkout queue information
checkout_queues = {
    # Format: "checkout_id": {
    #     "camera_id": "esp32cam_02",
    #     "position": [x, y],
    #     "people_count": int,
    #     "queue_length": int,
    #     "wait_time_estimate": int (minutes),
    #     "last_update": timestamp,
    #     "status": "open/closed/maintenance"
    # }
    "CHECKOUT_WEST": {
        "camera_id": "esp32cam_02",
        "position": [18, 3],
        "people_count": 0,
        "queue_length": 0,
        "wait_time_estimate": 0,
        "last_update": None,
        "status": "open"
    },
    "CHECKOUT_EAST": {
        "camera_id": "esp32cam_03", 
        "position": [18, 14],
        "people_count": 0,
        "queue_length": 0,
        "wait_time_estimate": 0,
        "last_update": None,
        "status": "open"
    }
}

# Thread lock for checkout queue data
checkout_queues_lock = threading.Lock()

# Store priority products information with default test data
priority_products = {
    # Default priority products for testing
    "a2_iphone": {
        "product_name": "iPhone",
        "shelf_id": "A2",
        "position": [2, 3],
        "priority_level": 5,
        "category": "Electronics",
        "description": "Featured smartphone",
        "created_at": datetime.now().isoformat(),
        "is_active": True
    },
    "b2_refrigerator": {
        "product_name": "Refrigerator",
        "shelf_id": "B2",
        "position": [12, 3],
        "priority_level": 4,
        "category": "Home Appliances",
        "description": "Special offer appliance",
        "created_at": datetime.now().isoformat(),
        "is_active": True
    },
    "c1_playstation": {
        "product_name": "PlayStation",
        "shelf_id": "C1",
        "position": [1, 7],
        "priority_level": 3,
        "category": "Gaming",
        "description": "Popular gaming console",
        "created_at": datetime.now().isoformat(),
        "is_active": True
    }
}

# Thread lock for priority products data
priority_products_lock = threading.Lock()

# Tạo instance để chia sẻ với BeaconManager
app.current_beacon_rssi = current_beacon_rssi
app.beacon_lock = beacon_lock
app.socketio = socketio
app.crowded_areas = crowded_areas
app.crowded_areas_lock = crowded_areas_lock
app.checkout_queues = checkout_queues
app.checkout_queues_lock = checkout_queues_lock
app.priority_products = priority_products
app.priority_products_lock = priority_products_lock

# Khởi tạo BeaconManager với app instance
beacon_manager = None

# Khởi tạo GlassBreakService với app instance  
glass_break_service = None


# Ma trận vị trí và layout của map (20x20 grid) - 3 dãy song song, mỗi dãy 2 cụm, mỗi cụm 6 kệ
# 0 = đường đi trống, 1 = kệ hàng, 2 = vật cản, 3 = beacon, 4 = lối ra/vào
MAP_LAYOUT = {
    "width": 20,
    "height": 20,
    "grid": [
        [4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4],  # Row 0 - Entrance/Exit
        [0,0,0,0,0,0,0,0,0,3,0,0,0,0,0,0,0,0,0,0],  # Row 1 - Beacon 007 (9,1)
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],  # Row 2 - Walking path
        [0,3,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,3,0,0],  # Row 3 - Beacon 003 (1,3) + Dãy 1: Cụm A (6 kệ) + Cụm B (6 kệ) + Beacon 005 (17,3)
        [0,0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,0,0,0],  # Row 4 - Dãy 1: Cụm A (6 kệ) + Cụm B (6 kệ)
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],  # Row 5 - Walking path
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],  # Row 6 - Walking path
        [0,0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,0,0,0],  # Row 7 - Dãy 2: Cụm C (6 kệ) + Cụm D (6 kệ)
        [0,0,1,1,1,1,1,0,0,3,0,1,1,1,1,1,1,0,0,0],  # Row 8 - Beacon 009 (9,8) + Dãy 2: Cụm C (6 kệ) + Cụm D (6 kệ)
        [0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,0,0],  # Row 9 - Beacon 002 (1,9) + Beacon 004 (17,9)
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],  # Row 10 - Walking path
        [0,0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,0,0,0],  # Row 11 - Dãy 3: Cụm E (6 kệ) + Cụm F (6 kệ)
        [0,0,1,1,1,1,1,0,0,0,0,1,1,1,1,1,1,0,0,0],  # Row 12 - Dãy 3: Cụm E (6 kệ) + Cụm F (6 kệ)
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],  # Row 13 - Walking path
        [0,3,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,3,0,0],  # Row 14 - Beacon 001 (1,14) + Beacon 006 (17,14)
        [0,0,0,0,0,0,0,0,0,3,0,0,0,0,0,0,0,0,0,0],  # Row 15 - Beacon 008 (9,15)
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],  # Row 16 - Walking path
        [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],  # Row 17 - Walking path
        [2,2,2,5,2,2,2,2,2,2,2,2,2,2,5,2,2,2,2,2],  # Row 18 - Wall/Obstacles + Checkout (3,18) + (14,18)
        [4,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,4],  # Row 19 - Entrance/Exit
    ]
}

# Định nghĩa các khu vực và thông tin chi tiết - 3 dãy song song, mỗi dãy 2 cụm, mỗi cụm 6 kệ (36 kệ tổng)
SHELVES_INFO = {
    # Dãy 1 (Row 3-4): Cụm A (6 kệ) + Cụm B (6 kệ)
    "A1": {"position": [1,3], "size": [1,2], "category": "Electronics", "products": ["Smart TV", "LED TV"]},
    "A2": {"position": [2,3], "size": [1,2], "category": "Electronics", "products": ["iPhone", "Samsung Phone"]},
    "A3": {"position": [3,3], "size": [1,2], "category": "Electronics", "products": ["Laptop", "MacBook"]},
    "A4": {"position": [4,3], "size": [1,2], "category": "Electronics", "products": ["Tablet", "iPad"]},
    "A5": {"position": [5,3], "size": [1,2], "category": "Electronics", "products": ["Headphone", "Earbuds"]},
    "A6": {"position": [6,3], "size": [1,2], "category": "Electronics", "products": ["Smartwatch", "Fitness Tracker"]},
    
    "B1": {"position": [11,3], "size": [1,2], "category": "Home Appliances", "products": ["Washing Machine", "Dryer"]},
    "B2": {"position": [12,3], "size": [1,2], "category": "Home Appliances", "products": ["Refrigerator", "Freezer"]},
    "B3": {"position": [13,3], "size": [1,2], "category": "Home Appliances", "products": ["Microwave", "Oven"]},
    "B4": {"position": [14,3], "size": [1,2], "category": "Home Appliances", "products": ["Air Conditioner", "Fan"]},
    "B5": {"position": [15,3], "size": [1,2], "category": "Home Appliances", "products": ["Vacuum Cleaner", "Robot Vacuum"]},
    "B6": {"position": [16,3], "size": [1,2], "category": "Home Appliances", "products": ["Water Heater", "Air Purifier"]},
    
    # Dãy 2 (Row 7-8): Cụm C (6 kệ) + Cụm D (6 kệ)
    "C1": {"position": [1,7], "size": [1,2], "category": "Gaming", "products": ["PlayStation", "Xbox"]},
    "C2": {"position": [2,7], "size": [1,2], "category": "Gaming", "products": ["Nintendo Switch", "Steam Deck"]},
    "C3": {"position": [3,7], "size": [1,2], "category": "Gaming", "products": ["Gaming Chair", "Gaming Desk"]},
    "C4": {"position": [4,7], "size": [1,2], "category": "Gaming", "products": ["Gaming Mouse", "Gaming Keyboard"]},
    "C5": {"position": [5,7], "size": [1,2], "category": "Gaming", "products": ["Gaming Monitor", "4K Monitor"]},
    "C6": {"position": [6,7], "size": [1,2], "category": "Gaming", "products": ["VR Headset", "VR Controllers"]},
    
    "D1": {"position": [11,7], "size": [1,2], "category": "Computer", "products": ["Desktop PC", "All-in-One PC"]},
    "D2": {"position": [12,7], "size": [1,2], "category": "Computer", "products": ["Monitor", "Ultrawide Monitor"]},
    "D3": {"position": [13,7], "size": [1,2], "category": "Computer", "products": ["Keyboard", "Mechanical Keyboard"]},
    "D4": {"position": [14,7], "size": [1,2], "category": "Computer", "products": ["Mouse", "Trackpad"]},
    "D5": {"position": [15,7], "size": [1,2], "category": "Computer", "products": ["Webcam", "Microphone"]},
    "D6": {"position": [16,7], "size": [1,2], "category": "Computer", "products": ["Printer", "Scanner"]},
    
    # Dãy 3 (Row 11-12): Cụm E (6 kệ) + Cụm F (6 kệ)
    "E1": {"position": [1,11], "size": [1,2], "category": "Smart Home", "products": ["Smart Speaker", "Smart Display"]},
    "E2": {"position": [2,11], "size": [1,2], "category": "Smart Home", "products": ["Smart Bulb", "Smart Switch"]},
    "E3": {"position": [3,11], "size": [1,2], "category": "Smart Home", "products": ["Security Camera", "Doorbell Camera"]},
    "E4": {"position": [4,11], "size": [1,2], "category": "Smart Home", "products": ["Smart Lock", "Smart Thermostat"]},
    "E5": {"position": [5,11], "size": [1,2], "category": "Smart Home", "products": ["Robot Vacuum", "Smart Plug"]},
    "E6": {"position": [6,11], "size": [1,2], "category": "Smart Home", "products": ["Smart Sensor", "Hub Controller"]},
    
    "F1": {"position": [11,11], "size": [1,2], "category": "Accessories", "products": ["Phone Case", "Screen Protector"]},
    "F2": {"position": [12,11], "size": [1,2], "category": "Accessories", "products": ["Cable", "Charger"]},
    "F3": {"position": [13,11], "size": [1,2], "category": "Accessories", "products": ["Power Bank", "Wireless Charger"]},
    "F4": {"position": [14,11], "size": [1,2], "category": "Accessories", "products": ["Memory Card", "USB Drive"]},
    "F5": {"position": [15,11], "size": [1,2], "category": "Accessories", "products": ["Adapter", "Hub"]},
    "F6": {"position": [16,11], "size": [1,2], "category": "Accessories", "products": ["Stand", "Mount"]},
}

# Vị trí beacon cố định - Đặt theo yêu cầu tại 9 vị trí chiến lược
BEACON_POSITIONS = {
    # API Beacons (ESP32 cập nhật qua HTTP API - không có MAC address)
    "ESP32_BEACON_001": {"position": [1, 14], "coverage_radius": 5, "area": "South-West Zone", "type": "api"},
    "ESP32_BEACON_002": {"position": [1, 9], "coverage_radius": 5, "area": "Central-West Zone", "type": "api"}, 
    "ESP32_BEACON_003": {"position": [1, 3], "coverage_radius": 5, "area": "North-West Zone", "type": "api"},
    "ESP32_BEACON_009": {"position": [9, 8], "coverage_radius": 5, "area": "Central Zone", "type": "api"},
    
    # BLE Beacons (ESP32 cập nhật qua BLE scanning - có MAC address)
    "ESP32_BEACON_004": {"position": [17, 9], "coverage_radius": 6, "area": "Central-East Zone", "type": "ble", "mac": "80:4B:50:56:A6:91"},
    "ESP32_BEACON_005": {"position": [17, 3], "coverage_radius": 6, "area": "North-East Zone", "type": "ble", "mac": "60:A4:23:C9:85:C1"},
    "ESP32_BEACON_006": {"position": [17, 14], "coverage_radius": 6, "area": "South-East Zone", "type": "ble", "mac": "80:4B:50:54:91:77"},
    "ESP32_BEACON_007": {"position": [9, 1], "coverage_radius": 5, "area": "North Center", "type": "ble", "mac": "80:4B:50:54:96:4A"},
    "ESP32_BEACON_008": {"position": [9, 15], "coverage_radius": 5, "area": "South Center", "type": "ble","mac": "34:25:B4:A0:C1:48"},
}

# Lối ra/vào và điểm quan trọng
LANDMARKS = {
    "MAIN_ENTRANCE": {"position": [0,0], "type": "entrance"},
    "MAIN_EXIT": {"position": [0,19], "type": "exit"},
    "EMERGENCY_EXIT_1": {"position": [19,0], "type": "emergency_exit"},
    "EMERGENCY_EXIT_2": {"position": [19,19], "type": "emergency_exit"},
    "CUSTOMER_SERVICE": {"position": [9,9], "type": "service"},
    "CHECKOUT_AREA": {"position": [1,9], "type": "checkout"},
    "CHECKOUT_WEST": {"position": [18,3], "type": "checkout"},
    "CHECKOUT_EAST": {"position": [18,14], "type": "checkout"},
}

# ===== function helper ======
def tinhkhoangcach(rssi, tx_power=-59, n=2.0):
    """
    Tính khoảng cách từ RSSI sử dụng công thức logarithmic
    
    Args:
        rssi (int): Giá trị RSSI đo được (dBm)
        tx_power (int): Công suất phát tín hiệu tại 1m (dBm) - mặc định -59
        n (float): Path loss exponent (2.0 cho môi trường tự do, 2-4 cho indoor)
    
    Returns:
        float: Khoảng cách tính toán (mét)
    """
    try:
        if rssi == 0:
            return -1.0
        
        # Công thức: Distance = 10^((Tx Power - RSSI) / (10 * n))
        distance = math.pow(10, (tx_power - rssi) / (10.0 * n))
        return round(distance, 2)
    except:
        return -1.0

def a_star_pathfinding(start, goal, grid, force_priority=False):
    """
    A* pathfinding algorithm to find optimal path while avoiding crowded areas
    and optionally going through priority products
    
    Args:
        start (tuple): Starting position (x, y)
        goal (tuple): Goal position (x, y)
        grid (list): 2D grid representing the map
        force_priority (bool): If True, path must go through at least one priority product
        
    Returns:
        list: Path as list of (x, y) tuples, or None if no path found
    """
    from heapq import heappush, heappop
    
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def get_neighbors(pos):
        x, y = pos
        neighbors = []
        # Only cardinal directions to prevent diagonal movement through obstacles
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < len(grid) and 0 <= ny < len(grid[0])):
                neighbors.append((nx, ny))
        return neighbors
    
    def is_walkable(pos):
        x, y = pos
        if not (0 <= x < len(grid) and 0 <= y < len(grid[0])):
            return False
        cell_type = grid[x][y]
        # 0 = walkable, 1 = shelf (NOT walkable), 2 = obstacle (NOT walkable), 
        # 3 = beacon (walkable), 4 = entrance (walkable), 5 = checkout (walkable)
        return cell_type not in [1, 2]  # Shelves and obstacles block movement
    
    def get_crowd_penalty(pos):
        """Get crowd penalty for a position (higher penalty = avoid more)"""
        x, y = pos
        for area_data in get_crowded_areas_data().values():
            if 'affected_positions' in area_data:
                for affected_pos in area_data['affected_positions']:
                    if affected_pos[0] == x and affected_pos[1] == y:
                        # Penalty based on crowd level: level 1-2=+2, level 3=+5, level 4-5=+10
                        crowd_level = area_data.get('crowd_level', 0)
                        if crowd_level <= 2:
                            return 2
                        elif crowd_level == 3:
                            return 5
                        else:  # level 4-5
                            return 10
        return 0  # No crowd penalty
    
    def get_priority_positions():
        """Get all active priority product positions"""
        priority_positions = []
        with priority_products_lock:
            for product_data in priority_products.values():
                if product_data.get('is_active', True):
                    pos = product_data['position']
                    # Get adjacent walkable positions around the shelf
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            adj_x, adj_y = pos[0] + dx, pos[1] + dy
                            if is_walkable((adj_x, adj_y)):
                                priority_positions.append((adj_x, adj_y))
        return priority_positions
    
    def is_near_priority_product(pos):
        """Check if position is near a priority product"""
        priority_positions = get_priority_positions()
        return pos in priority_positions
    
    # Special handling if goal is not walkable
    if not is_walkable(goal):
        # Find nearest walkable position to goal
        from collections import deque
        queue = deque([(goal, 0)])
        visited = {goal}
        
        while queue:
            pos, dist = queue.popleft()
            if is_walkable(pos):
                goal = pos
                break
            if dist < 5:  # Limit search radius
                for neighbor in get_neighbors(pos):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))
        
        if not is_walkable(goal):
            return None  # No walkable position found near goal
    
    # If force_priority is True, try to find path through priority products
    if force_priority:
        priority_positions = get_priority_positions()
        if priority_positions:
            # Try to find a path that goes through at least one priority position
            best_path = None
            best_total_cost = float('inf')
            
            for priority_pos in priority_positions:
                # Find path from start to priority position
                path_to_priority = a_star_pathfinding_simple(start, priority_pos, grid)
                if not path_to_priority:
                    continue
                
                # Find path from priority position to goal
                path_from_priority = a_star_pathfinding_simple(priority_pos, goal, grid)
                if not path_from_priority:
                    continue
                
                # Combine paths (remove duplicate priority position)
                full_path = path_to_priority + path_from_priority[1:]
                total_cost = len(full_path)
                
                if total_cost < best_total_cost:
                    best_total_cost = total_cost
                    best_path = full_path
            
            if best_path:
                return best_path
            # If no path through priority products found, fall back to normal pathfinding
    
    # Normal A* algorithm with crowd avoidance
    return a_star_pathfinding_simple(start, goal, grid)

def a_star_pathfinding_simple(start, goal, grid):
    """
    Simple A* pathfinding without priority product constraints
    """
    from heapq import heappush, heappop
    
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    def get_neighbors(pos):
        x, y = pos
        neighbors = []
        for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            nx, ny = x + dx, y + dy
            if (0 <= nx < len(grid) and 0 <= ny < len(grid[0])):
                neighbors.append((nx, ny))
        return neighbors
    
    def is_walkable(pos):
        x, y = pos
        if not (0 <= x < len(grid) and 0 <= y < len(grid[0])):
            return False
        cell_type = grid[x][y]
        return cell_type not in [1, 2]
    
    def get_crowd_penalty(pos):
        x, y = pos
        for area_data in get_crowded_areas_data().values():
            if 'affected_positions' in area_data:
                for affected_pos in area_data['affected_positions']:
                    if affected_pos[0] == x and affected_pos[1] == y:
                        crowd_level = area_data.get('crowd_level', 0)
                        if crowd_level <= 2:
                            return 2
                        elif crowd_level == 3:
                            return 5
                        else:
                            return 10
        return 0
    
    # A* algorithm
    open_set = []
    heappush(open_set, (0, start))
    came_from = {}
    g_score = {start: 0}
    f_score = {start: heuristic(start, goal)}
    
    while open_set:
        current = heappop(open_set)[1]
        
        if current == goal:
            # Reconstruct path
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]  # Reverse to get start->goal order
        
        for neighbor in get_neighbors(current):
            if not is_walkable(neighbor):
                continue
                
            # Calculate cost with crowd penalty
            base_cost = 1
            crowd_penalty = get_crowd_penalty(neighbor)
            movement_cost = base_cost + crowd_penalty
            
            tentative_g_score = g_score[current] + movement_cost
            
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heappush(open_set, (f_score[neighbor], neighbor))
    
    return None  # No path found

def generate_text_directions(path):
    """
    Generate human-readable directions from a path
    
    Args:
        path (list): List of (x, y) tuples representing the path
        
    Returns:
        list: List of direction strings
    """
    if len(path) < 2:
        return ["You are already at your destination."]
    
    directions = []
    
    for i in range(len(path) - 1):
        current = path[i]
        next_pos = path[i + 1]
        
        dx = next_pos[0] - current[0]
        dy = next_pos[1] - current[1]
        
        if dx == 1:
            direction = "Go down"
        elif dx == -1:
            direction = "Go up"
        elif dy == 1:
            direction = "Go right"
        elif dy == -1:
            direction = "Go left"
        else:
            direction = "Continue"
        
        # Group consecutive moves in same direction
        if directions and directions[-1].startswith(direction.split()[1] if len(direction.split()) > 1 else direction):
            continue
        
        directions.append(f"{direction} to ({next_pos[0]}, {next_pos[1]})")
    
    directions.append("You have arrived at your destination!")
    return directions

def find_product_location(product_name):
    """
    Find the location of a specific product
    
    Args:
        product_name (str): Name of the product to find
        
    Returns:
        dict: Shelf information containing the product, or None if not found
    """
    for shelf_id, shelf_info in SHELVES_INFO.items():
        for product in shelf_info['products']:
            if product_name.lower() in product.lower():
                return {
                    "shelf_id": shelf_id,
                    "product": product,
                    "category": shelf_info['category'],
                    "position": shelf_info['position'],
                    "size": shelf_info['size'],
                    "center_position": [
                        shelf_info['position'][0] + shelf_info['size'][0] // 2,
                        shelf_info['position'][1] + shelf_info['size'][1] // 2
                    ]
                }
    return None

def store_beacon_rssi(rssi_data):
    """
    Lưu trữ dữ liệu RSSI từ beacon mà không cập nhật vị trí ngay lập tức
    
    Args:
        rssi_data (dict): Dữ liệu RSSI từ beacon
        
    Returns:
        bool: True nếu lưu thành công
    """
    if 'sgt_device' not in rssi_data or not rssi_data['sgt_device']:
        return False
        
    beacon_id = rssi_data['beacon_id']
    sgt_device = rssi_data['sgt_device']
    rssi = sgt_device.get('rssi', 0)
    
    if beacon_id in BEACON_POSITIONS and rssi != 0:
        distance = tinhkhoangcach(rssi)
        
        # Lưu trữ RSSI và khoảng cách của beacon với thread safety
        with beacon_lock:
            global current_beacon_rssi
            current_beacon_rssi[beacon_id] = {
                "rssi": rssi,
                "distance": distance,
                "timestamp": datetime.now().isoformat(),
                "position": BEACON_POSITIONS[beacon_id]['position']
            }
        
        return True
    
    return False

def find_nearest_beacon_from_stored():
    """
    Tìm beacon gần nhất dựa trên RSSI đã lưu trữ
    
    Returns:
        dict: Thông tin beacon gần nhất hoặc None
    """
    with beacon_lock:
        if not current_beacon_rssi:
            return None
        
        # Tạo bản sao của dữ liệu để tránh giữ lock quá lâu
        beacon_data_copy = dict(current_beacon_rssi)
    
    # Tìm beacon có khoảng cách nhỏ nhất (RSSI cao nhất)
    nearest_beacon = None
    min_distance = float('inf')
    
    # Xử lý dữ liệu ngoài lock
    for beacon_id, beacon_data in beacon_data_copy.items():
        if beacon_data['distance'] < min_distance:
            min_distance = beacon_data['distance']
            nearest_beacon = {
                "beacon_id": beacon_id,
                "position": beacon_data['position'],
                "distance": beacon_data['distance'],
                "rssi": beacon_data['rssi']
            }
    
    return nearest_beacon

def update_user_position():
    """
    Cập nhật vị trí người dùng dựa trên beacon gần nhất
    Chỉ cập nhật nếu không đang được admin điều khiển
    
    Returns:
        dict: Vị trí người dùng được cập nhật hoặc None nếu admin đang điều khiển
    """
    global current_user_position
    
    # Không cập nhật nếu admin đang điều khiển vị trí
    if current_user_position.get('admin_controlled', False):
        print("🔒 Position update skipped - Admin control active")
        return current_user_position
    
    nearest_beacon = find_nearest_beacon_from_stored()
    
    if nearest_beacon:
        current_user_position.update({
            "x": nearest_beacon['position'][0],
            "y": nearest_beacon['position'][1],
            "last_beacon": nearest_beacon['beacon_id'],
            "last_update": datetime.now().isoformat(),
            "distance_to_beacon": nearest_beacon['distance'],
            "rssi": nearest_beacon['rssi'],
            "admin_controlled": False  # Ensure admin_controlled is False for beacon updates
        })
        
        return current_user_position
    
    return None

# def periodic_position_update():
#     """
#     Hàm chạy trong background để cập nhật vị trí người dùng mỗi 3 giây
#     COMMENTED: Client sẽ gọi API để cập nhật vị trí thay vì dùng auto update
#     """
#     while True:
#         try:
#             # Cập nhật vị trí người dùng dựa trên beacon gần nhất
#             updated_position = update_user_position()
#             
#             if updated_position:
#                 print(f"🔄 Periodic position update: ({updated_position['x']}, {updated_position['y']}) from beacon {updated_position['last_beacon']}")
#                 
#                 # Gửi cập nhật vị trí qua WebSocket
#                 socketio.emit('position_update', {
#                     'position': updated_position,
#                     'nearby_shelves': get_nearby_shelves(updated_position)
#                 }, namespace='/')
#             else:
#                 print("⚠️ No beacon data available for position update")
#                 
#         except Exception as e:
#             print(f"❌ Error in periodic position update: {str(e)}")
#             import traceback
#             traceback.print_exc()
#         
#         # Chờ 3 giây trước khi cập nhật tiếp theo
#         time.sleep(3)

def find_closest_beacon(rssi_data):
    """
    Tìm beacon gần nhất dựa trên RSSI và cập nhật vị trí người dùng
    
    Args:
        rssi_data (dict): Dữ liệu RSSI từ beacon
        
    Returns:
        dict: Thông tin vị trí người dùng được cập nhật
    """
    if 'sgt_device' not in rssi_data or not rssi_data['sgt_device']:
        return None
        
    beacon_id = rssi_data['beacon_id']
    sgt_device = rssi_data['sgt_device']
    rssi = sgt_device.get('rssi', 0)
    
    if beacon_id in BEACON_POSITIONS and rssi != 0:
        beacon_pos = BEACON_POSITIONS[beacon_id]['position']
        distance = tinhkhoangcach(rssi)
        
        # Cập nhật vị trí người dùng (giả định người dùng ở gần beacon)
        # Có thể cải tiến bằng triangulation với nhiều beacon
        global current_user_position
        current_user_position.update({
            "x": beacon_pos[0],
            "y": beacon_pos[1], 
            "last_beacon": beacon_id,
            "last_update": datetime.now().isoformat(),
            "distance_to_beacon": distance,
            "rssi": rssi
        })
        
        return current_user_position
    
    return None

def get_nearby_shelves(position, radius=3):
    """
    Tìm các kệ hàng gần vị trí hiện tại
    
    Args:
        position (dict): Vị trí hiện tại {x, y}
        radius (int): Bán kính tìm kiếm
        
    Returns:
        list: Danh sách kệ hàng gần đó
    """
    nearby_shelves = []
    user_x, user_y = position['x'], position['y']
    
    for shelf_id, shelf_info in SHELVES_INFO.items():
        shelf_x, shelf_y = shelf_info['position']
        distance = math.sqrt((user_x - shelf_x)**2 + (user_y - shelf_y)**2)
        
        if distance <= radius:
            nearby_shelves.append({
                "id": shelf_id,
                "distance": round(distance, 2),
                "category": shelf_info['category'],
                "products": shelf_info['products']
            })
    
    return sorted(nearby_shelves, key=lambda x: x['distance'])

def update_crowded_area(area_data):
    """
    Cập nhật thông tin vùng đông người
    
    Args:
        area_data (dict): Thông tin vùng đông người từ AI
        
    Returns:
        bool: True nếu cập nhật thành công
    """
    try:
        required_fields = ['area_id', 'position', 'crowd_level', 'people_count']
        if not all(field in area_data for field in required_fields):
            return False
        
        area_id = area_data['area_id']
        center_pos = area_data['position']
        
        # Tính toán các vị trí trong bán kính 1 ô xung quanh (chỉ đường đi)
        affected_positions = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                x, y = center_pos[0] + dx, center_pos[1] + dy
                # Kiểm tra trong bounds và chỉ thêm nếu là đường đi (cell type 0, 3, 4, 5)
                if (0 <= x < MAP_LAYOUT['height'] and 0 <= y < MAP_LAYOUT['width'] and
                    MAP_LAYOUT['grid'][x][y] in [0, 3, 4, 5]):  # 0=walkable, 3=beacon, 4=entrance, 5=checkout
                    affected_positions.append([x, y])
        
        with crowded_areas_lock:
            crowded_areas[area_id] = {
                "position": area_data['position'],
                "size": area_data.get('size', [1, 1]),  # Keep original size for reference
                "affected_positions": affected_positions,  # New field for expanded positions
                "crowd_level": max(0, min(5, area_data['crowd_level'])),  # Clamp 0-5
                "people_count": max(0, area_data['people_count']),
                "last_update": datetime.now().isoformat(),
                "description": area_data.get('description', f"Area {area_id}"),
                "confidence": area_data.get('confidence', 0.8)  # AI confidence level
            }
        
        print(f"📊 Updated crowded area {area_id}: {area_data['people_count']} people, level {area_data['crowd_level']}, affecting {len(affected_positions)} walkable positions")
        return True
        
    except Exception as e:
        print(f"❌ Error updating crowded area: {str(e)}")
        return False

def get_crowded_areas_data():
    """
    Lấy dữ liệu tất cả vùng đông người
    
    Returns:
        dict: Copy của dữ liệu crowded areas
    """
    with crowded_areas_lock:
        return dict(crowded_areas)

def cleanup_old_crowded_areas(max_age_minutes=10):
    """
    Xóa dữ liệu vùng đông người cũ (quá 10 phút không cập nhật)
    
    Args:
        max_age_minutes (int): Thời gian tối đa (phút) trước khi xóa dữ liệu cũ
    """
    try:
        current_time = datetime.now()
        areas_to_remove = []
        
        with crowded_areas_lock:
            for area_id, area_info in crowded_areas.items():
                last_update = datetime.fromisoformat(area_info['last_update'])
                age_minutes = (current_time - last_update).total_seconds() / 60
                
                if age_minutes > max_age_minutes:
                    areas_to_remove.append(area_id)
            
            for area_id in areas_to_remove:
                del crowded_areas[area_id]
                print(f"🧹 Cleaned up old crowded area: {area_id}")
        
        return len(areas_to_remove)
        
    except Exception as e:
        print(f"❌ Error cleaning up crowded areas: {str(e)}")
        return 0

def get_crowd_level_description(level):
    """
    Chuyển đổi crowd level thành mô tả
    
    Args:
        level (int): Mức độ đông người (0-5)
        
    Returns:
        str: Mô tả mức độ đông người
    """
    descriptions = {
        0: "Empty",
        1: "Very Low", 
        2: "Low",
        3: "Moderate",
        4: "High",
        5: "Very Crowded"
    }
    return descriptions.get(level, "Unknown")

def update_checkout_queue(checkout_data):
    """
    Cập nhật thông tin hàng đợi quầy thu ngân từ AI
    
    Args:
        checkout_data (dict): Dữ liệu từ camera AI
        
    Returns:
        bool: True nếu cập nhật thành công
    """
    try:
        required_fields = ['camera_id', 'people_count']
        if not all(field in checkout_data for field in required_fields):
            return False
        
        camera_id = checkout_data['camera_id']
        
        # Tìm checkout tương ứng với camera_id
        checkout_id = None
        for cid, cdata in checkout_queues.items():
            if cdata['camera_id'] == camera_id:
                checkout_id = cid
                break
        
        if not checkout_id:
            print(f"❌ Camera ID {camera_id} không tương ứng với quầy thu ngân nào")
            return False
        
        with checkout_queues_lock:
            # Cập nhật dữ liệu
            checkout_queues[checkout_id].update({
                "people_count": max(0, checkout_data['people_count']),
                "queue_length": checkout_data.get('queue_length', checkout_data['people_count']),
                "wait_time_estimate": checkout_data.get('wait_time_estimate', checkout_data['people_count'] * 2),  # 2 phút/người
                "last_update": datetime.now().isoformat(),
                "status": checkout_data.get('status', 'open')
            })
        
        print(f"💳 Updated checkout {checkout_id}: {checkout_data['people_count']} people, camera {camera_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating checkout queue: {str(e)}")
        return False

def get_checkout_queues_data():
    """
    Lấy dữ liệu tất cả quầy thu ngân
    
    Returns:
        dict: Copy của dữ liệu checkout queues
    """
    with checkout_queues_lock:
        return dict(checkout_queues)

def find_best_checkout(user_position=None):
    """
    Tìm quầy thu ngân tốt nhất dựa trên:
    1. Số người chờ ít nhất
    2. Khoảng cách gần nhất (nếu user_position có sẵn)
    
    Args:
        user_position (dict): Vị trí hiện tại của user
        
    Returns:
        dict: Thông tin quầy thu ngân tốt nhất
    """
    try:
        checkout_data = get_checkout_queues_data()
        
        # Lọc các quầy đang mở
        open_checkouts = {
            cid: cdata for cid, cdata in checkout_data.items() 
            if cdata['status'] == 'open'
        }
        
        if not open_checkouts:
            return None
        
        best_checkout = None
        best_score = float('inf')
        
        for checkout_id, checkout_info in open_checkouts.items():
            # Tính điểm dựa trên số người chờ (trọng số cao)
            queue_score = checkout_info['people_count'] * 10
            
            # Tính điểm khoảng cách nếu có vị trí user
            distance_score = 0
            if user_position and user_position.get('x') is not None:
                user_x, user_y = user_position['x'], user_position['y']
                checkout_x, checkout_y = checkout_info['position']
                distance = math.sqrt((user_x - checkout_x)**2 + (user_y - checkout_y)**2)
                distance_score = distance * 2  # Trọng số thấp hơn
            
            total_score = queue_score + distance_score
            
            if total_score < best_score:
                best_score = total_score
                best_checkout = {
                    "checkout_id": checkout_id,
                    "position": checkout_info['position'],
                    "people_count": checkout_info['people_count'],
                    "queue_length": checkout_info['queue_length'],
                    "wait_time_estimate": checkout_info['wait_time_estimate'],
                    "distance": distance_score / 2 if user_position else None,
                    "camera_id": checkout_info['camera_id']
                }
        
        return best_checkout
        
    except Exception as e:
        print(f"❌ Error finding best checkout: {str(e)}")
        return None

def cleanup_old_checkout_data(max_age_minutes=15):
    """
    Xóa dữ liệu quầy thu ngân cũ (quá 15 phút không cập nhật)
    
    Args:
        max_age_minutes (int): Thời gian tối đa (phút) trước khi reset dữ liệu
    """
    try:
        current_time = datetime.now()
        
        with checkout_queues_lock:
            for checkout_id, checkout_info in checkout_queues.items():
                if checkout_info['last_update']:
                    last_update = datetime.fromisoformat(checkout_info['last_update'])
                    age_minutes = (current_time - last_update).total_seconds() / 60
                    
                    if age_minutes > max_age_minutes:
                        # Reset về giá trị mặc định
                        checkout_queues[checkout_id].update({
                            "people_count": 0,
                            "queue_length": 0,
                            "wait_time_estimate": 0,
                            "last_update": None
                        })
                        print(f"🧹 Reset old checkout data: {checkout_id}")
        
    except Exception as e:
        print(f"❌ Error cleaning up checkout data: {str(e)}")

def get_priority_products_data():
    """
    Lấy dữ liệu tất cả sản phẩm ưu tiên
    
    Returns:
        dict: Copy của dữ liệu priority products
    """
    with priority_products_lock:
        return dict(priority_products)

def add_priority_product(product_data):
    """
    Thêm sản phẩm ưu tiên mới
    
    Args:
        product_data (dict): Thông tin sản phẩm ưu tiên
        
    Returns:
        bool: True nếu thêm thành công
    """
    try:
        required_fields = ['product_name', 'shelf_id', 'priority_level']
        if not all(field in product_data for field in required_fields):
            return False
        
        product_name = product_data['product_name']
        shelf_id = product_data['shelf_id']
        
        # Kiểm tra shelf_id có tồn tại không
        if shelf_id not in SHELVES_INFO:
            return False
        
        # Kiểm tra sản phẩm có trong shelf không
        shelf_info = SHELVES_INFO[shelf_id]
        if product_name not in shelf_info['products']:
            return False
        
        # Tạo product_id unique
        product_id = f"{shelf_id}_{product_name.replace(' ', '_').lower()}"
        
        with priority_products_lock:
            priority_products[product_id] = {
                "product_name": product_name,
                "shelf_id": shelf_id,
                "position": shelf_info['position'],
                "priority_level": max(1, min(5, product_data['priority_level'])),  # Clamp 1-5
                "category": shelf_info['category'],
                "description": product_data.get('description', f"Priority product in {shelf_id}"),
                "created_at": datetime.now().isoformat(),
                "is_active": product_data.get('is_active', True)
            }
        
        print(f"✨ Added priority product: {product_name} in {shelf_id} (Level {product_data['priority_level']})")
        return True
        
    except Exception as e:
        print(f"❌ Error adding priority product: {str(e)}")
        return False

def update_priority_product(product_id, updates):
    """
    Cập nhật thông tin sản phẩm ưu tiên
    
    Args:
        product_id (str): ID của sản phẩm
        updates (dict): Dữ liệu cần cập nhật
        
    Returns:
        bool: True nếu cập nhật thành công
    """
    try:
        with priority_products_lock:
            if product_id not in priority_products:
                return False
            
            # Update allowed fields
            allowed_fields = ['priority_level', 'description', 'is_active']
            for field in allowed_fields:
                if field in updates:
                    if field == 'priority_level':
                        priority_products[product_id][field] = max(1, min(5, updates[field]))
                    else:
                        priority_products[product_id][field] = updates[field]
            
            priority_products[product_id]['updated_at'] = datetime.now().isoformat()
        
        print(f"🔄 Updated priority product: {product_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating priority product: {str(e)}")
        return False

def remove_priority_product(product_id):
    """
    Xóa sản phẩm ưu tiên
    
    Args:
        product_id (str): ID của sản phẩm
        
    Returns:
        bool: True nếu xóa thành công
    """
    try:
        with priority_products_lock:
            if product_id in priority_products:
                del priority_products[product_id]
                print(f"🗑️ Removed priority product: {product_id}")
                return True
        return False
        
    except Exception as e:
        print(f"❌ Error removing priority product: {str(e)}")
        return False

def get_active_priority_products():
    """
    Lấy danh sách sản phẩm ưu tiên đang hoạt động
    
    Returns:
        dict: Dữ liệu sản phẩm ưu tiên đang hoạt động
    """
    with priority_products_lock:
        return {
            pid: pdata for pid, pdata in priority_products.items() 
            if pdata.get('is_active', True)
        }
# ===== API ROUTES =====

@app.route('/')
def index():
    """Main page - Hiển thị bản đồ navigation"""
    # Lấy parameters từ URL để dẫn đường
    start_x = request.args.get('start_x', type=int)
    start_y = request.args.get('start_y', type=int)
    end_x = request.args.get('end_x', type=int)
    end_y = request.args.get('end_y', type=int)
    product = request.args.get('product', '')
    shelf_id = request.args.get('shelf', '')
    
    return render_template('index.html', 
                         start_x=start_x, start_y=start_y,
                         end_x=end_x, end_y=end_y,
                         product=product, shelf_id=shelf_id)

@app.route('/admin')
def admin():
    """Admin page - Điều khiển vị trí user (không cần mật khẩu)"""
    return render_template('admin.html')

@app.route('/api')
def api_info():
    """API information"""
    return jsonify({
        "status": "SmartMall Navigation System",
        "message": "Professional Indoor Navigation with Real-time Positioning & Crowd Detection",
        "version": "2.1",
        "features": [
            "Smart Product Search",
            "Real-time Position Tracking", 
            "Optimized Route Planning",
            "Category-based Navigation",
            "Professional UI/UX",
            "AI-powered Crowd Detection",
            "Real-time Crowd Monitoring",
            "Admin Position Control"
        ],
        "endpoints": {
            "/": "GET - Modern navigation interface",
            "/admin": "GET - Admin control panel (no password required)",
            "/api/beacon/rssi": "POST - Receive beacon data, GET - Get current RSSI data",
            "/api/navigation/products": "GET - Search products by name or category",
            "/api/navigation/shelves": "GET - Get all shelves information",
            "/api/navigation/route": "POST - Calculate optimal route between points (supports force_priority parameter)",
            "/api/map": "GET - Get store layout and map data (includes crowd data and priority products)",
            "/api/position": "GET - Get current user position",
            "/api/crowd/areas": "GET - Get all crowded areas information",
            "/api/crowd/update": "POST - Update crowd detection data (for AI systems)",
            "/api/crowd/clear": "POST - Clear all crowd data",
            "/api/checkout/queues": "GET - Get all checkout queue information",
            "/api/checkout/best": "GET - Find best checkout based on queue and distance",
            "/api/checkout/navigate": "POST - Calculate route to best checkout",
            "/api/checkout/update": "POST - Update checkout queue data (for AI systems)",
            "/api/priority/products": "GET - Get all priority products, POST - Add priority products",
            "/api/priority/products/<product_id>": "PUT - Update priority product, DELETE - Remove priority product",
            "/api/priority/products/clear": "POST - Clear all priority products",
            "/api/admin/position/set": "POST - Admin set user position manually",
            "/api/admin/stats": "GET - Get admin statistics and system status"
        },
        "websocket_events": {
            "connect": "Sends initial map and position data (includes priority products)",
            "crowd_update": "Real-time crowd area updates",
            "crowd_cleared": "Notification when crowd data is cleared",
            "position_update": "Real-time position updates",
            "checkout_update": "Real-time checkout queue updates",
            "priority_products_update": "Real-time priority products updates",
            "request_priority_products": "Request current priority products data",
            "admin_position_control": "Admin control user position via WebSocket",
            "admin_request_stats": "Admin request system statistics",
            "admin_clear_control": "Admin clear position control"
        }
    })

@app.route('/api/navigation/products', methods=['GET'])
def search_products():
    """Search for products in the store"""
    query = request.args.get('q', '').lower()
    category = request.args.get('category', '').lower()
    
    products = []
    for shelf_id, shelf_info in SHELVES_INFO.items():
        shelf_products = shelf_info['products']
        shelf_category = shelf_info['category'].lower()
        
        # Filter by category if specified
        if category and category not in shelf_category:
            continue
            
        # Search products
        for product in shelf_products:
            if not query or query in product.lower():
                products.append({
                    "product": product,
                    "shelf_id": shelf_id,
                    "category": shelf_info['category'],
                    "position": shelf_info['position'],
                    "size": shelf_info['size']
                })
    
    return jsonify({
        "status": "success",
        "query": query,
        "category": category,
        "results": products,
        "total": len(products)
    })

@app.route('/api/navigation/shelves', methods=['GET'])
def get_all_shelves():
    """Get all shelves with their products"""
    shelves = []
    for shelf_id, shelf_info in SHELVES_INFO.items():
        shelf_data = {
            "shelf_id": shelf_id,
            "category": shelf_info['category'],
            "products": shelf_info['products'],
            "position": shelf_info['position'],
            "size": shelf_info['size'],
            "center_position": [
                shelf_info['position'][0] + shelf_info['size'][0] // 2,
                shelf_info['position'][1] + shelf_info['size'][1] // 2
            ]
        }
        shelves.append(shelf_data)
    
    return jsonify({
        "status": "success",
        "shelves": shelves,
        "total": len(shelves)
    })

@app.route('/api/navigation/route', methods=['POST'])
def calculate_route():
    """Calculate route between two points using A* pathfinding with optional priority products"""
    try:
        data = request.get_json()
        start = data.get('start', {})
        end = data.get('end', {})
        force_priority = data.get('force_priority', False)  # New parameter
        
        if not start or not end:
            return jsonify({
                "status": "error",
                "message": "Start and end positions are required"
            }), 400
        
        start_x = start.get('x')
        start_y = start.get('y')
        end_x = end.get('x')
        end_y = end.get('y')
        
        if any(coord is None for coord in [start_x, start_y, end_x, end_y]):
            return jsonify({
                "status": "error",
                "message": "Invalid coordinates provided"
            }), 400
        
        # Validate coordinates are within map bounds
        if not (0 <= start_x < MAP_LAYOUT['height'] and 0 <= start_y < MAP_LAYOUT['width'] and
                0 <= end_x < MAP_LAYOUT['height'] and 0 <= end_y < MAP_LAYOUT['width']):
            return jsonify({
                "status": "error",
                "message": "Coordinates out of map bounds"
            }), 400
        
        # Calculate path using A* algorithm with priority product option
        path = a_star_pathfinding(
            (start_x, start_y), 
            (end_x, end_y), 
            MAP_LAYOUT['grid'],
            force_priority=force_priority
        )
        
        if path:
            # Check which priority products the path passes near
            priority_products_visited = []
            active_priorities = get_active_priority_products()
            
            for product_id, product_data in active_priorities.items():
                product_pos = product_data['position']
                # Check if path passes within 1 cell of the product
                for path_pos in path:
                    distance = abs(path_pos[0] - product_pos[0]) + abs(path_pos[1] - product_pos[1])
                    if distance <= 1:
                        priority_products_visited.append({
                            "product_id": product_id,
                            "product_name": product_data['product_name'],
                            "shelf_id": product_data['shelf_id'],
                            "priority_level": product_data['priority_level']
                        })
                        break
            
            return jsonify({
                "status": "success",
                "start": {"x": start_x, "y": start_y},
                "end": {"x": end_x, "y": end_y},
                "path": [{"x": x, "y": y} for x, y in path],
                "distance": len(path),
                "estimated_time": len(path) * 2,  # 2 seconds per step
                "force_priority": force_priority,
                "priority_products_visited": priority_products_visited,
                "total_priority_products": len(priority_products_visited)
            })
        else:
            return jsonify({
                "status": "error",
                "message": "No path found between start and end points"
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error calculating route: {str(e)}"
        }), 500

@app.route('/api/navigation/directions', methods=['GET'])
def get_directions():
    """Get directions with URL parameters"""
    try:
        # Get parameters from URL
        start_x = request.args.get('start_x', type=int)
        start_y = request.args.get('start_y', type=int)
        end_x = request.args.get('end_x', type=int)
        end_y = request.args.get('end_y', type=int)
        product = request.args.get('product', '')
        shelf_id = request.args.get('shelf', '')
        
        # If looking for a product or shelf, find the destination
        if product and not (end_x and end_y):
            # Search for product
            for sid, shelf_info in SHELVES_INFO.items():
                if product.lower() in [p.lower() for p in shelf_info['products']]:
                    end_x = shelf_info['position'][0] + shelf_info['size'][0] // 2
                    end_y = shelf_info['position'][1] + shelf_info['size'][1] // 2
                    shelf_id = sid
                    break
            
            if not (end_x and end_y):
                return jsonify({
                    "status": "error",
                    "message": f"Product '{product}' not found"
                }), 404
        
        if shelf_id and not (end_x and end_y):
            # Get shelf position
            if shelf_id in SHELVES_INFO:
                shelf_info = SHELVES_INFO[shelf_id]
                end_x = shelf_info['position'][0] + shelf_info['size'][0] // 2
                end_y = shelf_info['position'][1] + shelf_info['size'][1] // 2
            else:
                return jsonify({
                    "status": "error",
                    "message": f"Shelf '{shelf_id}' not found"
                }), 404
        
        # Use current position if start not specified
        if not (start_x and start_y):
            if current_user_position['last_beacon']:
                start_x = current_user_position['x']
                start_y = current_user_position['y']
            else:
                return jsonify({
                    "status": "error",
                    "message": "Current position not available and start position not specified"
                }), 400
        
        # Validate all coordinates are provided
        if not all([start_x is not None, start_y is not None, end_x is not None, end_y is not None]):
            return jsonify({
                "status": "error",
                "message": "Start and end coordinates are required"
            }), 400
        
        # Calculate route
        path = a_star_pathfinding(
            (start_x, start_y),
            (end_x, end_y),
            MAP_LAYOUT['grid']
        )
        
        if path:
            # Generate text directions
            directions = generate_text_directions(path)
            
            return jsonify({
                "status": "success",
                "start": {"x": start_x, "y": start_y},
                "end": {"x": end_x, "y": end_y},
                "product": product,
                "shelf_id": shelf_id,
                "path": [{"x": x, "y": y} for x, y in path],
                "directions": directions,
                "distance": len(path),
                "estimated_time": len(path) * 2
            })
        else:
            return jsonify({
                "status": "error",
                "message": "No path found"
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error getting directions: {str(e)}"
        }), 500

@app.route('/api/position', methods=['GET'])
def get_current_position():
    """Get current user position"""
    nearby_shelves = get_nearby_shelves(current_user_position) if current_user_position['last_beacon'] else []
    
    return jsonify({
        "status": "success",
        "position": current_user_position,
        "nearby_shelves": nearby_shelves
    })

@app.route('/api/debug/websocket', methods=['GET'])
def debug_websocket_status():
    """Endpoint to check WebSocket connection status"""
    return jsonify({
        "status": "success",
        "active_connections": len(socketio.server.eio.sockets),
        "last_position_update": current_user_position.get('last_update')
    })

@app.route('/api/position/update', methods=['GET'])
def update_position_endpoint():
    """
    API endpoint for client to call every 3 seconds to update position
    Client sẽ gọi endpoint này thay vì dùng automatic WebSocket updates
    """
    try:
        # Cập nhật vị trí người dùng dựa trên beacon gần nhất
        updated_position = update_user_position()
        
        if updated_position:
            print(f"🔄 API position update: ({updated_position['x']}, {updated_position['y']}) from beacon {updated_position['last_beacon']}")
            
            nearby_shelves = get_nearby_shelves(updated_position)
            
            return jsonify({
                "status": "success",
                "position_updated": True,
                "position": updated_position,
                "nearby_shelves": nearby_shelves,
                "timestamp": datetime.now().isoformat()
            })
        else:
            print("⚠️ No beacon data available for API position update")
            return jsonify({
                "status": "success",
                "position_updated": False,
                "message": "No beacon data available",
                "position": current_user_position,
                "nearby_shelves": get_nearby_shelves(current_user_position) if current_user_position['last_beacon'] else [],
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        print(f"❌ Error in API position update: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "message": f"Error updating position: {str(e)}",
            "position": current_user_position,
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/map', methods=['GET'])
def get_map():
    """Get map layout and information"""
    return jsonify({
        "status": "success",
        "map_layout": MAP_LAYOUT,
        "shelves_info": SHELVES_INFO,
        "beacon_positions": BEACON_POSITIONS,
        "landmarks": LANDMARKS,
        "crowded_areas": get_crowded_areas_data(),
        "checkout_queues": get_checkout_queues_data(),
        "priority_products": get_priority_products_data()
    })

@app.route('/api/crowd/areas', methods=['GET'])
def get_crowded_areas():
    """Get all current crowded areas information"""
    areas_data = get_crowded_areas_data()
    
    # Add descriptions to crowd levels
    for area_id, area_info in areas_data.items():
        area_info['crowd_description'] = get_crowd_level_description(area_info['crowd_level'])
    
    return jsonify({
        "status": "success",
        "total_areas": len(areas_data),
        "crowded_areas": areas_data,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/crowd/update', methods=['POST'])
def update_crowd_data():
    """
    API endpoint for Raspberry Pi AI to send crowd detection data
    
    Expected JSON format:
    {
        "area_id": "zone_A1",
        "position": [2, 3],
        "size": [3, 3],
        "crowd_level": 4,
        "people_count": 12,
        "confidence": 0.85,
        "description": "Shelf A1 area",
        "camera_id": "cam_001",
        "timestamp": "2024-01-01T12:00:00"
    }
    
    Or batch update:
    {
        "areas": [
            {area_data1},
            {area_data2},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        updated_areas = []
        failed_areas = []
        
        # Handle batch updates
        if 'areas' in data:
            areas_list = data['areas']
            if not isinstance(areas_list, list):
                return jsonify({
                    "status": "error",
                    "message": "Areas must be a list"
                }), 400
        else:
            # Single area update
            areas_list = [data]
        
        # Process each area
        for area_data in areas_list:
            # Validate required fields
            required_fields = ['area_id', 'position', 'crowd_level', 'people_count']
            if not all(field in area_data for field in required_fields):
                failed_areas.append({
                    "area_id": area_data.get('area_id', 'unknown'),
                    "error": "Missing required fields"
                })
                continue
            
            # Validate data types and ranges
            try:
                area_id = str(area_data['area_id'])
                position = area_data['position']
                crowd_level = int(area_data['crowd_level'])
                people_count = int(area_data['people_count'])
                
                if not isinstance(position, list) or len(position) != 2:
                    raise ValueError("Position must be [x, y]")
                
                if crowd_level < 0 or crowd_level > 5:
                    raise ValueError("Crowd level must be 0-5")
                    
                if people_count < 0:
                    raise ValueError("People count must be >= 0")
                
            except (ValueError, TypeError) as e:
                failed_areas.append({
                    "area_id": area_data.get('area_id', 'unknown'),
                    "error": f"Invalid data format: {str(e)}"
                })
                continue
            
            # Update the crowded area
            success = update_crowded_area(area_data)
            
            if success:
                updated_areas.append(area_id)
                print(f"🤖 AI Update - Area {area_id}: {people_count} people, level {crowd_level}")
                
                # Send real-time update to connected clients
                socketio.emit('crowd_update', {
                    'area_id': area_id,
                    'area_data': get_crowded_areas_data().get(area_id),
                    'timestamp': datetime.now().isoformat()
                }, namespace='/')
                
            else:
                failed_areas.append({
                    "area_id": area_id,
                    "error": "Failed to update area data"
                })
        
        # Cleanup old data
        cleaned_count = cleanup_old_crowded_areas()
        
        return jsonify({
            "status": "success",
            "message": f"Processed {len(areas_list)} area(s)",
            "updated_areas": updated_areas,
            "failed_areas": failed_areas,
            "total_updated": len(updated_areas),
            "total_failed": len(failed_areas),
            "cleaned_old_areas": cleaned_count,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error in crowd update API: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/api/crowd/clear', methods=['POST'])
def clear_crowd_data():
    """Clear all crowded areas data (for testing/reset)"""
    try:
        with crowded_areas_lock:
            cleared_count = len(crowded_areas)
            crowded_areas.clear()
        
        # Notify clients about clearing
        socketio.emit('crowd_cleared', {
            'message': 'All crowd data cleared',
            'timestamp': datetime.now().isoformat()
        }, namespace='/')
        
        return jsonify({
            "status": "success",
            "message": f"Cleared {cleared_count} crowded areas",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error clearing crowd data: {str(e)}"
        }), 500

@app.route('/api/checkout/queues', methods=['GET'])
def get_checkout_queues():
    """Get all checkout queue information"""
    queues_data = get_checkout_queues_data()
    
    return jsonify({
        "status": "success",
        "total_checkouts": len(queues_data),
        "checkout_queues": queues_data,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/checkout/best', methods=['GET'])
def get_best_checkout():
    """Find the best checkout based on queue length and distance"""
    try:
        # Lấy vị trí hiện tại của user nếu có
        user_position = current_user_position if current_user_position.get('last_beacon') else None
        
        best_checkout = find_best_checkout(user_position)
        
        if best_checkout:
            return jsonify({
                "status": "success",
                "best_checkout": best_checkout,
                "user_position": user_position,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Không có quầy thu ngân nào đang mở",
                "timestamp": datetime.now().isoformat()
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error finding best checkout: {str(e)}"
        }), 500

@app.route('/api/checkout/navigate', methods=['POST'])
def navigate_to_best_checkout():
    """Calculate route to the best checkout"""
    try:
        # Kiểm tra vị trí user
        if not current_user_position or not current_user_position.get('last_beacon'):
            return jsonify({
                "status": "error",
                "message": "Chưa xác định được vị trí hiện tại"
            }), 400
        
        # Tìm quầy thu ngân tốt nhất
        best_checkout = find_best_checkout(current_user_position)
        
        if not best_checkout:
            return jsonify({
                "status": "error",
                "message": "Không có quầy thu ngân nào đang mở"
            }), 404
        
        # Tính toán đường đi
        start_pos = current_user_position
        end_pos = {"x": best_checkout['position'][0], "y": best_checkout['position'][1]}
        
        path = a_star_pathfinding(
            (start_pos['x'], start_pos['y']),
            (end_pos['x'], end_pos['y']),
            MAP_LAYOUT['grid']
        )
        
        if path:
            directions = generate_text_directions(path)
            
            return jsonify({
                "status": "success",
                "best_checkout": best_checkout,
                "route": {
                    "start": {"x": start_pos['x'], "y": start_pos['y']},
                    "end": end_pos,
                    "path": [{"x": x, "y": y} for x, y in path],
                    "directions": directions,
                    "distance": len(path),
                    "estimated_time": len(path) * 2
                },
                "recommendation": f"Quầy {best_checkout['checkout_id']} - {best_checkout['people_count']} người chờ, dự kiến {best_checkout['wait_time_estimate']} phút",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Không thể tính toán đường đi đến quầy thu ngân"
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error calculating route to checkout: {str(e)}"
        }), 500

@app.route('/api/checkout/update', methods=['POST'])
def update_checkout_data():
    """
    API endpoint for camera AI to send checkout queue data
    
    Expected JSON format:
    {
        "camera_id": "esp32cam_02",
        "people_count": 3,
        "queue_length": 3,
        "wait_time_estimate": 6,
        "status": "open",
        "timestamp": "2024-01-01T12:00:00"
    }
    
    Or batch update:
    {
        "checkouts": [
            {checkout_data1},
            {checkout_data2}
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        updated_checkouts = []
        failed_checkouts = []
        
        # Handle batch updates
        if 'checkouts' in data:
            checkouts_list = data['checkouts']
            if not isinstance(checkouts_list, list):
                return jsonify({
                    "status": "error",
                    "message": "Checkouts must be a list"
                }), 400
        else:
            # Single checkout update
            checkouts_list = [data]
        
        # Process each checkout
        for checkout_data in checkouts_list:
            # Validate required fields
            required_fields = ['camera_id', 'people_count']
            if not all(field in checkout_data for field in required_fields):
                failed_checkouts.append({
                    "camera_id": checkout_data.get('camera_id', 'unknown'),
                    "error": "Missing required fields"
                })
                continue
            
            # Validate data types
            try:
                camera_id = str(checkout_data['camera_id'])
                people_count = int(checkout_data['people_count'])
                
                if people_count < 0:
                    raise ValueError("People count must be >= 0")
                
            except (ValueError, TypeError) as e:
                failed_checkouts.append({
                    "camera_id": checkout_data.get('camera_id', 'unknown'),
                    "error": f"Invalid data format: {str(e)}"
                })
                continue
            
            # Update the checkout data
            success = update_checkout_queue(checkout_data)
            
            if success:
                updated_checkouts.append(camera_id)
                print(f"🤖 AI Update - Camera {camera_id}: {people_count} people")
                
                # Send real-time update to connected clients
                socketio.emit('checkout_update', {
                    'camera_id': camera_id,
                    'checkout_data': get_checkout_queues_data(),
                    'timestamp': datetime.now().isoformat()
                }, namespace='/')
                
            else:
                failed_checkouts.append({
                    "camera_id": camera_id,
                    "error": "Failed to update checkout data"
                })
        
        # Cleanup old data
        cleanup_old_checkout_data()
        
        return jsonify({
            "status": "success",
            "message": f"Processed {len(checkouts_list)} checkout(s)",
            "updated_checkouts": updated_checkouts,
            "failed_checkouts": failed_checkouts,
            "total_updated": len(updated_checkouts),
            "total_failed": len(failed_checkouts),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error in checkout update API: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/api/beacon/ble', methods=['GET'])
def get_ble_beacon_data():
    """Get realtime BLE beacon data from BeaconManager"""
    global beacon_manager
    
    if not BEACON_MANAGER_AVAILABLE or not beacon_manager:
        return jsonify({
            "status": "error",
            "message": "BLE Beacon Manager not available or not initialized"
        }), 503
    
    try:
        # Lấy dữ liệu từ BeaconManager
        ble_data = beacon_manager.get_beacon_data()
        
        # Format dữ liệu để hiển thị
        formatted_data = {}
        for mac, readings in ble_data.items():
            if readings:
                latest = readings[-1]  # Lấy đọc mới nhất
                formatted_data[mac] = {
                    "latest_reading": latest,
                    "total_readings": len(readings),
                    "readings_history": readings[-5:] if len(readings) > 5 else readings  # 5 đọc gần nhất
                }
        
        return jsonify({
            "status": "success",
            "ble_beacon_count": len(formatted_data),
            "data": formatted_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error", 
            "message": f"Error getting BLE data: {str(e)}"
        }), 500

@app.route('/api/beacon/data', methods=['GET'])
def get_beacon_data():
    """Get all stored beacon data"""
    return jsonify({
        "status": "success",
        "total_records": len(beacon_data),
        "data": beacon_data
    })

@app.route('/api/beacon/rssi', methods=['GET'])
def get_current_beacon_rssi():
    """Get current RSSI data from all beacons"""
    with beacon_lock:
        beacon_rssi_copy = dict(current_beacon_rssi)
        beacon_count = len(current_beacon_rssi)
    
    return jsonify({
        "status": "success",
        "beacon_count": beacon_count,
        "beacon_rssi": beacon_rssi_copy,
        "nearest_beacon": find_nearest_beacon_from_stored()
    })

@app.route('/api/beacon/rssi', methods=['POST'])
def receive_beacon_rssi():
    """
    API endpoint để nhận dữ liệu RSSI từ beacons
    
    Expected JSON format:
    {
        "beacon_id": "ESP32_BEACON_001",
        "timestamp": 84824,
        "sgt_device": {
            "name": "SGT",
            "address": "68:5c:e4:ea:fa:6f",
            "rssi": -59,
            "distance": 8.912508965,
            "user_data": "181C"
        }
    }
    """
    try:
        # Lấy dữ liệu JSON từ request
        data = request.get_json()
        print(f"Received data: {data}")
        
        # Kiểm tra dữ liệu đầu vào
        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
            
        if 'beacon_id' not in data:
            return jsonify({
                "status": "error",
                "message": "beacon_id is required"
            }), 400
        
        # Thêm timestamp hiện tại nếu chưa có
        if 'timestamp' not in data:
            data['server_timestamp'] = datetime.now().isoformat()
        
        # Kiểm tra và xử lý SGT device data
        if 'sgt_device' in data and data['sgt_device'] is not None:
            sgt_device = data['sgt_device']
            beacon_id = data['beacon_id']
            
            print(f"🎯 SGT Device detected from {beacon_id}:")
            print(f"   📍 Name: {sgt_device.get('name', 'N/A')}")
            print(f"   📍 Address: {sgt_device.get('address', 'N/A')}")
            print(f"   📶 RSSI: {sgt_device.get('rssi', 'N/A')} dBm")
            print(f"   📏 Distance: ", tinhkhoangcach(int(sgt_device.get('rssi', '0'))))
            print(f"   🆔 User Data: {sgt_device.get('user_data', 'N/A')}")
            
            # Lưu trữ dữ liệu beacon thay vì cập nhật vị trí ngay lập tức
            stored = store_beacon_rssi(data)
            if stored:
                print(f"💾 Beacon data stored for {beacon_id}")
            else:
                print(f"❌ Failed to store beacon data for {beacon_id}")
        else:
            print(f"❌ No SGT device found from {data.get('beacon_id', 'Unknown')}")
        
        # Lưu dữ liệu vào memory
        beacon_data.append(data)
        
        # Giữ chỉ 1000 records gần nhất để tránh memory overflow
        if len(beacon_data) > 1000:
            beacon_data.pop(0)
        
        return jsonify({
            "status": "success",
            "message": "Beacon data stored successfully",
            "beacon_id": data.get('beacon_id'),
            "total_records": len(beacon_data),
            "stored_beacons": len(current_beacon_rssi)
        }), 200
        
    except json.JSONDecodeError:
        return jsonify({
            "status": "error",
            "message": "Invalid JSON format"
        }), 400
    except Exception as e:
        print(f"❌ Server error: {str(e)}")
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/api/priority/products', methods=['GET'])
def get_priority_products():
    """Get all priority products information"""
    try:
        products_data = get_priority_products_data()
        active_products = get_active_priority_products()
        
        return jsonify({
            "status": "success",
            "total_products": len(products_data),
            "active_products": len(active_products),
            "priority_products": products_data,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error getting priority products: {str(e)}"
        }), 500

@app.route('/api/priority/products', methods=['POST'])
def add_priority_products():
    """
    API endpoint to add priority products
    
    Expected JSON format:
    {
        "product_name": "iPhone",
        "shelf_id": "A2",
        "priority_level": 5,
        "description": "Featured product of the month",
        "is_active": true
    }
    
    Or batch add:
    {
        "products": [
            {product_data1},
            {product_data2},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        added_products = []
        failed_products = []
        
        # Handle batch adds
        if 'products' in data:
            products_list = data['products']
            if not isinstance(products_list, list):
                return jsonify({
                    "status": "error",
                    "message": "Products must be a list"
                }), 400
        else:
            # Single product add
            products_list = [data]
        
        # Process each product
        for product_data in products_list:
            # Validate required fields
            required_fields = ['product_name', 'shelf_id', 'priority_level']
            if not all(field in product_data for field in required_fields):
                failed_products.append({
                    "product_name": product_data.get('product_name', 'unknown'),
                    "error": "Missing required fields"
                })
                continue
            
            # Validate data types and ranges
            try:
                product_name = str(product_data['product_name'])
                shelf_id = str(product_data['shelf_id'])
                priority_level = int(product_data['priority_level'])
                
                if priority_level < 1 or priority_level > 5:
                    raise ValueError("Priority level must be 1-5")
                
                if shelf_id not in SHELVES_INFO:
                    raise ValueError(f"Shelf {shelf_id} does not exist")
                
                if product_name not in SHELVES_INFO[shelf_id]['products']:
                    raise ValueError(f"Product {product_name} not found in shelf {shelf_id}")
                
            except (ValueError, TypeError) as e:
                failed_products.append({
                    "product_name": product_data.get('product_name', 'unknown'),
                    "error": f"Invalid data: {str(e)}"
                })
                continue
            
            # Add the priority product
            success = add_priority_product(product_data)
            
            if success:
                product_id = f"{shelf_id}_{product_name.replace(' ', '_').lower()}"
                added_products.append(product_id)
                print(f"✨ API Add - Priority product {product_name} in {shelf_id}, level {priority_level}")
            else:
                failed_products.append({
                    "product_name": product_name,
                    "error": "Failed to add product"
                })
        
        # Send real-time update to connected clients
        if added_products:
            socketio.emit('priority_products_update', {
                'action': 'added',
                'products': added_products,
                'priority_products': get_priority_products_data(),
                'timestamp': datetime.now().isoformat()
            }, namespace='/')
        
        return jsonify({
            "status": "success",
            "message": f"Processed {len(products_list)} product(s)",
            "added_products": added_products,
            "failed_products": failed_products,
            "total_added": len(added_products),
            "total_failed": len(failed_products),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"❌ Error in priority products add API: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "status": "error",
            "message": f"Server error: {str(e)}"
        }), 500

@app.route('/api/priority/products/<product_id>', methods=['PUT'])
def update_priority_product_api(product_id):
    """Update priority product information"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        success = update_priority_product(product_id, data)
        
        if success:
            # Send real-time update to connected clients
            socketio.emit('priority_products_update', {
                'action': 'updated',
                'product_id': product_id,
                'priority_products': get_priority_products_data(),
                'timestamp': datetime.now().isoformat()
            }, namespace='/')
            
            return jsonify({
                "status": "success",
                "message": f"Priority product {product_id} updated successfully",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Priority product {product_id} not found or update failed"
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error updating priority product: {str(e)}"
        }), 500

@app.route('/api/priority/products/<product_id>', methods=['DELETE'])
def remove_priority_product_api(product_id):
    """Remove priority product"""
    try:
        success = remove_priority_product(product_id)
        
        if success:
            # Send real-time update to connected clients
            socketio.emit('priority_products_update', {
                'action': 'removed',
                'product_id': product_id,
                'priority_products': get_priority_products_data(),
                'timestamp': datetime.now().isoformat()
            }, namespace='/')
            
            return jsonify({
                "status": "success",
                "message": f"Priority product {product_id} removed successfully",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "error",
                "message": f"Priority product {product_id} not found"
            }), 404
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error removing priority product: {str(e)}"
        }), 500

@app.route('/api/priority/products/clear', methods=['POST'])
def clear_priority_products():
    """Clear all priority products (for testing/reset)"""
    try:
        with priority_products_lock:
            cleared_count = len(priority_products)
            priority_products.clear()
        
        # Notify clients about clearing
        socketio.emit('priority_products_update', {
            'action': 'cleared',
            'message': 'All priority products cleared',
            'priority_products': {},
            'timestamp': datetime.now().isoformat()
        }, namespace='/')
        
        return jsonify({
            "status": "success",
            "message": f"Cleared {cleared_count} priority products",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error clearing priority products: {str(e)}"
        }), 500

# ===== ADMIN API =====
@app.route('/api/admin/position/set', methods=['POST'])
def admin_set_position():
    """API endpoint for admin to manually set user position"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "status": "error",
                "message": "No JSON data provided"
            }), 400
        
        x = data.get('x')
        y = data.get('y')
        
        if x is None or y is None:
            return jsonify({
                "status": "error",
                "message": "X and Y coordinates are required"
            }), 400
        
        # Validate coordinates
        if not (0 <= x <= 19 and 0 <= y <= 19):
            return jsonify({
                "status": "error",
                "message": "Coordinates must be between 0 and 19"
            }), 400
        
        # Update user position with admin control flag
        global current_user_position
        current_user_position.update({
            "x": x,
            "y": y,
            "last_update": datetime.now().isoformat(),
            "admin_controlled": True,
            "last_beacon": "ADMIN_CONTROL"
        })
        
        # Send real-time update to all connected clients
        socketio.emit('position_update', {
            'position': current_user_position,
            'nearby_shelves': get_nearby_shelves(current_user_position),
            'admin_controlled': True
        }, namespace='/')
        
        return jsonify({
            "status": "success",
            "message": f"User position set to ({x}, {y}) by admin",
            "position": current_user_position,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error setting position: {str(e)}"
        }), 500

@app.route('/api/admin/stats', methods=['GET'])
def admin_stats():
    """Get admin statistics and system status"""
    try:
        return jsonify({
            "status": "success",
            "stats": {
                "current_position": current_user_position,
                "connected_clients": len(socketio.server.eio.sockets) if hasattr(socketio, 'server') else 0,
                "beacon_data_count": len(current_beacon_rssi),
                "crowded_areas_count": len(crowded_areas),
                "checkout_queues_count": len(checkout_queues),
                "priority_products_count": len(priority_products),
                "system_uptime": datetime.now().isoformat(),
                "admin_controlled": current_user_position.get('admin_controlled', False)
            },
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error getting stats: {str(e)}"
        }), 500

# ===== GLASS BREAK SERVICE API =====
@app.route('/api/security/glass-break/status', methods=['GET'])
def get_glass_break_service_status():
    """Get Glass Break Service status"""
    try:
        global glass_break_service
        
        if glass_break_service:
            status_data = glass_break_service.get_status()
            return jsonify({
                "status": "success",
                "service_status": status_data,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "status": "info", 
                "message": "Glass Break Service not available",
                "service_status": {"running": False, "available": False},
                "timestamp": datetime.now().isoformat()
            })
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error getting Glass Break Service status: {str(e)}"
        }), 500

@app.route('/api/security/glass-break/start', methods=['POST'])
def start_glass_break_service():
    """Start Glass Break Service manually"""
    try:
        global glass_break_service
        
        if not GLASS_BREAK_SERVICE_AVAILABLE:
            return jsonify({
                "status": "error",
                "message": "Glass Break Service module not available"
            }), 400
        
        if not glass_break_service:
            glass_break_service = GlassBreakService(app_instance=app)
        
        if glass_break_service.running:
            return jsonify({
                "status": "info",
                "message": "Glass Break Service is already running"
            })
        
        # Test API connection first
        if not glass_break_service.test_api_connection():
            return jsonify({
                "status": "error", 
                "message": "Glass Break Service API test failed"
            }), 500
        
        glass_break_service.start()
        
        return jsonify({
            "status": "success",
            "message": "Glass Break Service started successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error starting Glass Break Service: {str(e)}"
        }), 500

@app.route('/api/security/glass-break/stop', methods=['POST'])
def stop_glass_break_service():
    """Stop Glass Break Service manually"""
    try:
        global glass_break_service
        
        if not glass_break_service:
            return jsonify({
                "status": "info",
                "message": "Glass Break Service is not running"
            })
        
        glass_break_service.stop()
        
        return jsonify({
            "status": "success",
            "message": "Glass Break Service stopped successfully",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error stopping Glass Break Service: {str(e)}"
        }), 500

@app.route('/api/security/glass-break/test', methods=['POST'])
def test_glass_break_api():
    """Test Glass Break API connection"""
    try:
        global glass_break_service
        
        if not GLASS_BREAK_SERVICE_AVAILABLE:
            return jsonify({
                "status": "error",
                "message": "Glass Break Service module not available"
            }), 400
        
        if not glass_break_service:
            glass_break_service = GlassBreakService(app_instance=app)
        
        test_result = glass_break_service.test_api_connection()
        
        return jsonify({
            "status": "success" if test_result else "error",
            "message": "API test successful" if test_result else "API test failed",
            "test_result": test_result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error testing Glass Break API: {str(e)}"
        }), 500

# ===== WEBSOCKET EVENTS =====
@socketio.on('connect')
def handle_connect():
    """Xử lý khi client kết nối WebSocket"""
    # Gửi dữ liệu map và vị trí hiện tại cho client mới
    emit('map_data', {
        'map_layout': MAP_LAYOUT,
        'shelves_info': SHELVES_INFO,
        'beacon_positions': BEACON_POSITIONS,
        'landmarks': LANDMARKS,
        'crowded_areas': get_crowded_areas_data(),
        'checkout_queues': get_checkout_queues_data(),
        'priority_products': get_priority_products_data()
    })
    
    emit('position_update', {
        'position': current_user_position,
        'nearby_shelves': get_nearby_shelves(current_user_position) if current_user_position['last_beacon'] else []
    })

@socketio.on('disconnect')
def handle_disconnect():
    """Xử lý khi client ngắt kết nối WebSocket"""
    pass

@socketio.on('request_position')
def handle_position_request():
    """Xử lý yêu cầu vị trí từ client"""
    emit('position_update', {
        'position': current_user_position,
        'nearby_shelves': get_nearby_shelves(current_user_position) if current_user_position['last_beacon'] else []
    })

@socketio.on('request_crowd_data')
def handle_crowd_data_request():
    """Xử lý yêu cầu dữ liệu vùng đông người từ client"""
    emit('crowd_data', {
        'crowded_areas': get_crowded_areas_data(),
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('request_checkout_data')
def handle_checkout_data_request():
    """Xử lý yêu cầu dữ liệu quầy thu ngân từ client"""
    emit('checkout_data', {
        'checkout_queues': get_checkout_queues_data(),
        'timestamp': datetime.now().isoformat()
    })

@socketio.on('request_priority_products')
def handle_priority_products_request():
    """Xử lý yêu cầu dữ liệu sản phẩm ưu tiên từ client"""
    emit('priority_products_update', {
        'action': 'data_response',
        'priority_products': get_priority_products_data(),
        'active_products': get_active_priority_products(),
        'timestamp': datetime.now().isoformat()
    })

# ===== ADMIN WEBSOCKET EVENTS =====
@socketio.on('admin_position_control')
def handle_admin_position_control(data):
    """Xử lý yêu cầu điều khiển vị trí từ admin"""
    try:
        position = data.get('position', {})
        x = position.get('x')
        y = position.get('y')
        
        if x is None or y is None:
            emit('admin_position_update', {
                'success': False,
                'error': 'Invalid position data'
            })
            return
        
        # Validate coordinates
        if not (0 <= x <= 19 and 0 <= y <= 19):
            emit('admin_position_update', {
                'success': False,
                'error': 'Coordinates out of bounds'
            })
            return
        
        # Update user position
        global current_user_position
        current_user_position.update({
            "x": x,
            "y": y,
            "last_update": datetime.now().isoformat(),
            "admin_controlled": True,
            "last_beacon": "ADMIN_CONTROL"
        })
        
        # Confirm to admin
        emit('admin_position_update', {
            'success': True,
            'position': current_user_position,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send update to all clients (including admin)
        socketio.emit('position_update', {
            'position': current_user_position,
            'nearby_shelves': get_nearby_shelves(current_user_position),
            'admin_controlled': True
        }, namespace='/')
        
        print(f"👑 Admin moved user to position ({x}, {y})")
        
    except Exception as e:
        print(f"❌ Error in admin position control: {str(e)}")
        emit('admin_position_update', {
            'success': False,
            'error': str(e)
        })

@socketio.on('admin_request_stats')
def handle_admin_stats_request():
    """Xử lý yêu cầu thống kê từ admin"""
    try:
        stats = {
            "current_position": current_user_position,
            "connected_clients": len(socketio.server.eio.sockets) if hasattr(socketio, 'server') else 0,
            "beacon_data_count": len(current_beacon_rssi),
            "crowded_areas_count": len(crowded_areas),
            "checkout_queues_count": len(checkout_queues),
            "priority_products_count": len(priority_products),
            "system_uptime": datetime.now().isoformat(),
            "admin_controlled": current_user_position.get('admin_controlled', False)
        }
        
        emit('admin_stats_update', {
            'stats': stats,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"❌ Error getting admin stats: {str(e)}")
        emit('admin_stats_update', {
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        })

@socketio.on('admin_clear_control')
def handle_admin_clear_control():
    """Xử lý yêu cầu xóa điều khiển admin"""
    try:
        global current_user_position
        current_user_position['admin_controlled'] = False
        current_user_position['last_beacon'] = None
        
        emit('admin_position_update', {
            'success': True,
            'message': 'Admin control cleared',
            'position': current_user_position
        })
        
        print("👑 Admin control cleared - returning to beacon-based positioning")
        
    except Exception as e:
        print(f"❌ Error clearing admin control: {str(e)}")
        emit('admin_position_update', {
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    print("🚀 Starting SmartMall Navigation System...")
    print("📡 System Ready - Professional Indoor Navigation")
    
    # Khởi tạo và bắt đầu BeaconManager
    try:
        if BEACON_MANAGER_AVAILABLE:
            beacon_manager = BeaconManager(config_file='beacons.json', app_instance=app)
            beacon_threads = beacon_manager.start()
        else:
            print("⚠️ BeaconManager not available - running without BLE support")
            beacon_manager = None
    except Exception as e:
        print(f"⚠️ BeaconManager initialization failed: {e}")
        beacon_manager = None
    
    # Khởi tạo và bắt đầu GlassBreakService
    try:
        if GLASS_BREAK_SERVICE_AVAILABLE:
            glass_break_service = GlassBreakService(app_instance=app)
            # Test API connection first
            if glass_break_service.test_api_connection():
                glass_break_service.start()
                print("✅ Glass Break Detection Service started successfully!")
            else:
                print("⚠️ Glass Break Service API test failed - service not started")
                glass_break_service = None
        else:
            print("⚠️ GlassBreakService not available - running without glass break detection")
            glass_break_service = None
    except Exception as e:
        print(f"⚠️ GlassBreakService initialization failed: {e}")
        glass_break_service = None
    
    try:
        socketio.run(app, debug=False, host='0.0.0.0', port=8080)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down system...")
        if BEACON_MANAGER_AVAILABLE and beacon_manager:
            beacon_manager.stop()
        if GLASS_BREAK_SERVICE_AVAILABLE and glass_break_service:
            glass_break_service.stop()
        print("✅ System shutdown complete!")
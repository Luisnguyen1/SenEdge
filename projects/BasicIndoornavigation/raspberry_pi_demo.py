#!/usr/bin/env python3
"""
Demo script cho Raspberry Pi AI để gửi thông tin vùng đông người
Chạy script này trên Raspberry Pi để test tính năng crowd detection
"""

import requests
import json
import time
import random
from datetime import datetime

# Cấu hình server
SERVER_URL = "https://8080-cs-864258374040-default.cs-asia-southeast1-bool.cloudshell.dev"  # Thay đổi IP theo server thực tế
API_ENDPOINT = f"{SERVER_URL}/api/crowd/update"

# Định nghĩa các khu vực có thể có người
DETECTION_ZONES = [
    {
        "area_id": "entrance_main",
        "position": [0, 9],
        "size": [2, 2],
        "description": "Main Entrance Area"
    },
    {
        "area_id": "checkout_zone",
        "position": [1, 8],
        "size": [2, 3],
        "description": "Checkout Counter Area"
    },
    {
        "area_id": "shelf_A1_A2",
        "position": [2, 1],
        "size": [2, 6],
        "description": "Electronics & Home Appliances"
    },
    {
        "area_id": "shelf_B1_B2", 
        "position": [6, 1],
        "size": [2, 6],
        "description": "Gaming & Computer Section"
    },
    {
        "area_id": "central_walkway",
        "position": [8, 8],
        "size": [3, 4],
        "description": "Central Walking Area"
    },
    {
        "area_id": "shelf_C3_C4",
        "position": [10, 11],
        "size": [2, 6],
        "description": "Storage & Network Equipment"
    }
]

def simulate_ai_detection():
    """
    Mô phỏng AI detection kết quả từ camera
    Trong thực tế, đây sẽ là kết quả từ computer vision model
    """
    detected_areas = []
    
    for zone in DETECTION_ZONES:
        # Mô phỏng việc có thể detect hoặc không detect người trong khu vực
        if random.random() > 0.3:  # 70% chance có người
            people_count = random.randint(1, 15)
            
            # Tính crowd level dựa trên số người
            if people_count <= 2:
                crowd_level = 1
            elif people_count <= 4:
                crowd_level = 2
            elif people_count <= 7:
                crowd_level = 3
            elif people_count <= 10:
                crowd_level = 4
            else:
                crowd_level = 5
                
            detected_areas.append({
                "area_id": zone["area_id"],
                "position": zone["position"],
                "size": zone["size"],
                "crowd_level": crowd_level,
                "people_count": people_count,
                "confidence": round(random.uniform(0.7, 0.95), 2),
                "description": zone["description"],
                "camera_id": f"cam_{random.randint(1, 6):03d}",
                "timestamp": datetime.now().isoformat()
            })
    
    return detected_areas

def send_crowd_data(areas_data):
    """
    Gửi dữ liệu crowd detection lên server
    
    Args:
        areas_data (list): List các area được detect
        
    Returns:
        bool: True nếu gửi thành công
    """
    try:
        # Chuẩn bị payload
        payload = {
            "areas": areas_data,
            "system_info": {
                "device_id": "raspberry_pi_ai_001",
                "ai_model": "YOLOv8_person_detection",
                "detection_time": datetime.now().isoformat()
            }
        }
        
        # Gửi POST request
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'RaspberryPi-AI-Agent/1.0'
        }
        
        response = requests.post(
            API_ENDPOINT, 
            json=payload, 
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully sent data for {len(areas_data)} areas")
            print(f"   📊 Updated: {result.get('total_updated', 0)} areas")
            print(f"   ❌ Failed: {result.get('total_failed', 0)} areas")
            if result.get('failed_areas'):
                for failed in result['failed_areas']:
                    print(f"   ⚠️ Failed area {failed['area_id']}: {failed['error']}")
            return True
        else:
            print(f"❌ Server error: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {SERVER_URL}")
        return False
    except requests.exceptions.Timeout:
        print("❌ Request timeout")
        return False
    except Exception as e:
        print(f"❌ Error sending data: {str(e)}")
        return False

def test_single_area():
    """Test gửi dữ liệu cho 1 area"""
    print("\n🧪 Testing single area update...")
    
    test_data = {
        "area_id": "test_zone_001",
        "position": [5, 5],
        "size": [2, 2],
        "crowd_level": 3,
        "people_count": 8,
        "confidence": 0.87,
        "description": "Test Zone for Demo",
        "camera_id": "test_cam_001",
        "timestamp": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(API_ENDPOINT, json=test_data, timeout=10)
        if response.status_code == 200:
            print("✅ Single area test successful")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Single area test failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Single area test error: {str(e)}")

def main():
    """Main function để chạy AI crowd detection simulation"""
    print("🤖 Raspberry Pi AI Crowd Detection Demo")
    print(f"🔗 Server: {SERVER_URL}")
    print("=" * 50)
    
    # Test kết nối server
    try:
        response = requests.get(f"{SERVER_URL}/api", timeout=5)
        if response.status_code == 200:
            print("✅ Server connection successful")
            server_info = response.json()
            print(f"   📊 Server: {server_info.get('message', 'Unknown')}")
            print(f"   🔢 Version: {server_info.get('version', 'Unknown')}")
        else:
            print(f"⚠️ Server responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to server: {str(e)}")
        print("Please check server URL and make sure server is running")
        return
    
    # Test single area
    test_single_area()
    
    print("\n🔄 Starting continuous crowd detection simulation...")
    print("Press Ctrl+C to stop")
    
    try:
        cycle = 0
        while True:
            cycle += 1
            print(f"\n📸 Detection Cycle {cycle} - {datetime.now().strftime('%H:%M:%S')}")
            
            # Mô phỏng AI detection
            detected_areas = simulate_ai_detection()
            
            if detected_areas:
                print(f"👥 Detected {len(detected_areas)} crowded areas:")
                for area in detected_areas:
                    print(f"   🏷️ {area['area_id']}: {area['people_count']} people (level {area['crowd_level']})")
                
                # Gửi dữ liệu lên server
                success = send_crowd_data(detected_areas)
                
                if not success:
                    print("⚠️ Failed to send data, will retry next cycle")
            else:
                print("👻 No crowded areas detected in this cycle")
            
            # Chờ 5 giây trước chu kỳ tiếp theo (trong thực tế có thể 10-30 giây)
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping crowd detection simulation...")
        print("👋 Demo finished!")

if __name__ == "__main__":
    main()
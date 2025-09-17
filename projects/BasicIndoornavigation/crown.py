import requests
import json
from datetime import datetime

def update_crowd_position():
    """Cập nhật vị trí đám đông tại (3,8)"""
    
    # URL của server
    api_url = 'http://192.168.137.94:8080/api/crowd/update'
    
    # Dữ liệu đám đông theo format đúng (areas array)
    crowd_data = {
        "areas": [
            {
                "area_id": "crowd_area_3_8",
                "position": [3, 8],
                "size": [2, 2],
                "crowd_level": 4,
                "people_count": 15,
                "confidence": 0.85,
                "description": "Khu vực đông đúc tại (3,8)",
                "camera_id": "cam_test_001"
            }
        ]
    }
    
    try:
        response = requests.post(api_url, json=crowd_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Cập nhật crowd thành công!")
            print(f"📊 Updated: {result.get('total_updated', 0)} areas")
            print(f"❌ Failed: {result.get('total_failed', 0)} areas")
            return result
        else:
            print(f"❌ Lỗi: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Lỗi kết nối: {e}")
        return None

def clear_crowd_position():
    """Xóa vùng đông đúc"""
    
    api_url = 'http://192.168.137.94:8080/api/crowd/clear'
    
    try:
        response = requests.post(api_url, json={})
        if response.status_code == 200:
            print("✅ Xóa tất cả crowd thành công!")
        else:
            print(f"❌ Lỗi: {response.status_code}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def update_crowd_level(level=4, people_count=None):
    """Cập nhật với level tùy chỉnh"""
    
    levels = {1: 3, 2: 6, 3: 10, 4: 15, 5: 25}
    final_count = people_count or levels.get(level, 15)
    
    api_url = 'http://192.168.137.94:8080/api/crowd/update'
    
    crowd_data = {
        "areas": [
            {
                "area_id": "crowd_area_3_8",
                "position": [3, 8],
                "size": [2, 2],
                "crowd_level": level,
                "people_count": final_count,
                "confidence": 0.9,
                "description": f"Crowd level {level} tại (3,8) - {final_count} người",
                "camera_id": "cam_test_001"
            }
        ]
    }
    
    try:
        response = requests.post(api_url, json=crowd_data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Cập nhật crowd level {level} thành công!")
            print(f"📊 Updated: {result.get('total_updated', 0)} areas")
        else:
            print(f"❌ Lỗi: {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Lỗi: {e}")

def send_crowd_simple(position=[3, 8], people_count=15, level=4):
    """Hàm đơn giản nhất để gửi crowd data"""
    
    api_url = 'http://192.168.137.94:8080/api/crowd/update'
    
    crowd_data = {
        "areas": [
            {
                "area_id": f"crowd_{position[0]}_{position[1]}",
                "position": position,
                "size": [4, 4],
                "crowd_level": level,
                "people_count": people_count,
                "confidence": 0.8,
                "description": f"Crowd at ({position[0]}, {position[1]}) - {people_count} people",
                "camera_id": "manual_test"
            }
        ]
    }
    
    try:
        response = requests.post(api_url, json=crowd_data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Gửi thành công crowd tại {position}!")
            print(f"   📊 Updated: {result.get('total_updated', 0)}")
            print(f"   ❌ Failed: {result.get('total_failed', 0)}")
            if result.get('failed_areas'):
                for failed in result['failed_areas']:
                    print(f"   ⚠️ Failed: {failed['area_id']} - {failed['error']}")
            return True
        else:
            print(f"❌ Server error: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Gửi vị trí đám đông tại (3,8)...")
    
    # Cách 1: Gửi đơn giản nhất
    send_crowd_simple([3, 9], 15, 4)
    
    # Cách 2: Sử dụng các function khác
    # update_crowd_position()
    # update_crowd_level(5, 30)  # Level 5, 30 người
    # clear_crowd_position()     # Xóa tất cả crowd
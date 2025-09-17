import requests
import json

# Test glass break alert
test_data = {
    "device_id": "GLASS_SENSOR_001",
    "location": "Phòng họp tầng 2",
    "severity": "high",
    "status": "active"
}

print("Testing glass break alert...")

try:
    response = requests.post(
        "https://dashboard-sgteam.onrender.com/api/security/glass-break",
        json=test_data,
        headers={'Content-Type': 'application/json'},
        timeout=10
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    
except Exception as e:
    print(f"Error: {e}")
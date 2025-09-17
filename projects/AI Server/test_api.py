#!/usr/bin/env python3
"""
Test script cho API crowd detection
"""
import requests
import json
import time

def test_api():
    """Test API upload endpoint"""
    print("🧪 Testing Crowd Detection API...")
    
    # Test endpoint
    url = "http://192.168.1.187:7863/upload"
    
    try:
        # Test với test image
        print("📤 Uploading test image...")
        with open('test_image.jpg', 'rb') as f:
            files = {'file': ('test_image.jpg', f, 'image/jpeg')}
            response = requests.post(url, files=files, timeout=60)
        
        print(f"✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("📊 API Response:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Kiểm tra analysis results
            if 'analysis' in result and result['analysis']:
                analysis = result['analysis']
                if 'crowd_analysis' in analysis:
                    crowd_data = analysis['crowd_analysis']
                    print(f"\n🎯 CROWD DETECTION SUMMARY:")
                    print(f"   👥 Total people: {analysis.get('total_people', 0)}")
                    print(f"   🏃 Crowds detected: {crowd_data.get('total_crowds', 0)}")
                    print(f"   👫 People in crowds: {crowd_data.get('total_people_in_crowds', 0)}")
                    print(f"   🚶 Isolated people: {crowd_data.get('isolated_people', 0)}")
                    
                    if crowd_data.get('crowds'):
                        print(f"\n📍 CROWD DETAILS:")
                        for i, crowd in enumerate(crowd_data['crowds']):
                            print(f"   Crowd {i+1}: {crowd['people_count']} people at center ({crowd['center'][0]:.0f}, {crowd['center'][1]:.0f})")
                
                print(f"\n⏱️ Processing time: {analysis.get('processing_time', 'N/A')}")
                print(f"🤖 Inference time: {analysis.get('inference_time', 'N/A')}")
            
            print("\n✅ API test completed successfully!")
            return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection refused. Make sure the server is running on port 7860")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_other_endpoints():
    """Test other API endpoints"""
    base_url = "http://127.0.0.1:7860"
    
    print("\n🧪 Testing other endpoints...")
    
    # Test stats endpoint
    try:
        response = requests.get(f"{base_url}/stats", timeout=10)
        if response.status_code == 200:
            print("✅ /stats endpoint working")
            stats = response.json()
            print(f"   Stats: {stats}")
        else:
            print(f"❌ /stats failed: {response.status_code}")
    except Exception as e:
        print(f"❌ /stats error: {e}")
    
    # Test latest endpoint  
    try:
        response = requests.get(f"{base_url}/latest", timeout=10)
        if response.status_code == 200:
            print("✅ /latest endpoint working")
        else:
            print(f"⚠️ /latest returned: {response.status_code} (normal if no data)")
    except Exception as e:
        print(f"❌ /latest error: {e}")

if __name__ == "__main__":
    print("🚀 Starting API Test")
    print("="*50)
    
    # Wait a bit for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    success = test_api()
    
    if success:
        test_other_endpoints()
        print("\n🎉 All tests completed!")
    else:
        print("\n❌ Main test failed, skipping other tests")

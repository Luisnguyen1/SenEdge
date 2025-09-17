from flask import Flask, request, jsonify
import os
from datetime import datetime
from rpi_crowd_detector import RPiCrowdDetector
import json
import numpy as np
import requests
import threading

def convert_numpy_types(obj):
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    else:
        return obj

# Cấu hình server quản lý
MANAGEMENT_SERVER_URL = "http://192.168.137.251:8080"  # Có thể thay đổi theo môi trường
DASHBOARD_UPLOAD_URL = "https://dashboard-sgteam.onrender.com/api/navigation/upload-image"  # Dashboard admin URL
CAMERA_ID = "cam_001"  # ID camera mặc định

# Map camera_id với position trên map 20x20 và thông tin khu vực
CAMERA_POSITION_MAP = {
    "cam_001": {
        "position": [1, 0],      # Main entrance
        "area_name": "Main Entrance",
        "zone_size": [3, 2]      # Monitor entrance area
    },
    "cam_002": {
        "position": [18, 0],     # Secondary entrance/exit
        "area_name": "Secondary Exit",
        "zone_size": [3, 2]
    },
    "cam_003": {
        "position": [0, 2],      # Dãy 1 - Walking path near Cụm A
        "area_name": "Row 1 - Cluster A Area",
        "zone_size": [4, 3]
    },
    "cam_004": {
        "position": [8, 2],      # Dãy 1 - Center corridor
        "area_name": "Row 1 - Center Corridor",
        "zone_size": [3, 3]
    },
    "cam_005": {
        "position": [19, 6],     # Dãy 1 - Walking path near Cụm B
        "area_name": "Row 1 - Cluster B Area",
        "zone_size": [4, 3]
    },
    "cam_006": {
        "position": [0, 6],      # Dãy 2 - Walking path near Cụm C
        "area_name": "Row 2 - Cluster C Area",
        "zone_size": [4, 3]
    },
    "cam_007": {
        "position": [8, 6],      # Dãy 2 - Center corridor
        "area_name": "Row 2 - Center Corridor",
        "zone_size": [3, 3]
    },
    "cam_008": {
        "position": [19, 10],    # Dãy 2 - Walking path near Cụm D
        "area_name": "Row 2 - Cluster D Area",
        "zone_size": [4, 3]
    },
    "cam_009": {
        "position": [0, 10],     # Dãy 3 - Walking path near Cụm E
        "area_name": "Row 3 - Cluster E Area",
        "zone_size": [4, 3]
    },
    "cam_010": {
        "position": [8, 10],     # Dãy 3 - Center corridor
        "area_name": "Row 3 - Center Corridor",
        "zone_size": [3, 3]
    },
    "cam_011": {
        "position": [19, 13],    # Dãy 3 - Walking path near Cụm F
        "area_name": "Row 3 - Cluster F Area",
        "zone_size": [4, 3]
    },
    "cam_012": {
        "position": [9, 15],     # Main walking area
        "area_name": "Central Walking Area",
        "zone_size": [6, 4]
    },
    # ESP32-CAM devices - Checkout counter cameras
    "esp32cam_02": {
        "position": [5, 8],      # Checkout counter 1
        "area_name": "Checkout Counter 1",
        "zone_size": [3, 3]
    },
    "esp32cam_03": {
        "position": [15, 8],     # Checkout counter 2
        "area_name": "Checkout Counter 2",
        "zone_size": [3, 3]
    }
}

def upload_labeled_image_to_dashboard(image_path, analysis_result, camera_id):
    """
    Upload hình ảnh đã được label lên dashboard admin
    LUÔN upload dù có kết quả AI hay không
    """
    try:
        # Chuẩn bị processed_data từ kết quả phân tích (hoặc mặc định nếu không có)
        processed_data = {
            "objects": [],
            "confidence": 0.0,
            "total_people": analysis_result.get("total_people", 0),
            "crowd_analysis": analysis_result.get("crowd_analysis", {}),
            "timestamp": datetime.now().isoformat(),
            "analysis_status": "success" if not analysis_result.get("error") else "failed",
            "error_message": analysis_result.get("error", "")
        }
        
        # Extract objects và confidence từ analysis_result (nếu có)
        if "detections" in analysis_result and analysis_result["detections"]:
            for detection in analysis_result["detections"]:
                if detection.get("class") == "person":
                    processed_data["objects"].append("person")
                    processed_data["confidence"] = max(processed_data["confidence"], detection.get("confidence", 0.0))
        
        # Nếu không có detection nhưng có total_people, tạo objects mặc định
        elif processed_data["total_people"] > 0:
            processed_data["objects"] = ["person"] * processed_data["total_people"]
            processed_data["confidence"] = 0.7  # Default confidence cho trường hợp này
        
        # Nếu hoàn toàn không có dữ liệu người, vẫn upload với thông tin "no_detection"
        else:
            processed_data["objects"] = ["no_detection"]
            processed_data["confidence"] = 1.0  # Chắc chắn là không phát hiện được gì
        
        # Lấy thông tin location từ camera mapping
        camera_info = CAMERA_POSITION_MAP.get(camera_id, {})
        location = camera_info.get("area_name", "Unknown Area")
        
        # Kiểm tra file tồn tại
        if not os.path.exists(image_path):
            print(f"⚠️ Image not found: {image_path}")
            return False
        
        # Chuẩn bị files và data
        with open(image_path, 'rb') as img_file:
            files = {
                'file': ('image.jpg', img_file, 'image/jpeg')
            }
            
            data = {
                'device_id': camera_id,
                'location': location,
                'processed_data': json.dumps(processed_data)
            }
            
            response = requests.post(
                DASHBOARD_UPLOAD_URL,
                files=files,
                data=data,
                timeout=30  # Timeout 30s cho upload
            )
            
            if response.status_code == 200:
                status_icon = "✅" if processed_data["analysis_status"] == "success" else "⚠️"
                print(f"{status_icon} Uploaded image to dashboard: {camera_id} - {location}")
                print(f"   👥 Total people: {processed_data['total_people']}")
                print(f"   🎯 Confidence: {processed_data['confidence']:.2f}")
                print(f"   🔍 Objects: {processed_data['objects']}")
                if processed_data.get("error_message"):
                    print(f"   ❌ Analysis error: {processed_data['error_message']}")
                return True
            else:
                print(f"⚠️ Dashboard upload failed: {response.status_code} - {response.text}")
                return False
                
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not upload to dashboard: {e}")
        return False
    except Exception as e:
        print(f"❌ Error uploading image: {e}")
        return False

def send_checkout_update(analysis_result, camera_id):
    """
    Gửi thông tin cập nhật quầy tính tiền về server quản lý
    Chạy trong thread riêng để không chặn luồng chính
    """
    try:
        # Lấy thông tin từ kết quả AI
        people_count = analysis_result.get("total_people", 0)
        crowd_analysis = analysis_result.get("crowd_analysis", {})
        
        # Tính toán queue_length dựa trên crowd analysis
        queue_length = 0
        if "crowds" in crowd_analysis:
            # Nếu có crowds, lấy crowd lớn nhất làm queue
            max_crowd_size = 0
            for crowd in crowd_analysis["crowds"]:
                crowd_size = crowd.get("people_count", 0)
                if crowd_size > max_crowd_size:
                    max_crowd_size = crowd_size
            queue_length = max_crowd_size
        else:
            # Nếu không có crowds, tất cả people_count là queue
            queue_length = people_count
        
        # Ước tính thời gian chờ (30 giây mỗi người)
        wait_time_estimate = queue_length * 30  # seconds
        
        # Xác định trạng thái quầy
        if people_count == 0:
            status = "closed"
        elif queue_length <= 3:
            status = "open"
        elif queue_length <= 8:
            status = "busy"
        else:
            status = "very_busy"
        
        # Chuẩn bị payload
        checkout_data = {
            "camera_id": camera_id,
            "people_count": people_count,
            "queue_length": queue_length,
            "wait_time_estimate": wait_time_estimate,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "confidence": analysis_result.get("confidence", 0.0),
            "analysis_status": "success" if not analysis_result.get("error") else "failed"
        }
        
        # Gửi đến endpoint checkout
        response = requests.post(
            f"{MANAGEMENT_SERVER_URL}/api/checkout/update",
            json=checkout_data,
            timeout=5,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print(f"✅ Sent checkout update: {camera_id} - {people_count} people, queue: {queue_length}, status: {status}")
            print(f"   ⏱️ Wait time estimate: {wait_time_estimate}s")
        else:
            print(f"⚠️ Checkout update failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not reach management server for checkout: {e}")
    except Exception as e:
        print(f"❌ Error sending checkout update: {e}")

def send_crowd_update(analysis_result, camera_id=CAMERA_ID):
    """
    Gửi thông tin cập nhật đám đông về server quản lý
    Chạy trong thread riêng để không chặn luồng chính
    """
    try:
        if not analysis_result or "crowd_analysis" not in analysis_result:
            return
        
        crowd_data = analysis_result["crowd_analysis"]
        areas = []
        
        # Lấy thông tin position từ camera map
        camera_info = CAMERA_POSITION_MAP.get(camera_id, {
            "position": [10, 10],     # Default center position
            "area_name": "Unknown Area",
            "zone_size": [3, 3]       # Default zone size
        })
        
        base_position = camera_info["position"]
        area_name = camera_info["area_name"]
        default_zone_size = camera_info["zone_size"]
        
        # Xử lý từng cluster crowd thành area
        for i, crowd in enumerate(crowd_data.get("crowds", [])):
            area_id = f"zone_{camera_id}_{i+1}"
            
            # Tính toán offset position từ bbox (relative to camera base position)
            bbox = crowd.get("bbox", [0, 0, 100, 100])  # [x1, y1, x2, y2]
            
            # Calculate relative offset from center of image
            img_center_x = 320  # Assume 640px width / 2
            img_center_y = 240  # Assume 480px height / 2
            crowd_center_x = (bbox[0] + bbox[2]) / 2
            crowd_center_y = (bbox[1] + bbox[3]) / 2
            
            # Convert pixel offset to map offset (max ±2 cells from base position)
            offset_x = int((crowd_center_x - img_center_x) / img_center_x * 2)
            offset_y = int((crowd_center_y - img_center_y) / img_center_y * 2)
            
            # Final position = base position + offset
            final_x = max(0, min(19, base_position[0] + offset_x))
            final_y = max(0, min(19, base_position[1] + offset_y))
            
            # Tính size từ bbox hoặc dùng default
            bbox_width = bbox[2] - bbox[0]
            bbox_height = bbox[3] - bbox[1]
            
            # Scale bbox size to map size (proportional to image size)
            size_scale_x = max(1, int(bbox_width / 640 * default_zone_size[0]))
            size_scale_y = max(1, int(bbox_height / 480 * default_zone_size[1]))
            
            # Tính crowd level từ số người
            people_count = crowd.get("people_count", 0)
            if people_count == 0:
                crowd_level = 0
            elif people_count <= 2:
                crowd_level = 1
            elif people_count <= 5:
                crowd_level = 2
            elif people_count <= 10:
                crowd_level = 3
            elif people_count <= 15:
                crowd_level = 4
            else:
                crowd_level = 5
            
            area = {
                "area_id": area_id,
                "position": [final_x, final_y],
                "size": [size_scale_x, size_scale_y],
                "crowd_level": crowd_level,
                "people_count": people_count,
                "confidence": crowd.get("confidence", 0.0),
                "description": f"{area_name} - Crowd {i+1} ({people_count} people)",
                "camera_id": camera_id
            }
            areas.append(area)
        
        # Gửi batch update nếu có areas
        if areas:
            payload = {"areas": areas}
            
            response = requests.post(
                f"{MANAGEMENT_SERVER_URL}/api/crowd/update",
                json=payload,
                timeout=5,  # Timeout 5s để không chặn lâu
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                print(f"✅ Sent crowd update: {len(areas)} areas from {camera_id} ({area_name}) to management server")
            else:
                print(f"⚠️ Management server response: {response.status_code}")
                
        else:
            print(f"ℹ️ No crowd areas detected from {camera_id} ({area_name})")
            
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not reach management server: {e}")
    except Exception as e:
        print(f"❌ Error sending crowd update: {e}")

app = Flask(__name__)
UPLOAD_FOLDER = "received_images"
RESULTS_FOLDER = "analysis_results"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)

# Khởi tạo AI detector - OPTIMIZED cho RPi4
print("🤖 Đang khởi tạo AI Crowd Detector...")
try:
    # Option 1: Sử dụng local downloaded model (fastest)
    ai_detector = RPiCrowdDetector(
        weights='models_rpi/yolov5n.pt',  # Local optimized model
        img_size=416,                     # Balanced size for RPi4
        conf_thres=0.25                   # Lower threshold for better detection
    )
    print("✅ AI Detector sẵn sàng!")
except Exception as e:
    print(f"❌ Lỗi với local model: {e}")
    print("🔄 Thử với model mặc định...")
    try:
        # Fallback: Default model
        ai_detector = RPiCrowdDetector(
            weights='yolov5n.pt',         # Default model
            img_size=416,
            conf_thres=0.25
        )
        print("✅ AI Detector (default) sẵn sàng!")
    except Exception as e2:
        print(f"❌ Lỗi khởi tạo fallback detector: {e2}")
        ai_detector = None

@app.route('/upload', methods=['POST'])
def upload():
    # đổi từ "image" sang "file"
    if 'file' not in request.files:
        return {"status": "error", "message": "No file field"}, 400

    image = request.files['file']
    if image.filename == '':
        return {"status": "error", "message": "No file selected"}, 400

    # Lấy camera_id từ form data (ESP32 gửi lên)
    camera_id = request.form.get('camera_id', CAMERA_ID)  # Default fallback
    print(f"📹 Camera ID from ESP32: {camera_id}")
    
    # Validate camera_id
    if camera_id not in CAMERA_POSITION_MAP:
        print(f"⚠️ Unknown camera_id: {camera_id}, using default mapping")
        # Vẫn cho phép xử lý nhưng dùng default position

    # Lưu ảnh với camera_id trong tên file
    filename = f"{camera_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
    image_path = os.path.join(UPLOAD_FOLDER, filename)
    image.save(image_path)

    print(f"✅ Received image from {camera_id}: {image_path}")
    
    # Chạy AI phân tích đám đông
    analysis_result = None
    result_path = os.path.join(RESULTS_FOLDER, f"analysis_{filename}")
    
    if ai_detector:
        try:
            print(f"🤖 Analyzing crowd in: {filename}")
            
            # Chạy AI detection
            analysis_result = ai_detector.detect_single_image(
                image_path, 
                result_path, 
                visualize=True
            )
            
            if analysis_result:
                # Convert numpy types để tránh JSON serialization error
                analysis_result = convert_numpy_types(analysis_result)
                
                # Thêm camera info vào kết quả
                analysis_result["camera_id"] = camera_id
                analysis_result["camera_info"] = CAMERA_POSITION_MAP.get(camera_id, {
                    "area_name": "Unknown Area",
                    "position": [10, 10]
                })
                
                # Lưu kết quả JSON
                json_path = os.path.join(RESULTS_FOLDER, f"result_{filename}.json")
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(analysis_result, f, indent=2, ensure_ascii=False)
                
                print(f"💾 Analysis saved: {json_path}")
                
                # 🚀 Gửi thông tin về server quản lý (chạy trong thread riêng)
                threading.Thread(
                    target=send_crowd_update, 
                    args=(analysis_result, camera_id),
                    daemon=True
                ).start()
                
                # 🛒 Gửi thông tin checkout nếu là ESP32 camera
                if camera_id in ["esp32cam_02", "esp32cam_03"]:
                    threading.Thread(
                        target=send_checkout_update,
                        args=(analysis_result, camera_id),
                        daemon=True
                    ).start()
                
        except Exception as e:
            print(f"❌ AI Analysis error: {e}")
            analysis_result = {"error": str(e)}
    
    # � LUÔN gửi checkout update nếu là ESP32 camera (dù có lỗi AI)
    if camera_id in ["esp32cam_02", "esp32cam_03"]:
        # Tạo analysis_result mặc định cho checkout nếu AI failed
        checkout_analysis = analysis_result if analysis_result and not analysis_result.get("error") else {
            "total_people": 0,
            "crowd_analysis": {"crowds": []},
            "confidence": 0.0,
            "error": analysis_result.get("error", "AI analysis failed") if analysis_result else "No AI result",
            "camera_id": camera_id,
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"🛒 Forcing checkout update for {camera_id}")
        threading.Thread(
            target=send_checkout_update,
            args=(checkout_analysis, camera_id),
            daemon=True
        ).start()
    
    # �🚀 LUÔN upload hình ảnh lên dashboard (dù có kết quả AI hay không)
    # Tạo analysis_result mặc định nếu không có
    if not analysis_result:
        analysis_result = {
            "total_people": 0,
            "crowd_analysis": {"total_crowds": 0, "isolated_people": 0},
            "error": "AI analysis failed or not available",
            "camera_id": camera_id,
            "camera_info": CAMERA_POSITION_MAP.get(camera_id, {
                "area_name": "Unknown Area",
                "position": [10, 10]
            })
        }
    
    # Nếu không có file kết quả AI (result_path), sử dụng ảnh gốc
    upload_image_path = result_path if os.path.exists(result_path) else image_path
    
    # Upload lên dashboard (chạy trong thread riêng)
    threading.Thread(
        target=upload_labeled_image_to_dashboard,
        args=(upload_image_path, analysis_result, camera_id),
        daemon=True
    ).start()
    
    # Xóa ảnh gốc sau khi xử lý xong để tiết kiệm dung lượng
    try:
        if os.path.exists(image_path):
            os.remove(image_path)
            print(f"🗑️ Deleted original image: {filename}")
    except Exception as e:
        print(f"⚠️ Could not delete image {filename}: {e}")
    
    # Tạo response với kết quả AI
    response_data = {
        "status": "success", 
        "filename": filename,
        "camera_id": camera_id,
        "timestamp": datetime.now().isoformat(),
        "analysis": convert_numpy_types(analysis_result) if analysis_result else None,
        "note": "Original image deleted after processing"
    }
    
    # In summary nếu có kết quả
    if analysis_result and "crowd_analysis" in analysis_result:
        crowd_data = analysis_result["crowd_analysis"]
        camera_area = CAMERA_POSITION_MAP.get(camera_id, {}).get("area_name", "Unknown")
        print(f"📊 CROWD ANALYSIS SUMMARY [{camera_id} - {camera_area}]:")
        print(f"   👥 Total people: {analysis_result.get('total_people', 0)}")
        print(f"   🏃 Crowds detected: {crowd_data.get('total_crowds', 0)}")
        print(f"   👫 People in crowds: {crowd_data.get('total_people_in_crowds', 0)}")
        print(f"   🚶 Isolated people: {crowd_data.get('isolated_people', 0)}")
        print(f"   📍 Camera position: {CAMERA_POSITION_MAP.get(camera_id, {}).get('position', 'Unknown')}")
    
    return jsonify(response_data), 200

@app.route('/analysis/<filename>', methods=['GET'])
def get_analysis(filename):
    """Lấy kết quả phân tích cho một ảnh cụ thể"""
    json_filename = f"result_{filename}.json"
    json_path = os.path.join(RESULTS_FOLDER, json_filename)
    
    if not os.path.exists(json_path):
        return {"status": "error", "message": "Analysis not found"}, 404
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        return jsonify({
            "status": "success",
            "filename": filename,
            "analysis": analysis_data
        }), 200
        
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/latest', methods=['GET'])
def get_latest_analysis():
    """Lấy kết quả phân tích mới nhất"""
    try:
        # Tìm file JSON mới nhất
        json_files = [f for f in os.listdir(RESULTS_FOLDER) if f.endswith('.json')]
        if not json_files:
            return {"status": "error", "message": "No analysis found"}, 404
        
        latest_file = max(json_files, key=lambda f: os.path.getctime(os.path.join(RESULTS_FOLDER, f)))
        latest_path = os.path.join(RESULTS_FOLDER, latest_file)
        
        with open(latest_path, 'r', encoding='utf-8') as f:
            analysis_data = json.load(f)
        
        return jsonify({
            "status": "success",
            "filename": latest_file,
            "analysis": analysis_data
        }), 200
        
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/stats', methods=['GET'])
def get_stats():
    """Thống kê tổng quan"""
    try:
        # Đếm số ảnh đã nhận
        image_files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith('.jpg')]
        
        # Đếm số phân tích đã thực hiện
        json_files = [f for f in os.listdir(RESULTS_FOLDER) if f.endswith('.json')]
        
        return jsonify({
            "status": "success",
            "stats": {
                "total_images_received": len(image_files),
                "total_analyses_completed": len(json_files),
                "ai_detector_status": "active" if ai_detector else "inactive"
            }
        }), 200
        
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/cleanup', methods=['POST'])
def cleanup_old_files():
    """Dọn dẹp các file kết quả cũ"""
    try:
        # Lấy số ngày để giữ lại (mặc định 7 ngày)
        keep_days = request.json.get('keep_days', 7) if request.is_json else 7
        
        import time
        current_time = time.time()
        cutoff_time = current_time - (keep_days * 24 * 60 * 60)  # Convert days to seconds
        
        deleted_files = 0
        
        # Dọn dẹp thư mục received_images
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getctime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_files += 1
                        print(f"🗑️ Deleted old image: {filename}")
        
        # Dọn dẹp thư mục analysis_results
        if os.path.exists(RESULTS_FOLDER):
            for filename in os.listdir(RESULTS_FOLDER):
                file_path = os.path.join(RESULTS_FOLDER, filename)
                if os.path.isfile(file_path):
                    file_time = os.path.getctime(file_path)
                    if file_time < cutoff_time:
                        os.remove(file_path)
                        deleted_files += 1
                        print(f"🗑️ Deleted old result: {filename}")
        
        return jsonify({
            "status": "success",
            "message": f"Cleaned up {deleted_files} old files (older than {keep_days} days)",
            "deleted_count": deleted_files
        }), 200
        
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

@app.route('/cameras', methods=['GET', 'POST'])
def manage_cameras():
    """Quản lý mapping camera với position"""
    global CAMERA_POSITION_MAP
    
    if request.method == 'GET':
        return jsonify({
            "status": "success",
            "cameras": CAMERA_POSITION_MAP
        }), 200
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            if 'cameras' in data:
                # Cập nhật toàn bộ mapping
                CAMERA_POSITION_MAP.update(data['cameras'])
                print(f"🔧 Updated camera mapping: {len(data['cameras'])} cameras")
                
            elif 'camera_id' in data:
                # Cập nhật một camera cụ thể
                camera_id = data['camera_id']
                camera_info = {
                    "position": data.get('position', [10, 10]),
                    "area_name": data.get('area_name', 'New Area'),
                    "zone_size": data.get('zone_size', [3, 3])
                }
                CAMERA_POSITION_MAP[camera_id] = camera_info
                print(f"🔧 Updated camera {camera_id}: {camera_info}")
            
            return jsonify({
                "status": "success",
                "message": "Camera mapping updated",
                "cameras": CAMERA_POSITION_MAP
            }), 200
            
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

@app.route('/config', methods=['GET', 'POST'])
def manage_config():
    """Quản lý cấu hình server"""
    global MANAGEMENT_SERVER_URL, DASHBOARD_UPLOAD_URL, CAMERA_ID
    
    if request.method == 'GET':
        return jsonify({
            "status": "success",
            "config": {
                "management_server_url": MANAGEMENT_SERVER_URL,
                "dashboard_upload_url": DASHBOARD_UPLOAD_URL,
                "camera_id": CAMERA_ID,
                "total_cameras_mapped": len(CAMERA_POSITION_MAP)
            }
        }), 200
    
    elif request.method == 'POST':
        try:
            config = request.get_json()
            
            if 'management_server_url' in config:
                MANAGEMENT_SERVER_URL = config['management_server_url']
                print(f"🔧 Updated management server URL: {MANAGEMENT_SERVER_URL}")
            
            if 'dashboard_upload_url' in config:
                DASHBOARD_UPLOAD_URL = config['dashboard_upload_url']
                print(f"🔧 Updated dashboard upload URL: {DASHBOARD_UPLOAD_URL}")
            
            if 'camera_id' in config:
                CAMERA_ID = config['camera_id']
                print(f"🔧 Updated camera ID: {CAMERA_ID}")
            
            return jsonify({
                "status": "success",
                "message": "Configuration updated",
                "config": {
                    "management_server_url": MANAGEMENT_SERVER_URL,
                    "dashboard_upload_url": DASHBOARD_UPLOAD_URL,
                    "camera_id": CAMERA_ID,
                    "total_cameras_mapped": len(CAMERA_POSITION_MAP)
                }
            }), 200
            
        except Exception as e:
            return {"status": "error", "message": str(e)}, 500

@app.route('/clear_all', methods=['POST'])
def clear_all_files():
    """Xóa tất cả file (chỉ dùng khi cần thiết)"""
    try:
        deleted_count = 0
        
        # Xóa tất cả ảnh
        if os.path.exists(UPLOAD_FOLDER):
            for filename in os.listdir(UPLOAD_FOLDER):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
        
        # Xóa tất cả kết quả
        if os.path.exists(RESULTS_FOLDER):
            for filename in os.listdir(RESULTS_FOLDER):
                file_path = os.path.join(RESULTS_FOLDER, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
        
        print(f"🗑️ Cleared all files: {deleted_count} files deleted")
        
        return jsonify({
            "status": "success",
            "message": f"Cleared all files: {deleted_count} files deleted",
            "deleted_count": deleted_count
        }), 200
        
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 CROWD DETECTION SERVER STARTING")
    print("="*50)
    print(f"📡 Management Server: {MANAGEMENT_SERVER_URL}")
    print(f"🌐 Dashboard Upload: {DASHBOARD_UPLOAD_URL}")
    print(f"📹 Default Camera ID: {CAMERA_ID}")
    print(f"🗺️  Camera Mapping: {len(CAMERA_POSITION_MAP)} cameras configured")
    print(f"🌐 Server will run on: http://0.0.0.0:7863")
    print("="*50)
    
    # In ra camera mapping
    print("📹 CAMERA POSITION MAPPING:")
    for cam_id, info in CAMERA_POSITION_MAP.items():
        print(f"   {cam_id}: {info['area_name']} at {info['position']}")
    print("="*50 + "\n")
    
    # ⚠️ Quan trọng: host="0.0.0.0" để cho ESP32 truy cập qua LAN
    app.run(host="0.0.0.0", port=7863, debug=True)

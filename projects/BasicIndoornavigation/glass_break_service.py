import json
import threading
import time
import logging
import requests
from bluepy import btle
from datetime import datetime, timedelta

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GlassBreakService")

class GlassBreakService:
    """Service lắng nghe BLE để phát hiện glass breaking và noise."""
    
    def __init__(self, app_instance=None):
        """Khởi tạo GlassBreakService."""
        # Cấu hình BLE
        self.target_mac = "C0:2C:ED:90:AD:D3"
        self.char_uuid = "264d8f01-8faa-4620-9eeb-856adbe83170"
        
        # API configuration
        self.api_url = "https://dashboard-sgteam.onrender.com/api/security/glass-break"
        self.device_id = "GLASS_SENSOR_001"
        self.location = "Phòng họp tầng 2"
        
        # Service state
        self.running = False
        self.thread = None
        self.app_instance = app_instance
        self.data_lock = threading.Lock()
        
        # Alert management
        self.last_alert_time = None
        self.alert_cooldown = 30  # 30 giây cooldown giữa các alert
        self.recent_data = []  # Lưu dữ liệu gần đây để phân tích
        
        logger.info(f"🔧 GlassBreakService initialized for MAC: {self.target_mac}")
    
    def parse_sensor_data(self, raw_data):
        """Phân tích dữ liệu từ sensor để phát hiện glass breaking và noise."""
        try:
            # Chuyển bytes thành string
            data_str = raw_data.decode('utf-8', errors='ignore').strip()
            logger.debug(f"Raw data: {data_str}")
            
            # Phân tích các loại event
            if "glass_breaking" in data_str.lower():
                return "glass_breaking", data_str
            elif "noise" in data_str.lower():
                return "noise", data_str
            elif "alert" in data_str.lower():
                return "alert", data_str
            else:
                # Thử phân tích dữ liệu số để phát hiện anomaly
                numbers = self.extract_numbers(data_str)
                if numbers:
                    event_type = self.analyze_sensor_values(numbers)
                    return event_type, data_str
                    
            return "unknown", data_str
            
        except Exception as e:
            logger.error(f"Error parsing sensor data: {e}")
            return "error", str(raw_data)
    
    def extract_numbers(self, data_str):
        """Trích xuất các giá trị số từ chuỗi dữ liệu."""
        import re
        try:
            # Tìm tất cả số trong chuỗi
            numbers = re.findall(r'-?\d+\.?\d*', data_str)
            return [float(num) for num in numbers if num]
        except:
            return []
    
    def analyze_sensor_values(self, values):
        """Phân tích giá trị sensor để phát hiện glass breaking."""
        try:
            if not values:
                return "unknown"
            
            # Lưu dữ liệu vào buffer để phân tích trend
            timestamp = datetime.now()
            with self.data_lock:
                self.recent_data.append({
                    'timestamp': timestamp,
                    'values': values
                })
                
                # Chỉ giữ lại 10 giá trị gần nhất
                if len(self.recent_data) > 10:
                    self.recent_data.pop(0)
            
            # Phân tích threshold
            max_value = max(values)
            avg_value = sum(values) / len(values)
            
            # Threshold cho glass breaking (có thể điều chỉnh)
            if max_value > 1000 or avg_value > 500:
                return "glass_breaking"
            elif max_value > 200 or avg_value > 100:
                return "noise"
            
            return "normal"
            
        except Exception as e:
            logger.error(f"Error analyzing sensor values: {e}")
            return "error"
    
    def should_send_alert(self):
        """Kiểm tra xem có nên gửi alert hay không (cooldown check)."""
        if self.last_alert_time is None:
            return True
        
        time_since_last = datetime.now() - self.last_alert_time
        return time_since_last.total_seconds() >= self.alert_cooldown
    
    def send_glass_break_alert(self, sensor_data):
        """Gửi thông báo glass breaking đến API."""
        if not self.should_send_alert():
            logger.info(f"⏳ Alert in cooldown, skipping...")
            return False
        
        try:
            alert_data = {
                "device_id": self.device_id,
                "location": self.location,
                "severity": "high",
                "status": "active",
                "timestamp": datetime.now().isoformat(),
                "sensor_data": sensor_data,
                "event_type": "glass_breaking"
            }
            
            logger.info(f"🚨 Sending glass break alert to API...")
            
            response = requests.post(
                self.api_url,
                json=alert_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"✅ Alert sent successfully! Status: {response.status_code}")
                logger.info(f"📤 Response: {response.text}")
                self.last_alert_time = datetime.now()
                
                # Emit thông báo qua WebSocket nếu có Flask app
                self.emit_websocket_alert(alert_data)
                
                return True
            else:
                logger.error(f"❌ Failed to send alert. Status: {response.status_code}, Response: {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout when sending alert to API")
            return False
        except Exception as e:
            logger.error(f"❌ Error sending alert: {e}")
            return False
    
    def emit_websocket_alert(self, alert_data):
        """Gửi thông báo qua WebSocket nếu có Flask app."""
        try:
            if self.app_instance and hasattr(self.app_instance, 'socketio'):
                self.app_instance.socketio.emit('security_alert', {
                    'type': 'glass_breaking',
                    'device_id': alert_data['device_id'],
                    'location': alert_data['location'],
                    'severity': alert_data['severity'],
                    'timestamp': alert_data['timestamp'],
                    'message': f"🚨 Glass breaking detected at {alert_data['location']}"
                })
                logger.info("📡 WebSocket alert sent!")
        except Exception as e:
            logger.error(f"❌ Error sending WebSocket alert: {e}")
    
    def connect_and_monitor(self):
        """Kết nối đến BLE device và theo dõi dữ liệu."""
        logger.info(f"🔗 Connecting to glass break sensor: {self.target_mac}")
        
        class SensorDelegate(btle.DefaultDelegate):
            def __init__(self, service):
                btle.DefaultDelegate.__init__(self)
                self.service = service
                
            def handleNotification(self, cHandle, data):
                try:
                    hex_data = data.hex()
                    timestamp = datetime.now().strftime("%H:%M:%S")
                    
                    logger.debug(f"[{timestamp}] Handle: {hex(cHandle)} Data: {hex_data} (raw: {data})")
                    
                    # Phân tích dữ liệu
                    event_type, parsed_data = self.service.parse_sensor_data(data)
                    
                    if event_type == "glass_breaking":
                        logger.warning(f"🚨 GLASS BREAKING DETECTED! Data: {parsed_data}")
                        self.service.send_glass_break_alert(parsed_data)
                    elif event_type == "noise":
                        logger.info(f"🔊 Noise detected: {parsed_data}")
                    elif event_type != "normal" and event_type != "unknown":
                        logger.info(f"📊 Sensor event [{event_type}]: {parsed_data}")
                        
                except Exception as e:
                    logger.error(f"Error handling notification: {e}")
        
        peripheral = None
        reconnect_delay = 5
        max_reconnect_attempts = 3
        reconnect_count = 0
        
        while self.running:
            try:
                if peripheral is None:
                    logger.info(f"🔄 Attempting to connect... (attempt {reconnect_count + 1})")
                    peripheral = btle.Peripheral(self.target_mac)
                    peripheral.setDelegate(SensorDelegate(self))
                    
                    # Tìm và enable notification
                    char = peripheral.getCharacteristics(uuid=self.char_uuid)[0]
                    cccd_handle = char.getHandle() + 1
                    peripheral.writeCharacteristic(cccd_handle, b"\x01\x00", withResponse=True)
                    
                    logger.info(f"✅ Connected to glass break sensor successfully!")
                    reconnect_count = 0  # Reset counter khi kết nối thành công
                
                # Lắng nghe notifications
                if peripheral.waitForNotifications(5.0):
                    continue
                    
            except btle.BTLEDisconnectError:
                logger.warning(f"🔌 Sensor disconnected, reconnecting...")
                peripheral = None
                reconnect_count += 1
                
                if reconnect_count >= max_reconnect_attempts:
                    logger.error(f"❌ Max reconnection attempts reached. Waiting longer...")
                    time.sleep(reconnect_delay * 3)
                    reconnect_count = 0
                else:
                    time.sleep(reconnect_delay)
                
            except Exception as e:
                logger.error(f"❌ Sensor error: {str(e)}")
                try:
                    if peripheral:
                        peripheral.disconnect()
                except:
                    pass
                peripheral = None
                reconnect_count += 1
                time.sleep(reconnect_delay)
        
        # Cleanup
        if peripheral:
            try:
                peripheral.disconnect()
                logger.info("🔌 Disconnected from sensor")
            except:
                pass
    
    def start(self):
        """Bắt đầu service."""
        if self.running:
            logger.warning("⚠ Service is already running!")
            return
        
        logger.info("🚀 Starting Glass Break Detection Service...")
        self.running = True
        
        self.thread = threading.Thread(
            target=self.connect_and_monitor,
            name="GlassBreakServiceThread",
            daemon=True
        )
        self.thread.start()
        logger.info("✅ Glass Break Service started successfully!")
        
        return self.thread
    
    def stop(self):
        """Dừng service."""
        if not self.running:
            logger.warning("⚠ Service is not running!")
            return
        
        logger.info("🛑 Stopping Glass Break Detection Service...")
        self.running = False
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5.0)
        
        logger.info("✅ Glass Break Service stopped successfully!")
    
    def get_status(self):
        """Lấy trạng thái service."""
        return {
            "running": self.running,
            "target_mac": self.target_mac,
            "device_id": self.device_id,
            "location": self.location,
            "last_alert": self.last_alert_time.isoformat() if self.last_alert_time else None,
            "recent_data_count": len(self.recent_data) if hasattr(self, 'recent_data') else 0
        }
    
    def test_api_connection(self):
        """Test kết nối API."""
        try:
            test_data = {
                "device_id": self.device_id,
                "location": self.location,
                "severity": "high",
                "status": "active",
                "timestamp": datetime.now().isoformat(),
                "event_type": "test"
            }
            
            logger.info("🧪 Testing API connection...")
            
            response = requests.post(
                self.api_url,
                json=test_data,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            logger.info(f"✅ API Test - Status: {response.status_code}")
            logger.info(f"📤 API Test - Response: {response.text}")
            
            return response.status_code in [200, 201]
            
        except Exception as e:
            logger.error(f"❌ API Test failed: {e}")
            return False


def main():
    """Hàm chính để test service."""
    service = GlassBreakService()
    
    try:
        # Test API trước
        logger.info("=" * 60)
        logger.info("🧪 TESTING API CONNECTION")
        logger.info("=" * 60)
        
        if service.test_api_connection():
            logger.info("✅ API connection successful!")
        else:
            logger.error("❌ API connection failed!")
            return
        
        # Bắt đầu service
        logger.info("=" * 60)
        logger.info("🚀 STARTING GLASS BREAK DETECTION SERVICE")
        logger.info("=" * 60)
        
        service.start()
        
        logger.info("📡 Service is running... (Ctrl+C to stop)")
        logger.info(f"🎯 Monitoring MAC: {service.target_mac}")
        logger.info(f"🔧 Using UUID: {service.char_uuid}")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("\n⏹ Stopping service...")
    finally:
        service.stop()


if __name__ == "__main__":
    main()
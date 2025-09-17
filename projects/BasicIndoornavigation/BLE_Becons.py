import json
import threading
import time
import logging
import math
from bluepy import btle
from datetime import datetime

# Thiết lập logging đơn giản
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger("BeaconScanner")

class BeaconManager:
    """Quản lý kết nối và dữ liệu từ nhiều BLE beacons."""
    
    def __init__(self, config_file='beacons.json', app_instance=None):
        """Khởi tạo BeaconManager với file cấu hình và Flask app instance."""
        self.config_file = config_file
        self.beacon_data = {}  # Lưu list dữ liệu cho mỗi beacon
        self.data_lock = threading.Lock()
        self.running = True
        self.threads = []
        self.app_instance = app_instance  # Flask app instance để cập nhật biến
        self.load_config()
        
    def load_config(self):
        """Đọc cấu hình từ file JSON."""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            self.char_uuid = config.get("CHAR_UUID")
            self.beacons = config.get("beacons", [])
            print(f"Đã tải cấu hình: {len(self.beacons)} beacons")
        except Exception as e:
            print(f"Lỗi khi đọc cấu hình: {e}")
            raise
    
    def calculate_distance_from_rssi(self, rssi, tx_power=-59, n=2.0):
        """Tính khoảng cách từ RSSI."""
        try:
            if rssi == 0:
                return -1.0
            distance = math.pow(10, (tx_power - rssi) / (10.0 * n))
            return round(distance, 2)
        except:
            return -1.0
    
    def parse_data(self, raw_data):
        """Phân tích dữ liệu từ raw bytes để lấy username và RSSI."""
        try:
            # Chuyển bytes thành string
            data_str = raw_data.decode('utf-8')
            # Ví dụ: "181C:-61,2.29m" -> "181C:-61"
            if ':' in data_str and ',' in data_str:
                # Tách phần trước dấu phẩy đầu tiên
                username_rssi = data_str.split(',')[0]
                # Tách để lấy RSSI
                rssi_str = username_rssi.split(':')[1]
                rssi_value = int(rssi_str)
                return username_rssi, rssi_value
            return None, None
        except:
            return None, None
    
    def update_beacon_data(self, mac, parsed_value, rssi_value):
        """Lưu giá trị đã phân tích vào list và cập nhật API Flask nếu có."""
        if parsed_value and rssi_value is not None:
            with self.data_lock:
                if mac not in self.beacon_data:
                    self.beacon_data[mac] = []
                
                # Tính khoảng cách từ RSSI
                distance = self.calculate_distance_from_rssi(rssi_value)
                
                self.beacon_data[mac].append({
                    "value": parsed_value,
                    "rssi": rssi_value,
                    "distance": distance,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {mac}: {parsed_value} (RSSI: {rssi_value}, Distance: {distance}m)")
                
                # Cập nhật vào Flask app nếu có
                if self.app_instance:
                    self.update_flask_beacon_data(mac, rssi_value, distance)
    
    def update_flask_beacon_data(self, mac, rssi, distance):
        """Cập nhật dữ liệu beacon vào biến Flask app."""
        try:
            # Import Flask variables từ app instance
            if hasattr(self.app_instance, 'current_beacon_rssi') and hasattr(self.app_instance, 'beacon_lock'):
                with self.app_instance.beacon_lock:
                    # Mapping MAC address sang beacon ID trong Flask app
                    beacon_mapping = {
                        "80:4B:50:56:A6:91": "ESP32_BEACON_004",
                        "60:A4:23:C9:85:C1": "ESP32_BEACON_005", 
                        "80:4B:50:54:91:77": "ESP32_BEACON_006",
                        "80:4B:50:54:96:4A": "ESP32_BEACON_007",
                        "34:25:B4:A0:C1:48": "ESP32_BEACON_008"
                    }
                    
                    beacon_id = beacon_mapping.get(mac)
                    if beacon_id:
                        # Lấy position từ BEACON_POSITIONS trong Flask app
                        beacon_position = None
                        if hasattr(self.app_instance, '__dict__') and 'BEACON_POSITIONS' in dir(self.app_instance):
                            # Import BEACON_POSITIONS từ app module
                            import importlib
                            app_module = importlib.import_module('app')
                            if hasattr(app_module, 'BEACON_POSITIONS'):
                                beacon_position = app_module.BEACON_POSITIONS.get(beacon_id, {}).get('position', [0, 0])
                        
                        if beacon_position is None:
                            # Fallback positions nếu không lấy được từ app
                            fallback_positions = {
                                "ESP32_BEACON_004": [13, 9],
                                "ESP32_BEACON_005": [3, 5], 
                                "ESP32_BEACON_006": [13, 5],
                                "ESP32_BEACON_007": [3, 1],
                                "ESP32_BEACON_008": [14, 1]
                            }
                            beacon_position = fallback_positions.get(beacon_id, [0, 0])
                        
                        self.app_instance.current_beacon_rssi[beacon_id] = {
                            'rssi': rssi,
                            'distance': distance,
                            'timestamp': datetime.now().isoformat(),
                            'mac': mac,
                            'position': beacon_position
                        }
                        print(f"📡 Updated Flask beacon data: {beacon_id} -> RSSI: {rssi}, Distance: {distance}m")
                        
                        # Emit WebSocket update nếu có socketio
                        if hasattr(self.app_instance, 'socketio'):
                            self.app_instance.socketio.emit('beacon_update', {
                                'beacon_id': beacon_id,
                                'rssi': rssi,
                                'distance': distance,
                                'mac': mac,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            # Cập nhật vị trí user và emit position_update
                            try:
                                # Import function từ app module
                                import importlib
                                app_module = importlib.import_module('app')
                                
                                # Gọi function update_user_position để cập nhật vị trí
                                updated_position = app_module.update_user_position()
                                
                                if updated_position:
                                    # Lấy nearby_shelves
                                    nearby_shelves = app_module.get_nearby_shelves(updated_position)
                                    
                                    # Emit position update qua WebSocket
                                    self.app_instance.socketio.emit('position_update', {
                                        'position': updated_position,
                                        'nearby_shelves': nearby_shelves
                                    })
                                    print(f"🔄 Position updated via WebSocket: ({updated_position['x']}, {updated_position['y']})")
                                    
                            except Exception as e:
                                print(f"❌ Error updating position via WebSocket: {e}")
                        
        except Exception as e:
            print(f"❌ Lỗi khi cập nhật Flask app: {e}")
    
    def get_beacon_data(self, mac=None):
        """Lấy dữ liệu beacon."""
        with self.data_lock:
            if mac:
                return self.beacon_data.get(mac, [])
            return self.beacon_data.copy()
    
    def connect_to_beacon(self, beacon_info):
        """Kết nối đến một beacon và theo dõi dữ liệu."""
        mac = beacon_info["mac"]
        
        print(f"Đang kết nối tới beacon {mac}...")
        
        class BeaconDelegate(btle.DefaultDelegate):
            def __init__(self, manager, mac_addr):
                btle.DefaultDelegate.__init__(self)
                self.manager = manager
                self.mac_addr = mac_addr
                
            def handleNotification(self, cHandle, data):
                hex_data = data.hex()
                print(f"[NOTIFY] Handle: {hex(cHandle)}  Data: {hex_data}  (raw: {data})")
                
                # Phân tích dữ liệu để lấy username:rssi và RSSI value
                parsed_value, rssi_value = self.manager.parse_data(data)
                if parsed_value and rssi_value is not None:
                    self.manager.update_beacon_data(self.mac_addr, parsed_value, rssi_value)
        
        peripheral = None
        reconnect_delay = 5
        
        while self.running:
            try:
                if peripheral is None:
                    peripheral = btle.Peripheral(mac)
                    peripheral.setDelegate(BeaconDelegate(self, mac))
                    
                    char = peripheral.getCharacteristics(uuid=self.char_uuid)[0]
                    cccd_handle = char.getHandle() + 1
                    peripheral.writeCharacteristic(cccd_handle, b"\x01\x00", withResponse=True)
                    
                    print(f"Beacon {mac} kết nối thành công!")
                
                if peripheral.waitForNotifications(5.0):
                    continue
                    
            except btle.BTLEDisconnectError:
                print(f"Beacon {mac} mất kết nối, thử lại...")
                peripheral = None
                time.sleep(reconnect_delay)
                
            except Exception as e:
                print(f"Beacon {mac} lỗi: {str(e)}")
                try:
                    if peripheral:
                        peripheral.disconnect()
                except:
                    pass
                peripheral = None
                time.sleep(reconnect_delay)
        
        if peripheral:
            try:
                peripheral.disconnect()
            except:
                pass
    
    def start(self):
        """Bắt đầu quét tất cả các beacons."""
        print("=" * 50)
        print("🚀 BẮT ĐẦU QUÉT BEACONS")
        print("=" * 50)
        self.running = True
        
        for beacon in self.beacons:
            thread = threading.Thread(
                target=self.connect_to_beacon,
                args=(beacon,),
                name=f"Thread-{beacon['mac']}"
            )
            thread.daemon = True
            self.threads.append(thread)
            thread.start()
        
        return self.threads
    
    def stop(self):
        """Dừng tất cả các kết nối."""
        print("\n🛑 ĐANG DỪNG...")
        self.running = False
        
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=2.0)
        
        # In tóm tắt dữ liệu
        print("\n📊 TÓM TẮT DỮ LIỆU:")
        with self.data_lock:
            for mac, data_list in self.beacon_data.items():
                print(f"Beacon {mac}: {len(data_list)} giá trị")
                for item in data_list[-5:]:  # In 5 giá trị cuối
                    print(f"  [{item['timestamp']}] {item['value']}")
        
        print("✅ Đã dừng!")


def main():
    """Hàm chính để chạy chương trình."""
    manager = BeaconManager()
    
    try:
        manager.start()
        print("\n📡 Đang lắng nghe... (Ctrl+C để dừng)")
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹ Dừng chương trình...")
    finally:
        manager.stop()


if __name__ == "__main__":
    main()
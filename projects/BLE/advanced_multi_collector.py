# -*- coding: utf-8 -*-
"""
Advanced Multi-Beacon BLE RSSI Collector với Flask Web Interface
"""
import pexpect
import time
from datetime import datetime, timedelta
import threading
import json
import queue
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import signal
import sys

@dataclass
class BeaconReading:
    """Class để lưu trữ một reading"""
    timestamp: datetime
    scanner_mac: str
    detected_beacon: str
    rssi: int
    
    def to_dict(self):
        return {
            "timestamp": self.timestamp.isoformat(),
            "scanner_mac": self.scanner_mac,
            "detected_beacon": self.detected_beacon,
            "rssi": self.rssi
        }

@dataclass
class BeaconStats:
    """Class để lưu trữ thống kê của một beacon"""
    mac: str
    rssi: int
    count: int
    last_seen: datetime
    first_seen: datetime
    avg_rssi: float
    min_rssi: int
    max_rssi: int

class MultiBeaconCollector:
    """Class chính để quản lý thu thập dữ liệu từ nhiều beacons"""
    
    def __init__(self, config_file='beancons.json', setup_signals=True):
        self.config_file = config_file
        self.beacon_data = {}  # {scanner_mac: {detected_mac: BeaconStats}}
        self.all_readings = []  # List of BeaconReading
        self.connection_status = {}
        self.start_time = None
        self.running = False
        self.stats_lock = threading.Lock()
        self.executor = None
        
        # Cấu hình
        self.MAX_READINGS = 10000
        self.RECONNECT_DELAY = 5
        self.STATS_INTERVAL = 30
        self.CONNECTION_TIMEOUT = 15
        self.NOTIFICATION_TIMEOUT = 60
        
        # Setup signal handlers chỉ khi chạy trong main thread
        if setup_signals:
            try:
                signal.signal(signal.SIGINT, self._signal_handler)
                signal.signal(signal.SIGTERM, self._signal_handler)
            except ValueError:
                # Signal handlers chỉ có thể setup trong main thread
                print("Warning: Cannot setup signal handlers (not in main thread)")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\nReceived signal {signum}, shutting down gracefully...")
        self.stop()
    
    def load_beacon_config(self) -> List[Dict]:
        """Đọc cấu hình beacons từ file JSON"""
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return config['beacons']
        except Exception as e:
            print(f"Error loading beacon config: {e}")
            return []
    
    def add_reading(self, scanner_mac: str, detected_mac: str, rssi: int):
        """Thêm reading mới với thread safety"""
        with self.stats_lock:
            timestamp = datetime.now()
            
            # Tạo BeaconReading
            reading = BeaconReading(timestamp, scanner_mac, detected_mac, rssi)
            self.all_readings.append(reading)
            
            # Giới hạn số readings
            if len(self.all_readings) > self.MAX_READINGS:
                self.all_readings.pop(0)
            
            # Cập nhật beacon stats
            if scanner_mac not in self.beacon_data:
                self.beacon_data[scanner_mac] = {}
            
            if detected_mac not in self.beacon_data[scanner_mac]:
                # Beacon mới
                self.beacon_data[scanner_mac][detected_mac] = BeaconStats(
                    mac=detected_mac,
                    rssi=rssi,
                    count=1,
                    last_seen=timestamp,
                    first_seen=timestamp,
                    avg_rssi=float(rssi),
                    min_rssi=rssi,
                    max_rssi=rssi
                )
            else:
                # Cập nhật beacon hiện có
                stats = self.beacon_data[scanner_mac][detected_mac]
                stats.count += 1
                stats.last_seen = timestamp
                stats.rssi = rssi
                
                # Cập nhật min/max/avg
                stats.min_rssi = min(stats.min_rssi, rssi)
                stats.max_rssi = max(stats.max_rssi, rssi)
                
                # Tính average RSSI từ 10 readings gần nhất
                recent_readings = [r.rssi for r in self.all_readings[-10:] 
                                 if r.scanner_mac == scanner_mac and r.detected_beacon == detected_mac]
                if recent_readings:
                    stats.avg_rssi = sum(recent_readings) / len(recent_readings)
    
    def update_connection_status(self, beacon_mac: str, status: str, message: str = ""):
        """Cập nhật trạng thái kết nối"""
        with self.stats_lock:
            self.connection_status[beacon_mac] = {
                "status": status,
                "last_update": datetime.now(),
                "message": message
            }
    
    def get_stats(self) -> Dict:
        """Lấy thống kê hiện tại với thread safety"""
        with self.stats_lock:
            now = datetime.now()
            uptime = now - self.start_time if self.start_time else timedelta(0)
            
            # Convert BeaconStats to dict
            scanner_data = {}
            total_detected = 0
            for scanner_mac, detected_beacons in self.beacon_data.items():
                scanner_data[scanner_mac] = {}
                for detected_mac, stats in detected_beacons.items():
                    scanner_data[scanner_mac][detected_mac] = {
                        "mac": stats.mac,
                        "rssi": stats.rssi,
                        "count": stats.count,
                        "last_seen": stats.last_seen.isoformat(),
                        "first_seen": stats.first_seen.isoformat(),
                        "avg_rssi": round(stats.avg_rssi, 1),
                        "min_rssi": stats.min_rssi,
                        "max_rssi": stats.max_rssi
                    }
                total_detected += len(detected_beacons)
            
            return {
                "total_scanners": len(self.beacon_data),
                "total_detected_beacons": total_detected,
                "total_readings": len(self.all_readings),
                "uptime_seconds": uptime.total_seconds(),
                "connection_status": dict(self.connection_status),
                "scanner_data": scanner_data,
                "latest_readings": [r.to_dict() for r in self.all_readings[-20:]]
            }
    
    def print_stats(self):
        """In thống kê ra console"""
        stats = self.get_stats()
        print(f"\n{'='*100}")
        print(f"[{datetime.now()}] ADVANCED MULTI-BEACON STATISTICS")
        print(f"{'='*100}")
        print(f"Uptime: {stats['uptime_seconds']:.1f} seconds ({stats['uptime_seconds']/60:.1f} minutes)")
        print(f"Active scanners: {stats['total_scanners']}")
        print(f"Total detected beacons: {stats['total_detected_beacons']}")
        print(f"Total readings: {stats['total_readings']}")
        
        print(f"\nConnection Status:")
        for mac, status in stats['connection_status'].items():
            last_update = datetime.fromisoformat(status['last_update']).strftime("%H:%M:%S")
            print(f"  📡 {mac}: {status['status']} (last: {last_update})")
            if status['message']:
                print(f"      └─ {status['message']}")
        
        print(f"\nDetected Beacons by Scanner:")
        for scanner_mac, detected_beacons in stats['scanner_data'].items():
            print(f"  🔍 Scanner {scanner_mac} ({len(detected_beacons)} beacons detected):")
            for beacon_mac, data in detected_beacons.items():
                last_seen = datetime.fromisoformat(data['last_seen']).strftime("%H:%M:%S")
                print(f"    └─ 📍 {beacon_mac}:")
                print(f"        ├─ Current RSSI: {data['rssi']} dBm")
                print(f"        ├─ Average RSSI: {data['avg_rssi']} dBm")
                print(f"        ├─ Range: {data['min_rssi']} to {data['max_rssi']} dBm")
                print(f"        ├─ Count: {data['count']} readings")
                print(f"        └─ Last seen: {last_seen}")
        
        if stats['latest_readings']:
            print(f"\nLatest 10 readings:")
            for reading in stats['latest_readings'][-10:]:
                timestamp = reading['timestamp'][-8:]
                print(f"  {timestamp} - {reading['scanner_mac']} → {reading['detected_beacon']}: {reading['rssi']} dBm")
    
    def stats_thread_func(self):
        """Thread function để in stats định kỳ"""
        while self.running:
            time.sleep(self.STATS_INTERVAL)
            if self.running:
                self.print_stats()
    
    def connect_to_beacon(self, beacon_config: Dict):
        """Kết nối đến một beacon và thu thập dữ liệu"""
        mac_address = beacon_config['mac']
        notify_handle = beacon_config['notify_handle']
        
        print(f"[{datetime.now()}] 🔄 Starting connection thread for {mac_address}")
        
        while self.running:
            child = None
            try:
                self.update_connection_status(mac_address, "CONNECTING", "Attempting connection...")
                print(f"[{datetime.now()}] 🔗 Connecting to {mac_address}...")
                
                child = pexpect.spawn("gatttool -I", timeout=10)
                child.expect(r"\[LE\]>", timeout=10)
                
                child.sendline(f"connect {mac_address}")
                child.expect("Connection successful", timeout=self.CONNECTION_TIMEOUT)
                
                self.update_connection_status(mac_address, "CONNECTED", "Connection established")
                print(f"[{datetime.now()}] ✅ Connected successfully to {mac_address}")
                
                # Enable notifications
                child.sendline(f"char-write-req {notify_handle} 0100")
                child.expect(r"\[LE\]>", timeout=5)
                
                self.update_connection_status(mac_address, "LISTENING", "Notifications enabled, listening for data")
                print(f"[{datetime.now()}] 👂 Notifications enabled for {mac_address} - Listening...")
                
                # Lắng nghe notifications
                consecutive_timeouts = 0
                while self.running:
                    try:
                        child.expect(r"Notification handle = .*? \r", timeout=self.NOTIFICATION_TIMEOUT)
                        consecutive_timeouts = 0  # Reset timeout counter
                        line = child.after.decode().strip()
                        
                        if "value:" in line:
                            hex_data = line.split("value:")[1].strip()
                            
                            try:
                                bytes_data = bytes.fromhex(hex_data)
                                decoded_str = bytes_data.decode("utf-8")
                                
                                # Parse beacon data: Support multiple formats
                                # Format 1: "MAC,RSSI"
                                # Format 2: "MAC1,RSSI1;MAC2,RSSI2;..."
                                # Format 3: JSON format
                                
                                if decoded_str.startswith('{'):
                                    # JSON format
                                    try:
                                        data = json.loads(decoded_str)
                                        if 'beacons' in data:
                                            for beacon_info in data['beacons']:
                                                if 'mac' in beacon_info and 'rssi' in beacon_info:
                                                    self.add_reading(mac_address, beacon_info['mac'], beacon_info['rssi'])
                                    except json.JSONDecodeError:
                                        pass
                                else:
                                    # Simple format
                                    beacon_entries = decoded_str.split(';')
                                    
                                    for entry in beacon_entries:
                                        if ',' in entry:
                                            parts = entry.split(',')
                                            if len(parts) >= 2:
                                                detected_beacon_mac = parts[0].strip()
                                                try:
                                                    rssi = int(parts[1].strip())
                                                    self.add_reading(mac_address, detected_beacon_mac, rssi)
                                                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 📡 {mac_address} → 📍 {detected_beacon_mac}: {rssi} dBm")
                                                except ValueError:
                                                    continue
                                
                            except (UnicodeDecodeError, ValueError) as e:
                                print(f"[{datetime.now()}] ❌ Parse error from {mac_address}: {e}")
                                print(f"Raw hex: {hex_data}")
                    
                    except pexpect.TIMEOUT:
                        consecutive_timeouts += 1
                        if consecutive_timeouts >= 3:
                            self.update_connection_status(mac_address, "TIMEOUT", f"No data for {self.NOTIFICATION_TIMEOUT * consecutive_timeouts}s")
                            print(f"[{datetime.now()}] ⏰ Multiple timeouts from {mac_address} - reconnecting...")
                            break
                        else:
                            self.update_connection_status(mac_address, "WAITING", f"Timeout #{consecutive_timeouts}, still listening...")
                            print(f"[{datetime.now()}] ⏳ Timeout #{consecutive_timeouts} from {mac_address} - continuing...")
            
            except pexpect.TIMEOUT:
                self.update_connection_status(mac_address, "CONNECTION_FAILED", "Connection timeout")
                print(f"[{datetime.now()}] ❌ Connection timeout for {mac_address}")
            except Exception as e:
                self.update_connection_status(mac_address, "ERROR", str(e))
                print(f"[{datetime.now()}] ❌ Connection error for {mac_address}: {e}")
            finally:
                if child:
                    try:
                        child.close()
                    except:
                        pass
            
            if self.running:
                print(f"[{datetime.now()}] 🔄 Reconnecting to {mac_address} in {self.RECONNECT_DELAY} seconds...")
                time.sleep(self.RECONNECT_DELAY)
    
    def start(self):
        """Bắt đầu thu thập dữ liệu"""
        self.start_time = datetime.now()
        self.running = True
        
        # Đọc cấu hình beacons
        beacon_configs = self.load_beacon_config()
        if not beacon_configs:
            print("❌ No beacon configuration found!")
            return False
        
        print(f"[{self.start_time}] 🚀 Starting Advanced Multi-Beacon BLE RSSI Collector...")
        print(f"Target beacons: {len(beacon_configs)}")
        for config in beacon_configs:
            print(f"  📡 {config['mac']} (handle: {config['notify_handle']})")
        
        # Bắt đầu stats thread
        stats_thread = threading.Thread(target=self.stats_thread_func, daemon=True)
        stats_thread.start()
        
        # Khởi tạo ThreadPoolExecutor
        self.executor = ThreadPoolExecutor(max_workers=len(beacon_configs), thread_name_prefix="BeaconThread")
        
        # Submit connection tasks
        futures = []
        for config in beacon_configs:
            future = self.executor.submit(self.connect_to_beacon, config)
            futures.append(future)
        
        return True
    
    def stop(self):
        """Dừng thu thập dữ liệu"""
        print(f"\n[{datetime.now()}] 🛑 Stopping multi-beacon collector...")
        self.running = False
        
        if self.executor:
            self.executor.shutdown(wait=False)
        
        self.print_stats()
    
    def export_data(self, filename: Optional[str] = None):
        """Xuất dữ liệu ra file JSON"""
        if not filename:
            filename = f"advanced_beacon_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        data = {
            "export_time": datetime.now().isoformat(),
            "collector_version": "2.0",
            "stats": self.get_stats(),
            "all_readings": [r.to_dict() for r in self.all_readings]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"📁 Data exported to {filename}")
        return filename

def main():
    """Hàm main"""
    collector = MultiBeaconCollector()
    
    try:
        if collector.start():
            print("✅ Collector started successfully. Press Ctrl+C to stop.")
            
            # Keep running until interrupted
            while collector.running:
                time.sleep(1)
                
    except KeyboardInterrupt:
        pass
    finally:
        collector.stop()
        
        # Hỏi có muốn xuất dữ liệu không
        try:
            export = input("\n💾 Export data to JSON file? (y/n): ")
            if export.lower() == 'y':
                collector.export_data()
        except:
            pass
        
        print("👋 Goodbye!")

if __name__ == "__main__":
    main()

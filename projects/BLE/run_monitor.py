# -*- coding: utf-8 -*-
"""
Script để chạy cả Multi-Beacon BLE collector và Flask web server cùng lúc
"""
import threading
import time
from datetime import datetime
from advanced_multi_collector import MultiBeaconCollector

# Global collector instance
multi_collector = None

def run_multi_beacon_collector():
    """Chạy Multi-Beacon BLE collector trong thread riêng"""
    global multi_collector
    try:
        # Tạo collector với setup_signals=False vì đang chạy trong thread
        multi_collector = MultiBeaconCollector(setup_signals=False)
        print(f"[{datetime.now()}] Starting Multi-Beacon Collector...")
        if multi_collector.start():
            print(f"[{datetime.now()}] Multi-Beacon Collector started successfully")
            # Keep the collector running
            while multi_collector.running:
                time.sleep(1)
        else:
            print(f"[{datetime.now()}] Failed to start Multi-Beacon Collector")
    except Exception as e:
        print(f"[{datetime.now()}] Multi-Beacon Collector error: {e}")
        import traceback
        traceback.print_exc()

def run_flask_app():
    """Chạy Flask app trong thread riêng"""
    from flask_app_multi import app, set_collector
    
    # Set collector reference cho Flask app
    global multi_collector
    if multi_collector:
        set_collector(multi_collector)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        print(f"[{datetime.now()}] Flask App error: {e}")

if __name__ == "__main__":
    print("🚀 Starting Multi-Beacon BLE Monitor System...")
    print("="*60)
    
    # Bắt đầu Multi-Beacon collector thread
    print("📡 Starting Multi-Beacon Data Collector...")
    ble_thread = threading.Thread(target=run_multi_beacon_collector, daemon=True)
    ble_thread.start()
    
    # Đợi 5 giây để Multi-Beacon collector khởi động
    time.sleep(5)
    
    # Set collector cho Flask app sau khi collector đã khởi tạo
    if multi_collector:
        from flask_app_multi import set_collector
        set_collector(multi_collector)
        print("✅ Collector reference set for Flask app")
    
    # Bắt đầu Flask web server
    print("🌐 Starting Flask Web Server...")
    print("📱 Web interface: http://localhost:5000")
    print("📊 API Multi-Beacons: http://localhost:5000/api/multi-beacons")
    print("📈 API Scanner Status: http://localhost:5000/api/scanner-status")
    print("📋 API Latest Readings: http://localhost:5000/api/latest-readings")
    print("="*60)
    print("⏹️  Press Ctrl+C to stop both services")
    
    try:
        run_flask_app()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now()}] Shutting down...")
        if multi_collector:
            multi_collector.stop()
        print("👋 Goodbye!")

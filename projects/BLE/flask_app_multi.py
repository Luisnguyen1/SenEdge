# -*- coding: utf-8 -*-
"""
Flask Web App để hiển thị dữ liệu Multi-Beacon BLE RSSI
"""
from flask import Flask, render_template, jsonify
from datetime import datetime
import threading
import time

app = Flask(__name__)

# Global collector reference
multi_collector = None

def set_collector(collector):
    """Set collector instance from external source"""
    global multi_collector
    multi_collector = collector

def get_collector():
    """Get collector instance"""
    global multi_collector
    return multi_collector

@app.route('/')
def index():
    """Trang chính hiển thị dữ liệu multi-beacons"""
    return render_template('multi_beacon_index.html')

@app.route('/map')
def location_map():
    """Trang bản đồ vị trí indoor positioning"""
    return render_template('location_map.html')

@app.route('/api/multi-beacons')
def api_multi_beacons():
    """API endpoint trả về dữ liệu từ tất cả beacons dạng JSON"""
    collector = get_collector()
    if not collector:
        return jsonify({
            'error': 'Multi-beacon collector not available',
            'scanners': [],
            'total_scanners': 0,
            'total_detected_beacons': 0,
            'total_readings': 0,
            'uptime_seconds': 0,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
    
    try:
        stats = collector.get_stats()
        
        # Format dữ liệu cho web interface
        scanners_data = []
        for scanner_mac, detected_beacons in stats['scanner_data'].items():
            scanner_info = {
                'scanner_mac': scanner_mac,
                'detected_beacons': [],
                'beacon_count': len(detected_beacons),
                'connection_status': stats['connection_status'].get(scanner_mac, {})
            }
            
            for beacon_mac, beacon_data in detected_beacons.items():
                beacon_info = {
                    'mac_address': beacon_mac,
                    'rssi': beacon_data['rssi'],
                    'count': beacon_data['count'],
                    'avg_rssi': beacon_data['avg_rssi'],
                    'min_rssi': beacon_data['min_rssi'],
                    'max_rssi': beacon_data['max_rssi'],
                    'last_seen': datetime.fromisoformat(beacon_data['last_seen']).strftime("%H:%M:%S"),
                    'first_seen': datetime.fromisoformat(beacon_data['first_seen']).strftime("%H:%M:%S")
                }
                scanner_info['detected_beacons'].append(beacon_info)
            
            # Sắp xếp beacons theo RSSI (mạnh nhất trước)
            scanner_info['detected_beacons'].sort(key=lambda x: x['rssi'], reverse=True)
            scanners_data.append(scanner_info)
        
        return jsonify({
            'scanners': scanners_data,
            'total_scanners': stats['total_scanners'],
            'total_detected_beacons': stats['total_detected_beacons'],
            'total_readings': stats['total_readings'],
            'uptime_seconds': int(stats['uptime_seconds']),
            'latest_readings': stats['latest_readings'][-15:],  # 15 readings mới nhất
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting stats: {str(e)}',
            'scanners': [],
            'total_scanners': 0,
            'total_detected_beacons': 0,
            'total_readings': 0,
            'uptime_seconds': 0,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })

@app.route('/api/scanner-status')
def api_scanner_status():
    """API endpoint trả về trạng thái kết nối của các scanners"""
    collector = get_collector()
    if not collector:
        return jsonify({
            'error': 'Multi-beacon collector not available',
            'connection_status': {}
        })
    
    try:
        stats = collector.get_stats()
        
        # Format connection status
        formatted_status = {}
        for scanner_mac, status in stats['connection_status'].items():
            formatted_status[scanner_mac] = {
                'status': status['status'],
                'message': status['message'],
                'last_update': datetime.fromisoformat(status['last_update']).strftime("%H:%M:%S")
            }
        
        return jsonify({
            'connection_status': formatted_status,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting scanner status: {str(e)}',
            'connection_status': {}
        })

@app.route('/api/latest-readings')
def api_latest_readings():
    """API endpoint trả về readings mới nhất từ tất cả scanners"""
    collector = get_collector()
    if not collector:
        return jsonify({
            'error': 'Multi-beacon collector not available',
            'latest_readings': []
        })
    
    try:
        with collector.stats_lock:
            # Lấy 50 readings mới nhất
            readings = [r.to_dict() for r in collector.all_readings[-50:]]
        
        # Format readings cho web
        formatted_readings = []
        for reading in readings:
            formatted_readings.append({
                'timestamp': datetime.fromisoformat(reading['timestamp']).strftime("%H:%M:%S"),
                'scanner_mac': reading['scanner_mac'],
                'detected_beacon': reading['detected_beacon'],
                'rssi': reading['rssi']
            })
        
        return jsonify({
            'latest_readings': formatted_readings,
            'count': len(formatted_readings),
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting latest readings: {str(e)}',
            'latest_readings': []
        })

@app.route('/api/export')
def api_export():
    """API endpoint để export dữ liệu"""
    collector = get_collector()
    if not collector:
        return jsonify({
            'success': False,
            'error': 'Multi-beacon collector not available'
        })
    
    try:
        filename = collector.export_data()
        return jsonify({
            'success': True,
            'filename': filename,
            'message': f'Data exported successfully to {filename}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Export failed: {str(e)}'
        })

@app.route('/api/collector-control/<action>')
def api_collector_control(action):
    """API endpoint để điều khiển collector (start/stop)"""
    collector = get_collector()
    if not collector:
        return jsonify({
            'success': False,
            'error': 'Multi-beacon collector not available'
        })
    
    try:
        if action == 'stop':
            collector.stop()
            return jsonify({
                'success': True,
                'message': 'Collector stopped successfully'
            })
        elif action == 'status':
            return jsonify({
                'success': True,
                'running': collector.running,
                'start_time': collector.start_time.isoformat() if collector.start_time else None
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Unknown action: {action}'
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Control action failed: {str(e)}'
        })

@app.route('/api/positioning-data')
def api_positioning_data():
    """API endpoint trả về dữ liệu để tính toán vị trí từ các beacons"""
    collector = get_collector()
    if not collector:
        return jsonify({
            'error': 'Multi-beacon collector not available',
            'beacon_data': {}
        })
    
    try:
        stats = collector.get_stats()
        
        # Lấy dữ liệu beacon mới nhất từ tất cả scanners
        beacon_data = {}
        
        # Định nghĩa danh sách MAC addresses của 3 beacons chính
        target_beacons = [
            '80:4B:50:56:A6:91',  # Beacon 1
            '60:A4:23:C9:85:C1',  # Beacon 2  
            'C0:2C:ED:90:AD:A3'   # Beacon 3
        ]
        
        # Tổng hợp dữ liệu từ tất cả scanners
        for scanner_mac, detected_beacons in stats['scanner_data'].items():
            for beacon_mac, beacon_info in detected_beacons.items():
                if beacon_mac in target_beacons:
                    # Nếu beacon này chưa có hoặc có RSSI yếu hơn, cập nhật
                    if (beacon_mac not in beacon_data or 
                        beacon_info['rssi'] > beacon_data[beacon_mac]['rssi']):
                        beacon_data[beacon_mac] = {
                            'rssi': beacon_info['rssi'],
                            'avg_rssi': beacon_info['avg_rssi'],
                            'min_rssi': beacon_info['min_rssi'],
                            'max_rssi': beacon_info['max_rssi'],
                            'count': beacon_info['count'],
                            'last_seen': beacon_info['last_seen'],
                            'scanner_mac': scanner_mac
                        }
        
        return jsonify({
            'beacon_data': beacon_data,
            'total_beacons_detected': len(beacon_data),
            'target_beacons': target_beacons,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error getting positioning data: {str(e)}',
            'beacon_data': {}
        })

@app.route('/api/beacon-distances')
def api_beacon_distances():
    """API endpoint trả về khoảng cách ước tính đến các beacons"""
    collector = get_collector()
    if not collector:
        return jsonify({
            'error': 'Multi-beacon collector not available',
            'distances': {}
        })
    
    try:
        stats = collector.get_stats()
        
        # Hàm chuyển đổi RSSI thành khoảng cách (công thức đơn giản)
        def rssi_to_distance(rssi, tx_power=-59):
            if rssi == 0:
                return -1.0
            ratio = rssi * 1.0 / tx_power
            if ratio < 1.0:
                return pow(ratio, 10)
            else:
                accuracy = (0.89976) * pow(ratio, 7.7095) + 0.111
                return accuracy
        
        distances = {}
        target_beacons = [
            '80:4B:50:56:A6:91',  # Beacon 1
            '60:A4:23:C9:85:C1',  # Beacon 2  
            'C0:2C:ED:90:AD:A3'   # Beacon 3
        ]
        
        # Tính khoảng cách cho từng beacon
        for scanner_mac, detected_beacons in stats['scanner_data'].items():
            for beacon_mac, beacon_info in detected_beacons.items():
                if beacon_mac in target_beacons:
                    distance = rssi_to_distance(beacon_info['rssi'])
                    
                    if beacon_mac not in distances:
                        distances[beacon_mac] = []
                    
                    distances[beacon_mac].append({
                        'distance': round(distance, 2),
                        'rssi': beacon_info['rssi'],
                        'scanner': scanner_mac,
                        'accuracy': 'high' if beacon_info['rssi'] > -60 else 'medium' if beacon_info['rssi'] > -80 else 'low'
                    })
        
        # Tính khoảng cách trung bình cho mỗi beacon
        avg_distances = {}
        for beacon_mac, distance_list in distances.items():
            if distance_list:
                avg_distance = sum(d['distance'] for d in distance_list) / len(distance_list)
                best_rssi = max(d['rssi'] for d in distance_list)
                avg_distances[beacon_mac] = {
                    'average_distance': round(avg_distance, 2),
                    'best_rssi': best_rssi,
                    'measurement_count': len(distance_list),
                    'all_measurements': distance_list
                }
        
        return jsonify({
            'distances': avg_distances,
            'timestamp': datetime.now().strftime("%H:%M:%S")
        })
        
    except Exception as e:
        return jsonify({
            'error': f'Error calculating distances: {str(e)}',
            'distances': {}
        })

if __name__ == '__main__':
    print("🌐 Starting Multi-Beacon Flask Web Server...")
    print("📱 Access the web interface at: http://localhost:5000")
    print("📊 API endpoints:")
    print("   - http://localhost:5000/api/multi-beacons")
    print("   - http://localhost:5000/api/scanner-status")
    print("   - http://localhost:5000/api/latest-readings")
    print("   - http://localhost:5000/api/export")
    print("⏹️  Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)

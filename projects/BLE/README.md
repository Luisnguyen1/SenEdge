# Multi-Beacon BLE Collector

Hệ thống thu thập dữ liệu RSSI từ nhiều BLE beacons đồng thời trên Raspberry Pi.

## 📋 Tính năng

### ✨ Tính năng chính
- **Kết nối đồng thời**: Kết nối đến nhiều beacons cùng một lúc
- **Thu thập real-time**: Thu thập dữ liệu RSSI liên tục từ tất cả beacons
- **Web Dashboard**: Giao diện web để theo dõi real-time
- **Thống kê chi tiết**: Hiển thị thống kê về từng beacon được phát hiện
- **Export dữ liệu**: Xuất dữ liệu ra file JSON
- **Auto-reconnect**: Tự động kết nối lại khi bị ngắt

### 📊 Dữ liệu thu thập
Mỗi beacon scanner sẽ gửi về danh sách các beacon và RSSI mà nó phát hiện được:
- **Scanner MAC**: Địa chỉ MAC của beacon đang scan
- **Detected MAC**: Địa chỉ MAC của beacon được phát hiện  
- **RSSI**: Cường độ tín hiệu
- **Timestamp**: Thời gian thu thập
- **Thống kê**: Min/Max/Average RSSI, số lần phát hiện

## 🛠️ Cài đặt

### 1. Chuẩn bị môi trường
```bash
# Cài đặt BlueZ tools (nếu chưa có)
sudo apt update
sudo apt install bluez bluez-tools

# Clone repository hoặc copy files
cd /path/to/your/project
```

### 2. Cấu hình beacons
Chỉnh sửa file `beancons.json`:
```json
{
    "beacons": [
        {
            "mac": "80:4B:50:56:A6:91",
            "notify_handle": "0x0021"
        },
        {
            "mac": "60:A4:23:C9:85:C1", 
            "notify_handle": "0x0022"
        },
        {
            "mac": "C0:2C:ED:90:AD:A3",
            "notify_handle": "0x0022"
        }
    ]
}
```

### 3. Chạy collector
```bash
python run_multi_collector.py
```

## 📱 Cách sử dụng

### Option 1: Console Mode
- Hiển thị dữ liệu trực tiếp trong terminal
- In thống kê mỗi 30 giây
- Phù hợp cho debugging và monitoring cơ bản

### Option 2: Web Dashboard Mode  
- Mở trình duyệt và truy cập: `http://localhost:5000`
- Giao diện web real-time với charts và tables
- Điều khiển start/stop collector từ web
- Export dữ liệu từ giao diện

## 📁 Cấu trúc files

```
├── beancons.json                 # Cấu hình beacons
├── requirements.txt              # Python dependencies
├── run_multi_collector.py        # Script chính để chạy
├── advanced_multi_collector.py   # Core collector engine
├── web_multi_collector.py        # Flask web interface
├── templates/
│   └── dashboard.html            # Web dashboard template
├── easy.py                       # Collector đơn giản (tham khảo)
└── README.md                     # File này
```

## 🔧 Cấu hình nâng cao

### Thay đổi cấu hình trong advanced_multi_collector.py:
```python
# Số readings tối đa lưu trong memory
MAX_READINGS = 10000

# Thời gian reconnect khi mất kết nối (giây)
RECONNECT_DELAY = 5

# Interval in thống kê (giây)
STATS_INTERVAL = 30

# Timeout kết nối (giây)
CONNECTION_TIMEOUT = 15

# Timeout chờ notification (giây)  
NOTIFICATION_TIMEOUT = 60
```

## 📋 Format dữ liệu

### Dữ liệu từ beacon (qua BLE notification):
```
# Format 1: Single beacon
"MAC_ADDRESS,RSSI"
# Ví dụ: "A1:B2:C3:D4:E5:F6,-65"

# Format 2: Multiple beacons
"MAC1,RSSI1;MAC2,RSSI2;MAC3,RSSI3"
# Ví dụ: "A1:B2:C3:D4:E5:F6,-65;B2:C3:D4:E5:F6:A1,-72"

# Format 3: JSON (tương lai)
{"beacons": [{"mac": "A1:B2:C3:D4:E5:F6", "rssi": -65}]}
```

### Dữ liệu export ra JSON:
```json
{
  "export_time": "2025-01-01T12:00:00",
  "collector_version": "2.0",
  "stats": {
    "total_scanners": 3,
    "total_detected_beacons": 5,
    "total_readings": 1250,
    "uptime_seconds": 3600,
    "scanner_data": {
      "80:4B:50:56:A6:91": {
        "A1:B2:C3:D4:E5:F6": {
          "rssi": -65,
          "count": 45,
          "avg_rssi": -67.2,
          "min_rssi": -75,
          "max_rssi": -58,
          "last_seen": "2025-01-01T12:00:00"
        }
      }
    }
  },
  "all_readings": [...]
}
```

## 🚨 Troubleshooting

### Lỗi kết nối Bluetooth:
```bash
# Kiểm tra Bluetooth service
sudo systemctl status bluetooth

# Restart Bluetooth
sudo systemctl restart bluetooth

# Kiểm tra quyền truy cập
sudo chmod 666 /dev/rfcomm*
```

### Lỗi "gatttool not found":
```bash
sudo apt install bluez bluez-tools
```

### Lỗi permissions:
```bash
# Thêm user vào bluetooth group
sudo usermod -a -G dialout $USER
sudo usermod -a -G bluetooth $USER

# Logout và login lại
```

### Beacon không kết nối được:
1. Kiểm tra MAC address trong `beancons.json`
2. Kiểm tra notify handle có đúng không
3. Đảm bảo beacon đang ở chế độ connectable
4. Kiểm tra khoảng cách và nhiễu

## 📊 Web Dashboard Features

- **Real-time stats**: Tổng số scanners, beacons, readings
- **Connection status**: Trạng thái kết nối của từng beacon
- **Scanner overview**: Danh sách beacons được phát hiện bởi từng scanner
- **Recent readings**: Bảng readings mới nhất
- **Controls**: Start/Stop collector, Export data
- **Auto-refresh**: Cập nhật mỗi 2 giây

## 🔄 API Endpoints

- `GET /api/stats` - Lấy thống kê hiện tại
- `GET /api/start` - Bắt đầu collector
- `GET /api/stop` - Dừng collector  
- `GET /api/export` - Export dữ liệu ra file
- `GET /api/readings` - Lấy 100 readings mới nhất

## 📝 Logs và Monitoring

Collector sẽ in logs với format:
```
[2025-01-01 12:00:00] 🔗 Connecting to 80:4B:50:56:A6:91...
[2025-01-01 12:00:01] ✅ Connected successfully to 80:4B:50:56:A6:91
[2025-01-01 12:00:02] 👂 Notifications enabled for 80:4B:50:56:A6:91
[12:00:03] 📡 80:4B:50:56:A6:91 → 📍 A1:B2:C3:D4:E5:F6: -65 dBm
```

## 🤝 Đóng góp

Hệ thống có thể được mở rộng với:
- Database storage (InfluxDB, PostgreSQL)
- Advanced analytics và machine learning
- REST API cho integration
- Mobile app
- Alerting system
- Geographic mapping

## 📄 License

MIT License - Sử dụng tự do cho mục đích học tập và thương mại.

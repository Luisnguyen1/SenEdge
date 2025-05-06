# IoT-AI Retail Assistant

Hệ thống hỗ trợ mua sắm thông minh tích hợp IoT và AI.

## Quản lý dự án
- [Sheet quản lý dự án và tiến độ thực hiện](https://docs.google.com/spreadsheets/d/13m0ShLNtGouON7MF4_G_lY2k21fo5KolhyPQXGdVfVA/edit?usp=sharing)

## Cấu trúc dự án

```
.
├── backend/           # Backend chính của hệ thống
├── chatbot/          # Module RAG Chatbot
├── data_crawling/    # Scripts thu thập dữ liệu
├── map/              # Module định vị và dẫn đường
├── sensor_report/    # Module phân tích dữ liệu IoT
└── document/         # Tài liệu hệ thống
```

## Tài liệu

- [Chi tiết hệ thống](document.md)
- [Sequence Diagram](sequencsDiagram.md)
- [Sơ đồ bản đồ](map/map.md)

## Yêu cầu

### Cài đặt

1. Python 3.9+
2. Node.js 16+
3. MongoDB
4. Docker & Docker Compose

### Các gói phụ thuộc

Cài đặt các gói Python:
```powershell
pip install -r requirements.txt
```

## Khởi động

### Sử dụng Docker

```powershell
docker-compose up --build
```

### Khởi động từng module

1. Backend:
```powershell
cd backend
python main.py
```

2. Chatbot:
```powershell
cd chatbot
python app.py
```

3. Map:
```powershell
cd map
python run.py
```

4. Sensor Report:
```powershell
cd sensor_report
python main.py
```

## Lưu ý

- Đảm bảo MongoDB đang chạy trước khi khởi động hệ thống
- Cấu hình các biến môi trường trong file `.env`
- Kiểm tra các cổng 5000, 5001, 5002 không bị sử dụng

## Đóng góp

Tham khảo [CONTRIBUTING.md](CONTRIBUTING.md) cho chi tiết về quy trình đóng góp.

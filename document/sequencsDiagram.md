# Sequence Diagram cho Hệ thống IoT-AI Retail Assistant

## 1. Luồng Chính (Main Flow)

```mermaid
sequenceDiagram
    actor Customer as Khách hàng
    participant App as Mobile/Web App
    participant Chat as RAG Chatbot
    participant Nav as Navigation System
    participant IoT as IoT Analytics
    participant DB as Databases
    
    Customer->>App: Mở ứng dụng
    App->>IoT: Khởi tạo theo dõi vị trí
    IoT->>App: Gửi dữ liệu quầy thu ngân
    
    rect rgb(200, 230, 200)
        Note right of Customer: Luồng tư vấn sản phẩm
        Customer->>App: Nhập câu hỏi về sản phẩm
        App->>Chat: Gửi query
        Chat->>DB: Tìm kiếm thông tin
        DB->>Chat: Trả về dữ liệu sản phẩm
        Chat->>App: Phản hồi + đề xuất sản phẩm
    end
    
    rect rgb(230, 200, 230)
        Note right of Customer: Luồng dẫn đường
        Customer->>App: Chọn sản phẩm để tìm
        App->>Nav: Yêu cầu chỉ đường
        Nav->>IoT: Kiểm tra tình trạng khu vực
        IoT->>Nav: Trả về density map
        Nav->>App: Trả về lộ trình tối ưu
        App->>Customer: Hiển thị chỉ dẫn
    end
    
    rect rgb(200, 200, 230)
        Note right of Customer: Luồng thanh toán
        Customer->>App: Yêu cầu thanh toán
        App->>IoT: Kiểm tra quầy thu ngân
        IoT->>App: Đề xuất quầy optimal
        App->>Nav: Tính toán đường đến quầy
        Nav->>App: Trả về lộ trình
        App->>Customer: Hiển thị chỉ dẫn đến quầy
    end
```

## 2. Luồng RAG Chatbot Detail

```mermaid
sequenceDiagram    actor U as User
    participant C as Chatbot Frontend
    participant R as RAG Engine
    participant V as Vector DB
    participant P as Product DB
    
    U->>C: Gửi câu hỏi
    C->>R: Query Processing
    R->>V: Vector Search
    V->>R: Related Documents
    R->>P: Get Product Details
    P->>R: Product Data
    R->>C: Generate Response
    C->>U: Hiển thị kết quả
    
    Note right of R: Embedding + LLM Processing
```

## 3. Luồng Indoor Navigation Detail

```mermaid
sequenceDiagram    actor U as User
    participant A as App
    participant B as BLE Scanner
    participant P as Position Engine
    participant R as Route Calculator
    participant M as Map Renderer
    
    U->>A: Request Navigation
    
    loop Every 1s
        A->>B: Scan BLE Signals
        B->>P: RSSI Data
        P->>P: Trilateration
        P->>A: Current Position
    end
    
    A->>R: Calculate Route
    R->>M: Draw Route
    M->>A: Map View
    A->>U: Turn-by-turn Navigation
```

## 4. Luồng IoT Analytics Detail

```mermaid
sequenceDiagram
    participant C as Cameras
    participant E as Edge Device
    participant A as Analytics Engine
    participant D as Dashboard
    participant N as Navigation System
    
    loop Real-time
        C->>E: Video Feed
        E->>E: People Detection
        E->>A: Queue Analytics
        A->>A: Process Data
        A->>D: Update Metrics
    end
    
    N->>A: Request Queue Status
    A->>N: Optimal Route
```

## 5. Xử lý Lỗi và Recovery

```mermaid
sequenceDiagram
    participant App
    participant System
    participant Backup
    
    rect rgb(255, 200, 200)
        Note right of App: Error Handling
        App->>System: Request
        System-->>App: Error Response
        App->>Backup: Fallback Request
        Backup->>App: Backup Response
    end
    
    rect rgb(200, 255, 200)
        Note right of App: Auto Recovery
        System->>System: Self Monitoring
        System->>System: Detect Issues
        System->>System: Auto Restart/Heal
    end
```

## 6. Data Synchronization

```mermaid
sequenceDiagram
    participant Edge
    participant Cloud
    participant Cache
    
    loop Every 5min
        Edge->>Cloud: Send Analytics
        Cloud->>Edge: Update Config
    end
    
    loop Every 1min
        Edge->>Cache: Update Local Cache
        Cache->>Edge: Serve Requests
    end
```

Các sequence diagram trên mô tả:
1. Luồng chính của hệ thống
2. Chi tiết xử lý của RAG Chatbot
3. Chi tiết hoạt động của Indoor Navigation
4. Chi tiết phân tích IoT Analytics
5. Xử lý lỗi và recovery
6. Đồng bộ hóa dữ liệu

Mỗi module có thể hoạt động độc lập nhưng vẫn tích hợp chặt chẽ với nhau thông qua các API và event system. Việc này đảm bảo tính modular và khả năng scale của hệ thống.

# Tổng quan Hệ thống IoT-AI Retail Assistant

## 1. Kiến trúc Tổng thể
Diagram này mô tả một kiến trúc hệ thống IoT với ba tầng chính: Tầng ứng dụng, Tầng dịch vụ, và Tầng IoT. Dưới đây là phân tích kỹ thuật chi tiết từng tầng và cách chúng tương tác.

1. Tầng ứng dụng (User Interface Layer)

Tầng này là giao diện người dùng cuối, nơi người dùng tương tác với hệ thống. Nó bao gồm:


Mobile App:

Ứng dụng di động, có thể được phát triển trên iOS hoặc Android.

Chức năng: Hiển thị dữ liệu IoT (như thông tin môi trường, vị trí), gửi yêu cầu (ví dụ: hỏi chatbot), và nhận thông báo.

Kết nối: Giao tiếp với tầng dịch vụ qua API (REST hoặc WebSocket).

Web App:

Ứng dụng web, chạy trên trình duyệt.

Chức năng: Tương tự Mobile App nhưng tối ưu cho màn hình lớn hơn, phù hợp với người dùng trên máy tính.

Kết nối: Cũng sử dụng API để giao tiếp với tầng dịch vụ.

Admin Dashboard:

Bảng điều khiển dành cho quản trị viên.
Chức năng: Quản lý hệ thống (xem dữ liệu IoT, cấu hình thiết bị, phân tích hiệu suất), giám sát trạng thái thiết bị IoT, và truy cập báo cáo phân tích.

Kết nối: Truy cập tầng dịch vụ để lấy dữ liệu và gửi lệnh quản trị.

Luồng dữ liệu: Tầng ứng dụng gửi yêu cầu đến tầng dịch vụ (ví dụ: truy vấn chatbot, yêu cầu phân tích dữ liệu) và nhận kết quả trả về để hiển thị.

2. Service Layer

Đây là tầng trung gian, xử lý logic nghiệp vụ và kết nối các tầng khác. Nó bao gồm các dịch vụ:
RAG Chatbot Service:
Dịch vụ chatbot sử dụng mô hình Retrieval-Augmented Generation (RAG).
Chức năng: Trả lời câu hỏi người dùng bằng cách truy xuất thông tin từ Vector DB (dữ liệu dạng vector, thường dùng cho tìm kiếm ngữ nghĩa) và kết hợp với mô hình ngôn ngữ để sinh câu trả lời tự nhiên.

Ví dụ: Người dùng hỏi "Món hàng này còn không", chatbot lấy dữ liệu từ Vector DB và trả lời dựa trên thông tin trong kho.

Analytics Service:
Chức năng: Xử lý dữ liệu từ Analytics DB và dữ liệu thời gian thực từ tầng IoT để tạo báo cáo, biểu đồ, hoặc dự đoán.
Ví dụ: Phân tích xu hướng mua hàng trong khoảng thời gian 2 tháng gần nhất để biết mặt hàng nào bán chạy.
Navigation Service:
Dịch vụ điều hướng, có thể hỗ trợ định vị (indoor navigation).

Chức năng: Sử dụng dữ liệu từ BLE Beacons (ở tầng IoT) để xác định vị trí người dùng và cung cấp hướng dẫn di chuyển.
Ví dụ: Hỗ trợ người dùng tìm đường trong một tòa nhà lớn dựa trên tín hiệu BLE.

Kết nối với tầng dữ liệu:

Các dịch vụ này truy xuất dữ liệu từ Product DB (thông tin sản phẩm), Analytics DB (dữ liệu phân tích), và Vector DB (dữ liệu vector cho AI).

Chúng cũng gửi dữ liệu đã xử lý (như kết quả phân tích) trở lại các cơ sở dữ liệu này.

Kết nối với tầng IoT:

Tầng dịch vụ nhận dữ liệu thời gian thực từ tầng IoT qua Gateway và gửi lệnh điều khiển (nếu cần) đến các thiết bị IoT.

3. Tầng dữ liệu (Data Layer)

Tầng này lưu trữ dữ liệu cần thiết cho hệ thống, bao gồm:

Product DB:

Cơ sở dữ liệu quan hệ (SQL), lưu thông tin sản phẩm.

Ví dụ: Danh sách thiết bị IoT, thông số kỹ thuật, hoặc thông tin cấu hình.
Analytics DB:
Cơ sở dữ liệu phân tích, có thể là SQL hoặc NoSQL (như MongoDB).
Lưu trữ dữ liệu lịch sử từ tầng IoT (như nhiệt độ, chuyển động) và kết quả phân tích từ Analytics Service.
Vector DB:
Cơ sở dữ liệu vector (như Pinecone, Weaviate), lưu trữ dữ liệu dạng vector.
Dùng cho các tác vụ AI như tìm kiếm ngữ nghĩa hoặc hỗ trợ chatbot (RAG Chatbot Service).
Ví dụ: Lưu trữ embedding của dữ liệu IoT để chatbot truy vấn nhanh.

Quản lý dữ liệu:
Dữ liệu từ tầng IoT được gửi lên qua Gateway, sau đó được xử lý bởi tầng dịch vụ và lưu vào các cơ sở dữ liệu này.
Tầng dịch vụ truy xuất dữ liệu từ đây để phục vụ tầng ứng dụng.

4. Tầng IoT (IoT Layer)

Tầng này bao gồm các thiết bị IoT, giao thức kết nối, và thiết bị tính toán tại chỗ. Cụ thể:
BLE Beacons (BGG220-EK):

Thiết bị phát tín hiệu Bluetooth Low Energy (BLE), mã sản phẩm BGG220-EK.
Chức năng: Phát tín hiệu để định vị trong không gian nhỏ (indoor positioning).
Ứng dụng: Hỗ trợ Navigation Service xác định vị trí người dùng.

Mesh Network (EFR32MG21):

Mạng lưới (mesh network) sử dụng chip EFR32MG21 của Silicon Labs.

Chức năng: Kết nối nhiều thiết bị IoT trong một mạng lưới, đảm bảo độ tin cậy và mở rộng phạm vi kết nối.
Ví dụ: Các cảm biến môi trường và chuyển động kết nối với nhau qua mesh network, gửi dữ liệu đến Gateway.
Computing (Raspberry Pi):
Raspberry Pi là thiết bị tính toán tại chỗ (edge computing).
Chức năng: Xử lý dữ liệu cục bộ từ các cảm biến để giảm tải cho hệ thống trung tâm, gửi dữ liệu đã xử lý lên Gateway.
Gateway:
Cổng kết nối giữa tầng IoT và tầng dịch vụ.
Chức năng: Thu thập dữ liệu từ các thiết bị IoT (qua BLE hoặc mesh network) và gửi lên tầng dịch vụ qua giao thức như MQTT hoặc HTTP.
Cũng nhận lệnh từ tầng dịch vụ để điều khiển thiết bị IoT.
Environmental (X026-DK2608A):
Cảm biến môi trường, mã sản phẩm X026-DK2608A.
Chức năng: Đo các thông số như nhiệt độ, độ ẩm, ánh sáng, hoặc chất lượng không khí.
Dữ liệu từ cảm biến này được gửi qua mesh network hoặc Raspberry Pi đến Gateway.
Motion:
Cảm biến chuyển động.
Chức năng: Phát hiện chuyển động trong khu vực được giám sát.
Ứng dụng: Kích hoạt cảnh báo (qua Admin Dashboard) hoặc ghi lại dữ liệu chuyển động để phân tích.
5. Luồng dữ liệu
Thu thập dữ liệu:
Các cảm biến (Environmental, Motion) và BLE Beacons thu thập dữ liệu.
Dữ liệu được gửi qua Mesh Network (EFR32MG21) hoặc xử lý cục bộ bởi Raspberry Pi, sau đó chuyển đến Gateway.
Xử lý và lưu trữ:
Gateway gửi dữ liệu lên tầng dịch vụ.
Analytics Service xử lý dữ liệu và lưu vào Analytics DB.
RAG Chatbot Service sử dụng Vector DB để trả lời truy vấn.
Navigation Service dùng dữ liệu từ BLE Beacons để hỗ trợ điều hướng.
Hiển thị và tương tác:
Tầng ứng dụng (Mobile App, Web App, Admin Dashboard) lấy dữ liệu từ tầng dịch vụ để hiển thị cho người dùng.
Người dùng gửi yêu cầu (như hỏi chatbot hoặc xem báo cáo) ngược lại qua tầng ứng dụng.

```mermaid
graph TB
    subgraph "Tầng Ứng dụng"
        A[Mobile App]
        B[Web App]
        C[Admin Dashboard]
    end

    subgraph "Tầng Service"
        D[RAG Chatbot Service]
        E[Navigation Service]
        F[Analytics Service]
        G[Gateway Service]
    end

    subgraph "Tầng IoT"
        H[BLE Beacons/BG220-EK]
        I[Environmental/XG26-DK2608A]
        J[Motion/XG24-EK2703A]
        K[Mesh Network/EFR32MG21]
        L[Edge Computing/Raspberry Pi]
    end

    subgraph "Tầng Dữ liệu"
        M[(Product DB)]
        N[(Analytics DB)]
        O[(Vector DB)]
    end

    A --> D & E & F
    B --> D & E & F
    C --> F & G
    
    D --> M & O
    E --> H & K
    F --> N & L
    G --> I & J & K & L
    
    H --> K
    I --> K
    J --> K
    K --> L
    L --> G
```

## 2. Luồng Dữ liệu Tổng thể
1. Giới thiệu về Sơ đồ
Sơ đồ được cung cấp là một sequence diagram (sơ đồ tuần tự) minh họa quy trình tương tác và luồng dữ liệu trong một hệ sinh thái IoT (Internet of Things). Nó trình bày cách các thành phần chính, bao gồm Người dùng (User), Giao diện Mobile/Web, IoT Gateway, Dịch vụ Đám mây (Cloud Services), và Cơ sở Dữ liệu (Databases), hoạt động và trao đổi dữ liệu. Sơ đồ được thiết kế với nền tối, chữ trắng và xám, đảm bảo tính dễ đọc và chuyên nghiệp, phù hợp để phân tích trong các báo cáo kỹ thuật.

2. Phân tích Thành phần Chính
Bảng dưới đây tóm tắt các thành phần chính và vai trò của chúng trong sơ đồ:

Thành phần	Mô tả	Vị trí trong Sơ đồ
Người dùng (User)	Điểm khởi đầu, thực hiện các hành động như truy cập ứng dụng.	Bên trái, hộp chữ nhật nhãn "User".
Giao diện Mobile/Web	Giao diện người dùng sử dụng để tương tác, hiển thị kết quả cuối cùng.	Bên phải User, hộp chữ nhật nhãn "Mobile/Web".
IoT Gateway	Trung gian thu thập dữ liệu cảm biến, kết nối giao diện và dịch vụ đám mây.	Trung tâm, hộp chữ nhật nhãn "IoT Gateway".
Dịch vụ Đám mây	Xử lý dữ liệu, lưu trữ phân tích, và phản hồi yêu cầu dịch vụ.	Bên phải IoT Gateway, hộp chữ nhật nhãn "Cloud Services".
Cơ sở Dữ liệu	Lưu trữ dữ liệu phân tích và cung cấp dữ liệu khi được truy vấn.	Bên phải cùng, hộp chữ nhật nhãn "Databases".
Mỗi thành phần được đại diện bởi một lifeline (đường đời) dọc, với hộp chữ nhật ở đầu biểu thị tên thành phần, và các mũi tên ngang thể hiện luồng dữ liệu hoặc tương tác.

3. Phân tích Luồng Dữ liệu và Tương tác
Sơ đồ được chia thành hai giai đoạn chính, được minh họa qua các mũi tên và nhãn chi tiết. Dưới đây là phân tích từng giai đoạn:

3.1. Giai đoạn Thu thập Dữ liệu IoT ([IoT Data Collection])
Luồng "Stream sensor data": Một mũi tên được nhãn "Stream sensor data" bắt đầu từ IoT Gateway và chỉ sang Cloud Services, biểu thị việc truyền dữ liệu cảm biến liên tục từ các thiết bị IoT đến dịch vụ đám mây.
Luồng "Store analytics": Một mũi tên khác được nhãn "Store analytics" bắt đầu từ Cloud Services và chỉ sang Databases, thể hiện việc lưu trữ dữ liệu phân tích đã xử lý vào cơ sở dữ liệu.
Giai đoạn này được đánh dấu bằng nhãn bổ sung [IoT Data Collection], đặt dọc theo tương tác từ IoT Gateway đến Cloud Services, nhấn mạnh tính liên tục của quy trình thu thập dữ liệu.
3.2. Giai đoạn Tương tác Người dùng ([User Interaction])
Giai đoạn này bắt đầu từ hành động của người dùng và bao gồm các bước sau:

Luồng "Truy cập ứng dụng": Mũi tên được nhãn "Truy cập ứng dụng" (bằng tiếng Việt, nghĩa là "Access Application") bắt đầu từ User và chỉ sang Mobile/Web, thể hiện người dùng khởi động giao diện.
Luồng "Request service": Mũi tên được nhãn "Request service" bắt đầu từ Mobile/Web, đi qua IoT Gateway, và chỉ sang Cloud Services, thể hiện yêu cầu dịch vụ được truyền qua hệ thống.
Luồng "Query data": Mũi tên được nhãn "Query data" bắt đầu từ Cloud Services và chỉ sang Databases, thể hiện việc truy vấn dữ liệu từ cơ sở dữ liệu.
Luồng "Return results": Mũi tên được nhãn "Return results" bắt đầu từ Databases và chỉ sang Cloud Services, thể hiện việc trả về kết quả truy vấn.
Luồng "Response": Mũi tên được nhãn "Response" bắt đầu từ Cloud Services, đi qua IoT Gateway, và chỉ sang Mobile/Web, thể hiện phản hồi được gửi lại giao diện người dùng.
Luồng "Display results": Cuối cùng, mũi tên được nhãn "Display results" bắt đầu từ Mobile/Web và chỉ sang User, thể hiện kết quả cuối cùng được hiển thị cho người dùng.
Giai đoạn này được đánh dấu bằng nhãn bổ sung [User Interaction], đặt dọc theo tương tác từ Mobile/Web đến Cloud Services, nhấn mạnh quy trình tương tác do người dùng khởi xướng.
4. Thiết kế Hình ảnh và Ghi chú
Màu sắc và bố cục: Sơ đồ sử dụng nền tối với chữ trắng và xám cho các nhãn và ghi chú, đảm bảo tính dễ đọc, đặc biệt trong môi trường trình bày chuyên nghiệp.
Biểu thị luồng dữ liệu: Các mũi tên được sử dụng để chỉ hướng luồng dữ liệu, với đường thẳng cho các tương tác chính và đường gạch đứt cho các ghi chú phụ, giúp phân biệt rõ ràng.
Bố cục đối xứng: IoT Gateway được đặt ở trung tâm, đóng vai trò hub kết nối giao diện người dùng (Mobile/Web) với hậu cảnh (Cloud Services và Databases), tạo cảm giác cân đối và logic.
Chi tiết cấu trúc: Lifelines được biểu thị bằng đường gạch đứt dọc từ mỗi hộp thành phần, và các tương tác được thể hiện bằng mũi tên liền, với hướng chỉ rõ luồng dữ liệu.

```mermaid
sequenceDiagram
    participant U as User
    participant App as Mobile/Web
    participant GW as IoT Gateway
    participant Cloud as Cloud Services
    participant DB as Databases

    U->>App: Truy cập ứng dụng
    activate App
    
    par IoT Data Collection
        GW->>Cloud: Stream sensor data
        Cloud->>DB: Store analytics
    and User Interaction
        App->>Cloud: Request service
        Cloud->>DB: Query data
        DB->>Cloud: Return results
        Cloud->>App: Response
    end
    
    App->>U: Display results
    deactivate App
```

## 3. Phân bố Thiết bị

### 3.1 Sơ đồ Phân bố Vật lý

```mermaid
graph TD
    subgraph "Khu vực Siêu thị"
        A[Entrance] --> B[Main Area]
        B --> C[Checkout Area]
        
        subgraph "Entrance"
            D[BG220-EK Beacon #1]
            E[XG26-DK2608A #1]
        end
        
        subgraph "Main Area"
            F[BG220-EK Beacon #2]
            G[EFR32MG21 #1]
            H[XG24-EK2703A]
        end
        
        subgraph "Checkout"
            I[BG220-EK Beacon #3]
            J[XG26-DK2608A #2]
            K[EFR32MG21 #2]
            L[Raspberry Pi 4]
        end
    end
```

### 3.2 Vùng Phủ Sóng

```mermaid
graph TD
    subgraph "Coverage Map"
        A((BG220-EK #1)) --- B((BG220-EK #2))
        B --- C((BG220-EK #3))
        
        D{EFR32MG21 #1} -.-> A
        D -.-> B
        E{EFR32MG21 #2} -.-> B
        E -.-> C
        
        F[XG26-DK2608A #1] -.-> D
        G[XG24-EK2703A] -.-> D & E
        H[XG26-DK2608A #2] -.-> E
        
        I[(Raspberry Pi 4)] === E
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style B fill:#f9f,stroke:#333,stroke-width:2px
    style C fill:#f9f,stroke:#333,stroke-width:2px
    style D fill:#bbf,stroke:#333,stroke-width:2px
    style E fill:#bbf,stroke:#333,stroke-width:2px
    style F fill:#bfb,stroke:#333,stroke-width:2px
    style G fill:#fbf,stroke:#333,stroke-width:2px
    style H fill:#bfb,stroke:#333,stroke-width:2px
    style I fill:#ff9,stroke:#333,stroke-width:2px
```

## 4. Tích hợp Module

### 4.1 Communication Flow

```mermaid
sequenceDiagram
    participant IoT as IoT Devices
    participant Edge as Edge Computing
    participant Service as Services
    participant UI as User Interface

    IoT->>Edge: Raw Data
    Edge->>Edge: Pre-processing
    Edge->>Service: Processed Data
    
    par Real-time Updates
        Service-->>UI: WebSocket Updates
    and Database Storage
        Service->>Service: Data Storage
    end
    
    UI->>Service: User Requests
    Service->>UI: Responses
```

### 4.2 Error Handling

```mermaid
stateDiagram-v2
    [*] --> Normal
    Normal --> Error: Device Failure
    Normal --> Warning: Performance Issue
    
    Error --> Recovery: Auto-retry
    Recovery --> Normal: Success
    Recovery --> Fallback: Failure
    
    Warning --> Normal: Self-heal
    Warning --> Error: Deteriorate
    
    Fallback --> Normal: Device Restored
```

## 5. Security Architecture

```mermaid
graph TD
    subgraph "Security Layers"
        A[Device Security]
        B[Network Security]
        C[Application Security]
        D[Data Security]
    end
    
    A -->|Secure Boot| B
    B -->|TLS/SSL| C
    C -->|JWT/OAuth| D
    
    subgraph "Device Security"
        A1[Secure Elements]
        A2[Encrypted Storage]
        A3[Secure Updates]
    end
    
    subgraph "Network Security"
        B1[Encrypted Comms]
        B2[Firewall]
        B3[IDS/IPS]
    end
    
    subgraph "Application Security"
        C1[Authentication]
        C2[Authorization]
        C3[Input Validation]
    end
    
    subgraph "Data Security"
        D1[Encryption at Rest]
        D2[Access Control]
        D3[Audit Logging]
    end
```

## 6. Monitoring & Maintenance

### 6.1 System Health Monitoring

```mermaid
graph TD
    A[System Metrics] --> B{Health Check}
    B -->|Healthy| C[Normal Operation]
    B -->|Warning| D[Alert Generation]
    B -->|Critical| E[Emergency Response]
    
    D --> F[Auto-scaling]
    D --> G[Load Balancing]
    
    E --> H[Failover]
    E --> I[System Recovery]
```

### 6.2 Maintenance Workflow

```mermaid
graph LR
    A[Monitor] --> B[Detect]
    B --> C[Analyze]
    C --> D[Plan]
    D --> E[Execute]
    E --> A
```

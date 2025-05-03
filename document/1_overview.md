# Tổng quan Hệ thống IoT-AI Retail Assistant

## 1. Kiến trúc Tổng thể
Diagram này mô tả một kiến trúc hệ thống IoT với ba tầng chính: Tầng ứng dụng, Tầng dịch vụ, và Tầng IoT. Dưới đây là phân tích kỹ thuật chi tiết từng tầng và cách chúng tương tác.

### 1.1. Tầng ứng dụng (User Interface Layer)

Tầng này là giao diện người dùng cuối, nơi người dùng tương tác với hệ thống. Nó bao gồm:

**Mobile App:**
- Ứng dụng di động, có thể được phát triển trên iOS hoặc Android.
- Chức năng: Hiển thị dữ liệu IoT (như thông tin môi trường, vị trí), gửi yêu cầu (ví dụ: hỏi chatbot), và nhận thông báo.
- Kết nối: Giao tiếp với tầng dịch vụ qua API (REST hoặc WebSocket).

**Web App:**
- Ứng dụng web, chạy trên trình duyệt.
- Chức năng: Tương tự Mobile App nhưng tối ưu cho màn hình lớn hơn, phù hợp với người dùng trên máy tính.
- Kết nối: Cũng sử dụng API để giao tiếp với tầng dịch vụ.

**Admin Dashboard:**
- Chức năng: Quản lý hệ thống (xem dữ liệu IoT, cấu hình thiết bị, phân tích hiệu suất), giám sát trạng thái thiết bị IoT, và truy cập báo cáo phân tích.
- Kết nối: Truy cập tầng dịch vụ để lấy dữ liệu và gửi lệnh quản trị.
- Luồng dữ liệu: Tầng ứng dụng gửi yêu cầu đến tầng dịch vụ (ví dụ: truy vấn chatbot, yêu cầu phân tích dữ liệu) và nhận kết quả trả về để hiển thị.

### 1.2. Service Layer
Đây là tầng trung gian, xử lý logic nghiệp vụ và kết nối các tầng khác. Nó bao gồm các dịch vụ:

**RAG Chatbot Service:**
- Dịch vụ chatbot sử dụng mô hình Retrieval-Augmented Generation (RAG).
- Chức năng: Trả lời câu hỏi người dùng bằng cách truy xuất thông tin từ Vector DB (dữ liệu dạng vector, thường dùng cho tìm kiếm ngữ nghĩa) và kết hợp với mô hình ngôn ngữ để sinh câu trả lời tự nhiên.
- Ví dụ: Người dùng hỏi "Món hàng này còn không", chatbot lấy dữ liệu từ Vector DB và trả lời dựa trên thông tin trong kho.

**Analytics Service:**
- Chức năng: Xử lý dữ liệu từ Analytics DB và dữ liệu thời gian thực từ tầng IoT để tạo báo cáo, biểu đồ, hoặc dự đoán.
- Ví dụ: Phân tích xu hướng mua hàng trong khoảng thời gian 2 tháng gần nhất để biết mặt hàng nào bán chạy.

**Navigation Service:**
- Dịch vụ điều hướng, có thể hỗ trợ định vị (indoor navigation).
 Chức năng: Sử dụng dữ liệu từ BLE Beacons (ở tầng IoT) để xác định vị trí người dùng và cung cấp hướng dẫn di chuyển.
- Ví dụ: Hỗ trợ người dùng tìm đường trong một tòa nhà lớn dựa trên tín hiệu BLE.

**Kết nối với tầng dữ liệu:**
- Các dịch vụ này truy xuất dữ liệu từ Product DB (thông tin sản phẩm), Analytics DB (dữ liệu phân tích), và Vector DB (dữ liệu vector cho AI).
- Chúng cũng gửi dữ liệu đã xử lý (như kết quả phân tích) trở lại các cơ sở dữ liệu này.

**Kết nối với tầng IoT:**
- Tầng dịch vụ nhận dữ liệu thời gian thực từ tầng IoT qua Gateway và gửi lệnh điều khiển (nếu cần) đến các thiết bị IoT.

### 1.3. Tầng dữ liệu (Data Layer)
Tầng này lưu trữ dữ liệu cần thiết cho hệ thống, bao gồm:

**Product DB:**
- Cơ sở dữ liệu quan hệ (SQL), lưu thông tin sản phẩm.
- Ví dụ: Danh sách thiết bị IoT, thông số kỹ thuật, hoặc thông tin cấu hình.

**Analytics DB:**
- Cơ sở dữ liệu phân tích, có thể là SQL hoặc NoSQL (như MongoDB).
- Lưu trữ dữ liệu lịch sử từ tầng IoT (như nhiệt độ, chuyển động) và kết quả phân tích từ Analytics Service.

**Vector DataBase:**
- Cơ sở dữ liệu vector (như Pinecone, Weaviate), lưu trữ dữ liệu dạng vector.
- Dùng cho các tác vụ AI như tìm kiếm ngữ nghĩa hoặc hỗ trợ chatbot (RAG Chatbot Service).
- Ví dụ: Lưu trữ embedding của dữ liệu IoT để chatbot truy vấn nhanh.

**Quản lý dữ liệu:**
- Dữ liệu từ tầng IoT được gửi lên qua Gateway, sau đó được xử lý bởi tầng dịch vụ và lưu vào các cơ sở dữ liệu này.
- Tầng dịch vụ truy xuất dữ liệu từ đây để phục vụ tầng ứng dụng.

### 1.4. Tầng IoT (IoT Layer)
Tầng này bao gồm các thiết bị IoT, giao thức kết nối, và thiết bị tính toán tại chỗ. Cụ thể:

**BLE Beacons (BGG220-EK):**
- Thiết bị phát tín hiệu Bluetooth Low Energy (BLE), mã sản phẩm BGG220-EK.
- Chức năng: Phát tín hiệu để định vị trong không gian nhỏ (indoor positioning).
- Ứng dụng: Hỗ trợ Navigation Service xác định vị trí người dùng.

**Mesh Network (EFR32MG21):**
- Mạng lưới (mesh network) sử dụng chip EFR32MG21 của Silicon Labs.
- Chức năng: Kết nối nhiều thiết bị IoT trong một mạng lưới, đảm bảo độ tin cậy và mở rộng phạm vi kết nối.
- Ví dụ: Các cảm biến môi trường và chuyển động kết nối với nhau qua mesh network, gửi dữ liệu đến Gateway.

**Computing (Raspberry Pi):**
- Raspberry Pi là thiết bị tính toán tại chỗ (edge computing).
- Chức năng: Xử lý dữ liệu cục bộ từ các cảm biến để giảm tải cho hệ thống trung tâm, gửi dữ liệu đã xử lý lên Gateway.

**Gateway:**
- Cổng kết nối giữa tầng IoT và tầng dịch vụ.
- Chức năng: Thu thập dữ liệu từ các thiết bị IoT (qua BLE hoặc mesh network) và gửi lên tầng dịch vụ qua giao thức như MQTT hoặc HTTP.
- Cũng nhận lệnh từ tầng dịch vụ để điều khiển thiết bị IoT.

**Environmental (X026-DK2608A):**
- Chức năng: Đo các thông số như nhiệt độ, độ ẩm, ánh sáng, hoặc chất lượng không khí.
- Dữ liệu từ cảm biến này được gửi qua mesh network hoặc Raspberry Pi đến Gateway.

**Motion:**
- Chức năng: Phát hiện chuyển động trong khu vực được giám sát.
- Ứng dụng: Kích hoạt cảnh báo (qua Admin Dashboard) hoặc ghi lại dữ liệu chuyển động để phân tích.

### 1.5. Luồng dữ liệu

**Thu thập dữ liệu:**
- Các cảm biến (Environmental, Motion) và BLE Beacons thu thập dữ liệu.
- Dữ liệu được gửi qua Mesh Network (EFR32MG21) hoặc xử lý cục bộ bởi Raspberry Pi, sau đó chuyển đến Gateway.

**Xử lý và lưu trữ:**
- Gateway gửi dữ liệu lên tầng dịch vụ.
- Analytics Service xử lý dữ liệu và lưu vào Analytics DB.
- RAG Chatbot Service sử dụng Vector DB để trả lời truy vấn.
- Navigation Service dùng dữ liệu từ BLE Beacons để hỗ trợ điều hướng.

**Hiển thị và tương tác:**
- Tầng ứng dụng (Mobile App, Web App, Admin Dashboard) lấy dữ liệu từ tầng dịch vụ để hiển thị cho người dùng.
- Người dùng gửi yêu cầu (như hỏi chatbot hoặc xem báo cáo) ngược lại qua tầng ứng dụng.

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

### 2.1. Giới thiệu về Sơ đồ

Sơ đồ là một sequence diagram minh họa quy trình tương tác và luồng dữ liệu trong một hệ sinh thái IoT (Internet of Things). Nó trình bày cách các thành phần chính, bao gồm Người dùng (User), Giao diện Mobile/Web, IoT Gateway, Dịch vụ Đám mây (Cloud Services), và Cơ sở Dữ liệu (Databases), hoạt động và trao đổi dữ liệu. Sơ đồ được thiết kế với nền tối, chữ trắng và xám, đảm bảo tính dễ đọc và chuyên nghiệp, phù hợp để phân tích trong các báo cáo kỹ thuật.

### 2.2. Luồng Dữ liệu
Sơ đồ được chia thành hai giai đoạn chính, được minh họa qua các mũi tên và nhãn chi tiết. Dưới đây là phân tích từng giai đoạn:

#### 2.2.1. Giai đoạn Thu thập Dữ liệu IoT ([IoT Data Collection])
- Luồng "Stream sensor data": Một mũi tên được nhãn "Stream sensor data" bắt đầu từ IoT Gateway và chỉ sang Cloud Services, biểu thị việc truyền dữ liệu cảm biến liên tục từ các thiết bị IoT đến dịch vụ đám mây.
- Luồng "Store analytics": Một mũi tên khác được nhãn "Store analytics" bắt đầu từ Cloud Services và chỉ sang Databases, thể hiện việc lưu trữ dữ liệu phân tích đã xử lý vào cơ sở dữ liệu.
- Giai đoạn này được đánh dấu bằng nhãn bổ sung [IoT Data Collection], đặt dọc theo tương tác từ IoT Gateway đến Cloud Services, nhấn mạnh tính liên tục của quy trình thu thập dữ liệu.

#### 2.2.2. Giai đoạn Tương tác Người dùng ([User Interaction])
Giai đoạn này bắt đầu từ hành động của người dùng và bao gồm các bước sau:

- Luồng "Truy cập ứng dụng": Mũi tên được nhãn "Truy cập ứng dụng" (bằng tiếng Việt, nghĩa là "Access Application") bắt đầu từ User và chỉ sang Mobile/Web, thể hiện người dùng khởi động giao diện.
-  Luồng "Request service": Mũi tên được nhãn "Request service" bắt đầu từ Mobile/Web, đi qua IoT Gateway, và chỉ sang Cloud Services, thể hiện yêu cầu dịch vụ được truyền qua hệ thống.
- Luồng "Query data": Mũi tên được nhãn "Query data" bắt đầu từ Cloud Services và chỉ sang Databases, thể hiện việc truy vấn dữ liệu từ cơ sở dữ liệu.
- Luồng "Return results": Mũi tên được nhãn "Return results" bắt đầu từ Databases và chỉ sang Cloud Services, thể hiện việc trả về kết quả truy vấn.
- Luồng "Response": Mũi tên được nhãn "Response" bắt đầu từ Cloud Services, đi qua IoT Gateway, và chỉ sang Mobile/Web, thể hiện phản hồi được gửi lại giao diện người dùng.
- Luồng "Display results": Cuối cùng, mũi tên được nhãn "Display results" bắt đầu từ Mobile/Web và chỉ sang User, thể hiện kết quả cuối cùng được hiển thị cho người dùng.
Giai đoạn này được đánh dấu bằng nhãn bổ sung [User Interaction], đặt dọc theo tương tác từ Mobile/Web đến Cloud Services, nhấn mạnh quy trình tương tác do người dùng khởi xướng.

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

**Giới thiệu về sơ đồ:**

Sơ đồ  là một sequence diagram hoặc sơ đồ phân bố vật lý, minh họa cách các thiết bị IoT được triển khai trong một môi trường được giám sát, có thể là không gian bán lẻ, thương mại, hoặc một khu vực cần quản lý. Sơ đồ được thiết kế với cấu trúc phân cấp, thể hiện mối quan hệ giữa các khu vực chính (Entrance, Main Area, Checkout Area) và các thiết bị được bố trí trong chúng. Đây là một tài liệu quan trọng cho việc thiết kế hệ thống, lập kế hoạch triển khai, và quản lý vận hành, đảm bảo rằng các thành phần được bố trí hợp lý để tối ưu hóa chức năng.

### 3.2. Phân tích các thành phần chính

#### 3.2.1. Khu vực Entrance (Cửa vào)
**Mô tả:**
Đây là điểm khởi đầu của sơ đồ, đại diện cho cửa vào chính của không gian được giám sát. Đây là nơi đầu tiên mà người hoặc tài sản đi vào, do đó cần các thiết bị để phát hiện và ghi nhận.

**Thiết bị liên quan:**
- BG220-EK Beacon 
- XG26-DK2608A #1

**Mối quan hệ:** 
Khu vực Entrance là điểm tiếp xúc đầu tiên, nơi các thiết bị beacon và cảm biến làm việc cùng nhau để phát hiện và ghi nhận sự xuất hiện của người hoặc tài sản, tạo nền tảng cho các hoạt động giám sát tiếp theo.

#### 3.2.2. Khu vực chính
**Mô tả:**
Đây là khu vực trung tâm, kết nối trực tiếp với Entrance, đại diện cho không gian hoạt động chính trong môi trường. Đây là nơi diễn ra các hoạt động chính, như di chuyển khách hàng, trưng bày sản phẩm, hoặc quản lý tài sản.

**Thiết bị liên quan:**
- BG220-EK Beacon
- EFR32MG21
- XG24-EK2703A
  
#### 3.2.3. Checkout Area (Khu vực thanh toán)
**Mô tả:** Đây là một khu vực phụ thuộc của Main Area, được thiết kế đặc biệt cho quy trình thanh toán hoặc thoát khỏi không gian. Đây là khu vực quan trọng, nơi các giao dịch được thực hiện, đòi hỏi sự giám sát và xử lý dữ liệu chính xác.

**Thiết bị liên quan:**
- BG220-EK Beacon : Một thiết bị beacon thứ ba, được đặt tại khu vực thanh toán để theo dõi hoạt động cụ thể như di chuyển khách hàng, hỗ trợ thanh toán không tiếp xúc, hoặc xác định vị trí tại quầy thanh toán.
- XG26-DK2608A : Một thiết bị cảm biến hoặc mô-đun giao tiếp khác, hỗ trợ các hoạt động thanh toán, có thể ghi nhận dữ liệu môi trường hoặc truyền thông tin giao dịch.
- EFR32MG21 : Hai đơn vị của bộ vi xử lý này, gợi ý rằng khu vực này cần nhiều khả năng xử lý hơn hoặc có cấu hình dự phòng để đảm bảo độ tin cậy. Thiết bị này có thể xử lý giao tiếp không dây hoặc xử lý dữ liệu giao dịch.
- Raspberry Pi 4: Một máy tính bảng đơn, có thể được sử dụng cho xử lý dữ liệu địa phương, điều khiển, hoặc tích hợp với các hệ thống bên ngoài như hệ thống điểm bán hàng (POS), nền tảng IoT, hoặc đám mây. Raspberry Pi 4 thường được sử dụng trong các dự án IoT nhờ khả năng tính toán mạnh mẽ và hỗ trợ nhiều giao thức.

**Mối quan hệ:** Checkout Area là một phần nhỏ của Main Area, nơi các giao dịch được thực hiện. Sự hiện diện của nhiều thiết bị (beacon, cảm biến, bộ vi xử lý và Raspberry Pi) cho thấy một hệ thống phức tạp được thiết kế cho giám sát thời gian thực, thu thập dữ liệu, và tự động hóa quy trình thanh toán.

### 3.3. Cấu trúc phân cấp và luồng dữ liệu
Sơ đồ thể hiện một luồng dữ liệu phân cấp, với các mối quan hệ rõ ràng:
- Entrance là điểm khởi đầu, kết nối với Main Area, đại diện cho luồng tự nhiên của người hoặc tài sản từ cửa vào đến khu vực chính.
- Main Area chia nhánh thành Checkout Area, cho thấy khu vực thanh toán là một chức năng chuyên biệt trong không gian chính.
- Các mũi tên trong sơ đồ chỉ ra hướng luồng dữ liệu hoặc sự phụ thuộc, với Entrance dẫn đến Main Area, và Main Area dẫn đến Checkout Area. Điều này phản ánh quy trình logic của việc di chuyển hoặc xử lý dữ liệu trong môi trường, từ phát hiện ban đầu đến xử lý giao dịch cuối cùng.

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

### 3.4 Vùng Phủ Sóng

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
Sơ đồ được cung cấp là một biểu đồ luồng dữ liệu (flowchart) minh họa quy trình tương tác và luồng dữ liệu trong một hệ sinh thái IoT (Internet of Things), nhấn mạnh vào việc sử dụng Edge Computing để xử lý dữ liệu gần nguồn và hỗ trợ cập nhật thời gian thực.

Sơ đồ mô tả sự phối hợp giữa bốn thành phần chính:
- IoT Devices
- Edge Computing
- Services
- User Interface

**Phân tích thành phần và vai trò**

**1. IoT Devices:**

- Mô tả:
Là nguồn tạo ra Raw Data, bao gồm cảm biến, thiết bị kết nối và các nguồn dữ liệu khác.

- Vị trí:
Nằm bên trái sơ đồ, xuất hiện cả trên và dưới, biểu thị tính liên tục của quá trình thu thập dữ liệu.

- Vai trò:
Gửi Raw Data đến Edge Computing để xử lý sơ bộ.

**2. Edge Computing:**

- Mô tả:
Là lớp trung gian xử lý, thực hiện Pre-processing dữ liệu để giảm độ trễ, tối ưu tài nguyên mạng và hỗ trợ xử lý thời gian thực.

- Vị trí:
Nằm ngay bên phải của IoT Devices, cả trên và dưới sơ đồ.

- Vai trò:
Nhận Raw Data, thực hiện Pre-processing → tạo Processed Data → chuyển đến Services.

**3. Services:**

- Mô tả:
Là trung tâm xử lý dữ liệu, bao gồm hai chức năng chính:
   - Real-Time Update
   - Database Storage

- Vị trí:
Bên phải Edge Computing, cả trên và dưới.

- Vai trò:

   - Real-time Updates: Tạo ra Real-time Updates và WebSockt Updates gửi đến User Interface.
   - Database Storage: Lưu Processed Data để phục vụ User Requests sau này.

**4. User Interface**
- Mô tả:
Giao diện mà người dùng trực tiếp tương tác để theo dõi và truy xuất dữ liệu.

- Vị trí:
Ở bên phải cuối cùng của sơ đồ.

- Vai trò:
   - Nhận Real-time Updates và WebSocket Updates để hiển thị dữ liệu thời gian thực.
   - Gửi User Requests đến Services và nhận lại Responses từ dữ liệu lưu trữ.
   - Luồng dữ liệu và tương tác
IoT Devices → Edge Computing:
Sinh ra Raw Data → gửi đến Edge Computing.

Edge Computing:

Thực hiện Pre-processing → tạo ra Processed Data.

Edge Computing → Services:

Processed Data được:

Gửi đến [Real-time Updates] → tạo WebSocket Updates đến User Interface.

Gửi đến [Database Storage] để lưu trữ.

Services ↔ User Interface:

User Interface nhận dữ liệu thời gian thực từ Services.

Người dùng gửi User Requests → hệ thống trả về Responses từ Database Storage.

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

**1. Giới thiệu về sơ đồ**
Sơ đồ "4.2 Error Handling" là một state diagram minh họa quá trình xử lý lỗi trong một hệ thống kỹ thuật như hệ thống IoT, hệ thống tự động hóa, hoặc hệ thống CNTT.

Sơ đồ thể hiện quá trình chuyển đổi giữa các trạng thái sau:

Normal

Warning

Error

Recovery

Fallback

**2. Phân tích các trạng thái**

**Normal**

Mô tả: Trạng thái khởi đầu khi hệ thống hoạt động bình thường, không có lỗi được phát hiện.

Vị trí: Nằm ở trên cùng của sơ đồ, với một vòng tròn nhỏ phía trên biểu thị điểm bắt đầu.

Vai trò: Là trạng thái ổn định và mục tiêu duy trì của hệ thống.

**Warning**

Mô tả: Xuất hiện khi hệ thống phát hiện vấn đề tiềm ẩn.

Nhãn con:
  - Performance Issue: hiệu suất giảm như độ trễ cao, phản hồi chậm.
  - Deteriorate: thiết bị có dấu hiệu hoạt động không ổn định, ví dụ tín hiệu yếu.

Vai trò: Cảnh báo sớm để thực hiện phòng ngừa trước khi chuyển thành lỗi nghiêm trọng.

**Error**

Mô tả: Hệ thống đã gặp lỗi nghiêm trọng làm ảnh hưởng đến hoạt động bình thường.

Nhãn: Device Failure

Vai trò: Kích hoạt quy trình phục hồi tự động (Auto-retry), yêu cầu xử lý lỗi.

**Recovery**

Mô tả: Hệ thống thực hiện các biện pháp tự động để khắc phục lỗi.

Nhãn: Auto-retry

Vai trò: Cố gắng khôi phục hệ thống về trạng thái Normal mà không cần can thiệp thủ công.

**Fallback**

Mô tả: Trạng thái cuối khi quá trình Recovery thất bại.

Nhãn: Failure

Vai trò: Chuyển sang chế độ dự phòng, duy trì hoạt động cơ bản, tránh dừng toàn bộ hệ thống.

**3. Luồng chuyển đổi trạng thái**
- Normal → Warning:
Khi phát hiện Performance Issue hoặc Deteriorate. Hệ thống có khả năng giám sát và cảnh báo sớm.

- Warning → Normal:
Hệ thống có thể tự phục hồi (Self-heal), điều chỉnh cấu hình hoặc kết nối để quay lại hoạt động bình thường.

- Warning → Error:
Nếu không khắc phục được, cảnh báo chuyển thành lỗi nghiêm trọng (Device Failure).

- Error → Recovery:
Hệ thống tự động khởi động lại, kiểm tra lại thiết bị hoặc chạy quy trình sửa lỗi (Auto-retry).

- Recovery → Normal:
Nếu Auto-retry thành công, hệ thống quay lại trạng thái hoạt động ổn định (Device Restored).

- Recovery → Fallback:
Nếu Auto-retry thất bại, hệ thống chuyển sang chế độ dự phòng (Fallback) để duy trì tối thiểu hoạt động.

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

### 1. Tổng thể sơ đồ
Sơ đồ được chia thành 2 phần:

- Phần 1: mô tả các lĩnh vực bảo mật chính (Data, Application, Network, Device).

- Phần 2: thể hiện Security Layers (các tầng bảo mật), cho thấy mối quan hệ tuần tự từ phần cứng đến dữ liệu.

**Các khối bảo mật chính**

**a. Data Security**

- Encryption at Rest: Mã hóa dữ liệu khi lưu trữ, đảm bảo dữ liệu không bị truy cập trái phép nếu thiết bị bị đánh cắp.
- Access Control: Quản lý quyền truy cập, đảm bảo chỉ người/phần mềm được phép mới truy cập tài nguyên.
- Audit Logging: Ghi lại các hành vi truy cập hệ thống nhằm kiểm tra và phát hiện bất thường.

**b. Application Security**

- Authentication: Xác thực người dùng (đăng nhập, xác minh).
- Authorization: Phân quyền – xác định người dùng được làm gì sau khi đăng nhập.
- Input Validation: Kiểm tra dữ liệu đầu vào nhằm tránh tấn công như SQL injection, XSS.

**c. Network Security**

- Encrypted Comms: Mã hóa các giao tiếp mạng (ví dụ: TLS/SSL).
- Firewall: Tường lửa – kiểm soát lưu lượng ra/vào hệ thống.
- IDS/IPS: Hệ thống phát hiện và phòng ngừa xâm nhập (Intrusion Detection/Prevention Systems).

**d. Device Security**
- Secure Elements: Phần cứng chuyên biệt lưu trữ khóa/bảo mật (ví dụ: TPM, HSM).
- Encrypted Storage: Mã hóa dữ liệu lưu trên thiết bị.
- Secure Updates: Cập nhật phần mềm bảo mật, xác minh nguồn gốc cập nhật.

### 2. Security Layers (Tầng bảo mật - cột dọc bên phải)
Đây là cấu trúc phân tầng bảo mật, thể hiện sự phụ thuộc lẫn nhau:

- Device Security:
Cung cấp nền tảng phần cứng an toàn.

- Secure Boot:
Đảm bảo hệ thống khởi động chỉ với mã đã được xác thực.

- Network Security:
Bảo vệ dữ liệu truyền tải.

- TLS/SSL:
Mã hóa lớp truyền tải, tăng tính bảo mật mạng.

- Application Security:
Kiểm soát truy cập và dữ liệu ứng dụng.

- JWT/OAuth:
Các giao thức xác thực và phân quyền hiện đại.

- Data Security:
Bảo vệ dữ liệu cuối cùng – nơi hệ thống xử lý và lưu trữ.



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

#### 6.1.1. Mục đích
Sơ đồ mô tả quy trình giám sát và phản hồi tình trạng hệ thống trong thời gian thực, thường được áp dụng trong các hệ thống đám mây, hệ thống phân tán, hoặc nền tảng dịch vụ có yêu cầu cao về tính sẵn sàng.
Quy trình này giúp hệ thống tự động phân loại mức độ ổn định và đưa ra các phản ứng phù hợp nhằm đảm bảo tính liên tục của dịch vụ và ngăn ngừa gián đoạn.

#### 6.2.2. Các thành phần chính của sơ đồ
*6.2.2.1. System Metrics – Các chỉ số hệ thống*
Là dữ liệu đo lường định kỳ từ hệ thống.

Bao gồm:
- Sử dụng CPU, bộ nhớ (RAM)
- Dung lượng đĩa, tốc độ đọc/ghi
- Tốc độ phản hồi API hoặc giao tiếp mạng
- Tỷ lệ lỗi (error rate), số lượng request, độ trễ (latency)

Mục đích: Cung cấp thông tin để đánh giá tình trạng hiện tại.

*6.2.2.2. Health Check – Kiểm tra tình trạng hệ thống*
Là bước đánh giá tập trung, dựa trên các system metrics.

So sánh với các ngưỡng định sẵn (thresholds) để phân loại trạng thái.

Kết quả phân loại thành 3 trạng thái:
- Healthy: Hệ thống hoạt động tốt, không có dấu hiệu bất thường.
- Warning: Một số chỉ số vượt ngưỡng cảnh báo, nhưng chưa ảnh hưởng nghiêm trọng đến toàn bộ hệ thống.
- Critical: Một hoặc nhiều chỉ số vượt ngưỡng nghiêm trọng, có khả năng gây gián đoạn hệ thống.

#### 6.2.3. Phản ứng tương ứng với từng trạng thái
*6.2.3.1. Trạng thái Healthy*
- Hành động: Duy trì hoạt động bình thường (Normal Operation).
- Không cần thay đổi cấu hình hoặc can thiệp.
- Hệ thống tiếp tục chạy như hiện tại, không phát sinh log cảnh báo.

*6.2.3.2. Trạng thái Warning*
- Hành động đầu tiên: Sinh cảnh báo (Alert Generation).
- Gửi thông báo qua email, tin nhắn, dashboard giám sát hoặc hệ thống cảnh báo (Alertmanager, Prometheus, v.v.).
- Các hành động tiếp theo để giảm tải:
  - Auto-scaling (Tự động mở rộng): Tăng số lượng tài nguyên (ví dụ: container, VM) để xử lý tải cao hơn. Thường áp dụng trong môi trường cloud hoặc containerized (như Kubernetes).
  -Load Balancing (Cân bằng tải): Phân phối lại lưu lượng truy cập giữa các node hoặc instance để tránh quá tải cục bộ.

      Cải thiện hiệu suất và tránh tạo điểm nghẽn (bottleneck).

*6.3.3.3. Trạng thái Critical*
Hành động đầu tiên: Kích hoạt cơ chế ứng phó khẩn cấp (Emergency Response).

Các hành động sau để duy trì dịch vụ:

- Failover:

Tự động chuyển hoạt động sang node/instance khác đã được cấu hình sẵn.

Áp dụng với các hệ thống có thiết lập dự phòng (redundancy).

- System Recovery (Phục hồi hệ thống):

Có thể bao gồm khởi động lại dịch vụ, rollback phiên bản, hoặc khởi tạo lại môi trường.

Mục tiêu là đưa hệ thống trở lại trạng thái hoạt động ổn định.



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

Đây là một Maintenance Workflow Diagram (sơ đồ quy trình bảo trì), thể hiện các bước tuần tự để phát hiện, phân tích, lên kế hoạch và thực hiện hoạt động bảo trì, sau đó quay lại giám sát để tiếp tục vòng lặp.

**1. Monitor (Giám sát)**

Mục tiêu: Thu thập dữ liệu và giám sát tình trạng hệ thống/máy móc/thiết bị theo thời gian thực.

Hoạt động:

Dùng cảm biến, hệ thống SCADA, hoặc phần mềm giám sát.

Theo dõi các thông số như nhiệt độ, độ rung, áp suất, lỗi hệ thống, thời gian hoạt động, v.v.

Kết quả: Dữ liệu thô hoặc cảnh báo được ghi nhận để phát hiện bất thường.

**2. Detect (Phát hiện)**

Mục tiêu: Xác định dấu hiệu hỏng hóc hoặc tình trạng bất thường từ dữ liệu thu thập.

Hoạt động:

So sánh dữ liệu với ngưỡng an toàn.

Sử dụng thuật toán phát hiện bất thường (AI/ML hoặc rule-based).

Kích hoạt cảnh báo nếu có dấu hiệu hỏng hóc.

Kết quả: Một vấn đề cụ thể được xác định để phân tích tiếp theo.

**3. Analyze (Phân tích)**

Mục tiêu: Hiểu nguyên nhân gốc rễ và mức độ nghiêm trọng của vấn đề.

Hoạt động:

Phân tích dữ liệu lịch sử.

Áp dụng kỹ thuật như RCA (Root Cause Analysis), FMEA (Failure Mode and Effects Analysis).

Ước lượng tác động, chi phí và thời gian cần để xử lý.

Kết quả: Một đánh giá đầy đủ về vấn đề và đề xuất hướng xử lý.

**4. Plan (Lập kế hoạch)**

Mục tiêu: Xây dựng kế hoạch bảo trì cụ thể dựa trên phân tích.

Hoạt động:

Quyết định loại bảo trì (dự phòng, khắc phục, thay thế...).

Phân bổ nguồn lực: nhân sự, thiết bị, linh kiện.

Lập lịch trình bảo trì.

Kết quả: Kế hoạch hành động chi tiết để xử lý vấn đề.

**5. Execute (Thực hiện)**

Mục tiêu: Triển khai các hành động đã được lên kế hoạch.

Hoạt động:
- Thực hiện sửa chữa, thay thế hoặc điều chỉnh hệ thống.
- Cập nhật trạng thái thực hiện vào hệ thống quản lý.

Kết quả: Vấn đề được xử lý; hệ thống hoạt động trở lại bình thường.

Vòng lặp (Feedback Loop)
- Sau khi Execute, hệ thống quay lại bước Monitor.
- Đảm bảo kết quả thực hiện đúng kỳ vọng.
- Bắt đầu chu kỳ giám sát mới để phát hiện lỗi tiếp theo.
- Vòng lặp này đảm bảo bảo trì liên tục và cải tiến không ngừng.

Ý nghĩa tổng thể
Sơ đồ này đại diện cho quy trình bảo trì dựa trên dữ liệu hoặc bảo trì tiên đoán (Predictive Maintenance). Nó hỗ trợ tổ chức:
- Giảm thiểu thời gian chết (downtime).
- Tối ưu hóa chi phí vận hành.
- Nâng cao hiệu suất thiết bị và tuổi thọ máy móc.

```mermaid
graph LR
    A[Monitor] --> B[Detect]
    B --> C[Analyze]
    C --> D[Plan]
    D --> E[Execute]
    E --> A
```

# Tổng quan Hệ thống IoT-AI Retail Assistant

## 1. Kiến trúc Tổng thể

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

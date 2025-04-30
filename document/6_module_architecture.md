# Mô tả Chi tiết Kiến trúc Module Hệ thống IoT-AI Retail Assistant

## 1. Tổng quan Kiến trúc

```mermaid
flowchart TB
    subgraph "Sensor Layer" 
        IoTCam["IoT Cameras\n(Raspberry Pi Camera)"]
        MotionSens["Motion Sensors\n(XG24-EK2703A)"]
        EnvSens["Environmental Sensors\n(XG26-DK2608A)"]
    end
    
    subgraph "Edge AI Processing"
        CV["Computer Vision\n(TensorFlow/MobileNet SSD)"]
        SP["Stream Processing\n(Apache Kafka)"]
        EP["Edge Processing\n(Raspberry Pi 4)"]
    end
    
    subgraph "Analytics Engine"
        ZC["Zone Classification"]
        QD["Queue Detection"]
        CD["Crowd Density Analysis"]
        PA["Predictive Analytics"]
    end
    
    subgraph "Dual Routing"
        SHC["Salemans/HR Coordination"]
        CR["Counter Recommendation"]
        RA["Route Advisor"]
    end
    
    subgraph "Output Layer"
        DB["Dashboard\n(Real-time metrics)"]
        AS["Alert System\n(Staff coordination)"]
        CB["Chatbot Integration\n(Customer interaction)"]
        MA["Mobile App\n(Navigation)"]
    end
    
    IoTCam --> |Video Stream| CV
    MotionSens --> |Movement Data| SP
    EnvSens --> |Environmental Data| SP
    
    CV --> |Processed Frames| EP
    SP --> |Structured Data| EP
    
    EP --> |Crowd Data| ZC
    EP --> |Queue Metrics| QD
    EP --> |Density Heatmap| CD
    
    ZC & QD & CD --> |Analytics| PA
    
    PA --> |Staff Alerts| SHC
    PA --> |Customer Guidance| CR
    PA --> |Navigation Data| RA
    
    SHC --> |Notifications| AS
    CR --> |Recommendations| CB
    RA --> |Navigation| MA
    
    ZC & QD & CD --> |Metrics| DB
    
    classDef sensorLayer fill:#f9d5e5,stroke:#333,stroke-width:1px
    classDef edgeLayer fill:#eeeeee,stroke:#333,stroke-width:1px
    classDef analyticsLayer fill:#d5e8f9,stroke:#333,stroke-width:1px
    classDef routingLayer fill:#e3f9d5,stroke:#333,stroke-width:1px
    classDef outputLayer fill:#f9e8d5,stroke:#333,stroke-width:1px
    
    class IoTCam,MotionSens,EnvSens sensorLayer
    class CV,SP,EP edgeLayer
    class ZC,QD,CD,PA analyticsLayer
    class SHC,CR,RA routingLayer
    class DB,AS,CB,MA outputLayer
```

## 2. Data Flow từ Sensor đến Analytics

```mermaid
sequenceDiagram
    participant Camera as IoT Cameras
    participant Motion as Motion Sensors
    participant CV as Computer Vision
    participant Edge as Edge Processing
    participant Analytics as Analytics Engine
    participant Routing as Dual Routing
    participant Output as Output Layer
    
    par Video Processing
        Camera->>CV: Video Stream (30fps)
        CV->>CV: Object Detection
        CV->>CV: Person Counting
        CV->>Edge: People Count & Positions
    and Sensor Data
        Motion->>Edge: Movement Detection
        Note over Motion,Edge: Real-time movement data
    end
    
    Edge->>Edge: Data Fusion
    Edge->>Edge: Preliminary Analysis
    
    Edge->>Analytics: Processed Data
    
    Analytics->>Analytics: Zone Classification
    Note over Analytics: Categorize store zones by density
    
    Analytics->>Analytics: Queue Detection
    Note over Analytics: Identify queues at counters
    
    Analytics->>Analytics: Predictive Analytics
    Note over Analytics: Estimate wait times and trends
    
    Analytics->>Routing: Analytics Results
    
    par Staff Coordination
        Routing->>Output: Staff Alerts
        Note over Routing,Output: Direct staff to busy areas
    and Customer Guidance
        Routing->>Output: Counter Recommendations
        Note over Routing,Output: Guide customers to optimal counters
    end
```

## 3. Computer Vision Processing Pipeline

```mermaid
flowchart LR
    subgraph "CV Pipeline"
        direction TB
        A[Raw Frame] --> B{Preprocessing}
        B --> C[Object Detection]
        C --> D[Person Tracking]
        D --> E[Zone Mapping]
        E --> F[Density Calculation]
        F --> G[Queue Analysis]
    end
    
    subgraph "Models"
        direction TB
        M1[MobileNet SSD]
        M2[DeepSORT Tracker]
        M3[Zone Classifier]
        M4[Queue Detector]
    end
    
    C -.-> M1
    D -.-> M2
    E -.-> M3
    G -.-> M4
    
    subgraph "Outputs"
        O1[Person Count]
        O2[Zone Heatmap]
        O3[Queue Metrics]
        O4[Movement Patterns]
    end
    
    F --> O1 & O2
    G --> O3
    D --> O4
    
    classDef pipeline fill:#e1f5fe,stroke:#333,stroke-width:1px
    classDef models fill:#fff9c4,stroke:#333,stroke-width:1px
    classDef outputs fill:#e8f5e9,stroke:#333,stroke-width:1px
    
    class A,B,C,D,E,F,G pipeline
    class M1,M2,M3,M4 models
    class O1,O2,O3,O4 outputs
```

## 4. Dual Routing Decision System

```mermaid
stateDiagram-v2
    [*] --> AnalyzeData
    
    state "Analyze Data" as AnalyzeData {
        [*] --> ProcessMetrics
        ProcessMetrics --> EvaluateZones
        EvaluateZones --> QueueAssessment
        QueueAssessment --> [*]
    }
    
    AnalyzeData --> DecisionPoint
    
    state "Decision Point" as DecisionPoint {
        [*] --> EvaluateSituation
        EvaluateSituation --> NeedsStaff : Crowded zone
        EvaluateSituation --> NeedsGuidance : Long queues
        NeedsStaff --> [*]
        NeedsGuidance --> [*]
    }
    
    state "Staff Coordination" as StaffCoord {
        [*] --> PrioritizeZones
        PrioritizeZones --> AssignStaff
        AssignStaff --> NotifyStaff
        NotifyStaff --> [*]
    }
    
    state "Customer Guidance" as CustGuide {
        [*] --> IdentifyBestCounter
        IdentifyBestCounter --> CalculateRoute
        CalculateRoute --> DeliverRecommendation
        DeliverRecommendation --> [*]
    }
    
    DecisionPoint --> StaffCoord : Staff needed
    DecisionPoint --> CustGuide : Customer guidance needed
    
    StaffCoord --> [*]
    CustGuide --> [*]
```

## 5. Tương tác với Chatbot (RAG)

```mermaid
sequenceDiagram
    actor Customer as Customer
    participant Chatbot as RAG Chatbot
    participant AnalyticsAPI as Analytics API
    participant QueueSystem as Queue System
    participant NavSystem as Navigation System
    
    Customer->>Chatbot: "Tôi muốn thanh toán"
    Chatbot->>AnalyticsAPI: Kiểm tra tình trạng quầy
    AnalyticsAPI->>QueueSystem: Lấy dữ liệu hàng đợi
    QueueSystem->>AnalyticsAPI: Trả về số liệu quầy
    AnalyticsAPI->>Chatbot: Dữ liệu quầy thu ngân
    
    Chatbot->>Customer: "Quầy 3 đang ít người nhất (2 phút chờ)"
    Customer->>Chatbot: "Dẫn tôi đến quầy đó"
    
    Chatbot->>NavSystem: Yêu cầu lộ trình
    NavSystem->>Chatbot: Lộ trình tối ưu
    Chatbot->>Customer: "Đang dẫn đường tới Quầy 3..."
    
    Note over Customer,NavSystem: Chuyển sang Map Interface
```

## 6. Alert System for Staff

```mermaid
flowchart TD
    A[Analytics Engine] --> B{Alert Condition?}
    B -->|Yes| C[Generate Alert]
    B -->|No| D[Continue Monitoring]
    
    C --> E{Alert Type}
    E -->|Queue Threshold| F[Queue Alert]
    E -->|Zone Crowding| G[Zone Alert]
    E -->|System Issue| H[System Alert]
    
    F --> I[Notify Cashiers]
    G --> J[Notify Floor Staff]
    H --> K[Notify IT Team]
    
    I & J & K --> L[Track Resolution]
    L --> M{Resolved?}
    M -->|Yes| N[Close Alert]
    M -->|No| O[Escalate]
    
    O --> P[Notify Management]
    P --> L
    
    N --> D
    
    classDef analytics fill:#f9f,stroke:#333,stroke-width:1px
    classDef decision fill:#bbf,stroke:#333,stroke-width:1px
    classDef alert fill:#fbb,stroke:#333,stroke-width:1px
    classDef notify fill:#bfb,stroke:#333,stroke-width:1px
    classDef resolution fill:#ffb,stroke:#333,stroke-width:1px
    
    class A analytics
    class B,E,M decision
    class C,F,G,H alert
    class I,J,K,P notify
    class L,N,O resolution
```

## 7. Dashboard Integration

```mermaid
flowchart TD
    subgraph "Data Sources"
        A1[Camera Data]
        A2[Sensor Data]
        A3[Queue Metrics]
        A4[Staff Positions]
    end
    
    subgraph "Real-time Processing"
        B1[Stream Processing]
        B2[Aggregation]
        B3[Analytics]
    end
    
    subgraph "Dashboard Components"
        C1[Store Overview]
        C2[Heatmap View]
        C3[Queue Monitor]
        C4[Staff Monitor]
        C5[Alert Panel]
    end
    
    A1 & A2 & A3 & A4 --> B1
    B1 --> B2
    B2 --> B3
    
    B3 --> C1 & C2 & C3 & C4 & C5
    
    C1 --> D[Management View]
    C2 & C3 --> E[Operations View]
    C4 & C5 --> F[Staff View]
    
    classDef sources fill:#dcedc8,stroke:#333,stroke-width:1px
    classDef processing fill:#b3e5fc,stroke:#333,stroke-width:1px
    classDef dashboard fill:#ffccbc,stroke:#333,stroke-width:1px
    classDef views fill:#d1c4e9,stroke:#333,stroke-width:1px
    
    class A1,A2,A3,A4 sources
    class B1,B2,B3 processing
    class C1,C2,C3,C4,C5 dashboard
    class D,E,F views
```

## 8. Integration với Hardware

```mermaid
flowchart TB
    subgraph "Hardware Layer"
        H1["BG220-EK\n(BLE Beacons)"]
        H2["XG26-DK2608A\n(Environmental)"]
        H3["XG24-EK2703A\n(Motion)"]
        H4["EFR32MG21\n(Mesh Network)"]
        H5["Raspberry Pi 4\n(Edge Computing)"]
        H6["Pi Camera Modules"]
    end
    
    subgraph "Software Layer" 
        S1["Firmware"]
        S2["Edge Software"]
        S3["Computer Vision"]
        S4["Analytics Engine"]
    end
    
    subgraph "Communication Layer"
        C1["BLE"]
        C2["Mesh Network"]
        C3["WiFi"]
        C4["MQTT"]
    end
    
    H1 -->|Beacon Data| C1
    H2 & H3 -->|Sensor Data| C2
    H4 -->|Network Management| C2
    H5 -->|Data Processing| C3
    H6 -->|Video Stream| H5
    
    C1 & C2 -->|Data Transport| C4
    C3 -->|Server Connection| C4
    
    C4 -->|Messaging| S2
    S2 -->|Data Processing| S3
    S3 -->|Analysis| S4
    S1 -->|Controls| H1 & H2 & H3 & H4
    
    classDef hardware fill:#ffcdd2,stroke:#333,stroke-width:1px
    classDef software fill:#c8e6c9,stroke:#333,stroke-width:1px
    classDef communication fill:#bbdefb,stroke:#333,stroke-width:1px
    
    class H1,H2,H3,H4,H5,H6 hardware
    class S1,S2,S3,S4 software
    class C1,C2,C3,C4 communication

```

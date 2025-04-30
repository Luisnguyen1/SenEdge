# Tài liệu Dự án IoT-AI Retail Assistant

Dự án IoT-AI Retail Assistant kết hợp 3 module chính để cung cấp giải pháp toàn diện cho hệ thống bán lẻ thông minh.

## Cấu trúc Tài liệu

1. [Tổng quan Hệ thống](document/1_overview.md)
2. [RAG Chatbot](document/2_chatbot.md)
3. [Indoor Navigation](document/3_navigation.md)
4. [IoT Analytics](document/4_analytics.md)
5. [Kế hoạch Thực hiện](document/5_implementation_plan.md)
6. [Kiến trúc Module](document/6_module_architecture.md)
7. [Crowd Density Detection](document/7_crowd_detection.md)

## Kiến trúc Tổng thể

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Web UI/Mobile App]
        B[Indoor Navigation UI]
        C[Chatbot Interface]
    end
    
    subgraph "Backend Services"
        D[RAG Chatbot Service]
        E[Navigation Service]
        F[IoT Analytics Service]
        G[Product Management]
    end
    
    subgraph "IoT Layer"
        H[BLE Beacons]
        I[IoT Cameras]
        J[Environmental Sensors]
    end
    
    subgraph "Data Layer"
        K[(Product Database)]
        L[(Analytics Database)]
        M[(Vector Database)]
    end
    
    A --> D
    A --> E
    A --> F
    H --> E
    I --> F
    J --> F
    D --> K
    D --> M
    F --> L
```

## Hệ thống Phân tích Mật độ Đám đông

```mermaid
flowchart TB
    subgraph "Input"
        A1["Camera Feed\n(Raspberry Pi Camera)"]
    end
    
    subgraph "Processing Pipeline"
        B1["Frame Extractor\n(5fps)"]
        B2["Image Preprocessing\n(Resize 96x96, Normalize 0-1)"]
        B3["TFLite Person Detection Model\n(MobileNet SSD)"]
        B4["Confidence Score Output\n(Per Grid Cell)"]
        B5["Crowd Density Classification\n(LOW/MEDIUM/HIGH)"]
    end
    
    subgraph "Output & Actions"
        C1["Zone Status Dashboard"]
        C2["Salemans/HR Coordination"]
        C3["Alert System"]
    end
    
    A1 --> B1
    B1 --> B2
    B2 --> B3
    B3 --> B4
    B4 --> B5
    
    B5 --> C1
    B5 --> C2
    B5 --> C3
    
    classDef input fill:#f9d5e5,stroke:#333,stroke-width:1px
    classDef processing fill:#d5e8f9,stroke:#333,stroke-width:1px
    classDef output fill:#e3f9d5,stroke:#333,stroke-width:1px
    
    class A1 input
    class B1,B2,B3,B4,B5 processing
    class C1,C2,C3 output
```

## Tương tác Người dùng

```mermaid
sequenceDiagram
    actor Customer as Customer
    participant Chatbot as RAG Chatbot
    participant Navigation as Navigation System
    participant Analytics as IoT Analytics
    
    Customer->>Chatbot: Product Inquiry
    Chatbot->>Customer: Product Recommendations
    Customer->>Chatbot: "I want to buy this"
    Chatbot->>Navigation: Request Route
    Navigation->>Analytics: Check Queue Status
    Analytics->>Navigation: Queue Information
    Navigation->>Customer: Optimal Route
```

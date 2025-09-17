# Feature: Crowd Density Detection

## 1. Problem Definition: 

In large-scale retail environments such as shopping malls and supermarkets, uncontrolled crowd density in specific areas can lead to inefficient operations, reduced customer experience, and increased risk of security incidents. Traditional manual monitoring is limited by human latency and coverage distance, making it inadequate for real-time response.

The Crowd Density Detection module uses edge-deployed computer vision models as an optimization solution to address this problem. The system can automatically identify areas with high human presence, enabling timely coordination of salesmen by providing actionable alerts, enhancing service responsiveness, and controlling situations.


## 2. System Overview
### 2.1. Position in the AIoT Architecture
The crowd detection for sales and security coordination is a core sub-module within the AI Layer of the overall AIoT system. It interfaces directly with the Vision Sensing Layer (camera inputs), the Real-time Analytics Layer (for zone-based decision logic), and the Alert & Integration Layer (to coordinate actions with staff or mall systems). It operates alongside other modules such as warehouse monitoring and cashier guidance, but focuses specifically on spatial human density analysis to trigger real-time operational responses.

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
### 2.2. Processing Pipeline

**1. Input:**

Live video feeds from overhead or wide-angle surveillance cameras are streamed to an edge device positioned in key shopping zones (e.g., aisles, entrances, promotional booths).

**2. AI inference:**

Each video frame is passed through a TensorFlow Lite Person Detection Model running on the edge device. This lightweight CNN-based model detects the presence of humans per frame and outputs bounding boxes with confidence scores.

**3. Decisions Logic:**

A zone-mapping module associates each detection with predefined zones. A time-based aggregation function estimates human density trends using a rolling window. When a zone exceeds a preconfigured crowd threshold (e.g., more than 10 detected persons over 15 seconds), the system flags the area as congested.

**4. Alert/Action:**

Upon crowd detection, the decision engine triggers:

- Security Coordination Alert to mall security systems via API.
- Sales Staff: Dispatch Request to the human resource scheduling system. The alerts are sent through the MQTT or HTTPS protocol and visualized on a central dashboard with zone highlights.

This real-time edge processing reduces latency and network load, ensuring rapid response and seamless integration into operational workflows.

## 3. Why use TensorFlow

The system leverages the **TensorFlow Lite Person Detection** model, a pre-trained lightweight convolutional neural network (CNN) designed for binary classification (person vs. background). It is deployed on edge devices (e.g., Raspberry Pi 4) to perform on-device inference from live camera streams. The model processes input frames in real-time and outputs bounding boxes around detected human figures, along with confidence scores.

### 3.1. Model Selection Rationale
The TensorFlow Lite Person Detection model was selected due to its strong balance between computational efficiency and functional adequacy for density estimation:

- Lightweight Architecture: The model uses a streamlined CNN architecture specifically optimized for mobile and embedded environments, enabling deployment without GPU acceleration.
- Low Latency: Benchmark tests show inference times of less than 30 ms per frame on Raspberry Pi 4, supporting real-time processing even at 15–30 FPS input.
- Purpose-Fit Classification: Since the feature requires only binary person detection rather than multi-class object recognition, the simplicity of the model aligns well with the system's functional goals (zone-based crowd estimation).

### 3.2. Alternative Model Comparison

| Model                | Accuracy   | Latency on Edge | Complexity | Suitability |
|----------------------|------------|------------------|------------|-------------|
| TFLite Person Detection | Moderate   | <30ms            | Low        | High        |
| YOLOv5 (Nano)        | High       | ~80–120ms        | Medium     | Medium      |
| MobileNet SSD        | High       | ~60–90ms         | Medium     | Medium      |
| YOLOv8 (Small)       | Very High  | ~100–150ms       | High       | Low         |

While YOLO and SSD variants offer improved precision and multi-class detection, they introduce significantly higher inference latency, and their capabilities are not strictly necessary for this binary classification task. Thus, TensorFlow Lite Person Detection presents the best trade-off for the deployment context — real-time, edge-constrained, and crowd-specific.

## 4. 4. Inference Pipeline and Density Classification Logic
### 4.1. Preprocessing Steps

Incoming video streams from surveillance cameras are sampled at a configurable frame rate (typically 1–3 FPS) to balance real-time responsiveness and computational load. Each frame is resized to the model’s expected input dimensions (e.g., 96x96 for TensorFlow Lite's person detection model), optionally converted to grayscale, and pixel values are normalized to the 0,1 range. These steps ensure compatibility and optimal performance for inference on edge devices.

```python 
def preprocess_frame(frame, input_size=(96, 96)):
    # Resize frame to match model input
    resized = cv2.resize(frame, input_size)
    
    # Convert to grayscale if model expects 1 channel
    grayscale = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    
    # Normalize pixel values to [0, 1]
    normalized = grayscale.astype(np.float32) / 255.0
    
    # Add batch and channel dimensions
    input_tensor = np.expand_dims(normalized, axis=(0, -1))
    
    return input_tensor
```

### 4.2. Person Detection Inference
Each preprocessed frame is passed through the TensorFlow Lite person detection model, a quantized, lightweight CNN designed for real-time performance on edge devices such as the Raspberry Pi 4. The model returns a list of bounding boxes and corresponding confidence scores indicating the likelihood of a person being present in each region of the frame.

To ensure detection reliability, a confidence threshold (typically ≥ 0.5) is applied to filter out false positives or uncertain predictions. Only bounding boxes exceeding this threshold are considered valid detections.

```python
def run_inference(interpreter, input_tensor, threshold=0.5):
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    interpreter.set_tensor(input_details[0]['index'], input_tensor)
    interpreter.invoke()

    boxes = None
    classes = None
    scores = None

    for output in output_details:
        if 'detection_boxes' in output['name']:
            boxes = interpreter.get_tensor(output['index'])[0]
        elif 'detection_classes' in output['name']:
            classes = interpreter.get_tensor(output['index'])[0]
        elif 'detection_scores' in output['name']:
            scores = interpreter.get_tensor(output['index'])[0]

    if boxes is None or classes is None or scores is None:
        print("Error: The required output tensors were not found!")
        return []

    results = []
    for i in range(len(scores)):
        if scores[i] >= threshold and int(classes[i]) == 1:  
            results.append(boxes[i])

    return results
```
### 4.3. Spatial Mapping and Density Scoring
Detected bounding boxes are projected onto a predefined zone grid that spatially segments the monitored environment (e.g., 3x3 or 5x5 grid). Each bounding box is assigned to the corresponding zone based on its centroid position. The system then calculates the number of persons detected per zone over a defined time window (e.g., 10 seconds) and classifies crowd density levels based on tunable thresholds:

- Low: 0–2 persons
- Medium: 3–5 persons
- High: ≥6 persons

This zonal scoring mechanism provides localized crowding estimates that support both visualization and decision-making logic.

**Grid-based Zone Analysis**
```mermaid
flowchart TB
    subgraph "Store Floor Plan"
        A["Entrance Zone"] 
        B["Main Shopping Area"]
        C["Checkout Zone"]
    end
    
    subgraph "Grid Overlay"
        D["3x3 Grid System"]
        
        D1["Grid 1"] 
        D2["Grid 2"]
        D3["Grid 3"]
        D4["Grid 4"] 
        D5["Grid 5"]
        D6["Grid 6"]
        D7["Grid 7"] 
        D8["Grid 8"]
        D9["Grid 9"]
    end
    
    subgraph "Zone Assignment"
        E["Entrance = Grids 1,2,4"]
        F["Shopping = Grids 3,5,6,7"]
        G["Checkout = Grids 8,9"]
    end
    
    D --> D1 & D2 & D3 & D4 & D5 & D6 & D7 & D8 & D9
    
    D1 & D2 & D4 --> E
    D3 & D5 & D6 & D7 --> F
    D8 & D9 --> G
    
    E --> A
    F --> B
    G --> C
    
    classDef floor fill:#bbdefb,stroke:#333,stroke-width:1px
    classDef grid fill:#dcedc8,stroke:#333,stroke-width:1px
    classDef zone fill:#f3e5f5,stroke:#333,stroke-width:1px
    classDef cell fill:#e8f5e9,stroke:#333,stroke-width:1px
    
    class A,B,C floor
    class D grid
    class E,F,G zone
    class D1,D2,D3,D4,D5,D6,D7,D8,D9 cell
```
### 4.4. Rule-Based Trigger System
To initiate operational responses, a rule engine continuously monitors zonal density scores and applies temporal logic conditions. For example:

**Rule Format:**
If ≥6 persons are detected in Zone A1 for more than 10 consecutive seconds, → Trigger staff dispatch alert.

Rules are configurable per zone and time range, enabling granular control over alert frequency and action thresholds. This logic ensures that transient detections do not cause false alarms, while persistent crowding conditions reliably generate actionable alerts.

## 5. Alert and Visualization System
### 5.1. Alert Channels
To ensure effective response coordination and incident awareness, the system supports multiple alert delivery channels tailored to operational roles:

**Push Notifications to HR System:**
Alerts are directly transmitted via secured internal APIs to the human resources department’s task coordination platform. These notifications can initiate workflows such as dispatching floor staff to high-density zones.

### 5.2. Alert Triggers and Conditions
The alert system is governed by a set of rule-based triggers that analyze model outputs in real-time. These rules are configurable to align with operational and safety policies.

- Basic Density Rule: 
Alerts are triggered when the number of persons detected in a specific grid zone exceeds a predefined threshold within a time window.
```python
if (zone A detections >= 10) in last 15 seconds → TRIGGER alert_level: high
```

- Custom Rule Sets: Administrators may configure alert sensitivity based on contextual factors:

   - Time of Day: Higher thresholds during peak hours.
   - Day of Week: Weekend configurations for higher traffic.
   - Specific Zone Configurations: Different trigger rules for the entrance, food court, and electronics area.

```python
if zone B detections >= 15 between 5PM–8PM → alert_level: normal
```

**Staff Coordination System**

```mermaid
stateDiagram-v2
    [*] --> MonitoringState
    
    state MonitoringState {
        [*] --> NormalState
        NormalState --> MediumState : Medium Density
        MediumState --> HighState : High Density
        HighState --> MediumState : Density Decreases
        MediumState --> NormalState : Density Decreases
    }
    
    MonitoringState --> AlertState : Threshold Exceeded
    
    state AlertState {
        [*] --> EvaluateZone
        EvaluateZone --> AssignPriority
        AssignPriority --> NotifyStaff
    }
    
    AlertState --> ResponseState : Staff Notified
    
    state ResponseState {
        [*] --> StaffEnRoute
        StaffEnRoute --> OnSite
        OnSite --> ResolutionCheck
        ResolutionCheck --> Resolved : Problem Fixed
        ResolutionCheck --> Escalation : Not Resolved
        Escalation --> [*]
        Resolved --> [*]
    }
    
    ResponseState --> MonitoringState : Situation Resolved
```
### 5.3. API Format for Alert Dispatch
The system exposes a RESTful API endpoint for real-time alert dispatch to ensure interoperability and centralized staff coordination. This allows backend systems like the HR platform or operational management tools to receive structured alert data and take predefined actions.
   
**Payload Format:**
```json
{
  "zone_id": "A1",
  "density": "High",
  "timestamp": "2025-04-29T14:33:21Z",
  "action": "dispatch_staff"
}
```
**Description:**

- zone_id: Spatial reference indicating the location within the monitored area.
- density: Classified crowding level based on real-time inference (e.g., Low, Medium, High).
- timestamp: ISO 8601 UTC timestamp for traceability.
- action: Recommended system response (e.g., notify staff, restrict access, log-only).

This API allows seamless integration with third-party systems for logging, visualization, or automatic personnel routing.

### 5.4. Visualization Dashboard
The visualization dashboard serves as the centralized interface for monitoring real-time crowd conditions, reviewing historical alerts, and supporting rapid situational awareness by security or HR personnel.

**Key Components:**

- Heatmap Visualization:
Displays dynamic color-coded overlays on the floor plan or video feed, representing crowd density in predefined zones. Color gradations (e.g., green/yellow/red) correspond to Low, Medium, and High density levels, respectively.

```mermaid
flowchart TB
    A["Zone Density Data"] --> B["Heatmap Generator"]
    
    subgraph "Heatmap Visualization"
        B --> C["Color Coding"]
        C --> D["Overlay on Store Map"]
        D --> E["Real-time Updates"]
    end
    
    subgraph "Dashboard Display"
        E --> F["Management View"]
        E --> G["Operations View"]
        E --> H["Mobile Staff View"]
    end
    
    classDef data fill:#bbdefb,stroke:#333,stroke-width:1px
    classDef vis fill:#dcedc8,stroke:#333,stroke-width:1px
    classDef dash fill:#f3e5f5,stroke:#333,stroke-width:1px
    
    class A data
    class B,C,D,E vis
    class F,G,H dash
```

- Real-time Video Overlay:
Live camera feeds are enhanced with detection bounding boxes, providing transparency into the AI inference process and enabling human validation if required.

- Alert Log History:
Chronological record of triggered alerts with metadata including zone_id, density, timestamp, and action taken. Supports filtering by time, zone, or severity level.

## 6. Deployment Architecture and System Integration
### 6.1. Hardware & Edge AI Stack
The system is deployed in a modular Edge-AI pipeline optimized for real-time inference:

- Cameras capture live video streams positioned strategically across high-traffic zones.
- Video is streamed to edge compute units such as Raspberry Pi 4 or NVIDIA Jetson Nano/Xavier NX, which run the TensorFlow Lite person detection model locally.
- Detection results (bounding boxes, zone density status) are transmitted over LAN or Wi-Fi to a central server or cloud backend for aggregation, storage, visualization, and alert coordination.

This architecture minimizes network load and ensures privacy-preserving local inference.

### 6.2. Integration with HR System
The alert and dispatch loop integrates directly with enterprise human resources and floor staff systems:

- RESTful APIs are used to send alert events (location, timestamp, severity) to the HR task coordination system.
- Staff accounts are managed via role-based access control (RBAC).
- Each alert event includes acknowledgment tracking, ensuring that tasks are confirmed and closed in the backend system.

This creates a responsive and auditable loop for handling real-time crowding incidents.

### 6.3. Scalability & Reliability
- The system supports multiple camera streams, each assigned to a dedicated or shared edge processor depending on compute availability.
- Alert thresholds, zone definitions, and sensitivity levels are managed through a central configuration service, allowing dynamic reconfiguration without downtime.
- Modular services (inference, alerting, visualization) communicate via lightweight APIs or message queues, ensuring fault-tolerant scaling and easy maintainability.

```mermaid
graph TD
  subgraph Cameras
    CAM1[Camera 1]
    CAM2[Camera 2]
    CAMn[Camera N]
  end

  subgraph Edge Devices
    EDGE1[Raspberry Pi / Jetson<br>Edge AI Inference]
  end

  subgraph Backend
    CLOUD[Cloud / Local Server]
    DB[(Alert Logs DB)]
    DASHBOARD[Web Dashboard]
    HR[HR System]
  end

  CAM1 --> EDGE1
  CAM2 --> EDGE1
  CAMn --> EDGE1
  EDGE1 --> CLOUD
  CLOUD --> DB
  CLOUD --> DASHBOARD
  CLOUD --> HR
```

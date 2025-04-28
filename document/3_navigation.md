# Indoor Navigation Module Documentation

## 1. Tổng quan Module

Module Indoor Navigation cung cấp khả năng định vị và dẫn đường trong nhà dựa trên công nghệ BLE Beacon và thuật toán trilateration.

### 1.1 Kiến trúc Module

```mermaid
graph TB
    subgraph "Frontend Components"
        A[Map View]
        B[Navigation UI]
        C[Position Display]
    end
    
    subgraph "Core Services"
        D[BLE Scanner]
        E[Position Engine]
        F[Route Calculator]
        G[Map Service]
    end
    
    subgraph "Hardware Layer"
        H[BG220-EK Beacons]
        I[EFR32MG21 Mesh]
    end
    
    A --> G
    B --> F
    C --> E
    
    D --> E
    E --> F
    F --> B
    G --> A
    
    H --> D
    I --> D
```

## 2. Các Thành phần Chính

### 2.1 BLE Positioning System

```mermaid
sequenceDiagram
    participant M as Mobile Device
    participant B as BLE Beacons
    participant E as Position Engine
    participant R as Route Service
    
    loop Every 1s
        M->>B: Scan BLE Signals
        B->>M: RSSI Data
        M->>E: Send RSSI Data
        E->>E: Trilateration
        E->>M: Current Position
    end
    
    M->>R: Request Route
    R->>R: Calculate Path
    R->>M: Navigation Instructions
```

### 2.2 Trilateration Process

```mermaid
graph TD
    A[RSSI Data] --> B[Distance Calculation]
    B --> C[Position Estimation]
    C --> D[Kalman Filter]
    D --> E[Final Position]
    
    subgraph "RSSI to Distance"
        F[Path Loss Model]
        G[Signal Strength]
        H[Environmental Factors]
    end
    
    subgraph "Position Calculation"
        I[Circle Intersection]
        J[Least Squares]
        K[Error Minimization]
    end
    
    B --> F
    F --> G
    G --> H
    
    C --> I
    I --> J
    J --> K
```

### 2.3 Route Calculation

```mermaid
stateDiagram-v2
    [*] --> GetCurrentPosition
    GetCurrentPosition --> FindDestination
    FindDestination --> PathPlanning
    PathPlanning --> ObstacleCheck
    ObstacleCheck --> RouteOptimization
    RouteOptimization --> [*]
    
    ObstacleCheck --> PathPlanning: Obstacle Found
```

## 3. Implementation Details

### 3.1 Position Engine

```python
class PositionEngine:
    def __init__(self):
        self.kalman_filter = KalmanFilter()
        self.beacons = self.load_beacon_positions()
    
    def calculate_position(self, rssi_data):
        # Convert RSSI to distances
        distances = [
            rssi_to_distance(rssi) 
            for rssi in rssi_data
        ]
        
        # Trilateration calculation
        position = self.trilaterate(distances)
        
        # Apply Kalman filter for smoothing
        filtered_position = self.kalman_filter.update(position)
        
        return filtered_position
```

### 3.2 Route Calculator

```python
class RouteCalculator:
    def calculate_route(self, start, end, obstacles):
        # A* pathfinding implementation
        open_set = {start}
        came_from = {}
        
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, end)}
        
        while open_set:
            current = min(open_set, key=lambda x: f_score[x])
            
            if current == end:
                return self.reconstruct_path(came_from, current)
            
            # Process neighbors
            for neighbor in self.get_neighbors(current):
                if self.is_valid_move(current, neighbor, obstacles):
                    tentative_g_score = g_score[current] + 1
                    
                    if tentative_g_score < g_score.get(neighbor, float('inf')):
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = g_score[neighbor] + self.heuristic(neighbor, end)
                        open_set.add(neighbor)
        
        return None
```

### 3.3 Map Rendering

```mermaid
graph TB
    subgraph "Map Layers"
        A[Base Layer]
        B[POI Layer]
        C[Route Layer]
        D[Position Layer]
    end
    
    subgraph "Update Cycle"
        E[Position Update]
        F[Route Update]
        G[UI Update]
    end
    
    A --> B
    B --> C
    C --> D
    
    E --> G
    F --> G
```

## 4. Hardware Configuration

### 4.1 BLE Beacon Setup

```mermaid
graph TD
    subgraph "Beacon Configuration"
        A[BG220-EK Setup]
        B[EFR32MG21 Mesh]
        
        A1[Advertising Interval]
        A2[Transmission Power]
        A3[Battery Monitor]
        
        B1[Mesh Network]
        B2[Data Relay]
        B3[Power Management]
    end
    
    A --> A1
    A --> A2
    A --> A3
    
    B --> B1
    B --> B2
    B --> B3
```

### 4.2 Coverage Optimization

```mermaid
graph TD
    subgraph "Store Layout"
        A[Entrance Zone]
        B[Main Shopping Area]
        C[Checkout Zone]
    end
    
    subgraph "Beacon Placement"
        D[Beacon 1]
        E[Beacon 2]
        F[Beacon 3]
    end
    
    A --> D
    B --> E
    C --> F
    
    D --> |Coverage| B
    E --> |Coverage| C
    F --> |Coverage| B
```

## 5. Error Handling

### 5.1 Signal Loss Recovery

```mermaid
stateDiagram-v2
    [*] --> Normal
    Normal --> SignalWeak: RSSI < Threshold
    SignalWeak --> SignalLost: No Signal
    SignalLost --> Recovery: Signal Found
    Recovery --> Normal: Position Confirmed
    
    SignalWeak --> Normal: Signal Improved
    SignalLost --> LastKnown: Timeout
    LastKnown --> Recovery: Signal Found
```

### 5.2 Position Accuracy

```mermaid
graph LR
    A[Raw Position] --> B{Accuracy Check}
    B -->|Good| C[Use Direct]
    B -->|Fair| D[Apply Filter]
    B -->|Poor| E[Use Last Known]
    
    D --> F[Kalman Filter]
    E --> G[Dead Reckoning]
    
    F --> H[Final Position]
    C --> H
    G --> H
```

## 6. Performance Monitoring

### 6.1 Metrics

```mermaid
graph TD
    A[System Metrics] --> B{Category}
    B -->|Accuracy| C[Position Error]
    B -->|Performance| D[Update Rate]
    B -->|Hardware| E[Battery Level]
    
    C --> F[Dashboard]
    D --> F
    E --> F
```

### 6.2 Alert System

```yaml
# Alert Configuration
alerts:
  position_accuracy:
    threshold: 2.0  # meters
    window: 60s
    
  signal_strength:
    min_rssi: -85
    max_missing: 3
    
  battery_level:
    warning: 20%
    critical: 10%
```

## 7. API Documentation

### 7.1 Position Service API

```yaml
# Position API
GET /api/position
Response:
{
    "x": number,
    "y": number,
    "accuracy": number,
    "timestamp": string
}

# Route API
POST /api/route
Request:
{
    "start": {
        "x": number,
        "y": number
    },
    "end": {
        "x": number,
        "y": number
    }
}
Response:
{
    "route": [
        {
            "x": number,
            "y": number,
            "instruction": string
        }
    ],
    "distance": number,
    "estimated_time": number
}
```

### 7.2 WebSocket Events

```yaml
# Real-time Updates
position_update:
    type: "position"
    data: {
        "x": number,
        "y": number,
        "accuracy": number
    }

route_update:
    type: "route"
    data: {
        "current_segment": number,
        "next_instruction": string,
        "distance_remaining": number
    }
```

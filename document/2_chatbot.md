# RAG Chatbot Module Documentation

## 1. Tổng quan Module

RAG (Retrieval Augmented Generation) Chatbot là module tư vấn thông minh, kết hợp giữa tìm kiếm thông tin và sinh text để tạo ra câu trả lời chính xác và phù hợp với context.

### 1.1 Kiến trúc Module

```mermaid
graph TB
    subgraph "Frontend Layer"
        A[Chat Interface]
        B[Product Display]
        C[Analytics View]
    end
    
    subgraph "Backend Layer"
        D[RAG Engine]
        E[Vector Search]
        F[Response Generator]
        G[Analytics Engine]
    end
    
    subgraph "Data Layer"
        H[(Product DB)]
        I[(Vector DB)]
        J[(Analytics DB)]
    end
    
    A --> D
    B --> E
    C --> G
    
    D --> E
    D --> F
    E --> I
    E --> H
    F --> D
    G --> J
```

## 2. Chi tiết Thành phần

### 2.1 RAG Engine Flow

```mermaid
sequenceDiagram
    participant U as User
    participant R as RAG Engine
    participant V as Vector Search
    participant L as LLM
    participant D as Database
    
    U->>R: Query
    R->>R: Preprocess Query
    R->>V: Search Similar Content
    V->>D: Get Vectors
    D->>V: Return Matches
    V->>R: Context
    R->>L: Generate Response
    L->>R: Generated Text
    R->>U: Final Response
```

### 2.2 Vector Search Process

```mermaid
graph LR
    A[Query] --> B[Embedding]
    B --> C{Vector Search}
    C --> D[Top-K Results]
    D --> E[Re-ranking]
    E --> F[Context Selection]
    
    subgraph "Vector DB"
        G[(Product Vectors)]
        H[(Description Vectors)]
    end
    
    C --> G
    C --> H
```

### 2.3 Response Generation

```mermaid
stateDiagram-v2
    [*] --> QueryAnalysis
    QueryAnalysis --> ContextRetrieval
    ContextRetrieval --> PromptConstruction
    PromptConstruction --> ResponseGeneration
    ResponseGeneration --> PostProcessing
    PostProcessing --> [*]
    
    QueryAnalysis: Parse and understand query
    ContextRetrieval: Get relevant information
    PromptConstruction: Build LLM prompt
    ResponseGeneration: Generate response
    PostProcessing: Format and validate
```

## 3. Implementation Details

### 3.1 Embedding Model

```python
# Sử dụng SentenceTransformer cho embedding
from sentence_transformers import SentenceTransformer

class EmbeddingEngine:
    def __init__(self):
        self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        
    def encode(self, text):
        # Tạo vector embedding cho văn bản
        return self.model.encode(text)
    
    def batch_encode(self, texts):
        # Xử lý nhiều văn bản cùng lúc
        return self.model.encode(texts, batch_size=32)
```

### 3.2 RAG Process

```python
class RAGEngine:
    def process_query(self, query, k=3):
        # 1. Tạo embedding cho query
        query_vector = self.embedding_engine.encode(query)
        
        # 2. Tìm kiếm context liên quan
        similar_docs = self.vector_db.search(
            query_vector,
            k=k
        )
        
        # 3. Tạo prompt với context
        prompt = self.construct_prompt(query, similar_docs)
        
        # 4. Gọi LLM để sinh response
        response = self.llm.generate(prompt)
        
        return response
```

### 3.3 Mô hình Dữ liệu

```mermaid
erDiagram
    PRODUCT {
        string id PK
        string name
        string description
        float price
        string category
        vector embedding
    }
    
    CONVERSATION {
        string id PK
        string user_id FK
        timestamp created_at
        string context
    }
    
    MESSAGE {
        string id PK
        string conv_id FK
        string content
        string role
        timestamp timestamp
    }
    
    ANALYTICS {
        string id PK
        string query
        string response
        float relevance_score
        timestamp timestamp
    }
    
    CONVERSATION ||--o{ MESSAGE : contains
    CONVERSATION }|--|| ANALYTICS : generates
```

## 4. API Documentation

### 4.1 Endpoints

```mermaid
flowchart LR
    Gateway[API Gateway]
    Chat[/chat]
    Products[/products]
    Analytics[/analytics]
    RAG[RAG Service]
    PS[Product Service]
    AS[Analytics Service]

    Gateway --> Chat
    Gateway --> Products
    Gateway --> Analytics
    
    Chat --> RAG
    Products --> PS
    Analytics --> AS
```

### 4.2 API Schema

```yaml
# Chat Endpoint
POST /chat
Request:
{
    "query": string,
    "context": {
        "user_id": string,
        "conversation_id": string?,
        "products": string[]?
    }
}

Response:
{
    "response": string,
    "products": [
        {
            "id": string,
            "name": string,
            "description": string,
            "price": number,
            "relevance": number
        }
    ],
    "analytics": {
        "query_vector": number[],
        "response_time": number,
        "confidence": number
    }
}
```

## 5. Performance Monitoring

### 5.1 Metrics Collection

```mermaid
graph TD
    A[Metrics Collection] --> B{Metric Type}
    B -->|Performance| C[Response Time]
    B -->|Quality| D[Relevance Score]
    B -->|Usage| E[Query Volume]
    
    C --> F[Prometheus]
    D --> F
    E --> F
    
    F --> G[Grafana Dashboard]
```

### 5.2 Alerting Rules

```yaml
# Alert Configuration
rules:
  - name: high_latency
    condition: response_time > 2s
    duration: 5m
    
  - name: low_relevance
    condition: avg_relevance_score < 0.7
    duration: 15m
    
  - name: high_error_rate
    condition: error_rate > 5%
    duration: 5m
```

## 6. Tối ưu hóa

### 6.1 Caching Strategy

```mermaid
graph TD
    A[Query] --> B{Cache Hit?}
    B -->|Yes| C[Return Cached]
    B -->|No| D[Process Query]
    D --> E[Cache Result]
    E --> F[Return Result]
```

### 6.2 Vector Search Optimization

```mermaid
graph LR
    A[Query Vector] --> B{Index Type}
    B -->|HNSW| C[Approximate Search]
    B -->|Exact| D[Exhaustive Search]
    
    C --> E[Results]
    D --> E
    
    subgraph "Index Parameters"
        F[M=16]
        G[efConstruction=200]
        H[efSearch=50]
    end
```

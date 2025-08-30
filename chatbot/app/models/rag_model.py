"""
RAG Chatbot Model for MongoDB Atlas Vector Search with Gemini
"""
import os
import json
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer
import torch
import google.generativeai as genai
from datetime import datetime


FULL_MODEL_AVAILABLE = True

class RAGChatbot:
    def __init__(self):
        # Thêm conversation history
        self.conversation_history = []
        self.max_history_length = 3  # Số lượng tin nhắn tối đa được lưu
        
        # MongoDB connection
        self.mongodb_uri = os.getenv('MONGODB_URI', 'mongodb+srv://admin:vanmanh@sudo-code-nhom1.dmiub.mongodb.net/?retryWrites=true&w=majority&appName=Sudo-code-nhom1')
        try:
            self.client = MongoClient(self.mongodb_uri)
            self.db = self.client.get_database('chatbot_db')
            self.documents_collection = self.db.get_collection('documents')
            self.embeddings_collection = self.db.get_collection('embeddings')
            self.mongo_connected = True
            print("MongoDB connected successfully")
        except Exception as e:
            print(f"MongoDB connection error: {e}")
            self.mongo_connected = False
        
        # Check if full model dependencies are available
        if FULL_MODEL_AVAILABLE:
            try:
                # Load embedding model
                self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
                self.model.to(self.device)
                  # Initialize Gemini
                self.gemini_api_key = os.getenv('GEMINI_API_KEY')
                if self.gemini_api_key:
                    genai.configure(api_key=self.gemini_api_key)
                    # Sử dụng phiên bản Gemini mới
                    self.generation_model = genai.GenerativeModel('gemini-2.0-flash')
                    print("Gemini model initialized")
                else:
                    print("WARNING: GEMINI_API_KEY not found in environment variables")
                    self.generation_model = None
                
                self.model_initialized = True
                print("RAG model fully initialized")
            except Exception as e:
                print(f"Model initialization error: {e}")
                self.model_initialized = False
        else:
            self.model_initialized = False
            print("Running in basic mode without full RAG capabilities")
    
    def _embed_text(self, text):
        """Embed text using the SentenceTransformer model"""
        if not hasattr(self, 'model_initialized') or not self.model_initialized:
            return None
        
        try:
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            print(f"Embedding error: {e}")
            return None
    
    def _summarize_content(self, content, is_query=True):
        """
        Sử dụng LLM để tóm tắt nội dung trước khi lưu vào history
        """
        if not hasattr(self, 'generation_model') or self.generation_model is None:
            return content
            
        try:
            if is_query:
                prompt = f"""
Hãy tóm tắt câu hỏi sau của người dùng thành một câu ngắn gọn, súc tích nhưng vẫn giữ được ý chính và các từ khóa quan trọng. 
Chỉ trả về câu tóm tắt, không cần giải thích.

Câu hỏi cần tóm tắt: {content}

Tóm tắt:
"""
            else:
                prompt = f"""
Hãy tóm tắt câu trả lời sau thành 1-2 câu ngắn gọn, súc tích, giữ lại những thông tin quan trọng nhất.
Chỉ trả về câu tóm tắt, không cần giải thích.

Nội dung cần tóm tắt: {content}

Tóm tắt:
"""
            
            response = self.generation_model.generate_content(prompt)
            if hasattr(response, 'text'):
                return response.text.strip()
            elif hasattr(response, 'parts'):
                return response.parts[0].text.strip()
            else:
                return str(response).strip()
                
        except Exception as e:
            print(f"Error summarizing content: {e}")
            return content

    def _add_to_history(self, role, content):
        """Add a message to conversation history with summarization"""
        # Tóm tắt nội dung trước khi lưu
        is_query = (role == "user")
        summarized_content = self._summarize_content(content, is_query)
        
        self.conversation_history.append({
            "role": role,
            "content": summarized_content,
            "timestamp": datetime.now().isoformat(),
            "full_content": content  # Lưu cả nội dung gốc
        })
        
        # Giữ history trong giới hạn
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history.pop(0)

    def _get_conversation_context(self):
        """Format conversation history into a context string"""
        if not self.conversation_history:
            return ""
            
        context = "\nLịch sử hội thoại gần đây:\n"
        for msg in self.conversation_history:
            role = "Người dùng" if msg["role"] == "user" else "Trợ lý"
            context += f"{role}: {msg['content']}\n"
        return context

    def _calculate_cosine_similarity(self, vec1, vec2):
        """Calculate cosine similarity between two vectors"""
        if not vec1 or not vec2:
            return 0.0
        
        try:
            # Tính dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            
            # Tính magnitude
            magnitude1 = sum(a * a for a in vec1) ** 0.5
            magnitude2 = sum(b * b for b in vec2) ** 0.5
            
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
                
            return dot_product / (magnitude1 * magnitude2)
        except Exception as e:
            print(f"Error calculating similarity: {e}")
            return 0.0
    
    def vector_search(self, query_embedding, limit=5):
        """Search for similar documents in MongoDB using the query embedding"""
        if not hasattr(self, 'mongo_connected') or not self.mongo_connected:
            return []
        
        if query_embedding is None:
            return []
        
        try:
            # Lấy tất cả embedding từ collection
            all_embeddings = list(self.embeddings_collection.find({}, {"product_id": 1, "embedding": 1, "_id": 0}))
            
            # Tính cosine similarity trong Python thay vì MongoDB
            results = []
            for doc in all_embeddings:
                if "embedding" not in doc or not doc["embedding"]:
                    continue
                    
                doc_embedding = doc["embedding"]
                # Tính cosine similarity thủ công
                similarity = self._calculate_cosine_similarity(doc_embedding, query_embedding)
                results.append({"product_id": doc["product_id"], "similarity": similarity})
            
            # Sắp xếp kết quả theo similarity giảm dần
            results.sort(key=lambda x: x["similarity"], reverse=True)
              # Giới hạn số lượng kết quả
            return results[:limit]
        except Exception as e:
            print(f"Vector search error: {e}")
            return []
    
    def get_document_details(self, product_ids):
        """Get document details from MongoDB based on product IDs"""
        if not hasattr(self, 'mongo_connected') or not self.mongo_connected:
            return []
        
        try:
            # Lấy tất cả các trường quan trọng từ documents
            documents = list(self.documents_collection.find(
                {"product_id": {"$in": product_ids}},
                {"text": 1, "product_id": 1, "metadata": 1, "_id": 0}
            ))
            print(f"Raw documents from MongoDB: {json.dumps(documents, indent=2, ensure_ascii=False)}")
            return documents
        except Exception as e:
            print(f"Error retrieving documents: {e}")
            return []
    
    def format_context(self, documents):
        """Format the retrieved documents into a context string for Gemini"""
        if not documents:
            return "Không tìm thấy thông tin liên quan."
            
        context = ""
        
        for doc in documents:
            if not doc.get("text"):
                continue
                
            text = doc["text"]
            
            # Tìm các thông tin cơ bản
            name = ""
            price = ""
            specs = {}
            description = ""
            
            lines = text.split('\n')
            in_description = False
            
            for line in lines:
                line = line.strip()
                if line.startswith("Tên sản phẩm:"):
                    name = line.split(":", 1)[1].strip()
                elif line.startswith("price:"):
                    price = line.split(":", 1)[1].strip()
                elif "Thông số kỹ thuật:" in line:
                    # Lấy 4-5 thông số quan trọng nhất
                    important_specs = ["Công suất", "Sải cánh", "Tốc độ gió", "Bảo hành"]
                    for spec in important_specs:
                        for l in lines:
                            if spec in l and ":" in l:
                                key, value = l.split(":", 1)
                                specs[key.strip("- ")] = value.strip()
                                break
                elif "Mô tả sản phẩm:" in line or "Giới thiệu:" in line:
                    in_description = True
                elif in_description and line and not any(x in line for x in ["---", "Thông tin bổ sung:", "Thông số kỹ thuật:"]):
                    description += line + " "
            
            # Format ngắn gọn
            context += f"{name}"
            if price:
                context += f" - Giá: {price}"
            context += "\n"
            
            if specs:
                context += "Thông số: "
                context += ", ".join([f"{k}: {v}" for k, v in specs.items()])
                context += "\n"
            
            # Thêm mô tả ngắn gọn (2-3 câu đầu tiên)
            if description:
                sentences = description.split('.')
                short_desc = '.'.join(sentences[:3]) + '.'
                context += f"Mô tả: {short_desc}\n"
            
            context += "---\n"
        
        return context
    
    def generate_response(self, query, context):
        """Generate a response using Gemini based on the query and context"""
        print("Nội dung context:", context)
        if not hasattr(self, 'generation_model') or self.generation_model is None:
            return f"Gemini LLM không khả dụng. Câu hỏi: '{query}'. Đây là thông tin tìm được: {context}"
            
        try:
            # Thêm conversation history vào prompt
            conversation_context = self._get_conversation_context()
            
            # Create prompt for Gemini with context
            prompt = f"""
Bạn là một trợ lý AI chuyên nghiệp, thân thiện và hiểu biết sâu về các sản phẩm điện máy. Nhiệm vụ của bạn là trả lời câu hỏi của người dùng dựa trên thông tin sản phẩm dưới đây.

Hãy thực hiện các bước sau:
1. Phân tích rõ câu hỏi của người dùng để hiểu đúng nhu cầu (ví dụ: tính năng, công suất, độ bền, giá trị sử dụng...).
2. Tìm và chọn lọc những chi tiết liên quan trong phần thông số kỹ thuật và mô tả sản phẩm.
3. Trả lời một cách tự nhiên, dễ hiểu, chuyên nghiệp và đầy đủ, giúp người dùng dễ dàng ra quyết định mua hàng.
4. Nếu thông tin chưa đủ để trả lời chính xác, hãy lịch sự thông báo điều đó và đề xuất người dùng cung cấp thêm chi tiết cụ thể hơn.

Lưu ý:
- Ưu tiên trình bày các lợi ích nổi bật, ưu điểm thực tế của sản phẩm.
- Dùng văn phong thân thiện nhưng vẫn giữ sự chuyên nghiệp.
- Trả lời bằng tiếng Việt.

Thông tin sản phẩm phù hợp với người dùng đã tìm được trong database:
{context}

Câu hỏi của người dùng:
{query}

Trả lời:
"""

            response = self.generation_model.generate_content(prompt)
            
            # Xử lý các định dạng phản hồi khác nhau tùy thuộc vào phiên bản API
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'parts'):
                # Cho phiên bản mới hơn của thư viện
                return response.parts[0].text
            else:
                # Dự phòng cho các định dạng phản hồi khác
                return str(response)
        except Exception as e:
            print(f"Error generating response with Gemini: {e}")
            return f"Xin lỗi, đã xảy ra lỗi khi tạo câu trả lời: {e}. Đây là thông tin tìm được: {context}"
            
    def get_response(self, query):
        """
        Full RAG flow:
        1. Embedding the user query
        2. Vector search on MongoDB
        3. Retrieve documents from MongoDB
        4. Generate response with Gemini
        """
        # Basic fallback response if model or MongoDB is not available
        if not FULL_MODEL_AVAILABLE or not hasattr(self, 'model_initialized') or not self.model_initialized:
            response = f"Xin chào! Tôi hiện đang chạy ở chế độ cơ bản vì các thành phần RAG chưa được cài đặt đầy đủ. Câu hỏi của bạn là: '{query}'."
            self._add_to_history("user", query)
            self._add_to_history("assistant", response)
            return response
            
        if not hasattr(self, 'mongo_connected') or not self.mongo_connected:
            response = f"Tôi không thể kết nối với cơ sở dữ liệu MongoDB. Vui lòng kiểm tra kết nối của bạn. Câu hỏi của bạn là: '{query}'."
            self._add_to_history("user", query)
            self._add_to_history("assistant", response)
            return response
        
        try:
            # Lưu câu hỏi vào history
            self._add_to_history("user", query)
            
            # Step 1: Embed the query
            print(f"Embedding query: {query}")
            query_embedding = self._embed_text(query)
            
            # Step 2: Vector search on MongoDB Atlas
            print("Performing vector search...")
            search_results = self.vector_search(query_embedding)
            
            if not search_results:
                return f"Tôi không tìm thấy thông tin liên quan đến câu hỏi của bạn: '{query}'. Vui lòng thử với câu hỏi khác hoặc cung cấp thêm chi tiết."
            
            # Step 3: Get document details
            product_ids = [result["product_id"] for result in search_results]
            print(f"Retrieving details for products: {product_ids}")
            documents = self.get_document_details(product_ids)
            print(f"Retrieved documents: {documents}")
            # Step 4: Format context for Gemini
            context = self.format_context(documents)
            
            # Step 5: Generate response with Gemini
            print("Generating response with Gemini...")
            response = self.generate_response(query, context)
            
            # Lưu câu trả lời vào history
            self._add_to_history("assistant", response)
            
            return response
        except Exception as e:
            print(f"Error in RAG process: {e}")
            return f"Xin lỗi, đã xảy ra lỗi khi xử lý câu hỏi của bạn: {e}"
    
    def add_document(self, text, metadata=None):
        """Add a document to the MongoDB collection with embedding"""
        if not hasattr(self, 'mongo_connected') or not self.mongo_connected:
            print("Cannot add document: MongoDB not connected")
            return False
            
        if metadata is None:
            metadata = {}
        
        try:
            # Generate embedding for the document
            embedding = self._embed_text(text)
            
            # Create a unique ID for the document
            product_id = str(self.documents_collection.count_documents({}))
            
            # Create document for documents collection
            document = {
                "text": text,
                "product_id": product_id,
                "metadata": metadata
            }
            
            # Create document for embeddings collection
            embedding_doc = {
                "embedding": embedding,
                "product_id": product_id
            }
            
            # Insert documents into respective collections
            self.documents_collection.insert_one(document)
            self.embeddings_collection.insert_one(embedding_doc)
            
            print(f"Document added with ID: {product_id}")
            return True
        except Exception as e:
            print(f"Error adding document: {e}")
            return False

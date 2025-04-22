import json
import os
from pymongo import MongoClient
from sentence_transformers import SentenceTransformer

def upload_data_to_mongodb():
    """
    Đọc dữ liệu từ file JSON, tạo embedding và upload lên MongoDB
    Lưu dữ liệu sản phẩm vào collection 'documents' và embedding vào collection 'embeddings'
    """
    # Tải mô hình embedding
    print("Đang tải mô hình embedding...")
    model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
    print("Đã tải xong mô hình embedding!")
    
    # Kết nối trực tiếp tới MongoDB không qua env
    mongodb_uri = 'mongodb+srv://admin:vanmanh@sudo-code-nhom1.dmiub.mongodb.net/?retryWrites=true&w=majority&appName=Sudo-code-nhom1'
    
    try:
        # Thiết lập kết nối với các tùy chọn SSL
        client = MongoClient(
            mongodb_uri
        )
        db = client.get_database('chatbot_db')
        
        # Kiểm tra kết nối
        client.admin.command('ping')
        print("Kết nối MongoDB thành công!")
        
        # Tạo các collection nếu chưa tồn tại
        documents_collection = db.get_collection('documents')  # Collection cho dữ liệu sản phẩm
        embeddings_collection = db.get_collection('embeddings')  # Collection cho embedding
        
        # Đọc dữ liệu từ file JSON
        json_file_path = os.path.join(os.path.dirname(__file__), 'productdata.json')
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as file:
                product_data = json.load(file)
            
            print(f"Đã đọc {len(product_data)} sản phẩm từ file JSON")
            
            # Chuẩn bị dữ liệu để lưu vào MongoDB
            documents_to_insert = []
            embeddings_to_insert = []
            print(f"Bắt đầu tạo embedding cho {len(product_data)} sản phẩm...")
            
            for i, product in enumerate(product_data):
                # Kiểm tra dữ liệu và lọc các sản phẩm chỉ có URL
                if len(product) > 1:  # Nếu sản phẩm có nhiều thông tin hơn chỉ URL
                    # Tạo đoạn văn bản chỉ chứa các thông tin cơ bản theo yêu cầu
                    product_text = f"Tên sản phẩm: {product.get('name', 'Không có thông tin')}\n"
                    
                    if 'model' in product:
                        product_text += f"Model: {product.get('model', '')}\n"
                    
                    if 'brand' in product:
                        product_text += f"Thương hiệu: {product.get('brand', '')}\n"
                    
                    if 'warranty' in product:
                        product_text += f"Bảo hành: {product.get('warranty', '')}\n"
                    
                    if 'origin' in product:
                        product_text += f"Xuất xứ: {product.get('origin', '')}\n"
                    
                    # Nếu có key_features, thêm vào mô tả
                    if 'key_features' in product and isinstance(product['key_features'], list):
                        product_text += "Tính năng nổi bật:\n"
                        for feature in product['key_features']:
                            product_text += f"- {feature}\n"
                    
                    # Thêm specifications nếu có
                    if 'specifications' in product and isinstance(product['specifications'], dict):
                        product_text += "Thông số kỹ thuật:\n"
                        for key, value in product['specifications'].items():
                            product_text += f"- {key}: {value}\n"
                    
                    # Thêm description nếu có
                    if 'description' in product:
                        product_text += f"\nMô tả sản phẩm:\n{product.get('description', '')}\n"
                    
                    # Tạo embedding vector cho văn bản
                    embedding = model.encode(product_text).tolist()
                    
                    # Tạo một ID duy nhất cho document và embedding để liên kết chúng
                    product_id = str(i)
                    
                    # Tạo document để lưu vào collection documents - chỉ lưu dữ liệu sản phẩm, không lưu embedding
                    document = {
                        "text": product_text,
                        "product_id": product_id,
                        "metadata": {
                            **product,  # Lưu toàn bộ dữ liệu gốc của sản phẩm vào metadata
                            "source": "product_data",
                            "type": "product"
                        }
                    }
                    
                    # Tạo document để lưu vào collection embeddings - chỉ lưu embedding vector và product_id
                    embedding_doc = {
                        "embedding": embedding,
                        "product_id": product_id,
                    }
                    
                    documents_to_insert.append(document)
                    embeddings_to_insert.append(embedding_doc)
                    
                    # In tiến độ
                    if (i+1) % 10 == 0 or i == len(product_data) - 1:
                        print(f"Đã xử lý {i+1}/{len(product_data)} sản phẩm")
            
            if documents_to_insert and embeddings_to_insert:
                # Xóa dữ liệu cũ (nếu cần)
                documents_collection.delete_many({"metadata.source": "product_data"})
                embeddings_collection.delete_many({})
                
                # Thêm dữ liệu mới
                doc_result = documents_collection.insert_many(documents_to_insert)
                emb_result = embeddings_collection.insert_many(embeddings_to_insert)
                
                print(f"Đã thêm {len(doc_result.inserted_ids)} documents vào collection 'documents'")
                print(f"Đã thêm {len(emb_result.inserted_ids)} embedding vectors vào collection 'embeddings'")
                
            else:
                print("Không có dữ liệu hợp lệ để thêm vào MongoDB")
                
        except FileNotFoundError:
            print(f"Không tìm thấy file: {json_file_path}")
        except json.JSONDecodeError:
            print(f"File {json_file_path} không phải là JSON hợp lệ")
        
    except Exception as e:
        print(f"Lỗi: {str(e)}")
    finally:
        # Đóng kết nối
        if 'client' in locals():
            client.close()
            print("Đã đóng kết nối MongoDB")

if __name__ == "__main__":
    upload_data_to_mongodb()
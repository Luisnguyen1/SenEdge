FROM python:3.9-slim

WORKDIR /app

# Cài đặt các gói phụ thuộc cần thiết
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép mã nguồn vào container
COPY *.py .
COPY mediamart_menu.json .

# Tạo thư mục data để lưu kết quả
RUN mkdir -p data

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1

# Mở cổng cho Hugging Face Spaces (nếu cần)
EXPOSE 7860

# Chạy ứng dụng
CMD ["python", "crawlData.py"]

# 🤖 Enhanced AI Chatbot - Trợ lý thông minh SGTeam

## 📋 Tổng quan

Đây là một chatbot AI tiên tiến được xây dựng với công nghệ RAG (Retrieval-Augmented Generation), tích hợp với MongoDB Atlas Vector Search và Google Gemini AI. Giao diện người dùng được thiết kế hiện đại, tối giản và thân thiện với người dùng.

## ✨ Tính năng chính

### 🎨 **Giao diện người dùng nâng cao**

#### 1. **Thanh điều hướng (Top Navigation)**
- **Logo thương hiệu** SGTeam AI với hiệu ứng gradient
- **Thông tin phiên** hiển thị tiêu đề cuộc trò chuyện hiện tại
- **Nút điều khiển:**
  - 🌐 Chuyển đổi ngôn ngữ (Tiếng Việt/English)
  - ❓ Trung tâm hỗ trợ với hướng dẫn chi tiết
  - 🌙 Chế độ sáng/tối (Dark/Light mode)
  - 👤 Hồ sơ người dùng

#### 2. **Sidebar thông minh**
- **Nút trò chuyện mới** với hiệu ứng hover
- **Hành động nhanh:**
  - 💻 Hỗ trợ lập trình
  - 🌐 Dịch thuật
  - 📊 Phân tích dữ liệu
- **Lịch sử trò chuyện** với khả năng tìm kiếm
- **Cài đặt tùy chỉnh:**
  - Phong cách phản hồi (Thân thiện, Chuyên nghiệp, Tự nhiên, Kỹ thuật)
  - Độ dài phản hồi (Ngắn gọn, Vừa phải, Chi tiết)

#### 3. **Vùng chat chính**
- **Thanh trạng thái** hiển thị tình trạng AI
- **Màn hình chào mừng** với các gợi ý thông minh
- **Khung chat** hỗ trợ markdown và highlight code
- **Hiệu ứng typing** khi AI đang soạn thảo

#### 4. **Thanh nhập liệu nâng cao**
- **Gợi ý phản hồi nhanh** contextual
- **Đếm ký tự** (tối đa 4000 ký tự)
- **Tính năng đính kèm tệp** (PDF, Word, ảnh, text)
- **Nhập giọng nói** với Web Speech API
- **Bộ chọn emoji** tích hợp
- **Phím tắt thông minh**

### 🔧 **Tính năng kỹ thuật**

#### 1. **RAG (Retrieval-Augmented Generation)**
- Tích hợp MongoDB Atlas Vector Search
- Sử dụng SentenceTransformers để embedding
- Tìm kiếm vector similarity với cosine similarity
- Kết hợp với Google Gemini AI cho response generation

#### 2. **Xử lý tệp đa phương tiện**
- Hỗ trợ upload file: TXT, PDF, DOC, DOCX, JPG, PNG, GIF
- Giới hạn kích thước: 10MB per file
- Phân tích nội dung tự động
- Bảo mật với filename sanitization

#### 3. **Quản lý phiên làm việc**
- Auto-save lịch sử trò chuyện
- Khôi phục phiên làm việc
- Export chat history (TXT, JSON)
- Local storage persistence

#### 4. **Tùy chỉnh phản hồi**
- 4 phong cách phản hồi khác nhau
- 3 độ dài phản hồi
- Hỗ trợ đa ngôn ngữ (Vi/En)
- Context-aware quick replies

### 🎯 **Trải nghiệm người dùng (UX)**

#### 1. **Hiệu ứng và Animation**
- Smooth transitions với CSS transforms
- Loading indicators đẹp mắt
- Hover effects trên tất cả interactive elements
- Slide-in animations cho messages

#### 2. **Responsive Design**
- Desktop-first approach
- Mobile-friendly với collapsible sidebar
- Tablet optimization
- Touch-friendly controls

#### 3. **Accessibility**
- Keyboard navigation support
- Focus indicators rõ ràng
- Screen reader compatible
- High contrast support

#### 4. **Performance**
- Lazy loading components
- Efficient DOM manipulation
- Optimized CSS với CSS variables
- Minimal bundle size

### ⌨️ **Phím tắt và Lệnh nhanh**

#### Phím tắt:
- `Ctrl/Cmd + Enter`: Gửi tin nhắn
- `Ctrl/Cmd + K`: Focus vào input
- `Ctrl/Cmd + N`: Cuộc trò chuyện mới
- `Ctrl/Cmd + Shift + C`: Xóa chat
- `Escape`: Đóng modal/blur input

#### Lệnh slash:
- `/clear` - Xóa lịch sử trò chuyện
- `/new` - Bắt đầu cuộc trò chuyện mới
- `/export` - Xuất lịch sử chat
- `/help` - Hiển thị trợ giúp

### 🔔 **Hệ thống thông báo**
- Toast notifications cho các hành động
- Status indicators cho AI state
- Error handling với user-friendly messages
- Success confirmations

### 🎨 **Thiết kế UI/UX**

#### Color Scheme:
- **Primary**: Modern blue (#2563eb)
- **Secondary**: Slate gray (#64748b)
- **Accent**: Cyan (#06b6d4)
- **Background**: Clean whites và light grays
- **Dark mode**: Deep blues và grays

#### Typography:
- **Primary font**: Inter (modern, readable)
- **Secondary font**: Roboto (backup)
- **Code font**: Courier New (monospace)

#### Layout:
- **Grid-based** responsive layout
- **Flexbox** για component alignment
- **CSS Grid** cho complex layouts
- **Modular spacing** system

## 🚀 **Cài đặt và Chạy**

### Requirements:
```
flask==2.3.3
pymongo==4.6.0
python-dotenv==1.0.0
numpy<2
torch
huggingface_hub
transformers
sentence-transformers
google-generativeai==0.3.1
nltk
scikit-learn
pandas
pyarrow
```

### Environment Variables:
```bash
MONGODB_URI=your_mongodb_connection_string
GEMINI_API_KEY=your_gemini_api_key
DEBUG=True  # for development
```

### Chạy ứng dụng:
```bash
# Cài đặt dependencies
pip install -r requirements.txt

# Thiết lập environment variables
cp .env.example .env
# Chỉnh sửa .env với các thông tin cần thiết

# Chạy ứng dụng
python app.py
```

## 📁 **Cấu trúc thư mục**

```
chatbot/
├── app/
│   ├── __init__.py
│   ├── routes.py                 # Enhanced Flask routes
│   ├── models/
│   │   ├── __init__.py
│   │   └── rag_model.py         # RAG implementation
│   ├── static/
│   │   ├── css/
│   │   │   ├── enhanced-style.css    # Modern UI styles
│   │   │   └── markdown.css          # Markdown formatting
│   │   └── js/
│   │       └── enhanced-script.js    # Enhanced interactions
│   └── templates/
│       └── index.html           # Enhanced HTML template
├── app.py                       # Main Flask application
├── requirements.txt             # Python dependencies
├── Dockerfile                   # Container configuration
└── README.md                    # This file
```

## 🔧 **API Endpoints**

### Chat API:
- `POST /api/chat` - Gửi tin nhắn và nhận phản hồi
- `GET /api/health` - Kiểm tra trạng thái hệ thống
- `GET /api/suggestions` - Lấy gợi ý câu hỏi
- `POST /api/feedback` - Gửi feedback

### Session Management:
- `GET /api/sessions` - Lấy danh sách phiên
- `POST /api/sessions` - Tạo phiên mới
- `POST /api/export/{format}` - Export chat history

### Analytics:
- `GET /api/analytics` - Thống kê sử dụng

## 🎯 **Roadmap tương lai**

### v2.0 (Planned):
- [ ] User authentication và profiles
- [ ] Real-time collaboration
- [ ] Plugin system
- [ ] Advanced file analysis (PDF, Images với OCR)
- [ ] Voice responses với TTS
- [ ] Integration với external APIs
- [ ] Advanced analytics dashboard
- [ ] Multi-language models
- [ ] Custom AI training interface
- [ ] Team workspaces

### v2.1 (Future):
- [ ] Mobile app (React Native)
- [ ] Desktop app (Electron)
- [ ] API marketplace
- [ ] Advanced customization options
- [ ] Enterprise features
- [ ] Advanced security features

## 🤝 **Đóng góp**

Chúng tôi hoan nghênh mọi đóng góp! Vui lòng:

1. Fork repository
2. Tạo feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Mở Pull Request

## 📝 **License**

Distributed under the MIT License. See `LICENSE` for more information.

## 📞 **Liên hệ**

- **Team**: SGTeam
- **Email**: support@sgteam.ai
- **Website**: https://sgteam.ai

## 🙏 **Acknowledgments**

- [Google Gemini AI](https://ai.google.dev/) - LLM provider
- [MongoDB Atlas](https://www.mongodb.com/atlas) - Vector database
- [Hugging Face](https://huggingface.co/) - Embedding models
- [Flask](https://flask.palletsprojects.com/) - Web framework
- [Font Awesome](https://fontawesome.com/) - Icons
- [Highlight.js](https://highlightjs.org/) - Code highlighting

---

**Made with ❤️ by SGTeam**

document.addEventListener('DOMContentLoaded', function() {
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const clearChatButton = document.getElementById('clear-chat');
    const themeToggleButton = document.getElementById('theme-toggle');
    const voiceInputButton = document.getElementById('voice-input');
    
    // Auto-resize text area
    userInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
        if (this.scrollHeight > 200) {
            this.style.height = '200px';
        }
    });
    
    // Send message when enter key is pressed (without shift)
    userInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Send message when send button is clicked
    sendButton.addEventListener('click', sendMessage);
    
    // Clear chat history
    clearChatButton.addEventListener('click', function() {
        if (confirm('Bạn có chắc chắn muốn xóa lịch sử trò chuyện?')) {
            const firstMessage = chatMessages.firstElementChild;
            chatMessages.innerHTML = '';
            if (firstMessage) {
                chatMessages.appendChild(firstMessage);
            }
        }
    });
    
    // Toggle dark/light theme
    themeToggleButton.addEventListener('click', function() {
        document.body.classList.toggle('dark-theme');
        const icon = this.querySelector('i');
        if (document.body.classList.contains('dark-theme')) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            localStorage.setItem('theme', 'dark');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
            localStorage.setItem('theme', 'light');
        }
    });
    
    // Voice input functionality
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.lang = 'vi-VN';
        recognition.continuous = false;
        
        recognition.onresult = function(event) {
            const transcript = event.results[0][0].transcript;
            userInput.value = transcript;
            userInput.style.height = 'auto';
            userInput.style.height = (userInput.scrollHeight) + 'px';
        };
        
        voiceInputButton.addEventListener('click', function() {
            recognition.start();
            voiceInputButton.classList.add('recording');
        });
        
        recognition.onend = function() {
            voiceInputButton.classList.remove('recording');
        };
    } else {
        voiceInputButton.style.display = 'none';
    }
    
    // Check for saved theme preference
    if (localStorage.getItem('theme') === 'dark') {
        document.body.classList.add('dark-theme');
        const icon = themeToggleButton.querySelector('i');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }
    
    // Function to send message
    function sendMessage() {
        const message = userInput.value.trim();
        if (message === '') return;
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input
        userInput.value = '';
        userInput.style.height = 'auto';
        
        // Show loading indicator
        loadingIndicator.classList.add('visible');
        
        // Send message to backend
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: message
            })
        })
        .then(response => response.json())
        .then(data => {
            // Hide loading indicator
            loadingIndicator.classList.remove('visible');
            
            if (data.success) {
                // Add bot response to chat
                addMessage(data.response, 'bot');
            } else {
                // Display error
                addMessage('Xin lỗi, đã xảy ra lỗi: ' + (data.error || 'Không xác định'), 'bot');
            }
        })
        .catch(error => {
            // Hide loading indicator
            loadingIndicator.classList.remove('visible');
            
            // Display error
            console.error('Error:', error);
            addMessage('Xin lỗi, không thể kết nối với máy chủ. Vui lòng thử lại sau.', 'bot');
        });
    }
      // Function to add a message to the chat
    function addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        
        // Xử lý Markdown chỉ cho tin nhắn từ bot
        if (sender === 'bot') {
            // Cấu hình Marked.js với highlight.js
            marked.setOptions({
                highlight: function(code, lang) {
                    if (lang && hljs.getLanguage(lang)) {
                        return hljs.highlight(code, { language: lang }).value;
                    }
                    return hljs.highlightAuto(code).value;
                },
                breaks: true, // Cho phép xuống dòng với một dấu xuống dòng
                gfm: true // Sử dụng GitHub Flavored Markdown
            });
            
            // Chuyển đổi Markdown thành HTML
            messageText.innerHTML = marked.parse(text);
        } else {
            // Tin nhắn người dùng hiển thị như bình thường
            messageText.textContent = text;
        }
        
        messageContent.appendChild(messageText);
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        const now = new Date();
        messageTime.textContent = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        
        chatMessages.appendChild(messageDiv);
        
        // Kích hoạt highlight.js cho các code blocks
        if (sender === 'bot') {
            document.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        }
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});

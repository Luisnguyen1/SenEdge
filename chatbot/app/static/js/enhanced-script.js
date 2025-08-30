// Enhanced AI Chatbot JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Core Elements
    const chatMessages = document.getElementById('chat-messages');
    const userInput = document.getElementById('user-input');
    const sendButton = document.getElementById('send-button');
    const loadingIndicator = document.getElementById('loading-indicator');
    const welcomeScreen = document.getElementById('welcome-screen');
    
    // Navigation Elements
    const themeToggleButton = document.getElementById('theme-toggle');
    const languageToggle = document.getElementById('language-toggle');
    const helpCenter = document.getElementById('help-center');
    const userProfile = document.getElementById('user-profile');
      // Sidebar Elements
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const mobileBackdrop = document.getElementById('mobile-backdrop');
    const newChatBtn = document.getElementById('new-chat');
    const chatHistory = document.getElementById('chat-history');
    const responseStyle = document.getElementById('response-style');
    const responseLength = document.getElementById('response-length');
    
    // Input Elements
    const voiceInputButton = document.getElementById('voice-input');
    const attachmentButton = document.getElementById('attachment');
    const emojiPicker = document.getElementById('emoji-picker');
    const charCounter = document.getElementById('char-counter');
    const quickReplies = document.getElementById('quick-replies');
    
    // Status Elements
    const statusBar = document.getElementById('status-bar');
    const typingIndicator = document.getElementById('typing-indicator');
    const sessionTitle = document.getElementById('session-title');
    
    // Modal Elements
    const fileUploadModal = document.getElementById('file-upload-modal');
    const helpModal = document.getElementById('help-modal');
    const uploadArea = document.getElementById('upload-area');
    const fileInput = document.getElementById('file-input');
    
    // Toast Container
    const toastContainer = document.getElementById('toast-container');
    
    // State Management
    let currentLanguage = 'vi';
    let isTyping = false;
    let chatSessions = [];
    let currentSessionId = null;
    let attachedFiles = [];
    let speechRecognition = null;
    let isRecording = false;
    
    // Initialize Application
    init();
      function init() {
        // Check browser compatibility first
        if (!checkBrowserCompatibility()) {
            console.warn('Browser may have limited functionality. Some features might not work properly.');
        }
        
        setupEventListeners();
        loadUserPreferences();
        initializeSpeechRecognition();
        renderChatHistory();
        setupKeyboardShortcuts();
        checkAIStatus();
          // Show welcome screen initially
        checkAndShowWelcomeScreen();
    }
    
    function checkBrowserCompatibility() {
        let isCompatible = true;
        
        // Check for localStorage support
        try {
            const testKey = '__test_key__';
            localStorage.setItem(testKey, testKey);
            localStorage.removeItem(testKey);
            console.log('localStorage is available and working');
        } catch (e) {
            console.error('localStorage is not available:', e);
            isCompatible = false;
            
            // Create a warning for the user
            const warningElement = document.createElement('div');
            warningElement.className = 'storage-warning';
            warningElement.style.cssText = 'position: fixed; top: 0; left: 0; right: 0; background-color: #f8d7da; color: #721c24; padding: 10px; text-align: center; z-index: 9999;';
            warningElement.textContent = 'Cảnh báo: Trình duyệt của bạn không hỗ trợ lưu trữ dữ liệu. Lịch sử trò chuyện sẽ không được lưu lại.';
            document.body.prepend(warningElement);
            
            // Create a memory-based fallback for localStorage
            window.memoryStorage = {};
            window.localStorage = {
                getItem: function(key) {
                    return window.memoryStorage[key] || null;
                },
                setItem: function(key, value) {
                    window.memoryStorage[key] = value.toString();
                },
                removeItem: function(key) {
                    delete window.memoryStorage[key];
                },
                clear: function() {
                    window.memoryStorage = {};
                }
            };
        }
        
        return isCompatible;
    }function setupEventListeners() {
        console.log('Setting up event listeners...');
        console.log('Attachment button:', attachmentButton);
        console.log('File upload modal:', fileUploadModal);
        console.log('Help modal:', helpModal);
        
        // Check if critical elements exist
        if (!attachmentButton) {
            console.error('Attachment button not found!');
            // Continue anyway instead of returning
        }
        if (!fileUploadModal) {
            console.error('File upload modal not found!');
            // Continue anyway instead of returning
        }
        
        // Input Events
        if (userInput) userInput.addEventListener('input', handleInputChange);
        if (userInput) userInput.addEventListener('keydown', handleKeyDown);
        if (sendButton) sendButton.addEventListener('click', sendMessage);
        
        // Navigation Events
        if (themeToggleButton) themeToggleButton.addEventListener('click', toggleTheme);
        if (languageToggle) languageToggle.addEventListener('click', toggleLanguage);
        if (helpCenter) helpCenter.addEventListener('click', () => showModal(helpModal));
        if (userProfile) userProfile.addEventListener('click', handleUserProfile);
          // Sidebar Events
        if (sidebarToggle) sidebarToggle.addEventListener('click', toggleSidebar);
        if (mobileBackdrop) {
            mobileBackdrop.addEventListener('click', () => {
                if (window.innerWidth <= 768) {
                    sidebar.classList.remove('open');
                }
            });
        }
        if (newChatBtn) newChatBtn.addEventListener('click', startNewChat);
        if (responseStyle) {
            responseStyle.addEventListener('change', updateResponseStyle);
        }
        if (responseLength) {
            responseLength.addEventListener('change', updateResponseLength);
        }
        
        // Input Feature Events
        if (voiceInputButton) voiceInputButton.addEventListener('click', toggleVoiceInput);
        if (attachmentButton) attachmentButton.addEventListener('click', () => {
            console.log('Attachment button clicked!');
            showModal(fileUploadModal);
        });
        if (emojiPicker) emojiPicker.addEventListener('click', showEmojiPicker);
          // Quick Action Events
        document.querySelectorAll('.quick-btn').forEach(btn => {
            btn.addEventListener('click', (e) => handleQuickAction(e.target.dataset.action));
        });
        
        // Suggested Prompt Events
        document.querySelectorAll('.prompt-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const prompt = e.target.dataset.prompt || e.target.textContent;
                if (userInput) userInput.value = prompt;
                hideWelcomeScreen();
                sendMessage();
            });
        });
          // Modal Events
        document.querySelectorAll('.modal-close').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                const modal = e.target.closest('.modal-overlay');
                console.log('Close button clicked, modal:', modal);
                if (modal) {
                    hideModal(modal);
                } else {
                    // Fallback: close all active modals
                    document.querySelectorAll('.modal-overlay.active').forEach(m => hideModal(m));
                }
            });
        });
        
        // File Upload Events
        if (uploadArea) uploadArea.addEventListener('click', () => fileInput && fileInput.click());
        if (uploadArea) uploadArea.addEventListener('dragover', handleDragOver);
        if (uploadArea) uploadArea.addEventListener('drop', handleFileDrop);
        if (fileInput) fileInput.addEventListener('change', handleFileSelect);
          // Quick Reply Events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('quick-reply')) {
                if (userInput) userInput.value = e.target.textContent;
                sendMessage();
            }
        });
        
        // Outside Click Events
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal-overlay')) {
                hideModal(e.target);
            }
        });
        
        // Escape Key for Modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.modal-overlay.active').forEach(modal => {
                    hideModal(modal);
                });
            }
        });
        
        // Load chat sessions from localStorage
        try {
            chatSessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
            console.log('Loaded chat sessions:', chatSessions);
        } catch (error) {
            console.error('Error loading chat sessions:', error);
            chatSessions = [];
            // Attempt to initialize localStorage
            try {
                localStorage.setItem('chatSessions', JSON.stringify([]));
            } catch (error) {
                console.error('Error initializing localStorage:', error);
            }
        }
        
        // Additional modal close handlers for specific modals
        if (typeof setupModalCloseHandlers === 'function') {
            setupModalCloseHandlers();
        }
    }
    
    function handleInputChange() {
        const value = userInput.value;
        const charCount = value.length;
        
        // Update character counter
        charCounter.textContent = `${charCount}/4000`;
        
        // Auto-resize textarea
        userInput.style.height = 'auto';
        userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
        
        // Enable/disable send button
        sendButton.disabled = value.trim().length === 0;
        
        // Handle slash commands
        if (value.startsWith('/')) {
            handleSlashCommand(value);
        }
    }
    
    function handleKeyDown(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        } else if (e.key === 'Escape') {
            userInput.blur();
        }
    }
    
    function handleSlashCommand(command) {
        const cmd = command.toLowerCase().trim();
        switch (cmd) {
            case '/clear':
                clearChat();
                userInput.value = '';
                break;
            case '/new':
                startNewChat();
                userInput.value = '';
                break;
            case '/export':
                exportChat();
                userInput.value = '';
                break;
            case '/help':
                showModal(helpModal);
                userInput.value = '';
                break;
        }
    }
      function sendMessage() {
        const message = userInput.value.trim();
        console.log('sendMessage called with:', message);
        
        if (message === '' && attachedFiles.length === 0) {
            console.log('Message is empty, returning');
            return;
        }
        
        console.log('Sending message to backend:', message);
        
        // Hide welcome screen
        hideWelcomeScreen();
        
        // Add user message
        addMessage({
            text: message,
            sender: 'user',
            files: [...attachedFiles]
        });
        
        // Clear input
        userInput.value = '';
        userInput.style.height = 'auto';
        charCounter.textContent = '0/4000';
        sendButton.disabled = true;
        clearAttachments();
        
        // Show typing indicator
        showTypingIndicator();
        
        // Send to backend
        sendToBackend(message, attachedFiles);
    }
      function sendToBackend(message, files) {
        console.log('sendToBackend called with:', { message, files, currentLanguage });
        
        const formData = new FormData();
        formData.append('query', message);
        if (responseStyle) {
            formData.append('style', responseStyle.value);
            console.log('Response style:', responseStyle.value);
        }
        if (responseLength) {
            formData.append('length', responseLength.value);
            console.log('Response length:', responseLength.value);
        }
        formData.append('language', currentLanguage);
        
        // Add files if any
        files.forEach((file, index) => {
            formData.append(`file_${index}`, file);
        });
        
        console.log('Making fetch request to /api/chat');
        
        fetch('/api/chat', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            console.log('Response received:', response.status, response.statusText);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Response data:', data);
            hideTypingIndicator();
            
            if (data.success) {
                addMessage({
                    text: data.response,
                    sender: 'bot',
                    timestamp: new Date()
                });
                
                // Show quick replies if available
                if (data.quick_replies) {
                    showQuickReplies(data.quick_replies);
                }
            } else {
                console.error('API returned error:', data.error);
                showToast('Đã xảy ra lỗi khi xử lý tin nhắn', 'error');
                addMessage({
                    text: `Lỗi: ${data.error || 'Không thể xử lý yêu cầu'}`,
                    sender: 'bot',
                    error: true
                });
            }
        })
        .catch(error => {
            console.error('Fetch error:', error);
            hideTypingIndicator();
            showToast('Không thể kết nối với máy chủ', 'error');
            addMessage({
                text: `Lỗi kết nối: ${error.message}`,
                sender: 'bot',
                error: true
            });        });
    }
    
    function addMessage(messageData) {
        const { text, sender, files = [], timestamp = new Date(), error = false } = messageData;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        if (error) messageDiv.classList.add('error');
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        // Add files if any
        if (files.length > 0) {
            const filesDiv = document.createElement('div');
            filesDiv.className = 'message-files';
            files.forEach(file => {
                const fileSpan = document.createElement('span');
                fileSpan.className = 'file-attachment';
                fileSpan.innerHTML = `<i class=\"fas fa-paperclip\"></i> ${file.name}`;
                filesDiv.appendChild(fileSpan);
            });
            messageContent.appendChild(filesDiv);
        }
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        
        // Process markdown for bot messages
        if (sender === 'bot') {
            messageText.innerHTML = marked.parse(text);
            // Highlight code blocks
            messageText.querySelectorAll('pre code').forEach((block) => {
                hljs.highlightElement(block);
            });
        } else {
            messageText.textContent = text;
        }
        
        messageContent.appendChild(messageText);
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = formatTime(timestamp);
        
        messageDiv.appendChild(messageContent);
        messageDiv.appendChild(messageTime);
        chatMessages.appendChild(messageDiv);
        
        // Hide welcome screen if this is the first message
        hideWelcomeScreen();
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Update session
        updateCurrentSession();
    }
    
    function showTypingIndicator() {
        isTyping = true;
        typingIndicator.style.display = 'flex';
        updateAIStatus('typing');
    }
    
    function hideTypingIndicator() {
        isTyping = false;
        typingIndicator.style.display = 'none';
        updateAIStatus('online');
    }
    
    function showQuickReplies(replies) {
        quickReplies.innerHTML = '';
        replies.forEach(reply => {
            const btn = document.createElement('button');
            btn.className = 'quick-reply';
            btn.textContent = reply;
            quickReplies.appendChild(btn);
        });
        quickReplies.style.display = 'flex';
        
        // Auto-hide after 10 seconds
        setTimeout(() => {
            quickReplies.style.display = 'none';
        }, 10000);
    }    function checkAndShowWelcomeScreen() {
        // Kiểm tra xem có tin nhắn nào trong chat chưa
        const hasMessages = chatMessages.children.length > 0;
        console.log(`Has messages: ${chatMessages.children.length }`);
        if (!hasMessages) {
            showWelcomeScreen();
        } else {
            hideWelcomeScreen();
        }
    }
    
    function showWelcomeScreen() {
        if (welcomeScreen) {
            welcomeScreen.style.display = 'flex';
            chatMessages.style.display = 'none';
            chatMessages.classList.add('hidden');
        }
    }
    
    function hideWelcomeScreen() {
        if (welcomeScreen) {
            welcomeScreen.style.display = 'none';
            chatMessages.style.display = 'flex';
            chatMessages.classList.remove('hidden');
        }
    }
    
    function toggleTheme() {
        document.body.classList.toggle('dark-theme');
        const isDark = document.body.classList.contains('dark-theme');
        
        // Update icon
        const icon = themeToggleButton.querySelector('i');
        icon.className = isDark ? 'fas fa-sun' : 'fas fa-moon';
        
        // Save preference
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
        
        showToast(`Đã chuyển sang chế độ ${isDark ? 'tối' : 'sáng'}`, 'success');
    }
    
    function toggleLanguage() {
        currentLanguage = currentLanguage === 'vi' ? 'en' : 'vi';
        languageToggle.querySelector('span').textContent = currentLanguage.toUpperCase();
        
        // Update UI text based on language
        updateUILanguage();
        
        // Save preference
        localStorage.setItem('language', currentLanguage);
        
        showToast(currentLanguage === 'vi' ? 'Đã chuyển sang tiếng Việt' : 'Switched to English', 'success');
    }
    
    function toggleSidebar() {
        const isMobile = window.innerWidth <= 768;
        
        if (isMobile) {
            sidebar.classList.toggle('open');
        } else {
            sidebar.classList.toggle('closed');
        }
    }
      function startNewChat() {
        if (chatMessages.children.length > 0) {
            // Save current session
            saveCurrentSession();
        }
        
        // Clear chat
        chatMessages.innerHTML = '';
        checkAndShowWelcomeScreen();
        
        // Create new session
        currentSessionId = generateSessionId();
        updateSessionTitle('Cuộc trò chuyện mới');
        
        // Update history
        renderChatHistory();
        
        showToast('Đã bắt đầu cuộc trò chuyện mới', 'success');
    }
    
    function clearChat() {
        if (confirm('Bạn có chắc chắn muốn xóa lịch sử trò chuyện?')) {
            chatMessages.innerHTML = '';
            checkAndShowWelcomeScreen();
            showToast('Đã xóa lịch sử trò chuyện', 'success');
        }
    }
    
    function exportChat() {
        const messages = Array.from(chatMessages.children).map(msg => {
            const sender = msg.classList.contains('user-message') ? 'User' : 'Assistant';
            const text = msg.querySelector('.message-text').textContent;
            const time = msg.querySelector('.message-time').textContent;
            return `[${time}] ${sender}: ${text}`;
        }).join('\\n\\n');
        
        const blob = new Blob([messages], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `chat-export-${new Date().toISOString().split('T')[0]}.txt`;
        a.click();
        URL.revokeObjectURL(url);
        
        showToast('Đã xuất lịch sử trò chuyện', 'success');
    }
    
    function handleQuickAction(action) {
        let prompt = '';
        switch (action) {
            case 'code':
                prompt = 'Tôi cần hỗ trợ lập trình. ';
                break;
            case 'translate':
                prompt = 'Vui lòng dịch văn bản sau: ';
                break;
            case 'analyze':
                prompt = 'Hãy phân tích dữ liệu sau: ';
                break;
        }
        userInput.value = prompt;
        userInput.focus();
    }
    
    function handleUserProfile() {
        showToast('Tính năng hồ sơ người dùng đang được phát triển', 'info');
    }
    
    function toggleVoiceInput() {
        if (!speechRecognition) {
            showToast('Trình duyệt không hỗ trợ nhận dạng giọng nói', 'error');
            return;
        }
        
        if (isRecording) {
            speechRecognition.stop();
        } else {
            speechRecognition.start();
        }
    }
    
    function initializeSpeechRecognition() {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            speechRecognition = new SpeechRecognition();
            
            speechRecognition.lang = currentLanguage === 'vi' ? 'vi-VN' : 'en-US';
            speechRecognition.continuous = false;
            speechRecognition.interimResults = false;
            
            speechRecognition.onstart = function() {
                isRecording = true;
                voiceInputButton.classList.add('recording');
                voiceInputButton.innerHTML = '<i class=\"fas fa-stop\"></i>';
                showToast('Đang nghe...', 'info');
            };
            
            speechRecognition.onresult = function(event) {
                const transcript = event.results[0][0].transcript;
                userInput.value = transcript;
                handleInputChange();
                showToast('Đã nhận dạng giọng nói thành công', 'success');
            };
            
            speechRecognition.onend = function() {
                isRecording = false;
                voiceInputButton.classList.remove('recording');
                voiceInputButton.innerHTML = '<i class=\"fas fa-microphone\"></i>';
            };
            
            speechRecognition.onerror = function(event) {
                isRecording = false;
                voiceInputButton.classList.remove('recording');
                voiceInputButton.innerHTML = '<i class=\"fas fa-microphone\"></i>';
                showToast('Lỗi nhận dạng giọng nói: ' + event.error, 'error');
            };
        }
    }
    
    function showEmojiPicker() {
        // Simple emoji picker implementation
        const emojis = ['😀', '😂', '🤔', '👍', '❤️', '🎉', '🔥', '💡', '📝', '🚀'];
        const emojiMenu = document.createElement('div');
        emojiMenu.className = 'emoji-menu';
        emojiMenu.style.cssText = `
            position: absolute;
            bottom: 60px;
            right: 60px;
            background: var(--chat-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
            box-shadow: var(--shadow-lg);
            z-index: 1000;
        `;
        
        emojis.forEach(emoji => {
            const btn = document.createElement('button');
            btn.textContent = emoji;
            btn.style.cssText = `
                border: none;
                background: none;
                font-size: 20px;
                cursor: pointer;
                padding: 4px;
                border-radius: 4px;
                transition: background var(--transition-fast);
            `;
            btn.onclick = () => {
                userInput.value += emoji;
                handleInputChange();
                emojiMenu.remove();
            };
            emojiMenu.appendChild(btn);
        });
        
        document.body.appendChild(emojiMenu);
        
        // Remove on outside click
        setTimeout(() => {
            document.addEventListener('click', function removeEmojiMenu(e) {
                if (!emojiMenu.contains(e.target) && e.target !== emojiPicker) {
                    emojiMenu.remove();
                    document.removeEventListener('click', removeEmojiMenu);
                }
            });
        }, 0);
    }
    
    function handleFileSelect(e) {
        const files = Array.from(e.target.files);
        addAttachments(files);
    }
    
    function handleDragOver(e) {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    }
    
    function handleFileDrop(e) {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        const files = Array.from(e.dataTransfer.files);
        addAttachments(files);
    }
    
    function addAttachments(files) {
        const allowedTypes = ['text/plain', 'application/pdf', 'image/jpeg', 'image/png', 'image/gif'];
        const maxSize = 10 * 1024 * 1024; // 10MB
        
        files.forEach(file => {
            if (!allowedTypes.includes(file.type)) {
                showToast(`Loại tệp ${file.type} không được hỗ trợ`, 'error');
                return;
            }
            
            if (file.size > maxSize) {
                showToast(`Tệp ${file.name} quá lớn (tối đa 10MB)`, 'error');
                return;
            }
            
            attachedFiles.push(file);
            displayAttachment(file);
        });
        
        hideModal(fileUploadModal);
    }
    
    function displayAttachment(file) {
        const attachmentsDiv = document.getElementById('input-attachments');
        
        const attachmentDiv = document.createElement('div');
        attachmentDiv.className = 'attachment-item';
        attachmentDiv.innerHTML = `
            <i class=\"fas fa-paperclip\"></i>
            <span>${file.name}</span>
            <button type=\"button\" onclick=\"removeAttachment(this, '${file.name}')\" style=\"background: none; border: none; color: var(--error-color); margin-left: 8px;\">
                <i class=\"fas fa-times\"></i>
            </button>
        `;
        
        attachmentsDiv.appendChild(attachmentDiv);
    }
    
    function removeAttachment(button, fileName) {
        attachedFiles = attachedFiles.filter(file => file.name !== fileName);
        button.parentElement.remove();
    }
    
    function clearAttachments() {
        attachedFiles = [];
        document.getElementById('input-attachments').innerHTML = '';
    }
      function showModal(modal) {
        console.log('Showing modal:', modal);
        if (modal) {
            modal.classList.add('active');
            document.body.style.overflow = 'hidden';
        }
    }
    
    function hideModal(modal) {
        console.log('Hiding modal:', modal);
        if (modal) {
            modal.classList.remove('active');
            document.body.style.overflow = '';
        }
    }
    
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <div style=\"display: flex; align-items: center; gap: 8px;\">
                <i class=\"fas fa-${getToastIcon(type)}\"></i>
                <span>${message}</span>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        // Show toast
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Remove toast after 5 seconds
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }
    
    function getToastIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            default: return 'info-circle';
        }
    }
    
    function setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Enter to send message
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                sendMessage();
            }
            
            // Ctrl/Cmd + K to focus input
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                userInput.focus();
            }
            
            // Ctrl/Cmd + N for new chat
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                startNewChat();
            }
            
            // Ctrl/Cmd + Shift + C to clear chat
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'C') {
                e.preventDefault();
                clearChat();
            }
        });
    }
    
    function checkAIStatus() {
        // Simulate AI status check
        updateAIStatus('online');
    }
    
    function updateAIStatus(status) {
        const indicator = document.querySelector('.status-indicator');
        const statusText = document.querySelector('.status-text');
        
        indicator.className = `status-indicator ${status}`;
        
        switch (status) {
            case 'online':
                statusText.textContent = 'AI sẵn sàng';
                break;
            case 'typing':
                statusText.textContent = 'AI đang soạn thảo...';
                break;
            case 'offline':
                statusText.textContent = 'AI không khả dụng';
                break;
        }
    }
    
    function updateResponseStyle() {
        showToast(`Đã cập nhật phong cách phản hồi: ${responseStyle.options[responseStyle.selectedIndex].text}`, 'success');
    }
    
    function updateResponseLength() {
        showToast(`Đã cập nhật độ dài phản hồi: ${responseLength.options[responseLength.selectedIndex].text}`, 'success');
    }
    
    function loadUserPreferences() {
        // Load theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme === 'dark') {
            document.body.classList.add('dark-theme');
            themeToggleButton.querySelector('i').className = 'fas fa-sun';
        }
        
        // Load language
        const savedLanguage = localStorage.getItem('language');
        if (savedLanguage) {
            currentLanguage = savedLanguage;
            languageToggle.querySelector('span').textContent = currentLanguage.toUpperCase();
            updateUILanguage();
        }
        
        // Load other preferences
        const savedStyle = localStorage.getItem('responseStyle');
        if (savedStyle && responseStyle) {
            responseStyle.value = savedStyle;
        }
        
        const savedLength = localStorage.getItem('responseLength');
        if (savedLength && responseLength) {
            responseLength.value = savedLength;
        }
    }
    
    function updateUILanguage() {
        // This would contain all UI text translations
        const translations = {
            vi: {
                newChat: 'Trò chuyện mới',
                chatHistory: 'Lịch sử trò chuyện',
                aiReady: 'AI sẵn sàng',
                typeMessage: 'Nhập câu hỏi tại đây...'
            },
            en: {
                newChat: 'New Chat',
                chatHistory: 'Chat History',
                aiReady: 'AI Ready',
                typeMessage: 'Type your question here...'
            }
        };
        
        const t = translations[currentLanguage];
        
        // Update placeholders and text content
        if (userInput) {
            userInput.placeholder = t.typeMessage;
        }
        
        // Update speech recognition language
        if (speechRecognition) {
            speechRecognition.lang = currentLanguage === 'vi' ? 'vi-VN' : 'en-US';
        }
    }
      function renderChatHistory() {
        try {
            // Check if the chatHistory element exists
            if (!chatHistory) {
                console.error('Chat history element not found');
                return;
            }
            
            console.log('Rendering chat history');
            
            // Load chat sessions from localStorage
            let sessions = [];
            try {
                const sessionsData = localStorage.getItem('chatSessions');
                console.log('Retrieved sessions data:', sessionsData);
                sessions = JSON.parse(sessionsData || '[]');
            } catch (error) {
                console.error('Error parsing chat sessions from localStorage:', error);
                sessions = [];
            }
            
            console.log('Loaded sessions:', sessions);
            
            // Clear the chat history element
            chatHistory.innerHTML = '';
            
            // Create and append list items for each session
            sessions.forEach((session, index) => {
                const li = document.createElement('li');
                li.textContent = session.title || `Cuộc trò chuyện #${index + 1}`;
                li.dataset.sessionId = session.id;
                li.onclick = () => loadChatSession(session.id);
                
                if (session.id === currentSessionId) {
                    li.classList.add('active');
                }
                
                chatHistory.appendChild(li);
            });
            
            if (sessions.length === 0) {
                const emptyMsg = document.createElement('li');
                emptyMsg.classList.add('empty-history');
                emptyMsg.textContent = currentLanguage === 'vi' ? 'Chưa có lịch sử tư vấn' : 'No chat history';
                chatHistory.appendChild(emptyMsg);
            }
        } catch (error) {
            console.error('Error in renderChatHistory:', error);
        }
    }
      function saveCurrentSession() {
        if (!currentSessionId || !chatMessages || chatMessages.children.length === 0) {
            console.log('No session to save or no messages.');
            return;
        }
        
        try {
            const messages = Array.from(chatMessages.children).map(msg => ({
                sender: msg.classList.contains('user-message') ? 'user' : 'bot',
                text: msg.querySelector('.message-text')?.textContent || '',
                timestamp: msg.querySelector('.message-time')?.textContent || new Date().toLocaleTimeString()
            }));
            
            let sessions = [];
            try {
                sessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
            } catch (error) {
                console.error('Error parsing chat sessions from localStorage:', error);
                sessions = [];
            }
            
            const sessionIndex = sessions.findIndex(s => s.id === currentSessionId);
            
            const sessionData = {
                id: currentSessionId,
                title: generateSessionTitle(messages),
                messages: messages,
                timestamp: new Date().toISOString()
            };
            
            if (sessionIndex >= 0) {
                sessions[sessionIndex] = sessionData;
            } else {
                sessions.push(sessionData);
            }
            
            console.log('Saving session:', sessionData);
            try {
                localStorage.setItem('chatSessions', JSON.stringify(sessions));
                console.log('Session saved successfully');
            } catch (error) {
                console.error('Error saving to localStorage:', error);
                // Try to clear some space
                try {
                    if (sessions.length > 10) {
                        // Keep only the 10 most recent sessions
                        sessions = sessions.slice(-10);
                        localStorage.setItem('chatSessions', JSON.stringify(sessions));
                        console.log('Cleared some space in localStorage');
                    }
                } catch (clearError) {
                    console.error('Failed to clear space in localStorage:', clearError);
                }
            }
        } catch (error) {
            console.error('Error in saveCurrentSession:', error);
        }
    }
      function loadChatSession(sessionId) {
        try {
            let sessions = [];
            try {
                sessions = JSON.parse(localStorage.getItem('chatSessions') || '[]');
            } catch (error) {
                console.error('Error parsing chat sessions from localStorage:', error);
                sessions = [];
            }
            
            const session = sessions.find(s => s.id === sessionId);
            
            if (!session) {
                console.error('Session not found:', sessionId);
                return;
            }
            
            console.log('Loading session:', session);
            
            // Save current session before switching
            if (currentSessionId && currentSessionId !== sessionId) {
                saveCurrentSession();
            }
            
            // Load session
            currentSessionId = sessionId;
            
            if (chatMessages) {
                chatMessages.innerHTML = '';
                hideWelcomeScreen();
                
                session.messages.forEach(msg => {
                    addMessage({
                        text: msg.text,
                        sender: msg.sender,
                        timestamp: new Date()
                    });
                });
            } else {
                console.error('chatMessages element not found');
            }
            
            updateSessionTitle(session.title);
            renderChatHistory();
        } catch (error) {
            console.error('Error in loadChatSession:', error);
        }
    }
    
    function updateCurrentSession() {
        // Auto-save current session periodically
        if (currentSessionId) {
            clearTimeout(window.autoSaveTimeout);
            window.autoSaveTimeout = setTimeout(saveCurrentSession, 2000);
        }
    }
    
    function updateSessionTitle(title) {
        if (sessionTitle) {
            sessionTitle.textContent = title;
        }
    }
      function generateSessionId() {
        try {
            // Generate a unique session ID using timestamp and random string
            const timestamp = Date.now();
            const randomPart = Math.random().toString(36).substring(2, 11);
            return `session_${timestamp}_${randomPart}`;
        } catch (error) {
            console.error('Error generating session ID:', error);
            // Fallback to simpler ID generation
            return 'session_' + new Date().getTime();
        }
    }
    
    function generateSessionTitle(messages) {
        if (messages.length === 0) return 'Cuộc trò chuyện mới';
        
        const firstUserMessage = messages.find(m => m.sender === 'user');
        if (firstUserMessage) {
            const title = firstUserMessage.text.substring(0, 50);
            return title.length < firstUserMessage.text.length ? title + '...' : title;
        }
        
        return 'Cuộc trò chuyện mới';
    }
    
    function formatTime(date) {
        return date.toLocaleTimeString('vi-VN', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    function setupModalCloseHandlers() {
        // Specific handler for file upload modal close button
        const fileModalCloseBtn = fileUploadModal.querySelector('.modal-close');
        if (fileModalCloseBtn) {
            fileModalCloseBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('File modal close button clicked');
                hideModal(fileUploadModal);
            });
        }
        
        // Specific handler for help modal close button
        const helpModalCloseBtn = helpModal.querySelector('.modal-close');
        if (helpModalCloseBtn) {
            helpModalCloseBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Help modal close button clicked');
                hideModal(helpModal);
            });
        }
        
        // Click outside to close modal
        fileUploadModal.addEventListener('click', (e) => {
            if (e.target === fileUploadModal) {
                console.log('Clicked outside file modal');
                hideModal(fileUploadModal);
            }
        });
        
        helpModal.addEventListener('click', (e) => {
            if (e.target === helpModal) {
                console.log('Clicked outside help modal');
                hideModal(helpModal);
            }
        });
    }
    
    // Global functions for HTML onclick events
    window.removeAttachment = removeAttachment;
    
    // Test function to manually trigger modal
    window.testFileModal = function() {
        console.log('Testing file modal...');
        if (fileUploadModal) {
            showModal(fileUploadModal);
        } else {
            console.error('File upload modal not found!');
        }
    };
    
    // Test function to manually close modal
    window.closeFileModal = function() {
        console.log('Closing file modal...');
        if (fileUploadModal) {
            hideModal(fileUploadModal);
        }
    };
    
    // Handle window resize
    window.addEventListener('resize', () => {
        const isMobile = window.innerWidth <= 768;
        if (!isMobile && sidebar.classList.contains('open')) {
            sidebar.classList.remove('open');
            sidebar.classList.remove('closed');
        }
    });
    
    // Save preferences on page unload
    window.addEventListener('beforeunload', () => {
        saveCurrentSession();
        localStorage.setItem('responseStyle', responseStyle.value);
        localStorage.setItem('responseLength', responseLength.value);
    });
    
    // Initialize current session
    if (!currentSessionId) {
        currentSessionId = generateSessionId();
    }
});

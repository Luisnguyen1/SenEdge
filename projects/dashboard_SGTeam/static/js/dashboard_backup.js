/**
 * Professional Dashboard JavaScript
 * Handles Three.js 3D visualization, Chart.js charts, and real-time data updates
 */

class DashboardManager {
    constructor() {
        this.charts = {};
        this.threeScene = null;
        this.updateInterval = null;
        this.apiBaseUrl = '/api';
        this.messaging = null;
        
        this.firebaseInitializationPromise = this.initializeFirebase();
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupCharts();
        this.setup3DScene();
        this.startDataUpdates();
        this.loadInitialData();
        this._checkInitialNotificationStatus();
        
        // Auto-update FCM token after Firebase initialization
        this.firebaseInitializationPromise.then(() => {
            this.autoUpdateFCMToken();
        });
    }

    _checkInitialNotificationStatus() {
        // Update notification button based on current permission
        const permission = Notification.permission;
        this._updateNotificationButton(permission === 'granted' ? 'granted' : 
                                     permission === 'denied' ? 'denied' : 'default');
    }

    setupNavigation() {
        const navLinks = document.querySelectorAll('.nav-link');
        const sections = document.querySelectorAll('.dashboard-section');

        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                // Remove active class from all links
                navLinks.forEach(l => l.classList.remove('active'));
                // Add active class to clicked link
                link.classList.add('active');
                
                // Hide all sections
                sections.forEach(section => section.style.display = 'none');
                
                // Show selected section
                const sectionId = link.dataset.section + '-section';
                const targetSection = document.getElementById(sectionId);
                if (targetSection) {
                    targetSection.style.display = 'block';
                }

                // Special handling for 3D view
                if (link.dataset.section === '3d-view') {
                    this.resize3DScene();
                }
            });
        });
    }

    async initializeFirebase() {
        try {
            console.log('🔥 Initializing Firebase...');
            
            // Firebase configuration
            const firebaseConfig = {
                apiKey: "AIzaSyA_4Gmz40FYwltk-t6GJMazjY4E_v9t-JA",
                authDomain: "iot-challenge-2025.firebaseapp.com",
                projectId: "iot-challenge-2025",
                storageBucket: "iot-challenge-2025.firebasestorage.app",
                messagingSenderId: "1049728988575",
                appId: "1:1049728988575:web:c292236ada530366cab9aa",
                measurementId: "G-X9H0KG7VHV"
            };

            // Check Firebase SDK availability
            if (typeof firebase === 'undefined') {
                console.error('❌ Firebase SDK not loaded');
                return false;
            }

            // Initialize Firebase app (avoid duplicate initialization)
            if (!firebase.apps.length) {
                firebase.initializeApp(firebaseConfig);
                console.log('✅ Firebase app initialized');
            } else {
                console.log('🔄 Firebase app already initialized');
            }

            // Initialize messaging with service worker
            const messagingInitialized = await this._initializeMessaging();
            
            if (messagingInitialized) {
                // Set up message handlers
                this._setupMessageHandlers();
                console.log('✅ Firebase initialization completed');
                return true;
            } else {
                console.warn('⚠️ Firebase messaging initialization failed');
                return false;
            }
            
        } catch (error) {
            console.error('❌ Firebase initialization error:', error);
            return false;
        }
    }

    async _initializeMessaging() {
        try {
            // Register service worker first
            if ('serviceWorker' in navigator) {
                try {
                    const registration = await navigator.serviceWorker.register('/static/firebase-messaging-sw.js');
                    console.log('✅ Service worker registered:', registration.scope);
                    
                    // Wait for service worker to be ready
                    await navigator.serviceWorker.ready;
                    
                    // Initialize messaging (Firebase v9 compat mode)
                    this.messaging = firebase.messaging();
                    
                    console.log('✅ Firebase messaging initialized with service worker');
                    return true;
                    
                } catch (swError) {
                    console.warn('⚠️ Service worker registration failed:', swError.message);
                    // Fall back to messaging without service worker
                    this.messaging = firebase.messaging();
                    console.log('⚠️ Firebase messaging initialized without service worker');
                    return true;
                }
            } else {
                console.warn('⚠️ Service Worker not supported in this browser');
                this.messaging = firebase.messaging();
                console.log('⚠️ Firebase messaging initialized without service worker support');
                return true;
            }
        } catch (error) {
            console.error('❌ Messaging initialization error:', error);
            return false;
        }
    }

    _setupMessageHandlers() {
        if (!this.messaging) return;

        // Handle foreground messages
        this.messaging.onMessage((payload) => {
            console.log('📨 Foreground message received:', payload);
            this._handleForegroundMessage(payload);
        });

        // Note: onTokenRefresh has been removed in Firebase v9
        // Token refresh is now handled automatically when calling getToken()
        console.log('✅ Message handlers setup complete');
    }

    _handleForegroundMessage(payload) {
        const notification = payload.notification || {};
        const data = payload.data || {};
        
        const title = notification.title || 'SenEdge Security Alert';
        const body = notification.body || 'Glass break detected!';
        
        // Show browser notification if permission granted
        if (Notification.permission === 'granted') {
            const notificationOptions = {
                body: body,
                icon: '/static/favicon.svg',
                badge: '/static/favicon.svg',
                tag: data.type || 'senedge-alert',
                requireInteraction: true,
                data: data
            };
            
            new Notification(title, notificationOptions);
        }
        
        // Show in-app notification
        this._showInAppNotification(title, body, data);
        
        // Update dashboard if it's a glass break alert
        if (data.type === 'glass_break' || data.type === 'glass_break_test') {
            this._handleGlassBreakAlert(data);
        }
    }

    _showInAppNotification(title, body, data = {}) {
        const notificationDiv = document.createElement('div');
        notificationDiv.className = 'firebase-notification';
        
        const isGlassBreak = data.type === 'glass_break' || data.type === 'glass_break_test';
        const severity = data.severity || 'medium';
        
        notificationDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${isGlassBreak ? this._getSeverityColor(severity) : 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'};
            color: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            z-index: 10000;
            max-width: 400px;
            animation: slideInRight 0.4s ease-out;
            cursor: pointer;
        `;
        
        notificationDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 24px; margin-right: 10px;">
                    ${isGlassBreak ? '🚨' : '🔔'}
                </span>
                <strong style="font-size: 16px;">${title}</strong>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="margin-left: auto; background: none; border: none; color: white; font-size: 18px; cursor: pointer;">×</button>
            </div>
            <p style="margin: 0; line-height: 1.4; font-size: 14px;">${body}</p>
            ${isGlassBreak && data.location ? `
                <div style="margin-top: 10px; font-size: 12px; opacity: 0.9;">
                    📍 Location: ${data.location}<br>
                    🔧 Device: ${data.device_id || 'Unknown'}
                </div>
            ` : ''}
        `;

        // Add click handler to close notification
        notificationDiv.addEventListener('click', () => {
            notificationDiv.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => notificationDiv.remove(), 300);
        });

        document.body.appendChild(notificationDiv);

        // Auto remove after 8 seconds for glass break alerts, 5 seconds for others
        const autoRemoveDelay = isGlassBreak ? 8000 : 5000;
        setTimeout(() => {
            if (notificationDiv.parentElement) {
                notificationDiv.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => notificationDiv.remove(), 300);
            }
        }, autoRemoveDelay);

        // Add required CSS animations if not already present
        this._addNotificationStyles();
    }

    _getSeverityColor(severity) {
        const colors = {
            'low': 'linear-gradient(135deg, #ffd93d 0%, #ff6b35 100%)',
            'medium': 'linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%)',
            'high': 'linear-gradient(135deg, #ff4444 0%, #cc0000 100%)',
            'critical': 'linear-gradient(135deg, #cc0000 0%, #8b0000 100%)'
        };
        return colors[severity] || colors['medium'];
    }

    _addNotificationStyles() {
        if (document.getElementById('firebase-notification-styles')) return;

        const style = document.createElement('style');
        style.id = 'firebase-notification-styles';
        style.textContent = `
            @keyframes slideInRight {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            @keyframes slideOutRight {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
            .firebase-notification:hover {
                transform: scale(1.02);
                transition: transform 0.2s ease;
            }
        `;
        document.head.appendChild(style);
    }

    _handleGlassBreakAlert(data) {
        console.log('🚨 Processing glass break alert:', data);
        
        // Refresh security metrics to show the new alert
        setTimeout(() => {
            this.updateSecurityData();
        }, 1000);
        
        // Update 3D visualization if visible
        const currentSection = document.querySelector('.nav-link.active')?.dataset.section;
        if (currentSection === '3d-view') {
            this._highlight3DAlert(data);
        }
    }

    _highlight3DAlert(data) {
        // Add visual alert indication to 3D scene
        if (this.threeScene && this.threeScene.scene) {
            // Create alert indicator in 3D scene
            const alertGeometry = new THREE.SphereGeometry(0.2);
            const alertMaterial = new THREE.MeshBasicMaterial({ 
                color: 0xff0000,
                transparent: true,
                opacity: 0.8
            });
            const alertIndicator = new THREE.Mesh(alertGeometry, alertMaterial);
            
            // Position based on location or random position
            alertIndicator.position.set(
                Math.random() * 10 - 5,
                2,
                Math.random() * 10 - 5
            );
            
            this.threeScene.scene.add(alertIndicator);
            
            // Animate alert indicator
            const animate = () => {
                alertIndicator.material.opacity = 0.5 + Math.sin(Date.now() * 0.01) * 0.3;
            };
            
            const animationId = setInterval(animate, 50);
            
            // Remove after 10 seconds
            setTimeout(() => {
                clearInterval(animationId);
                this.threeScene.scene.remove(alertIndicator);
            }, 10000);
        }
    }

    async _refreshToken() {
        try {
            if (!this.messaging) return;
            
            const token = await this.messaging.getToken({
                vapidKey: 'BArYin6VlYKEaeCk0lfs_II6Jby7LOJvjgdw8L1zIFWbwN9kFOVCRDwBdF2no2Tl1lt5w0rLFxmqKox-HM-bCT4'
            });
            
            if (token) {
                localStorage.setItem('fcm_token', token);
                await this.sendTokenToBackend(token);
                console.log('🔄 FCM token refreshed and updated');
            }
        } catch (error) {
            console.error('❌ Error refreshing FCM token:', error);
        }
    }

    /**
     * Auto-update FCM token on page load
     * Checks permission and updates token if granted
     */
    async autoUpdateFCMToken() {
        try {
            console.log('🔄 Auto-updating FCM token...');
            
            // Check if Firebase messaging is initialized
            if (!this.messaging) {
                console.log('⚠️ Firebase messaging not initialized, skipping token update');
                return false;
            }
            
            // Check notification permission
            const permission = Notification.permission;
            console.log('📋 Current notification permission:', permission);
            
            if (permission === 'granted') {
                // Get current token
                const currentToken = await this.messaging.getToken({
                    vapidKey: 'BArYin6VlYKEaeCk0lfs_II6Jby7LOJvjgdw8L1zIFWbwN9kFOVCRDwBdF2no2Tl1lt5w0rLFxmqKox-HM-bCT4'
                });
                
                if (currentToken) {
                    const storedToken = localStorage.getItem('fcm_token');
                    
                    // Always send token to backend to ensure it's registered
                    const tokenSent = await this.sendTokenToBackend(currentToken);
                    
                    if (tokenSent) {
                        // Update stored token
                        localStorage.setItem('fcm_token', currentToken);
                        
                        // Update UI to show notifications are enabled
                        this._updateNotificationButton('granted');
                        
                        console.log('✅ FCM token auto-updated successfully');
                        
                        // Log token status
                        const isNewToken = storedToken !== currentToken;
                        console.log(`🔑 Token status: ${isNewToken ? 'New' : 'Existing'} token registered`);
                        
                        return true;
                    } else {
                        console.log('❌ Failed to send token to backend');
                        this._updateNotificationButton('error');
                        return false;
                    }
                } else {
                    console.log('❌ No FCM token available');
                    this._updateNotificationButton('error');
                    return false;
                }
            } else if (permission === 'denied') {
                console.log('❌ Notification permission denied');
                this._updateNotificationButton('denied');
                return false;
            } else {
                console.log('⚠️ Notification permission not granted, will prompt user');
                this._updateNotificationButton('default');
                
                // Auto-prompt for permission after a delay (non-intrusive)
                setTimeout(() => {
                    this._showAutoPromptMessage();
                }, 5000);
                
                return false;
            }
            
        } catch (error) {
            console.error('❌ Error in auto-update FCM token:', error);
            this._updateNotificationButton('error');
            return false;
        }
    }
    
    /**
     * Show a non-intrusive message to enable notifications
     */
    _showAutoPromptMessage() {
        // Don't show if already prompted or permission is not default
        if (Notification.permission !== 'default') return;
        
        const existingMessage = document.getElementById('auto-prompt-message');
        if (existingMessage) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.id = 'auto-prompt-message';
        messageDiv.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            box-shadow: 0 8px 20px rgba(0,0,0,0.3);
            z-index: 9999;
            max-width: 320px;
            font-size: 14px;
            animation: slideInRight 0.4s ease-out;
            cursor: pointer;
        `;
        
        messageDiv.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 20px; margin-right: 8px;">🔔</span>
                <strong>Kích hoạt thông báo bảo mật</strong>
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="margin-left: auto; background: none; border: none; color: white; font-size: 16px; cursor: pointer;">×</button>
            </div>
            <p style="margin: 0; line-height: 1.4; opacity: 0.9;">
                Nhận cảnh báo kính vỡ và thông báo bảo mật ngay lập tức
            </p>
            <button onclick="requestNotifications(); this.parentElement.remove();" 
                    style="margin-top: 10px; background: rgba(255,255,255,0.2); border: none; color: white; padding: 6px 12px; border-radius: 5px; cursor: pointer; font-size: 12px;">
                Kích hoạt ngay
            </button>
        `;
        
        document.body.appendChild(messageDiv);
        this._addNotificationStyles();
        
        // Auto remove after 15 seconds
        setTimeout(() => {
            if (messageDiv.parentElement) {
                messageDiv.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => messageDiv.remove(), 300);
            }
        }, 15000);
    }

    /**
     * Cleanup method to clear intervals and remove event listeners
     */
    cleanup() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
        
        if (this.tokenRefreshInterval) {
            clearInterval(this.tokenRefreshInterval);
            this.tokenRefreshInterval = null;
        }
        
        console.log('🧹 Dashboard cleanup completed');
    }

    async requestNotificationPermission() {
        try {
            if (!this.messaging) {
                console.log('Firebase messaging not initialized');
                return;
            }

            // Show a friendly message before requesting permission
            this.showPermissionPrompt();

            const permission = await Notification.requestPermission();
            
            if (permission === 'granted') {
                console.log('✅ Notification permission granted');
                this.hidePermissionPrompt();
                this.showNotificationStatus('success', '🔔 Thông báo đã được kích hoạt!');
                
                const token = await this.messaging.getToken({
                    vapidKey: 'BEV1qDUihIw_s1bpTKZ6JMKvYuBGGECXgc_ehGcp0MZqUSgN5JOkgF3whu4vi2-Z_hYsrDAcwEjoFNrcevDywks'
                });
                
                if (token) {
                    console.log('FCM Token generated:', token.substring(0, 20) + '...');
                    // Store token for backend use
                    localStorage.setItem('fcm_token', token);
                    
                    // Send token to backend
                    await this.sendTokenToBackend(token);
                    
                    // Show welcome notification
                    this.sendWelcomeNotification();
                } else {
                    console.log('No registration token available');
                }
            } else if (permission === 'denied') {
                console.log('❌ Notification permission denied');
                this.hidePermissionPrompt();
                this.showNotificationStatus('error', '❌ Bạn đã từ chối thông báo. Có thể bật lại trong cài đặt browser.');
            } else {
                console.log('⚠️ Notification permission default (not decided)');
                this.hidePermissionPrompt();
                this.showNotificationStatus('warning', '⚠️ Quyền thông báo chưa được cấp.');
            }
        } catch (error) {
            console.error('Error getting permission:', error);
            this.hidePermissionPrompt();
            this.showNotificationStatus('error', '❌ Lỗi khi yêu cầu quyền thông báo.');
        }
    }

    showPermissionPrompt() {
        const existingPrompt = document.getElementById('notification-prompt');
        if (existingPrompt) return;

        const prompt = document.createElement('div');
        prompt.id = 'notification-prompt';
        prompt.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            z-index: 10000;
            max-width: 350px;
            animation: slideIn 0.3s ease-out;
        `;
        
        prompt.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 24px; margin-right: 10px;">🔔</span>
                <strong>Kích hoạt thông báo</strong>
            </div>
            <p style="margin: 0; line-height: 1.4;">
                Để nhận cảnh báo kính vỡ và các thông báo bảo mật quan trọng, 
                vui lòng cho phép thông báo khi browser yêu cầu.
            </p>
        `;

        document.body.appendChild(prompt);

        // Add animation CSS
        if (!document.getElementById('notification-animations')) {
            const style = document.createElement('style');
            style.id = 'notification-animations';
            style.textContent = `
                @keyframes slideIn {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
                @keyframes slideOut {
                    from { transform: translateX(0); opacity: 1; }
                    to { transform: translateX(100%); opacity: 0; }
                }
            `;
            document.head.appendChild(style);
        }
    }

    hidePermissionPrompt() {
        const prompt = document.getElementById('notification-prompt');
        if (prompt) {
            prompt.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => prompt.remove(), 300);
        }
    }

    showNotificationStatus(type, message) {
        const statusDiv = document.createElement('div');
        statusDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 15px 20px;
            border-radius: 8px;
            color: white;
            font-weight: 500;
            z-index: 10001;
            animation: slideIn 0.3s ease-out;
            max-width: 350px;
        `;

        switch(type) {
            case 'success':
                statusDiv.style.background = 'linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%)';
                statusDiv.style.color = '#2d5a27';
                break;
            case 'error':
                statusDiv.style.background = 'linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%)';
                break;
            case 'warning':
                statusDiv.style.background = 'linear-gradient(135deg, #ffd93d 0%, #ff6b35 100%)';
                statusDiv.style.color = '#8b4513';
                break;
        }

        statusDiv.innerHTML = message;
        document.body.appendChild(statusDiv);

        setTimeout(() => {
            statusDiv.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => statusDiv.remove(), 300);
        }, 4000);
    }

    async sendWelcomeNotification() {
        // Send a welcome test notification
        try {
            const response = await fetch('/api/test-firebase', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    title: '🎉 Chào mừng đến SenEdge Dashboard!',
                    body: 'Thông báo đã được kích hoạt thành công. Bạn sẽ nhận được cảnh báo kính vỡ và các thông báo bảo mật quan trọng.'
                })
            });

            if (response.ok) {
                console.log('Welcome notification sent');
            }
        } catch (error) {
            console.log('Could not send welcome notification:', error);
        }
    }

    async sendTokenToBackend(token) {
        try {
            console.log('📤 Sending FCM token to backend...');
            
            const response = await fetch('/api/register-fcm-token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token })
            });
            
            if (response.ok) {
                const result = await response.json();
                
                // Log success with detailed info
                console.log('✅ FCM token processed successfully:', {
                    message: result.message,
                    total_tokens: result.total_tokens,
                    token_preview: result.token_preview,
                    is_new: result.is_new || false
                });
                
                // Show user-friendly message for new registrations
                if (result.is_new) {
                    this._showNotificationStatus('success', 
                        '✅ Thông báo đã được kích hoạt thành công!');
                } else {
                    console.log('🔄 FCM token refreshed/verified in backend');
                }
                
                return true;
            } else {
                const error = await response.json();
                console.error('❌ Failed to register FCM token:', error);
                this._showNotificationStatus('error', 
                    '❌ Lỗi đăng ký token thông báo: ' + (error.message || 'Unknown error'));
                return false;
            }
        } catch (error) {
            console.error('❌ Error sending token to backend:', error);
            this._showNotificationStatus('error', 
                '❌ Lỗi kết nối với server khi đăng ký thông báo');
            return false;
        }
    }

    // Enhanced debugging and status checking methods
    async checkNotificationStatus() {
        console.log('=== 🔍 Notification System Status Debug ===');
        console.log('📋 Browser Permission:', Notification.permission);
        console.log('🔑 Stored FCM Token:', localStorage.getItem('fcm_token')?.substring(0, 20) + '...' || 'None');
        console.log('🔥 Firebase Messaging:', !!this.messaging);
        console.log('⚙️ Service Worker Support:', 'serviceWorker' in navigator);
        
        if ('serviceWorker' in navigator) {
            try {
                const registrations = await navigator.serviceWorker.getRegistrations();
                console.log('🔧 SW Registrations:', registrations.length);
                registrations.forEach((reg, i) => {
                    console.log(`   SW ${i + 1}: ${reg.scope}`);
                });
            } catch (error) {
                console.log('❌ SW Registration check failed:', error);
            }
        }
        
        // Test backend connection and get status
        await this._testBackendConnection();
        
        // Check if we can generate a token
        if (this.messaging && Notification.permission === 'granted') {
            try {
                const token = await this.messaging.getToken({
                    vapidKey: 'BArYin6VlYKEaeCk0lfs_II6Jby7LOJvjgdw8L1zIFWbwN9kFOVCRDwBdF2no2Tl1lt5w0rLFxmqKox-HM-bCT4'
                });
                console.log('🔑 Current Token Available:', !!token);
            } catch (tokenError) {
                console.log('❌ Token Generation Error:', tokenError);
            }
        }
        
        console.log('=== End Debug Info ===');
    }

    async _testBackendConnection() {
        try {
            console.log('🔗 Testing backend connection...');
            const response = await fetch('/api/fcm-tokens/status');
            const result = await response.json();
            
            console.log('📊 Backend FCM Status:', {
                tokens_count: result.tokens_count,
                firebase_initialized: result.firebase_initialized,
                system_status: result.notification_system_status,
                message: result.message
            });
            
            if (result.tokens_count === 0) {
                console.log('⚠️ No tokens registered in backend. Consider requesting notification permission.');
            }
            
            return result;
        } catch (error) {
            console.error('❌ Backend connection test failed:', error);
            return null;
        }
    }

    // Manual permission request method (can be called from console)
    async requestNotifications() {
        console.log('🔔 Manual notification permission request triggered');
        return await this.requestNotificationPermissionAfterLogin();
    }

    // Test notification method (can be called from console)
    async testNotification() {
        try {
            console.log('🧪 Sending test notification...');
            const response = await fetch('/api/test-firebase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: '🧪 Manual Test Notification',
                    body: 'This is a manual test notification from the console'
                })
            });
            
            const result = await response.json();
            console.log('🧪 Test notification result:', result);
            return result;
        } catch (error) {
            console.error('❌ Test notification failed:', error);
            return { status: 'error', message: error.message };
        }
    }

    // Public method to request notification permission after login
    async requestNotificationPermissionAfterLogin() {
        try {
            // Wait for Firebase initialization to complete before proceeding
            await this.firebaseInitializationPromise;

            console.log('🔔 Requesting notification permission...');
            
            if (!this.messaging) {
                console.error('❌ Firebase messaging not initialized');
                this._showNotificationStatus('error', 
                    '❌ Firebase không được khởi tạo. Vui lòng tải lại trang.');
                return false;
            }

            // Check current permission status
            const currentPermission = Notification.permission;
            console.log('📋 Current notification permission:', currentPermission);

            if (currentPermission === 'granted') {
                console.log('✅ Notification permission already granted');
                this._updateNotificationButton('granted');
                return await this._getAndRegisterToken();
            }

            if (currentPermission === 'denied') {
                console.log('❌ Notification permission was denied previously');
                this._updateNotificationButton('denied');
                this._showNotificationStatus('error', 
                    '❌ Thông báo đã bị từ chối. Vui lòng bật thông báo trong cài đặt trình duyệt.'
                );
                return false;
            }

            // Show friendly prompt before browser permission dialog
            this._showPermissionPrompt();

            // Request permission
            const permission = await Notification.requestPermission();
            console.log('🔔 Permission request result:', permission);

            this._hidePermissionPrompt();

            if (permission === 'granted') {
                console.log('✅ Notification permission granted!');
                this._updateNotificationButton('granted');
                this._showNotificationStatus('success', 
                    '✅ Thông báo đã được kích hoạt thành công!');
                return await this._getAndRegisterToken();
            } else {
                console.log('❌ Notification permission denied');
                this._updateNotificationButton('denied');
                this._showNotificationStatus('error', 
                    '❌ Bạn đã từ chối thông báo. Có thể bật lại trong cài đặt browser.');
                return false;
            }

        } catch (error) {
            console.error('❌ Error requesting notification permission:', error);
            this._hidePermissionPrompt();
            this._updateNotificationButton('error');
            this._showNotificationStatus('error', 
                '❌ Lỗi khi yêu cầu quyền thông báo: ' + error.message);
            return false;
        }
    }

    _updateNotificationButton(status) {
        const button = document.getElementById('notification-button');
        if (!button) return;

        const statusDot = button.querySelector('.status-dot');
        const statusText = button.querySelector('span');

        switch(status) {
            case 'granted':
                statusDot.style.background = '#00ff00';
                statusText.textContent = 'Thông báo: Bật';
                button.style.background = 'rgba(0, 255, 0, 0.2)';
                button.onclick = () => this.checkNotificationStatus();
                break;
            case 'denied':
                statusDot.style.background = '#ff4444';
                statusText.textContent = 'Thông báo: Tắt';
                button.style.background = 'rgba(255, 68, 68, 0.2)';
                button.onclick = () => this._showNotificationStatus('warning', 
                    '⚠️ Thông báo đã bị tắt. Bật trong cài đặt browser để nhận cảnh báo bảo mật.');
                break;
            case 'error':
                statusDot.style.background = '#ffa500';
                statusText.textContent = 'Thông báo: Lỗi';
                button.style.background = 'rgba(255, 165, 0, 0.2)';
                button.onclick = () => this.requestNotificationPermissionAfterLogin();
                break;
            default:
                statusDot.style.background = '#ffa500';
                statusText.textContent = 'Bật thông báo';
                button.style.background = 'rgba(255, 165, 0, 0.2)';
                button.onclick = () => this.requestNotificationPermissionAfterLogin();
        }
    }

    async _getAndRegisterToken() {
        try {
            const token = await this.messaging.getToken({
                vapidKey: 'BArYin6VlYKEaeCk0lfs_II6Jby7LOJvjgdw8L1zIFWbwN9kFOVCRDwBdF2no2Tl1lt5w0rLFxmqKox-HM-bCT4'
            });
            
            if (token) {
                console.log('🔑 FCM Token generated:', token.substring(0, 20) + '...');
                localStorage.setItem('fcm_token', token);
                
                const tokenRegistered = await this.sendTokenToBackend(token);
                if (tokenRegistered) {
                    await this._sendWelcomeNotification();
                    return true;
                }
            } else {
                console.log('❌ No registration token available');
                this._showNotificationStatus('warning', 
                    '⚠️ Không thể tạo token thông báo. Vui lòng thử lại.');
            }
            return false;
        } catch (error) {
            console.error('❌ Error getting FCM token:', error);
            this._showNotificationStatus('error', 
                '❌ Lỗi khi tạo token thông báo: ' + error.message);
            return false;
        }
    }

    _showPermissionPrompt() {
        const existingPrompt = document.getElementById('notification-prompt');
        if (existingPrompt) return;

        const prompt = document.createElement('div');
        prompt.id = 'notification-prompt';
        prompt.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.3);
            z-index: 10000;
            max-width: 380px;
            animation: slideInRight 0.4s ease-out;
        `;
        
        prompt.innerHTML = `
            <div style="display: flex; align-items: center; margin-bottom: 15px;">
                <span style="font-size: 28px; margin-right: 12px;">🔔</span>
                <strong style="font-size: 18px;">Kích hoạt thông báo bảo mật</strong>
            </div>
            <p style="margin: 0; line-height: 1.5; font-size: 14px;">
                Để nhận cảnh báo <strong>kính vỡ</strong> và các thông báo bảo mật quan trọng ngay lập tức, 
                vui lòng cho phép thông báo khi trình duyệt yêu cầu.
            </p>
            <div style="margin-top: 15px; padding: 10px; background: rgba(255,255,255,0.1); border-radius: 6px; font-size: 12px;">
                💡 <em>Thông báo giúp bạn phản ứng nhanh với các sự cố bảo mật</em>
            </div>
        `;

        document.body.appendChild(prompt);
        this._addNotificationStyles();
    }

    _hidePermissionPrompt() {
        const prompt = document.getElementById('notification-prompt');
        if (prompt) {
            prompt.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => prompt.remove(), 300);
        }
    }

    _showNotificationStatus(type, message) {
        const statusDiv = document.createElement('div');
        statusDiv.className = 'notification-status';
        statusDiv.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 18px 24px;
            border-radius: 10px;
            color: white;
            font-weight: 500;
            z-index: 10001;
            animation: slideInRight 0.4s ease-out;
            max-width: 380px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.2);
        `;

        switch(type) {
            case 'success':
                statusDiv.style.background = 'linear-gradient(135deg, #4caf50 0%, #66bb6a 100%)';
                break;
            case 'error':
                statusDiv.style.background = 'linear-gradient(135deg, #f44336 0%, #ef5350 100%)';
                break;
            case 'warning':
                statusDiv.style.background = 'linear-gradient(135deg, #ff9800 0%, #ffb74d 100%)';
                statusDiv.style.color = '#1a1a1a';
                break;
        }

        statusDiv.innerHTML = `
            <div style="display: flex; align-items: center;">
                ${message}
                <button onclick="this.parentElement.parentElement.remove()" 
                        style="margin-left: auto; background: none; border: none; color: inherit; font-size: 20px; cursor: pointer; padding: 0; margin-left: 15px;">×</button>
            </div>
        `;

        document.body.appendChild(statusDiv);

        setTimeout(() => {
            if (statusDiv.parentElement) {
                statusDiv.style.animation = 'slideOutRight 0.3s ease-in';
                setTimeout(() => statusDiv.remove(), 300);
            }
        }, 5000);
    }

    async _sendWelcomeNotification() {
        try {
            const response = await fetch('/api/test-firebase', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: '🎉 Chào mừng đến SenEdge Dashboard!',
                    body: 'Thông báo bảo mật đã được kích hoạt thành công. Bạn sẽ nhận được cảnh báo kính vỡ và các thông báo quan trọng khác.'
                })
            });

            if (response.ok) {
                console.log('✅ Welcome notification sent');
            } else {
                console.log('⚠️ Could not send welcome notification');
            }
        } catch (error) {
            console.log('⚠️ Welcome notification error:', error);
        }
    }

    // Debug function - có thể gọi từ console
    checkNotificationStatus() {
        console.log('=== Notification Status Debug ===');
        console.log('Permission:', Notification.permission);
        console.log('FCM Token:', localStorage.getItem('fcm_token')?.substring(0, 20) + '...');
        console.log('Firebase messaging:', !!this.messaging);
        console.log('Service Worker:', 'serviceWorker' in navigator);
        
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.getRegistrations().then(registrations => {
                console.log('SW Registrations:', registrations.length);
                registrations.forEach((reg, i) => {
                    console.log(`SW ${i}:`, reg.scope);
                });
            });
        }
        
        // Test backend connection
        this.testBackendConnection();
    }

    async testBackendConnection() {
        try {
            console.log('🔗 Testing backend connection...');
            const response = await fetch('/api/fcm-tokens/status');
            const result = await response.json();
            console.log('📊 Backend FCM Status:', result);
            
            if (result.tokens_count === 0) {
                console.log('⚠️  No tokens registered in backend. Try requesting notification permission.');
            }
        } catch (error) {
            console.error('❌ Backend connection test failed:', error);
        }
    }

    setupCharts() {
        const chartConfigs = {
            'overview-chart': {
                type: 'line',
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#ffffff'
                            }
                        }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#ffffff' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        },
                        y: {
                            ticks: { color: '#ffffff' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    }
                }
            },
            'chatbot-conversations-chart': {
                type: 'bar',
                options: this.getChartOptions('Conversations')
            },
            'chatbot-response-chart': {
                type: 'line',
                options: this.getChartOptions('Response Time (ms)')
            },
            'chatbot-accuracy-chart': {
                type: 'line',
                options: this.getChartOptions('Accuracy (%)')
            },
            'chatbot-sentiment-chart': {
                type: 'doughnut',
                options: this.getDoughnutOptions()
            },
            'nav-accuracy-chart': {
                type: 'line',
                options: this.getChartOptions('Accuracy (%)')
            },
            'nav-completion-chart': {
                type: 'line',
                options: this.getChartOptions('Completion Rate (%)')
            },
            'nav-duration-chart': {
                type: 'bar',
                options: this.getChartOptions('Duration (seconds)')
            },
            'security-alerts-chart': {
                type: 'bar',
                options: this.getChartOptions('Alerts Count')
            },
            'security-access-chart': {
                type: 'line',
                options: this.getChartOptions('Access Attempts')
            },
            'security-camera-chart': {
                type: 'line',
                options: this.getChartOptions('Camera Status (%)')
            }
        };

        Object.keys(chartConfigs).forEach(chartId => {
            const canvas = document.getElementById(chartId);
            if (canvas) {
                const ctx = canvas.getContext('2d');
                this.charts[chartId] = new Chart(ctx, {
                    ...chartConfigs[chartId],
                    data: {
                        labels: [],
                        datasets: []
                    }
                });
            }
        });
    }

    getChartOptions(yLabel) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: {
                        color: '#ffffff'
                    }
                }
            },
            scales: {
                x: {
                    ticks: { color: '#ffffff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y: {
                    beginAtZero: true,
                    ticks: { color: '#ffffff' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                    title: {
                        display: true,
                        text: yLabel,
                        color: '#ffffff'
                    }
                }
            }
        };
    }

    getDoughnutOptions() {
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#ffffff'
                    }
                }
            }
        };
    }

    setup3DScene() {
        const container = document.getElementById('three-container');
        if (!container) return;

        // Scene setup
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x1a1a2e);

        // Camera setup
        const camera = new THREE.PerspectiveCamera(
            75,
            container.clientWidth / container.clientHeight,
            0.1,
            1000
        );
        camera.position.set(0, 10, 20);

        // Renderer setup
        const renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        container.appendChild(renderer.domElement);

        // Controls
        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.05;

        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(10, 10, 5);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        scene.add(directionalLight);

        // Building structure
        this.createBuilding(scene);
        
        // Security cameras
        this.createSecurityCameras(scene);
        
        // User indicators
        this.createUserIndicators(scene);

        // Animation loop
        const animate = () => {
            requestAnimationFrame(animate);
            controls.update();
            renderer.render(scene, camera);
        };
        animate();

        this.threeScene = { scene, camera, renderer, controls };

        // Handle window resize
        window.addEventListener('resize', () => this.resize3DScene());
    }

    createBuilding(scene) {
        // Floor
        const floorGeometry = new THREE.PlaneGeometry(30, 30);
        const floorMaterial = new THREE.MeshLambertMaterial({ 
            color: 0x404040,
            transparent: true,
            opacity: 0.8
        });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        scene.add(floor);

        // Building walls
        const wallMaterial = new THREE.MeshLambertMaterial({ 
            color: 0x2a5298,
            transparent: true,
            opacity: 0.7
        });

        // Create rooms
        const rooms = [
            { x: -8, z: -8, width: 6, depth: 6, name: 'Office A' },
            { x: 2, z: -8, width: 6, depth: 6, name: 'Office B' },
            { x: -8, z: 2, width: 6, depth: 6, name: 'Meeting Room' },
            { x: 2, z: 2, width: 6, depth: 6, name: 'Cafeteria' },
            { x: -2, z: -2, width: 4, depth: 4, name: 'Lobby' }
        ];

        rooms.forEach(room => {
            const roomGroup = new THREE.Group();
            
            // Walls
            const wallHeight = 4;
            const wallThickness = 0.2;

            // Front wall
            const frontWall = new THREE.Mesh(
                new THREE.BoxGeometry(room.width, wallHeight, wallThickness),
                wallMaterial
            );
            frontWall.position.set(0, wallHeight/2, room.depth/2);
            roomGroup.add(frontWall);

            // Back wall
            const backWall = new THREE.Mesh(
                new THREE.BoxGeometry(room.width, wallHeight, wallThickness),
                wallMaterial
            );
            backWall.position.set(0, wallHeight/2, -room.depth/2);
            roomGroup.add(backWall);

            // Left wall
            const leftWall = new THREE.Mesh(
                new THREE.BoxGeometry(wallThickness, wallHeight, room.depth),
                wallMaterial
            );
            leftWall.position.set(-room.width/2, wallHeight/2, 0);
            roomGroup.add(leftWall);

            // Right wall
            const rightWall = new THREE.Mesh(
                new THREE.BoxGeometry(wallThickness, wallHeight, room.depth),
                wallMaterial
            );
            rightWall.position.set(room.width/2, wallHeight/2, 0);
            roomGroup.add(rightWall);

            roomGroup.position.set(room.x, 0, room.z);
            scene.add(roomGroup);

            // Room label
            this.createTextLabel(scene, room.name, room.x, 5, room.z);
        });
    }

    createSecurityCameras(scene) {
        const cameraPositions = [
            { x: -10, y: 3.5, z: -10 },
            { x: 10, y: 3.5, z: -10 },
            { x: -10, y: 3.5, z: 10 },
            { x: 10, y: 3.5, z: 10 },
            { x: 0, y: 3.5, z: 0 }
        ];

        cameraPositions.forEach((pos, index) => {
            const cameraGroup = new THREE.Group();
            
            // Camera body
            const cameraGeometry = new THREE.BoxGeometry(0.3, 0.2, 0.3);
            const cameraMaterial = new THREE.MeshLambertMaterial({ color: 0x333333 });
            const camera = new THREE.Mesh(cameraGeometry, cameraMaterial);
            camera.castShadow = true;
            cameraGroup.add(camera);

            // Camera lens
            const lensGeometry = new THREE.CylinderGeometry(0.05, 0.05, 0.1);
            const lensMaterial = new THREE.MeshLambertMaterial({ color: 0x000000 });
            const lens = new THREE.Mesh(lensGeometry, lensMaterial);
            lens.rotation.x = Math.PI / 2;
            lens.position.z = 0.2;
            cameraGroup.add(lens);

            // Status indicator
            const statusGeometry = new THREE.SphereGeometry(0.03);
            const statusMaterial = new THREE.MeshLambertMaterial({ 
                color: 0x00ff00,
                emissive: 0x004400
            });
            const status = new THREE.Mesh(statusGeometry, statusMaterial);
            status.position.set(0.1, 0.1, 0.1);
            cameraGroup.add(status);

            cameraGroup.position.set(pos.x, pos.y, pos.z);
            cameraGroup.userData = { type: 'camera', id: index, status: 'online' };
            scene.add(cameraGroup);
        });
    }

    createUserIndicators(scene) {
        const userPositions = [
            { x: -6, z: -6 },
            { x: 4, z: -6 },
            { x: -6, z: 4 },
            { x: 4, z: 4 },
            { x: 0, z: 0 }
        ];

        userPositions.forEach((pos, index) => {
            const userGeometry = new THREE.CylinderGeometry(0.3, 0.3, 1.8);
            const userMaterial = new THREE.MeshLambertMaterial({ 
                color: 0x00ff88,
                transparent: true,
                opacity: 0.7
            });
            const user = new THREE.Mesh(userGeometry, userMaterial);
            user.position.set(pos.x, 0.9, pos.z);
            user.castShadow = true;
            user.userData = { type: 'user', id: index };
            scene.add(user);

            // Animate users
            const animate = () => {
                user.position.y = 0.9 + Math.sin(Date.now() * 0.001 + index) * 0.1;
                requestAnimationFrame(animate);
            };
            animate();
        });
    }

    createTextLabel(scene, text, x, y, z) {
        // This would typically use a text geometry or sprite
        // For simplicity, we'll create a placeholder
        const labelGeometry = new THREE.PlaneGeometry(2, 0.5);
        const labelMaterial = new THREE.MeshBasicMaterial({ 
            color: 0xffffff,
            transparent: true,
            opacity: 0.8
        });
        const label = new THREE.Mesh(labelGeometry, labelMaterial);
        label.position.set(x, y, z);
        label.lookAt(0, y, 0);
        scene.add(label);
    }

    resize3DScene() {
        if (!this.threeScene) return;

        const container = document.getElementById('three-container');
        if (!container) return;

        const { camera, renderer } = this.threeScene;
        
        camera.aspect = container.clientWidth / container.clientHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(container.clientWidth, container.clientHeight);
    }

    async loadInitialData() {
        try {
            await Promise.all([
                this.updateOverviewData(),
                this.updateChatbotData(),
                this.updateNavigationData(),
                this.updateSecurityData()
            ]);
        } catch (error) {
            console.error('Error loading initial data:', error);
        }
    }

    startDataUpdates() {
        // Update data every 30 seconds
        this.updateInterval = setInterval(() => {
            this.loadInitialData();
        }, 30000);
        
        // Check and refresh FCM token every 30 minutes
        this.tokenRefreshInterval = setInterval(() => {
            this.autoUpdateFCMToken();
        }, 30 * 60 * 1000);
    }

    async updateOverviewData() {
        try {
            const data = await this.fetchData('dashboard/overview');
            
            if (data && data.status === 'success') {
                const metrics = data.data.current_metrics;
                const systemStatus = data.data.systems_status;
                
                // Update metric values
                this.updateElement('active-users', metrics.active_users);
                this.updateElement('nav-requests', metrics.navigation_requests);
                this.updateElement('security-alerts', metrics.security_alerts);
                this.updateElement('glass-break-alerts', metrics.glass_break_alerts);
                
                // Update system status indicators
                this.updateSystemStatus('chatbot-status', systemStatus.chatbot);
                this.updateSystemStatus('navigation-status', systemStatus.navigation);
                this.updateSystemStatus('security-status', systemStatus.security);
                
                // Update 3D view metrics
                this.updateElement('3d-users', metrics.active_users);
                this.updateElement('3d-cameras', 5); // Fixed number of cameras
                this.updateElement('3d-alerts', metrics.security_alerts);
                
                // Update overview chart
                this.updateOverviewChart(data.data);
            }
        } catch (error) {
            console.error('Error updating overview data:', error);
        }
    }

    async fetchData(endpoint) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/${endpoint}`);
            
            // Check if redirected to login page
            if (response.redirected && response.url.includes('login')) {
                window.location.href = '/login';
                return null;
            }
            
            if (response.status === 401) {
                // Unauthorized, redirect to login
                window.location.href = '/login';
                return null;
            }
            
            return await response.json();
        } catch (error) {
            console.error(`Error fetching ${endpoint}:`, error);
            return null;
        }
    }
    
    async updateChatbotData() {
        try {
            const data = await this.fetchData('chatbot/metrics');
            
            if (data && data.status === 'success') {
                this.updateChatbotCharts(data.data);
            }
        } catch (error) {
            console.error('Error updating chatbot data:', error);
        }
    }

    async updateNavigationData() {
        try {
            const data = await this.fetchData('navigation/metrics');
            
            if (data && data.status === 'success') {
                this.updateNavigationCharts(data.data);
            }
        } catch (error) {
            console.error('Error updating navigation data:', error);
        }
    }

    async updateSecurityData() {
        try {
            const metricsData = await this.fetchData('security/metrics');
            const eventsData = await this.fetchData('security/glass-break/events');
            
            if (metricsData && metricsData.status === 'success') {
                this.updateSecurityCharts(metricsData.data);
            }
            
            if (eventsData && eventsData.status === 'success') {
                this.updateGlassBreakEvents(eventsData.data);
            }
        } catch (error) {
            console.error('Error updating security data:', error);
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }

    updateSystemStatus(elementId, status) {
        const element = document.getElementById(elementId);
        if (element) {
            element.classList.toggle('offline', status !== 'online');
        }
    }

    updateOverviewChart(data) {
        const chart = this.charts['overview-chart'];
        if (!chart) return;

        const now = new Date();
        const labels = [];
        const datasets = [
            {
                label: 'Active Users',
                data: [],
                borderColor: '#00ff88',
                backgroundColor: 'rgba(0, 255, 136, 0.1)',
                tension: 0.4
            },
            {
                label: 'Navigation Requests',
                data: [],
                borderColor: '#00d4ff',
                backgroundColor: 'rgba(0, 212, 255, 0.1)',
                tension: 0.4
            },
            {
                label: 'Security Alerts',
                data: [],
                borderColor: '#ff4444',
                backgroundColor: 'rgba(255, 68, 68, 0.1)',
                tension: 0.4
            }
        ];

        // Generate sample time series data
        for (let i = 23; i >= 0; i--) {
            const time = new Date(now.getTime() - i * 60 * 60 * 1000);
            labels.push(time.getHours() + ':00');
            
            datasets[0].data.push(Math.floor(Math.random() * 50) + 50);
            datasets[1].data.push(Math.floor(Math.random() * 30) + 10);
            datasets[2].data.push(Math.floor(Math.random() * 5));
        }

        chart.data.labels = labels;
        chart.data.datasets = datasets;
        chart.update();
    }

    updateChatbotCharts(data) {
        // Update conversations chart
        this.updateTimeSeriesChart('chatbot-conversations-chart', data, 'conversations', '#00ff88');
        
        // Update response time chart
        this.updateTimeSeriesChart('chatbot-response-chart', data, 'avg_response_time', '#00d4ff');
        
        // Update accuracy chart
        this.updateTimeSeriesChart('chatbot-accuracy-chart', data, 'intent_accuracy', '#ffff00', true);
        
        // Update sentiment chart
        this.updateSentimentChart(data);
    }

    updateNavigationCharts(data) {
        this.updateTimeSeriesChart('nav-accuracy-chart', data, 'accuracy', '#00ff88', true);
        this.updateTimeSeriesChart('nav-completion-chart', data, 'completion_rate', '#00d4ff', true);
        this.updateTimeSeriesChart('nav-duration-chart', data, 'avg_duration', '#ffff00');
    }

    updateSecurityCharts(data) {
        this.updateTimeSeriesChart('security-alerts-chart', data, 'alerts_count', '#ff4444');
        this.updateTimeSeriesChart('security-access-chart', data, 'access_attempts', '#00d4ff');
        this.updateTimeSeriesChart('security-camera-chart', data, 'camera_status', '#00ff88', true);
    }

    updateTimeSeriesChart(chartId, data, field, color, isPercentage = false) {
        const chart = this.charts[chartId];
        if (!chart || !data.length) return;

        const labels = data.slice(-20).map(item => {
            const date = new Date(item.timestamp);
            return date.getHours() + ':' + date.getMinutes().toString().padStart(2, '0');
        });

        const values = data.slice(-20).map(item => {
            let value = item[field];
            return isPercentage ? (value * 100).toFixed(1) : value;
        });

        chart.data.labels = labels;
        chart.data.datasets = [{
            label: field.replace('_', ' ').toUpperCase(),
            data: values,
            borderColor: color,
            backgroundColor: color + '20',
            tension: 0.4,
            fill: chart.config.type === 'line'
        }];

        chart.update();
    }

    updateSentimentChart(data) {
        const chart = this.charts['chatbot-sentiment-chart'];
        if (!chart || !data.length) return;

        const avgSentiment = data.reduce((sum, item) => sum + item.sentiment_score, 0) / data.length;
        
        chart.data.labels = ['Positive', 'Neutral', 'Negative'];
        chart.data.datasets = [{
            data: [
                (avgSentiment * 100).toFixed(1),
                ((1 - Math.abs(avgSentiment - 0.5) * 2) * 100).toFixed(1),
                ((1 - avgSentiment) * 100).toFixed(1)
            ],
            backgroundColor: ['#00ff88', '#ffff00', '#ff4444'],
            borderWidth: 2,
            borderColor: '#ffffff'
        }];

        chart.update();
    }

    updateGlassBreakEvents(events) {
        const container = document.getElementById('glass-break-events');
        if (!container) return;

        container.innerHTML = '';

        if (!events.length) {
            container.innerHTML = '<p style="text-align: center; opacity: 0.7;">No recent glass break events</p>';
            return;
        }

        events.slice(0, 5).forEach(event => {
            const eventDiv = document.createElement('div');
            eventDiv.className = 'alert-item';
            
            const severityClass = `severity-${event.severity}`;
            
            eventDiv.innerHTML = `
                <div>
                    <strong>${event.location}</strong><br>
                    <small>Device: ${event.device_id}</small><br>
                    <small>${new Date(event.timestamp).toLocaleString()}</small>
                </div>
                <div class="alert-severity ${severityClass}">
                    ${event.severity.toUpperCase()}
                </div>
            `;
            
            container.appendChild(eventDiv);
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const dashboard = new DashboardManager();
    
    // Make dashboard available globally for debugging and manual permission request
    window.dashboard = dashboard;
    window.checkNotifications = () => dashboard.checkNotificationStatus();
    window.requestNotifications = () => dashboard.requestNotificationPermissionAfterLogin();
    
    console.log('✅ SenEdge Dashboard initialized successfully');
    console.log('🔔 FCM token auto-update enabled');
});
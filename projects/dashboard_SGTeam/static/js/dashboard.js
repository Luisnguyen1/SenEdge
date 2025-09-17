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
        this.navigationImages = [];
        this.currentImageOffset = 0;
        this.imagesPerPage = 12;
        this.currentFilters = {
            device_id: '',
            hours: 24
        };
        
        this.init();
    }

    init() {
        this.setupNavigation();
        this.setupCharts();
        this.setup3DScene();
        this.startDataUpdates();
        this.loadInitialData();
        this.setupCameraImageHandlers();
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
                sections.forEach(section => {
                    section.style.display = 'none';
                });
                
                // Show target section
                const sectionName = link.getAttribute('data-section');
                const targetSection = document.getElementById(sectionName + '-section');
                if (targetSection) {
                    targetSection.style.display = 'block';
                    
                    // If switching to 3D section, ensure scene is properly rendered
                    if (sectionName === '3d-view' && this.threeScene) {
                        setTimeout(() => {
                            this.threeScene.resize();
                        }, 100);
                    }
                    
                    // If switching to navigation section, load camera images
                    if (sectionName === 'navigation') {
                        this.loadNavigationImages();
                    }
                }
            });
        });
    }

    setupCharts() {
        // Setup Overview Chart
        this.setupOverviewChart();
        
        // Setup Chatbot Charts
        this.setupChatbotCharts();
        
        // Setup Navigation Charts
        this.setupNavigationCharts();
        
        // Setup Security Charts  
        this.setupSecurityCharts();
    }

    setupOverviewChart() {
        const ctx = document.getElementById('overview-chart');
        if (!ctx) {
            console.warn('Overview chart canvas not found');
            return;
        }
        
        this.charts.overview = new Chart(ctx.getContext('2d'), {
            type: 'line',
            data: {
                labels: ['6h ago', '5h ago', '4h ago', '3h ago', '2h ago', '1h ago', 'Now'],
                datasets: [{
                    label: 'Active Users',
                    data: [12, 19, 3, 5, 2, 3, 8],
                    borderColor: '#00ff88',
                    backgroundColor: 'rgba(0, 255, 136, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Navigation Requests',
                    data: [8, 12, 15, 10, 14, 18, 22],
                    borderColor: '#00d4ff',
                    backgroundColor: 'rgba(0, 212, 255, 0.1)',
                    tension: 0.4
                }, {
                    label: 'Security Alerts',
                    data: [2, 1, 0, 3, 1, 0, 2],
                    borderColor: '#ff4444',
                    backgroundColor: 'rgba(255, 68, 68, 0.1)',
                    tension: 0.4
                }]
            },
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
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    },
                    y: {
                        ticks: {
                            color: '#ffffff'
                        },
                        grid: {
                            color: 'rgba(255, 255, 255, 0.1)'
                        }
                    }
                }
            }
        });
    }

    setupChatbotCharts() {
        // Conversations Chart
        const conversationsCtx = document.getElementById('chatbot-conversations-chart');
        if (conversationsCtx) {
            this.charts.chatbotConversations = new Chart(conversationsCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Completed', 'In Progress', 'Failed'],
                    datasets: [{
                        data: [75, 20, 5],
                        backgroundColor: ['#00ff88', '#ffa500', '#ff4444'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#ffffff'
                            }
                        }
                    }
                }
            });
        }

        // Response Time Chart
        const responseCtx = document.getElementById('chatbot-response-chart');
        if (responseCtx) {
            this.charts.chatbotResponse = new Chart(responseCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                    datasets: [{
                        label: 'Response Time (ms)',
                        data: [120, 100, 90, 110, 95, 105],
                        borderColor: '#00d4ff',
                        backgroundColor: 'rgba(0, 212, 255, 0.1)',
                        tension: 0.4
                    }]
                },
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
            });
        }

        // Accuracy Chart
        const accuracyCtx = document.getElementById('chatbot-accuracy-chart');
        if (accuracyCtx) {
            this.charts.chatbotAccuracy = new Chart(accuracyCtx.getContext('2d'), {
                type: 'radar',
                data: {
                    labels: ['Intent Recognition', 'Response Quality', 'Context Understanding', 'Task Completion', 'User Satisfaction'],
                    datasets: [{
                        label: 'Accuracy %',
                        data: [92, 88, 85, 90, 87],
                        borderColor: '#00ff88',
                        backgroundColor: 'rgba(0, 255, 136, 0.2)',
                        pointBackgroundColor: '#00ff88'
                    }]
                },
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
                        r: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                color: '#ffffff'
                            },
                            grid: {
                                color: 'rgba(255, 255, 255, 0.1)'
                            }
                        }
                    }
                }
            });
        }

        // Sentiment Chart
        const sentimentCtx = document.getElementById('chatbot-sentiment-chart');
        if (sentimentCtx) {
            this.charts.chatbotSentiment = new Chart(sentimentCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: ['Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative'],
                    datasets: [{
                        label: 'Sentiment Analysis',
                        data: [35, 40, 20, 4, 1],
                        backgroundColor: ['#00ff88', '#90ee90', '#ffa500', '#ff6b6b', '#ff4444']
                    }]
                },
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
            });
        }
    }

    setupNavigationCharts() {
        // Navigation Accuracy Chart
        const accuracyCtx = document.getElementById('nav-accuracy-chart');
        if (accuracyCtx) {
            this.charts.navAccuracy = new Chart(accuracyCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Successful', 'Failed', 'In Progress'],
                    datasets: [{
                        data: [85, 10, 5],
                        backgroundColor: ['#00ff88', '#ff4444', '#ffa500'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#ffffff'
                            }
                        }
                    }
                }
            });
        }

        // Completion Rate Chart
        const completionCtx = document.getElementById('nav-completion-chart');
        if (completionCtx) {
            this.charts.navCompletion = new Chart(completionCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    datasets: [{
                        label: 'Completion Rate %',
                        data: [92, 88, 94, 89, 91, 86, 93],
                        borderColor: '#00d4ff',
                        backgroundColor: 'rgba(0, 212, 255, 0.1)',
                        tension: 0.4
                    }]
                },
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
            });
        }

        // Duration Chart
        const durationCtx = document.getElementById('nav-duration-chart');
        if (durationCtx) {
            this.charts.navDuration = new Chart(durationCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: ['< 1 min', '1-2 min', '2-5 min', '5-10 min', '> 10 min'],
                    datasets: [{
                        label: 'Number of Requests',
                        data: [45, 62, 38, 15, 8],
                        backgroundColor: '#00ff88'
                    }]
                },
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
            });
        }
    }

    setupSecurityCharts() {
        // Security Alerts Chart
        const alertsCtx = document.getElementById('security-alerts-chart');
        if (alertsCtx) {
            this.charts.securityAlerts = new Chart(alertsCtx.getContext('2d'), {
                type: 'bar',
                data: {
                    labels: ['Today', 'Yesterday', '2 Days Ago', '3 Days Ago', '4 Days Ago'],
                    datasets: [{
                        label: 'Security Alerts',
                        data: [3, 7, 2, 5, 1],
                        backgroundColor: '#ff4444',
                        borderColor: '#ff2222',
                        borderWidth: 1
                    }]
                },
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
                            beginAtZero: true,
                            ticks: { color: '#ffffff' },
                            grid: { color: 'rgba(255, 255, 255, 0.1)' }
                        }
                    }
                }
            });
        }

        // Access Attempts Chart
        const accessCtx = document.getElementById('security-access-chart');
        if (accessCtx) {
            this.charts.securityAccess = new Chart(accessCtx.getContext('2d'), {
                type: 'line',
                data: {
                    labels: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'],
                    datasets: [{
                        label: 'Authorized',
                        data: [12, 8, 45, 62, 48, 25],
                        borderColor: '#00ff88',
                        backgroundColor: 'rgba(0, 255, 136, 0.1)',
                        tension: 0.4
                    }, {
                        label: 'Unauthorized',
                        data: [2, 1, 3, 5, 2, 1],
                        borderColor: '#ff4444',
                        backgroundColor: 'rgba(255, 68, 68, 0.1)',
                        tension: 0.4
                    }]
                },
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
            });
        }

        // Camera Status Chart
        const cameraCtx = document.getElementById('security-camera-chart');
        if (cameraCtx) {
            this.charts.securityCamera = new Chart(cameraCtx.getContext('2d'), {
                type: 'doughnut',
                data: {
                    labels: ['Online', 'Offline', 'Maintenance'],
                    datasets: [{
                        data: [24, 2, 1],
                        backgroundColor: ['#00ff88', '#ff4444', '#ffa500'],
                        borderWidth: 2,
                        borderColor: '#ffffff'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            labels: {
                                color: '#ffffff'
                            }
                        }
                    }
                }
            });
        }
    }

    setup3DScene() {
        const container = document.getElementById('three-container');
        if (!container) {
            console.warn('3D container not found');
            return;
        }

        this.threeScene = new Three3DScene(container);
        this.threeScene.init();
    }

    async loadInitialData() {
        try {
            // Load dashboard overview
            const overviewResponse = await fetch(`${this.apiBaseUrl}/dashboard/overview`);
            if (overviewResponse.ok) {
                const overviewData = await overviewResponse.json();
                if (overviewData.status === 'success') {
                    this.updateDashboardData(overviewData.data);
                }
            }
            
            // Load glass break events
            const eventsResponse = await fetch(`${this.apiBaseUrl}/security/glass-break/events`);
            if (eventsResponse.ok) {
                const eventsData = await eventsResponse.json();
                if (eventsData.status === 'success') {
                    this.updateGlassBreakEvents(eventsData.data);
                }
            } else {
                // Show sample data if API is not available
                this.updateGlassBreakEvents([
                    {
                        id: 1,
                        severity: 'high',
                        location: 'Building A - Floor 2 - Window 205',
                        device_id: 'GBS-001',
                        timestamp: new Date(Date.now() - 30 * 60 * 1000).toISOString(),
                        status: 'Investigating'
                    },
                    {
                        id: 2,
                        severity: 'medium',
                        location: 'Building B - Floor 1 - Entrance Glass',
                        device_id: 'GBS-002',
                        timestamp: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
                        status: 'Resolved'
                    },
                    {
                        id: 3,
                        severity: 'low',
                        location: 'Building C - Conference Room 3',
                        device_id: 'GBS-003',
                        timestamp: new Date(Date.now() - 5 * 60 * 60 * 1000).toISOString(),
                        status: 'False Alarm'
                    }
                ]);
            }
            
            // Load metrics data
            await this.loadMetrics();
            
        } catch (error) {
            console.error('Error loading initial data:', error);
            // Show sample data if there's an error
            this.updateDashboardData({
                current_metrics: {
                    active_users: 42,
                    conversations: 156,
                    navigation_requests: 89,
                    security_alerts: 3
                }
            });
        }
    }

    async loadMetrics() {
        try {
            // Load chatbot metrics
            const chatbotResponse = await fetch(`${this.apiBaseUrl}/chatbot/metrics`);
            if (chatbotResponse.ok) {
                const chatbotData = await chatbotResponse.json();
                if (chatbotData.status === 'success') {
                    this.updateChatbotMetrics(chatbotData.data);
                }
            }

            // Load navigation metrics
            const navResponse = await fetch(`${this.apiBaseUrl}/navigation/metrics`);
            if (navResponse.ok) {
                const navData = await navResponse.json();
                if (navData.status === 'success') {
                    this.updateNavigationMetrics(navData.data);
                }
            }

            // Load security metrics
            const securityResponse = await fetch(`${this.apiBaseUrl}/security/metrics`);
            if (securityResponse.ok) {
                const securityData = await securityResponse.json();
                if (securityData.status === 'success') {
                    this.updateSecurityMetrics(securityData.data);
                }
            }

        } catch (error) {
            console.error('Error loading metrics:', error);
        }
    }

    updateDashboardData(data) {
        // Update metrics cards if they exist
        if (data.current_metrics) {
            this.updateMetricCard('active-users', data.current_metrics.active_users || 0);
            this.updateMetricCard('nav-requests', data.current_metrics.navigation_requests || 0);
            this.updateMetricCard('security-alerts', data.current_metrics.security_alerts || 0);
            this.updateMetricCard('glass-break-alerts', data.current_metrics.glass_break_alerts || 0);
        }

        // Update 3D metrics
        this.updateMetricCard('3d-users', data.current_metrics?.active_users || 0);
        this.updateMetricCard('3d-cameras', 27); // Sample data
        this.updateMetricCard('3d-alerts', data.current_metrics?.security_alerts || 0);
    }

    updateChatbotMetrics(data) {
        if (!data || data.length === 0) return;
        
        const latest = data[0]; // Most recent data
        this.updateChatbotChart(latest);
    }

    updateNavigationMetrics(data) {
        if (!data || data.length === 0) return;
        
        const latest = data[0]; // Most recent data
        this.updateNavigationChart(latest);
    }

    updateSecurityMetrics(data) {
        if (!data || data.length === 0) return;
        
        const latest = data[0]; // Most recent data
        this.updateSecurityChart(latest);
    }

    updateMetricCard(id, value) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value.toLocaleString();
        }
    }

    updateChatbotChart(data) {
        if (!data || !this.charts.chatbot) return;
        
        const chart = this.charts.chatbot;
        const now = new Date().toLocaleTimeString();
        
        // Add new data point
        chart.data.labels.push(now);
        chart.data.datasets[0].data.push(data.avg_response_time);
        chart.data.datasets[1].data.push(data.active_users);
        
        // Keep only last 20 data points
        if (chart.data.labels.length > 20) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
            chart.data.datasets[1].data.shift();
        }
        
        chart.update('none');
    }

    updateNavigationChart(data) {
        if (!data || !this.charts.navigation) return;
        
        const chart = this.charts.navigation;
        const requests = data.navigation_requests || 0;
        const accuracy = data.accuracy || 0;
        
        const successful = Math.round(requests * accuracy);
        const failed = requests - successful;
        
        chart.data.datasets[0].data = [successful, failed, 0];
        chart.update('none');
    }

    updateSecurityChart(data) {
        if (!data || !this.charts.security) return;
        
        const chart = this.charts.security;
        
        // Simulate daily data (in real app, this would come from API)
        const alerts = data.alerts_count || 0;
        chart.data.datasets[0].data.shift();
        chart.data.datasets[0].data.push(alerts);
        
        chart.update('none');
    }

    updateGlassBreakEvents(events) {
        const container = document.getElementById('glass-break-events');
        if (!container || !events) return;
        
        container.innerHTML = '';
        
        events.slice(0, 10).forEach(event => {
            const eventElement = this.createEventElement(event);
            container.appendChild(eventElement);
        });
    }

    createEventElement(event) {
        const div = document.createElement('div');
        div.className = 'glass-break-event';
        
        const severityClass = this.getSeverityClass(event.severity);
        const timestamp = new Date(event.timestamp).toLocaleString();
        
        div.innerHTML = `
            <div class="event-header">
                <span class="event-severity ${severityClass}">${event.severity.toUpperCase()}</span>
                <span class="event-time">${timestamp}</span>
            </div>
            <div class="event-details">
                <strong>Location:</strong> ${event.location}<br>
                <strong>Device:</strong> ${event.device_id}<br>
                <strong>Status:</strong> ${event.status}
            </div>
        `;
        
        // Add styles for glass break events if not exists
        if (!document.querySelector('#glass-break-styles')) {
            const styles = document.createElement('style');
            styles.id = 'glass-break-styles';
            styles.textContent = `
                .glass-break-event {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 8px;
                    padding: 12px;
                    margin-bottom: 8px;
                    border-left: 4px solid #e74c3c;
                }
                
                .event-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 8px;
                }
                
                .event-severity {
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: bold;
                }
                
                .severity-low { background: #f39c12; }
                .severity-medium { background: #e67e22; }
                .severity-high { background: #e74c3c; }
                .severity-critical { background: #8e44ad; }
                
                .event-time {
                    font-size: 12px;
                    opacity: 0.8;
                }
                
                .event-details {
                    font-size: 14px;
                    line-height: 1.4;
                }
            `;
            document.head.appendChild(styles);
        }
        
        return div;
    }

    getSeverityClass(severity) {
        const severityMap = {
            'low': 'severity-low',
            'medium': 'severity-medium',
            'high': 'severity-high',
            'critical': 'severity-critical'
        };
        return severityMap[severity] || 'severity-medium';
    }

    startDataUpdates() {
        // Update data every 30 seconds
        this.updateInterval = setInterval(() => {
            this.loadInitialData();
        }, 30000);
    }

    setupCameraImageHandlers() {
        // Setup modal close handler
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeImageModal();
            }
        });
        
        // Close modal when clicking outside
        document.addEventListener('click', (e) => {
            const modal = document.getElementById('image-modal');
            if (modal && e.target === modal) {
                this.closeImageModal();
            }
        });
        
        // Auto-refresh navigation images every 60 seconds when on navigation section
        setInterval(() => {
            const activeSection = document.querySelector('.nav-link.active');
            if (activeSection && activeSection.getAttribute('data-section') === 'navigation') {
                this.loadNavigationImages(false); // Silent refresh
            }
        }, 60000);
    }

    async loadNavigationImages(showLoading = true) {
        try {
            if (showLoading) {
                this.showCameraLoading();
            }
            
            const params = new URLSearchParams({
                limit: this.imagesPerPage,
                hours: this.currentFilters.hours
            });
            
            if (this.currentFilters.device_id) {
                params.append('device_id', this.currentFilters.device_id);
            }
            
            const response = await fetch(`${this.apiBaseUrl}/navigation/images?${params}`);
            
            if (response.ok) {
                const result = await response.json();
                if (result.status === 'success') {
                    this.navigationImages = result.data;
                    this.currentImageOffset = 0;
                    this.renderCameraImages();
                    this.updateCameraStats(result);
                    this.updateDeviceFilter();
                } else {
                    console.error('Failed to load navigation images:', result.message);
                    this.showNoCameraImages('Error loading images: ' + result.message);
                }
            } else {
                console.error('HTTP error loading navigation images:', response.status);
                this.showNoCameraImages('Failed to connect to camera service');
            }
        } catch (error) {
            console.error('Error loading navigation images:', error);
            this.showNoCameraImages('Error loading camera images');
        }
    }

    async loadMoreImages() {
        try {
            const offset = this.navigationImages.length;
            const params = new URLSearchParams({
                limit: this.imagesPerPage,
                hours: this.currentFilters.hours,
                offset: offset
            });
            
            if (this.currentFilters.device_id) {
                params.append('device_id', this.currentFilters.device_id);
            }
            
            const response = await fetch(`${this.apiBaseUrl}/navigation/images?${params}`);
            
            if (response.ok) {
                const result = await response.json();
                if (result.status === 'success') {
                    this.navigationImages = [...this.navigationImages, ...result.data];
                    this.renderCameraImages();
                    this.updateCameraStats({ data: this.navigationImages, count: this.navigationImages.length });
                }
            }
        } catch (error) {
            console.error('Error loading more images:', error);
        }
    }

    renderCameraImages() {
        const container = document.getElementById('camera-images-container');
        if (!container) return;
        
        if (this.navigationImages.length === 0) {
            this.showNoCameraImages();
            return;
        }
        
        container.innerHTML = '';
        
        this.navigationImages.forEach((image, index) => {
            const imageCard = this.createCameraImageCard(image, index);
            container.appendChild(imageCard);
        });
        
        // Show/hide load more button
        const loadMoreBtn = document.getElementById('load-more-btn');
        if (loadMoreBtn) {
            loadMoreBtn.style.display = this.navigationImages.length >= this.imagesPerPage ? 'block' : 'none';
        }
    }

    createCameraImageCard(image, index) {
        const card = document.createElement('div');
        card.className = 'camera-image-card';
        card.onclick = () => this.openImageModal(image);
        
        const timestamp = new Date(image.timestamp).toLocaleString();
        const processedData = image.processed_data ? JSON.parse(image.processed_data) : null;
        
        card.innerHTML = `
            ${image.image_data ? 
                `<img class="camera-image" src="${image.image_data}" alt="Camera ${image.device_id}" loading="lazy">` :
                `<div class="camera-image" style="background: #333; display: flex; align-items: center; justify-content: center; color: #999;">
                    <span>📷 Image not available</span>
                 </div>`
            }
            <div class="camera-image-info">
                <div class="camera-device">📹 ${image.device_id}</div>
                <div class="camera-location">📍 ${image.location || 'Unknown location'}</div>
                <div class="camera-timestamp">🕒 ${timestamp}</div>
                ${processedData ? 
                    `<div class="camera-processed-data">🔍 ${Object.keys(processedData).length} data points</div>` :
                    ''
                }
            </div>
        `;
        
        return card;
    }

    updateCameraStats(result) {
        document.getElementById('total-images').textContent = result.count || 0;
        
        // Count unique devices
        const uniqueDevices = new Set(this.navigationImages.map(img => img.device_id));
        document.getElementById('active-devices').textContent = uniqueDevices.size;
        
        // Show last update time
        if (this.navigationImages.length > 0) {
            const lastUpdate = new Date(this.navigationImages[0].timestamp).toLocaleTimeString();
            document.getElementById('last-update').textContent = lastUpdate;
        } else {
            document.getElementById('last-update').textContent = '-';
        }
    }

    updateDeviceFilter() {
        const deviceFilter = document.getElementById('device-filter');
        if (!deviceFilter) return;
        
        // Get unique devices
        const uniqueDevices = [...new Set(this.navigationImages.map(img => img.device_id))];
        
        // Clear and rebuild options
        deviceFilter.innerHTML = '<option value="">All Devices</option>';
        uniqueDevices.forEach(device => {
            const option = document.createElement('option');
            option.value = device;
            option.textContent = device;
            if (device === this.currentFilters.device_id) {
                option.selected = true;
            }
            deviceFilter.appendChild(option);
        });
    }

    showCameraLoading() {
        const container = document.getElementById('camera-images-container');
        if (container) {
            container.innerHTML = `
                <div class="loading-placeholder">
                    <div class="loading-spinner"></div>
                    <p>Loading camera images...</p>
                </div>
            `;
        }
    }

    showNoCameraImages(message = 'No camera images found') {
        const container = document.getElementById('camera-images-container');
        if (container) {
            container.innerHTML = `
                <div class="no-images-message">
                    <h3>📷 ${message}</h3>
                    <p>Images will appear here when ESP32 cameras upload processed data.</p>
                    <button onclick="refreshCameraImages()" class="refresh-btn" style="margin-top: 1rem;">
                        🔄 Try Again
                    </button>
                </div>
            `;
        }
        
        // Hide load more button
        const loadMoreBtn = document.getElementById('load-more-btn');
        if (loadMoreBtn) {
            loadMoreBtn.style.display = 'none';
        }
    }

    openImageModal(image) {
        const modal = document.getElementById('image-modal');
        const modalImage = document.getElementById('modal-image');
        const modalInfo = document.getElementById('modal-info');
        
        if (!modal || !modalImage || !modalInfo) return;
        
        modalImage.src = image.image_data || '';
        modalImage.alt = `Camera Image from ${image.device_id}`;
        
        const timestamp = new Date(image.timestamp).toLocaleString();
        const processedData = image.processed_data ? JSON.parse(image.processed_data) : null;
        
        modalInfo.innerHTML = `
            <h3>📹 ${image.device_id}</h3>
            <div style="margin-bottom: 1.5rem;">
                <p><strong>📍 Location:</strong><br>${image.location || 'Unknown location'}</p>
                <p><strong>🕒 Timestamp:</strong><br>${timestamp}</p>
                <p><strong>📁 File Size:</strong><br>${this.formatFileSize(image.image_size)}</p>
                <p><strong>🏷️ Image Name:</strong><br>${image.image_name}</p>
                <p><strong>📊 Status:</strong><br><span style="color: ${image.status === 'active' ? '#00ff88' : '#ffa500'}">${image.status}</span></p>
            </div>
            ${processedData ? `
                <div style="margin-top: 1.5rem;">
                    <h4 style="color: #00d4ff; margin-bottom: 1rem; border-bottom: 1px solid #00d4ff; padding-bottom: 0.5rem;">
                        🔍 Processed Data Analysis
                    </h4>
                    <div style="background: rgba(0, 212, 255, 0.1); padding: 1rem; border-radius: 8px; margin-bottom: 1rem; border-left: 4px solid #00d4ff;">
                        ${this.formatProcessedDataSummary(processedData)}
                    </div>
                    <details style="margin-top: 1rem;">
                        <summary style="cursor: pointer; color: #00ff88; margin-bottom: 0.5rem; font-weight: bold;">
                            📋 Raw Data (Click to expand)
                        </summary>
                        <pre style="background: rgba(0, 0, 0, 0.4); padding: 1rem; border-radius: 6px; margin-top: 0.5rem; overflow-x: auto; font-size: 0.85rem; line-height: 1.4;">${JSON.stringify(processedData, null, 2)}</pre>
                    </details>
                </div>
            ` : `
                <div style="margin-top: 1.5rem;">
                    <p style="color: rgba(255, 255, 255, 0.7); font-style: italic;">
                        No processed data available for this image.
                    </p>
                </div>
            `}
        `;
        
        modal.classList.add('active');
        
        // Add keyboard navigation
        modal.focus();
    }

    formatProcessedDataSummary(data) {
        if (!data || typeof data !== 'object') return 'No valid data';
        
        let summary = '';
        
        // Common analysis fields
        if (data.objects && Array.isArray(data.objects)) {
            summary += `<p><strong>🎯 Detected Objects:</strong> ${data.objects.join(', ')}</p>`;
        }
        
        if (data.confidence !== undefined) {
            const confidence = (data.confidence * 100).toFixed(1);
            summary += `<p><strong>🎲 Confidence:</strong> ${confidence}%</p>`;
        }
        
        if (data.motion !== undefined) {
            summary += `<p><strong>🏃 Motion Detected:</strong> ${data.motion ? 'Yes' : 'No'}</p>`;
        }
        
        if (data.faces_count !== undefined) {
            summary += `<p><strong>👥 Faces Count:</strong> ${data.faces_count}</p>`;
        }
        
        if (data.vehicle_count !== undefined) {
            summary += `<p><strong>🚗 Vehicles Count:</strong> ${data.vehicle_count}</p>`;
        }
        
        if (data.timestamp) {
            const processTime = new Date(data.timestamp).toLocaleString();
            summary += `<p><strong>⏱️ Processing Time:</strong> ${processTime}</p>`;
        }
        
        // If no standard fields found, show data count
        if (!summary) {
            const dataKeys = Object.keys(data);
            summary = `<p><strong>📊 Data Fields:</strong> ${dataKeys.length} field(s) - ${dataKeys.join(', ')}</p>`;
        }
        
        return summary || '<p>No summary available</p>';
    }

    closeImageModal() {
        const modal = document.getElementById('image-modal');
        if (modal) {
            modal.classList.remove('active');
            // Clear image src to free memory
            const modalImage = document.getElementById('modal-image');
            if (modalImage) {
                modalImage.src = '';
            }
        }
    }

    formatFileSize(bytes) {
        if (!bytes) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // Cleanup method
    destroy() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        if (this.threeScene) {
            this.threeScene.destroy();
        }
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
    }
}

// Three.js 3D Scene Class
class Three3DScene {
    constructor(container) {
        this.container = container;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.animationId = null;
        this.objects = [];
        
        // Building data for visualization
        this.buildingData = [
            { id: 'building-a', x: -20, z: -20, height: 15, status: 'normal' },
            { id: 'building-b', x: 20, z: -20, height: 12, status: 'alert' },
            { id: 'building-c', x: -20, z: 20, height: 18, status: 'normal' },
            { id: 'building-d', x: 20, z: 20, height: 10, status: 'warning' }
        ];
    }

    init() {
        this.setupScene();
        this.setupCamera();
        this.setupRenderer();
        this.setupLights();
        this.createBuildings();
        this.setupControls();
        this.animate();
        
        // Handle window resize
        window.addEventListener('resize', () => this.resize());
    }

    setupScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a1a);
        this.scene.fog = new THREE.Fog(0x1a1a1a, 50, 200);
    }

    setupCamera() {
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(75, aspect, 0.1, 1000);
        this.camera.position.set(30, 30, 30);
        this.camera.lookAt(0, 0, 0);
    }

    setupRenderer() {
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        this.container.appendChild(this.renderer.domElement);
    }

    setupLights() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
        this.scene.add(ambientLight);
        
        // Directional light
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(50, 50, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);
        
        // Point lights for buildings
        this.buildingData.forEach(building => {
            const light = new THREE.PointLight(this.getStatusColor(building.status), 0.5, 30);
            light.position.set(building.x, building.height + 2, building.z);
            this.scene.add(light);
        });
    }

    createBuildings() {
        // Ground
        const groundGeometry = new THREE.PlaneGeometry(100, 100);
        const groundMaterial = new THREE.MeshLambertMaterial({ color: 0x333333 });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);
        
        // Buildings
        this.buildingData.forEach(building => {
            this.createBuilding(building);
        });
    }

    createBuilding(buildingData) {
        const geometry = new THREE.BoxGeometry(8, buildingData.height, 8);
        const material = new THREE.MeshPhongMaterial({
            color: this.getStatusColor(buildingData.status),
            transparent: true,
            opacity: 0.8
        });
        
        const building = new THREE.Mesh(geometry, material);
        building.position.set(buildingData.x, buildingData.height / 2, buildingData.z);
        building.castShadow = true;
        building.userData = buildingData;
        
        this.scene.add(building);
        this.objects.push(building);
        
        // Add label
        this.addBuildingLabel(buildingData);
    }

    addBuildingLabel(buildingData) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        canvas.width = 256;
        canvas.height = 64;
        
        context.fillStyle = '#ffffff';
        context.font = '20px Arial';
        context.textAlign = 'center';
        context.fillText(buildingData.id.toUpperCase(), 128, 32);
        context.fillText(buildingData.status.toUpperCase(), 128, 52);
        
        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.SpriteMaterial({ map: texture });
        const sprite = new THREE.Sprite(material);
        
        sprite.position.set(buildingData.x, buildingData.height + 5, buildingData.z);
        sprite.scale.set(8, 2, 1);
        
        this.scene.add(sprite);
    }

    getStatusColor(status) {
        const colors = {
            'normal': 0x27ae60,
            'warning': 0xf39c12,
            'alert': 0xe74c3c,
            'critical': 0x8e44ad
        };
        return colors[status] || colors['normal'];
    }

    setupControls() {
        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.25;
            this.controls.enableZoom = true;
        }
    }

    animate() {
        this.animationId = requestAnimationFrame(() => this.animate());
        
        if (this.controls) {
            this.controls.update();
        }
        
        // Rotate buildings slightly
        this.objects.forEach(obj => {
            if (obj.userData && obj.userData.status === 'alert') {
                obj.rotation.y += 0.01;
            }
        });
        
        this.renderer.render(this.scene, this.camera);
    }

    resize() {
        if (!this.camera || !this.renderer) return;
        
        const width = this.container.clientWidth;
        const height = this.container.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    destroy() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }
        
        if (this.renderer) {
            this.renderer.dispose();
            if (this.container.contains(this.renderer.domElement)) {
                this.container.removeChild(this.renderer.domElement);
            }
        }
        
        // Clean up Three.js objects
        this.objects.forEach(obj => {
            if (obj.geometry) obj.geometry.dispose();
            if (obj.material) obj.material.dispose();
        });
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboard = new DashboardManager();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboard) {
        window.dashboard.destroy();
    }
});

// Global functions for HTML event handlers
function refreshCameraImages() {
    if (window.dashboard) {
        window.dashboard.loadNavigationImages(true);
    }
}

function filterCameraImages() {
    if (!window.dashboard) return;
    
    const deviceFilter = document.getElementById('device-filter');
    const timeFilter = document.getElementById('time-filter');
    
    if (deviceFilter && timeFilter) {
        window.dashboard.currentFilters.device_id = deviceFilter.value;
        window.dashboard.currentFilters.hours = parseInt(timeFilter.value);
        window.dashboard.loadNavigationImages(true);
    }
}

function loadMoreImages() {
    if (window.dashboard) {
        window.dashboard.loadMoreImages();
    }
}

function closeImageModal() {
    if (window.dashboard) {
        window.dashboard.closeImageModal();
    }
}
// Admin Panel JavaScript for SmartMall Navigation
class AdminPanel {
    constructor() {
        this.socket = null;
        this.currentPosition = { x: 9, y: 9 };
        this.mapData = null;
        this.positionUpdateCount = 0;
        this.isSimulating = false;
        this.simulationPath = [];
        this.simulationIndex = 0;
        
        this.init();
    }

    init() {
        this.initWebSocket();
        this.bindEvents();
        this.setupKeyboardControls();
        this.updateUI();
        
        console.log('Admin Panel initialized');
    }

    // WebSocket Management
    initWebSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Admin connected to WebSocket');
            this.updateConnectionStatus('connected');
            this.showToast('Connected to server', 'success');
            this.socket.emit('request_position');
        });

        this.socket.on('disconnect', () => {
            console.log('Admin disconnected from WebSocket');
            this.updateConnectionStatus('disconnected');
            this.showToast('Disconnected from server', 'error');
        });

        this.socket.on('map_data', (data) => {
            console.log('Received map data:', data);
            this.mapData = data;
            this.renderMap();
        });

        this.socket.on('position_update', (data) => {
            console.log('Received position update:', data);
            this.handlePositionUpdate(data);
        });

        // Listen for admin-specific position updates
        this.socket.on('admin_position_update', (data) => {
            console.log('Received admin position update:', data);
            this.handleAdminPositionUpdate(data);
        });

        this.socket.on('connect_error', () => {
            this.updateConnectionStatus('error');
            this.showToast('Connection error', 'error');
        });
    }

    // Event Bindings
    bindEvents() {
        // Manual position set
        document.getElementById('setPositionBtn').addEventListener('click', () => {
            this.setManualPosition();
        });

        // Position presets
        document.querySelectorAll('.preset-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const x = parseInt(e.target.getAttribute('data-x'));
                const y = parseInt(e.target.getAttribute('data-y'));
                this.updateUserPosition(x, y);
            });
        });

        // Admin actions
        document.getElementById('resetPositionBtn').addEventListener('click', () => {
            this.resetPosition();
        });

        document.getElementById('simulateMovementBtn').addEventListener('click', () => {
            this.toggleSimulation();
        });

        document.getElementById('clearAllDataBtn').addEventListener('click', () => {
            this.clearAllData();
        });

        // Map controls
        document.getElementById('centerMapBtn').addEventListener('click', () => {
            this.centerMapOnUser();
        });

        document.getElementById('refreshMapBtn').addEventListener('click', () => {
            this.refreshMap();
        });

        document.getElementById('toggleGridBtn').addEventListener('click', () => {
            this.toggleGrid();
        });

        // Manual input validation
        const manualInputs = document.querySelectorAll('#manualX, #manualY');
        manualInputs.forEach(input => {
            input.addEventListener('input', (e) => {
                let value = parseInt(e.target.value);
                if (value < 0) e.target.value = 0;
                if (value > 19) e.target.value = 19;
            });
        });
    }

    // Keyboard Controls
    setupKeyboardControls() {
        document.addEventListener('keydown', (e) => {
            // Only handle arrow keys when admin panel is focused
            if (document.activeElement.tagName === 'INPUT') return;
            
            let newX = this.currentPosition.x;
            let newY = this.currentPosition.y;
            let moved = false;

            switch (e.key) {
                case 'ArrowUp':
                    e.preventDefault();
                    if (newX > 0) {
                        newX--;
                        moved = true;
                    }
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    if (newX < 19) {
                        newX++;
                        moved = true;
                    }
                    break;
                case 'ArrowLeft':
                    e.preventDefault();
                    if (newY > 0) {
                        newY--;
                        moved = true;
                    }
                    break;
                case 'ArrowRight':
                    e.preventDefault();
                    if (newY < 19) {
                        newY++;
                        moved = true;
                    }
                    break;
            }

            if (moved) {
                this.updateUserPosition(newX, newY);
                this.showMovementIndicator();
            }
        });

        // Show keyboard help
        document.addEventListener('keydown', (e) => {
            if (e.key.startsWith('Arrow')) {
                document.getElementById('lastMovement').textContent = new Date().toLocaleTimeString();
            }
        });
    }

    // Position Management
    updateUserPosition(x, y) {
        // Validate bounds
        if (x < 0 || x > 19 || y < 0 || y > 19) {
            this.showToast('Position out of bounds (0-19)', 'error');
            return;
        }

        // Update position immediately for responsive UI
        this.currentPosition = { x, y };
        this.positionUpdateCount++;
        
        // Update UI immediately
        this.updatePositionDisplay();
        this.renderMap();
        
        // Send position update via WebSocket
        this.socket.emit('admin_position_control', {
            position: { x, y },
            timestamp: new Date().toISOString(),
            admin_controlled: true
        });

        // Update status
        document.getElementById('positionUpdates').textContent = this.positionUpdateCount;
        document.getElementById('lastMovement').textContent = new Date().toLocaleTimeString();
        
        console.log(`Admin moved user to position (${x}, ${y})`);
        this.showToast(`Position updated to (${x}, ${y})`, 'success');
    }

    setManualPosition() {
        const x = parseInt(document.getElementById('manualX').value);
        const y = parseInt(document.getElementById('manualY').value);
        
        if (isNaN(x) || isNaN(y)) {
            this.showToast('Please enter valid coordinates', 'error');
            return;
        }
        
        this.updateUserPosition(x, y);
    }

    resetPosition() {
        this.updateUserPosition(9, 9);
        document.getElementById('manualX').value = 9;
        document.getElementById('manualY').value = 9;
        this.showToast('Position reset to center', 'info');
    }

    // Simulation
    toggleSimulation() {
        const btn = document.getElementById('simulateMovementBtn');
        
        if (this.isSimulating) {
            this.stopSimulation();
            btn.innerHTML = '<i class="fas fa-route"></i> Simulate Path Movement';
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-info');
        } else {
            this.startSimulation();
            btn.innerHTML = '<i class="fas fa-stop"></i> Stop Simulation';
            btn.classList.remove('btn-info');
            btn.classList.add('btn-danger');
        }
    }

    startSimulation() {
        // Create a random path for simulation
        this.simulationPath = this.generateRandomPath();
        this.simulationIndex = 0;
        this.isSimulating = true;
        
        this.showToast('Starting movement simulation', 'info');
        this.runSimulation();
    }

    stopSimulation() {
        this.isSimulating = false;
        this.simulationPath = [];
        this.simulationIndex = 0;
        this.showToast('Simulation stopped', 'warning');
    }

    generateRandomPath() {
        const path = [];
        const startX = this.currentPosition.x;
        const startY = this.currentPosition.y;
        
        // Generate a path that visits different areas
        const waypoints = [
            { x: 0, y: 0 },     // Entrance
            { x: 3, y: 3 },     // Shelf area
            { x: 9, y: 9 },     // Center
            { x: 16, y: 7 },    // Another shelf area
            { x: 18, y: 14 },   // Checkout
            { x: startX, y: startY } // Back to start
        ];
        
        // Simple path generation (straight lines between waypoints)
        for (let i = 0; i < waypoints.length - 1; i++) {
            const from = waypoints[i];
            const to = waypoints[i + 1];
            const stepPath = this.generateStraightPath(from, to);
            path.push(...stepPath);
        }
        
        return path;
    }

    generateStraightPath(from, to) {
        const path = [];
        let x = from.x;
        let y = from.y;
        
        while (x !== to.x || y !== to.y) {
            path.push({ x, y });
            
            if (x < to.x) x++;
            else if (x > to.x) x--;
            
            if (y < to.y) y++;
            else if (y > to.y) y--;
        }
        
        path.push({ x: to.x, y: to.y });
        return path;
    }

    runSimulation() {
        if (!this.isSimulating || this.simulationIndex >= this.simulationPath.length) {
            this.stopSimulation();
            return;
        }
        
        const nextPos = this.simulationPath[this.simulationIndex];
        this.updateUserPosition(nextPos.x, nextPos.y);
        this.simulationIndex++;
        
        // Continue simulation after delay
        setTimeout(() => this.runSimulation(), 1000); // 1 second delay
    }

    // Data Management
    clearAllData() {
        if (confirm('Are you sure you want to clear all data? This will reset the user position and clear crowd data.')) {
            // Reset position
            this.resetPosition();
            
            // Clear crowd data via API
            fetch('/api/crowd/clear', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            })
            .then(response => response.json())
            .then(data => {
                console.log('Crowd data cleared:', data);
                this.showToast('All data cleared', 'success');
            })
            .catch(error => {
                console.error('Error clearing data:', error);
                this.showToast('Error clearing data', 'error');
            });
        }
    }

    // UI Updates
    updatePositionDisplay() {
        document.getElementById('currentX').textContent = this.currentPosition.x;
        document.getElementById('currentY').textContent = this.currentPosition.y;
        document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        
        // Update manual inputs
        document.getElementById('manualX').value = this.currentPosition.x;
        document.getElementById('manualY').value = this.currentPosition.y;
    }

    updateConnectionStatus(status) {
        const indicator = document.getElementById('statusIndicator');
        const text = document.getElementById('statusText');
        const wsStatus = document.getElementById('wsStatus');
        
        indicator.className = 'status-dot';
        
        switch (status) {
            case 'connected':
                indicator.classList.add('connected');
                text.textContent = 'Connected';
                wsStatus.textContent = 'Connected';
                break;
            case 'connecting':
                indicator.classList.add('connecting');
                text.textContent = 'Connecting...';
                wsStatus.textContent = 'Connecting';
                break;
            case 'disconnected':
            case 'error':
                text.textContent = 'Disconnected';
                wsStatus.textContent = 'Disconnected';
                break;
        }
    }

    updateUI() {
        this.updatePositionDisplay();
        document.getElementById('positionUpdates').textContent = this.positionUpdateCount;
        document.getElementById('connectedUsers').textContent = '--';
        document.getElementById('wsStatus').textContent = 'Connecting';
        document.getElementById('lastMovement').textContent = '--';
    }

    // Map Rendering
    renderMap() {
        if (!this.mapData) return;
        
        const mapGrid = document.getElementById('mapGrid');
        mapGrid.innerHTML = '';
        
        const grid = this.mapData.map_layout.grid;
        
        for (let row = 0; row < grid.length; row++) {
            for (let col = 0; col < grid[row].length; col++) {
                const cell = document.createElement('div');
                cell.className = 'map-cell';
                cell.setAttribute('data-row', row);
                cell.setAttribute('data-col', col);
                
                // Add cell type class
                const cellType = grid[row][col];
                switch (cellType) {
                    case 0:
                        cell.classList.add('cell-walkable');
                        break;
                    case 1:
                        cell.classList.add('cell-shelf');
                        break;
                    case 2:
                        cell.classList.add('cell-obstacle');
                        break;
                    case 3:
                        cell.classList.add('cell-beacon');
                        break;
                    case 4:
                        cell.classList.add('cell-entrance');
                        break;
                    case 5:
                        cell.classList.add('cell-checkout');
                        break;
                }
                
                // Add user position
                if (row === this.currentPosition.x && col === this.currentPosition.y) {
                    cell.classList.add('cell-user');
                }
                
                // Add tooltip
                cell.title = `(${row}, ${col}) - ${this.getCellTypeText(cellType)}`;
                
                mapGrid.appendChild(cell);
            }
        }
    }

    getCellTypeText(cellType) {
        const types = {
            0: 'Walkable',
            1: 'Shelf',
            2: 'Obstacle',
            3: 'Beacon',
            4: 'Entrance',
            5: 'Checkout'
        };
        return types[cellType] || 'Unknown';
    }

    // Map Controls
    centerMapOnUser() {
        // Scroll to user position (if needed for larger maps)
        const userCell = document.querySelector(`[data-row="${this.currentPosition.x}"][data-col="${this.currentPosition.y}"]`);
        if (userCell) {
            userCell.scrollIntoView({ behavior: 'smooth', block: 'center' });
            this.showToast('Centered on user position', 'info');
        }
    }

    refreshMap() {
        if (this.socket) {
            this.socket.emit('request_position');
            this.showToast('Map refreshed', 'info');
        }
    }

    toggleGrid() {
        const mapGrid = document.getElementById('mapGrid');
        mapGrid.classList.toggle('grid-hidden');
        this.showToast('Grid toggled', 'info');
    }

    // Event Handlers
    handlePositionUpdate(data) {
        if (data.position) {
            // Update current position from any source (including admin control)
            this.currentPosition.x = data.position.x;
            this.currentPosition.y = data.position.y;
            
            // Update UI immediately
            this.updatePositionDisplay();
            this.renderMap();
            
            console.log(`Position updated to (${data.position.x}, ${data.position.y}) - Admin controlled: ${data.admin_controlled || false}`);
        }
    }

    handleAdminPositionUpdate(data) {
        console.log('Admin position update confirmed:', data);
        if (data.success) {
            this.showToast('Position update confirmed', 'success');
        } else {
            this.showToast('Position update failed', 'error');
        }
    }

    // UI Helpers
    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        
        container.appendChild(toast);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    showMovementIndicator() {
        const indicator = document.getElementById('movementIndicator');
        indicator.classList.add('show');
        
        setTimeout(() => {
            indicator.classList.remove('show');
        }, 1000);
    }
}

// Initialize admin panel when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.adminPanel = new AdminPanel();
});

// Add some helpful keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + R for refresh
    if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
        e.preventDefault();
        if (window.adminPanel) {
            window.adminPanel.refreshMap();
        }
    }
    
    // Escape to stop simulation
    if (e.key === 'Escape') {
        if (window.adminPanel && window.adminPanel.isSimulating) {
            window.adminPanel.toggleSimulation();
        }
    }
});

// Prevent accidental page navigation
window.addEventListener('beforeunload', (e) => {
    if (window.adminPanel && window.adminPanel.isSimulating) {
        e.preventDefault();
        e.returnValue = 'Simulation is running. Are you sure you want to leave?';
    }
});
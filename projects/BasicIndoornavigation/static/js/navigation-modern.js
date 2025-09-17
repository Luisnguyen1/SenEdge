// Modern Indoor Navigation System - Enhanced UI/UX
class ModernIndoorNavigationApp {
    constructor() {
        this.socket = null;
        this.mapData = null;
        this.currentPosition = null;
        this.previousPosition = null;
        this.nearbyShelves = [];
        this.crowdedAreas = {};  // Store crowded areas data
        this.checkoutQueues = {}; // Store checkout queue data
        this.priorityProducts = {}; // Store priority products data
        this.isConnected = false;
        this.currentRoute = null;
        this.routeStartPosition = null;
        this.routeEndPosition = null;
        this.isMobile = this.detectMobile();
        this.checkoutQueues = {}; // Store checkout queue data
        // Movement animation properties
        this.isAnimating = false;
        this.animationSpeed = 200; // milliseconds per step (reduced for smoother animation)
        this.currentAnimationPath = [];
        this.animationStepIndex = 0;
        // Cấu hình server URL
        this.apiBaseUrl = 'http://192.168.137.251:8080';
        this.categories = [
            { name: 'Electronics', icon: 'fas fa-tv', color: '#667eea' },
            { name: 'Home Appliances', icon: 'fas fa-blender', color: '#764ba2' },
            { name: 'Gaming', icon: 'fas fa-gamepad', color: '#10b981' },
            { name: 'Audio', icon: 'fas fa-headphones', color: '#f59e0b' }
        ];
    }

    detectMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    }

    init() {
        this.setupUI();
        this.initializeWebSocket();
        this.setupEventListeners();
        this.loadMapData();
        this.setupMobileOptimizations();
        this.initializeCategories();
        this.startConnectionHealthCheck();
        this.startPositionUpdateInterval(); // Thêm interval để backup WebSocket
        
        // Show loading initially
        this.showLoadingOverlay();
        
        // Request initial position
        setTimeout(() => {
            this.requestCurrentPosition();
            this.hideLoadingOverlay();
            
            // Check URL parameters for shelf navigation after initial load
            this.checkUrlParameters();
        }, 1000);
    }

    setupUI() {
        // Initialize UI components
        this.updateConnectionStatus(false, 'Đang kết nối...');
        this.updateLocationDisplay('Đang xác định vị trí...');
    }

    showLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.add('active');
        }
    }

    hideLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.classList.remove('active');
        }
    }

    // Check URL parameters for automatic navigation
    checkUrlParameters() {
        const urlParams = new URLSearchParams(window.location.search);
        const shelfParam = urlParams.get('shelf');
        
        if (shelfParam) {
            // Try to navigate immediately if position is available
            if (this.currentPosition && this.currentPosition.last_beacon) {
                this.navigateToShelfFromUrl(shelfParam);
            } else {
                // Retry up to 3 times with increasing delays
                let retryCount = 0;
                const maxRetries = 3;
                
                const retryNavigation = () => {
                    if (this.currentPosition && this.currentPosition.last_beacon) {
                        this.navigateToShelfFromUrl(shelfParam);
                    } else if (retryCount < maxRetries) {
                        retryCount++;
                        setTimeout(retryNavigation, 2000 * retryCount); // 2s, 4s, 6s delays
                    } else {
                        console.log('Could not get user position for shelf navigation from URL');
                        this.showToast(`Chưa xác định được vị trí để dẫn đường đến kệ ${shelfParam}`, 'warning');
                    }
                };
                
                setTimeout(retryNavigation, 2000);
            }
        }
    }

    async navigateToShelfFromUrl(shelfId) {
        // Only proceed if we have current position
        if (!this.currentPosition || !this.currentPosition.last_beacon) {
            console.log('Position not available yet, cannot navigate to shelf from URL');
            return;
        }

        // Find shelf information
        if (!this.mapData || !this.mapData.shelves_info) {
            console.log('Map data not loaded yet, cannot navigate to shelf');
            return;
        }

        const shelfInfo = this.mapData.shelves_info[shelfId];
        if (!shelfInfo) {
            this.showToast(`Không tìm thấy kệ ${shelfId}`, 'error');
            return;
        }

        // Calculate center position of the shelf
        const shelfCenterX = shelfInfo.position[0] + Math.floor(shelfInfo.size[0] / 2);
        const shelfCenterY = shelfInfo.position[1] + Math.floor(shelfInfo.size[1] / 2);

        // Auto navigate to the shelf
        try {
            await this.calculateRoute(
                this.currentPosition, 
                { x: shelfCenterX, y: shelfCenterY }, 
                `Kệ ${shelfId} - ${shelfInfo.category}`
            );
            
            this.showToast(`Đã tự động dẫn đường đến kệ ${shelfId}`, 'success');
        } catch (error) {
            console.error('Error navigating to shelf from URL:', error);
            this.showToast(`Không thể dẫn đường đến kệ ${shelfId}`, 'error');
        }
    }

    // ===== WebSocket Management =====
    initializeWebSocket() {
        try {
            this.socket = io(this.apiBaseUrl);
            
            this.socket.on('connect', () => {
                this.isConnected = true;
                this.updateConnectionStatus(true, 'Đã kết nối');
                this.requestCurrentPosition();
            });

            this.socket.on('disconnect', () => {
                this.isConnected = false;
                this.updateConnectionStatus(false, 'Mất kết nối');
            });

            this.socket.on('map_data', (data) => {
                console.log('Received map data via WebSocket:', data);
                if (data && data.map_layout) {
                    // Store the received map data
                    this.mapData = data;
                    
                    // Store crowded areas if available
                    if (data.crowded_areas) {
                        console.log('Storing crowded areas from WebSocket:', data.crowded_areas);
                        this.crowdedAreas = data.crowded_areas;
                    }
                    
                    // Store checkout queues if available
                    if (data.checkout_queues) {
                        console.log('Storing checkout queues from WebSocket:', data.checkout_queues);
                        this.checkoutQueues = data.checkout_queues;
                    }
                    
                    // Store priority products if available
                    if (data.priority_products) {
                        console.log('Storing priority products from WebSocket:', data.priority_products);
                        this.priorityProducts = data.priority_products;
                    }
                    
                    this.renderMap();
                    this.showToast('Đã nhận dữ liệu bản đồ từ WebSocket', 'success');
                } else {
                    console.warn('Invalid map data received:', data);
                }
            });

            this.socket.on('position_update', (data) => {
                console.log('📡 Received position_update via WebSocket:', data);
                this.updateUserPosition(data);
            });

            // New: Handle crowd detection updates
            this.socket.on('crowd_update', (data) => {
                this.updateCrowdedArea(data);
            });

            this.socket.on('crowd_data', (data) => {
                if (data.crowded_areas) {
                    this.crowdedAreas = data.crowded_areas;
                    this.renderCrowdedAreas();
                }
            });

            this.socket.on('crowd_cleared', (data) => {
                this.crowdedAreas = {};
                this.renderCrowdedAreas();
                this.showToast('Dữ liệu vùng đông người đã được xóa', 'info');
            });

            // New: Handle checkout queue updates
            this.socket.on('checkout_update', (data) => {
                this.updateCheckoutQueues(data);
            });

            this.socket.on('checkout_data', (data) => {
                if (data.checkout_queues) {
                    this.checkoutQueues = data.checkout_queues;
                    this.renderCheckoutQueues();
                }
            });

            // New: Handle priority products updates
            this.socket.on('priority_products_update', (data) => {
                console.log('📦 Received priority_products_update via WebSocket:', data);
                if (data.priority_products) {
                    this.priorityProducts = data.priority_products;
                    this.renderPriorityProducts();
                    
                    // Show notification for priority product changes
                    if (data.action) {
                        const actionMessages = {
                            'added': 'Đã thêm sản phẩm ưu tiên mới',
                            'updated': 'Đã cập nhật sản phẩm ưu tiên',
                            'removed': 'Đã xóa sản phẩm ưu tiên',
                            'cleared': 'Đã xóa tất cả sản phẩm ưu tiên'
                        };
                        this.showToast(actionMessages[data.action] || 'Sản phẩm ưu tiên đã được cập nhật', 'info');
                    }
                }
            });

            this.socket.on('connect_error', () => {
                this.isConnected = false;
                this.updateConnectionStatus(false, 'Lỗi kết nối');
            });

        } catch (error) {
            this.updateConnectionStatus(false, 'Lỗi WebSocket');
        }
    }

    requestCurrentPosition() {
        if (this.socket && this.isConnected) {
            this.socket.emit('request_position');
        }
    }

    startConnectionHealthCheck() {
        setInterval(() => {
            if (!this.isConnected) {
                this.initializeWebSocket();
            }
        }, 5000);
    }

    startPositionUpdateInterval() {
        // Backup mechanism: Call API every 5 seconds để đảm bảo position được cập nhật
        setInterval(() => {
            this.updatePositionFromAPI();
        }, 5000);
    }

    async updatePositionFromAPI() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/position/update`);
            if (response.ok) {
                const data = await response.json();
                if (data.position && data.position_updated) {
                    // Chỉ cập nhật nếu position thực sự thay đổi
                    this.updateUserPosition({ 
                        position: data.position, 
                        nearby_shelves: data.nearby_shelves 
                    });
                }
            }
        } catch (error) {
            // Silent error handling - no console logs
        }
    }

    // ===== UI Updates =====
    updateConnectionStatus(connected, message) {
        const statusDot = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        
        if (statusDot) {
            statusDot.className = connected ? 'status-dot connected' : 'status-dot';
        }
        
        if (statusText) {
            statusText.textContent = message;
        }
    }

    updateLocationDisplay(text) {
        const locationText = document.getElementById('locationText');
        if (locationText) {
            locationText.textContent = text;
        }
    }

    updateUserPosition(data, forceUpdate = false) {
        if (!data || !data.position) return;

        const newPosition = data.position;
        
        // Check if position actually changed
        if (!forceUpdate && this.currentPosition && 
            this.currentPosition.x === newPosition.x && 
            this.currentPosition.y === newPosition.y) {
            return;
        }

        const isFirstPosition = !this.currentPosition || !this.currentPosition.last_beacon;
        const oldPosition = this.currentPosition ? { ...this.currentPosition } : null;
        
        console.log(`🔄 Position updated: (${newPosition.x}, ${newPosition.y}) from beacon ${newPosition.last_beacon}`);
        
        // Update location display
        const zone = this.getZoneForPosition(newPosition.x, newPosition.y);
        this.updateLocationDisplay(`Tọa độ (${newPosition.x}, ${newPosition.y}) - ${zone}`);
        
        // Animate movement if we have valid old and new positions
        if (oldPosition && oldPosition.last_beacon && newPosition.last_beacon && 
            (oldPosition.x !== newPosition.x || oldPosition.y !== newPosition.y)) {
            // Use animation for smooth movement
            this.animateMovement(oldPosition, newPosition);
        } else {
            // First position or admin control - instant update
            this.currentPosition = newPosition;
            this.updateMapPositionInstant(newPosition);
        }
        
        // Store the new position for next update
        this.previousPosition = oldPosition;
        this.currentPosition = newPosition;
        
        // Update info panel
        this.updatePositionInfo();
        
        // Update nearby shelves
        if (data.nearby_shelves) {
            this.nearbyShelves = data.nearby_shelves;
            this.updateNearbyShelves();
        }

        // If this is the first time we get position, check URL parameters for auto navigation
        if (isFirstPosition && newPosition.last_beacon) {
            setTimeout(() => {
                this.checkUrlParameters();
            }, 500);
        }
    }

    getZoneForPosition(x, y) {
        // Map zones based on position
        if (y <= 5) return 'Khu vực Bắc';
        if (y >= 15) return 'Khu vực Nam';
        if (x <= 5) return 'Khu vực Tây';
        if (x >= 15) return 'Khu vực Đông';
        return 'Khu vực Trung tâm';
    }

    calculateOptimalPath(start, end) {
        // Use A* pathfinding algorithm to find optimal path avoiding obstacles
        if (!start || !end) return [];
        
        // If start and end are the same, return single point
        if (start.x === end.x && start.y === end.y) {
            return [{ x: start.x, y: start.y }];
        }
        
        // For very close distances, use direct path
        const distance = Math.abs(start.x - end.x) + Math.abs(start.y - end.y);
        if (distance <= 2) {
            return this.calculateDirectPath(start, end);
        }
        
        return this.aStarPathfinding(start, end);
    }
    
    aStarPathfinding(start, end) {
        const openSet = [];
        const closedSet = new Set();
        const cameFrom = new Map();
        const gScore = new Map();
        const fScore = new Map();
        
        const startKey = `${start.x},${start.y}`;
        const endKey = `${end.x},${end.y}`;
        
        openSet.push({ x: start.x, y: start.y });
        gScore.set(startKey, 0);
        fScore.set(startKey, this.heuristic(start, end));
        
        while (openSet.length > 0) {
            // Find node with lowest fScore
            let current = openSet[0];
            let currentIndex = 0;
            
            for (let i = 1; i < openSet.length; i++) {
                const nodeKey = `${openSet[i].x},${openSet[i].y}`;
                const currentKey = `${current.x},${current.y}`;
                if (fScore.get(nodeKey) < fScore.get(currentKey)) {
                    current = openSet[i];
                    currentIndex = i;
                }
            }
            
            // Remove current from openSet
            openSet.splice(currentIndex, 1);
            const currentKey = `${current.x},${current.y}`;
            closedSet.add(currentKey);
            
            // If we reached the goal
            if (current.x === end.x && current.y === end.y) {
                return this.reconstructPath(cameFrom, current);
            }
            
            // Check all neighbors
            const neighbors = this.getValidNeighbors(current);
            
            for (const neighbor of neighbors) {
                const neighborKey = `${neighbor.x},${neighbor.y}`;
                
                if (closedSet.has(neighborKey)) continue;
                
                const tentativeGScore = gScore.get(currentKey) + this.getMovementCost(current, neighbor);
                
                if (!openSet.some(node => node.x === neighbor.x && node.y === neighbor.y)) {
                    openSet.push(neighbor);
                } else if (tentativeGScore >= (gScore.get(neighborKey) || Infinity)) {
                    continue;
                }
                
                cameFrom.set(neighborKey, current);
                gScore.set(neighborKey, tentativeGScore);
                fScore.set(neighborKey, tentativeGScore + this.heuristic(neighbor, end));
            }
        }
        
        // No path found, return direct path as fallback
        return this.calculateDirectPath(start, end);
    }
    
    heuristic(nodeA, nodeB) {
        // Manhattan distance
        return Math.abs(nodeA.x - nodeB.x) + Math.abs(nodeA.y - nodeB.y);
    }
    
    getValidNeighbors(node) {
        const neighbors = [];
        const directions = [
            { x: 0, y: 1 },  // Up
            { x: 0, y: -1 }, // Down
            { x: 1, y: 0 },  // Right
            { x: -1, y: 0 }  // Left
        ];
        
        for (const dir of directions) {
            const newX = node.x + dir.x;
            const newY = node.y + dir.y;
            
            // Use isWalkable which already checks bounds and cell types
            if (this.isWalkable(newX, newY)) {
                neighbors.push({ x: newX, y: newY });
            }
        }
        
        return neighbors;
    }
    
    isWalkable(x, y) {
        // Check bounds first
        if (x < 0 || y < 0 || x >= 20 || y >= 20) {
            return false;
        }
        
        // Check grid map directly for cell type
        const grid = this.mapData?.map_layout ? this.mapData.map_layout.grid : this.mapData?.grid;
        if (grid && grid[x] && grid[x][y] !== undefined) {
            const cellType = grid[x][y];
            // Cell type 1 = shelf, 2 = obstacle - both are not walkable
            if (cellType === 1 || cellType === 2) {
                return false;
            }
        }
        
        // Check if it's a crowded area
        if (this.crowdedAreas) {
            for (const areaId in this.crowdedAreas) {
                const area = this.crowdedAreas[areaId];
                if (area.position && area.size) {
                    const [areaX, areaY] = area.position;
                    const [areaW, areaH] = area.size;
                    
                    if (x >= areaX && x < areaX + areaW && 
                        y >= areaY && y < areaY + areaH) {
                        // Avoid high crowd areas, but allow low crowd areas with penalty
                        if (area.crowd_level > 7) {
                            return false;
                        }
                    }
                }
            }
        }
        
        return true; // Position is walkable
    }
    
    getMovementCost(from, to) {
        let baseCost = 1;
        
        // Add penalty for crowded areas
        if (this.crowdedAreas) {
            for (const areaId in this.crowdedAreas) {
                const area = this.crowdedAreas[areaId];
                if (area.position && area.size) {
                    const [areaX, areaY] = area.position;
                    const [areaW, areaH] = area.size;
                    
                    if (to.x >= areaX && to.x < areaX + areaW && 
                        to.y >= areaY && to.y < areaY + areaH) {
                        // Add cost penalty based on crowd level
                        baseCost += area.crowd_level * 0.5;
                    }
                }
            }
        }
        
        return baseCost;
    }
    
    reconstructPath(cameFrom, current) {
        const path = [{ x: current.x, y: current.y }];
        
        let currentKey = `${current.x},${current.y}`;
        while (cameFrom.has(currentKey)) {
            current = cameFrom.get(currentKey);
            path.unshift({ x: current.x, y: current.y });
            currentKey = `${current.x},${current.y}`;
        }
        
        return path;
    }
    
    calculateDirectPath(start, end) {
        // Fallback: simple direct path if A* fails
        const path = [];
        let currentX = start.x;
        let currentY = start.y;
        
        path.push({ x: currentX, y: currentY });
        
        // Move toward target
        while (currentX !== end.x || currentY !== end.y) {
            if (currentX < end.x) currentX++;
            else if (currentX > end.x) currentX--;
            else if (currentY < end.y) currentY++;
            else if (currentY > end.y) currentY--;
            
            path.push({ x: currentX, y: currentY });
        }
        
        return path;
    }

    async animateMovement(fromPosition, toPosition) {
        // Skip animation if already animating or positions are the same
        if (this.isAnimating || !fromPosition || !toPosition || 
            (fromPosition.x === toPosition.x && fromPosition.y === toPosition.y)) {
            this.updateMapPositionInstant(toPosition);
            return;
        }
        
        this.isAnimating = true;
        
        // Calculate optimal path using A* algorithm to avoid obstacles
        const path = this.calculateOptimalPath(fromPosition, toPosition);
        
        if (path.length <= 1) {
            this.updateMapPositionInstant(toPosition);
            this.isAnimating = false;
            return;
        }
        
        this.currentAnimationPath = path;
        this.animationStepIndex = 0;
        
        // Clear previous user position
        this.clearUserFromMap();
        
        // Animate through each step
        for (let i = 0; i < path.length; i++) {
            const step = path[i];
            
            // Clear previous step
            if (i > 0) {
                const prevStep = path[i - 1];
                this.clearUserFromPosition(prevStep.x, prevStep.y);
            }
            
            // Show user at current step
            this.showUserAtPosition(step.x, step.y);
            
            // Wait before next step
            if (i < path.length - 1) {
                await this.sleep(this.animationSpeed);
            }
        }
        
        // Animation complete
        this.isAnimating = false;
        this.currentPosition = { ...toPosition };
        
        console.log(`✨ Animated movement completed to (${toPosition.x}, ${toPosition.y}) via optimal path`);
    }
    
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    clearUserFromMap() {
        document.querySelectorAll('.map-cell.cell-user').forEach(cell => {
            cell.classList.remove('cell-user');
            this.restoreCellContent(cell);
        });
    }
    
    clearUserFromPosition(x, y) {
        const cell = document.querySelector(`[data-row="${x}"][data-col="${y}"]`);
        if (cell) {
            cell.classList.remove('cell-user');
            this.restoreCellContent(cell);
        }
    }
    
    showUserAtPosition(x, y) {
        const cell = document.querySelector(`[data-row="${x}"][data-col="${y}"]`);
        if (cell) {
            cell.classList.add('cell-user');
            cell.innerHTML = '<i class="fas fa-user"></i>';
        }
    }
    
    restoreCellContent(cell) {
        const originalCellType = cell.getAttribute('data-cell-type');
        if (originalCellType) {
            cell.innerHTML = this.getCellContent(parseInt(originalCellType), 
                parseInt(cell.getAttribute('data-row')), 
                parseInt(cell.getAttribute('data-col')));
        } else {
            cell.innerHTML = '';
        }
    }
    
    updateMapPositionInstant(position) {
        // Clear all previous user positions
        this.clearUserFromMap();
        
        // Show user at new position if valid
        if (position && (position.last_beacon || position.admin_controlled)) {
            this.showUserAtPosition(position.x, position.y);
            console.log(`🎯 User position instantly updated to (${position.x}, ${position.y})`);
            this.centerMapOnUser();
        }
    }

    updateMapPosition() {
        // Delegate to instant update function
        this.updateMapPositionInstant(this.currentPosition);
    }

    centerMapOnUser() {
        // Center if we have valid position (from beacon or admin control)
        if (!this.currentPosition || 
            (!this.currentPosition.last_beacon && !this.currentPosition.admin_controlled)) return;
        
        const cell = document.querySelector(`[data-row="${this.currentPosition.x}"][data-col="${this.currentPosition.y}"]`);
        if (cell) {
            cell.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
        }
    }

    updatePositionInfo() {
        const currentCoords = document.getElementById('currentCoords');
        const currentZone = document.getElementById('currentZone');
        const nearestBeacon = document.getElementById('nearestBeacon');

        if (this.currentPosition && 
            (this.currentPosition.last_beacon || this.currentPosition.admin_controlled)) {
            if (currentCoords) {
                currentCoords.textContent = `(${this.currentPosition.x}, ${this.currentPosition.y})`;
            }
            if (currentZone) {
                currentZone.textContent = this.getZoneForPosition(this.currentPosition.x, this.currentPosition.y);
            }
            if (nearestBeacon) {
                const beaconText = this.currentPosition.admin_controlled ? 
                    'User1' : this.currentPosition.last_beacon;
                nearestBeacon.textContent = beaconText;
            }
        } else {
            // Show waiting message when position not available
            if (currentCoords) {
                currentCoords.textContent = 'Đang xác định...';
            }
            if (currentZone) {
                currentZone.textContent = '--';
            }
            if (nearestBeacon) {
                nearestBeacon.textContent = '--';
            }
        }
    }

    updateNearbyShelves() {
        const container = document.getElementById('nearbyShelves');
        if (!container) return;

        // Only show nearby shelves if we have real position and shelves data
        if (!this.currentPosition || !this.currentPosition.last_beacon || this.nearbyShelves.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-search"></i>
                    <p>${!this.currentPosition || !this.currentPosition.last_beacon ? 'Chưa xác định vị trí' : 'Không có kệ hàng gần đây'}</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.nearbyShelves.map(shelf => `
            <div class="shelf-item" onclick="app.navigateToShelf('${shelf.shelf_id || shelf.id}')">
                <div class="shelf-info">
                    <div class="shelf-name">${shelf.shelf_id || shelf.id}</div>
                    <div class="shelf-category">${shelf.category}</div>
                    <div class="shelf-distance">${shelf.distance.toFixed(1)}m</div>
                </div>
                <button class="navigate-btn">
                    <i class="fas fa-directions"></i>
                </button>
            </div>
        `).join('');
    }

    // ===== Checkout Queue Management =====
    updateCheckoutQueues(data) {
        if (data.checkout_data) {
            this.checkoutQueues = data.checkout_data;
            this.renderCheckoutQueues();
            
            // Show notification for significant queue changes
            const totalPeople = Object.values(this.checkoutQueues).reduce((sum, queue) => sum + queue.people_count, 0);
            if (totalPeople > 5) {
                this.showToast(`Cảnh báo: Có ${totalPeople} người đang chờ tại các quầy thu ngân`, 'warning');
            }
        }
    }

    renderCheckoutQueues() {
        // Don't render checkout indicators on map anymore
        // Only update the checkout summary panel
        this.updateCheckoutSummary();
    }

    renderCheckoutQueue(checkoutId, checkoutData) {
        // This method is no longer used for map rendering
        // Checkout info is now only shown in the summary panel
        console.log(`Checkout ${checkoutId} at position [${checkoutData.position[0]}, ${checkoutData.position[1]}] with ${checkoutData.people_count} people`);
    }

    updateCheckoutSummary() {
        const checkoutSummary = document.getElementById('checkoutSummary');
        if (!checkoutSummary) return;

        const queues = Object.values(this.checkoutQueues);
        if (queues.length === 0) {
            checkoutSummary.innerHTML = `
                <div class="checkout-summary-header">
                    <h4><i class="fas fa-cash-register"></i> Quầy Thu Ngân</h4>
                </div>
                <div class="checkout-empty">
                    <i class="fas fa-info-circle"></i>
                    <span>Chưa có dữ liệu quầy thu ngân</span>
                </div>
            `;
            return;
        }

        const totalPeople = queues.reduce((sum, queue) => sum + queue.people_count, 0);
        const avgWaitTime = queues.length > 0 ? Math.round(queues.reduce((sum, queue) => sum + queue.wait_time_estimate, 0) / queues.length) : 0;
        const openCheckouts = queues.filter(queue => queue.status === 'open').length;

        // Find best checkout (least people)
        const bestCheckout = queues
            .filter(queue => queue.status === 'open')
            .reduce((best, current) => {
                if (!best || current.people_count < best.people_count) return current;
                return best;
            }, null);

        let checkoutDetails = '';
        Object.entries(this.checkoutQueues).forEach(([checkoutId, data]) => {
            const statusIcon = data.status === 'open' ? 'fa-check-circle' : 
                             data.status === 'closed' ? 'fa-times-circle' : 'fa-wrench';
            const statusColor = data.status === 'open' ? '#10b981' : 
                              data.status === 'closed' ? '#ef4444' : '#f59e0b';
            
            const isBest = bestCheckout && data === bestCheckout;
            
            checkoutDetails += `
                <div class="checkout-item ${isBest ? 'checkout-best' : ''}" onclick="app.navigateToCheckout('${checkoutId}')">
                    <div class="checkout-item-header">
                        <span class="checkout-name">${checkoutId.replace('CHECKOUT_', 'Quầy ')}</span>
                        <i class="fas ${statusIcon}" style="color: ${statusColor}"></i>
                        ${isBest ? '<span class="best-badge">Ít người nhất</span>' : ''}
                    </div>
                    <div class="checkout-item-stats">
                        <span><i class="fas fa-users"></i> ${data.people_count} người</span>
                        <span><i class="fas fa-clock"></i> ${data.wait_time_estimate}p</span>
                        <span><i class="fas fa-map-marker-alt"></i> (${data.position[0]}, ${data.position[1]})</span>
                    </div>
                </div>
            `;
        });

        checkoutSummary.innerHTML = `
            <div class="checkout-summary-header">
                <h4><i class="fas fa-cash-register"></i> Quầy Thu Ngân</h4>
                <button class="checkout-nav-btn" onclick="app.navigateToCheckout()">
                    <i class="fas fa-route"></i> Đi đến quầy ít người nhất
                </button>
            </div>
            <div class="checkout-stats-grid">
                <div class="checkout-stat">
                    <i class="fas fa-users"></i>
                    <span class="checkout-number">${totalPeople}</span>
                    <span class="checkout-label">Tổng người chờ</span>
                </div>
                <div class="checkout-stat">
                    <i class="fas fa-clock"></i>
                    <span class="checkout-number">${avgWaitTime}p</span>
                    <span class="checkout-label">Thời gian TB</span>
                </div>
                <div class="checkout-stat">
                    <i class="fas fa-cash-register"></i>
                    <span class="checkout-number">${openCheckouts}</span>
                    <span class="checkout-label">Quầy mở</span>
                </div>
            </div>
            <div class="checkout-details">
                ${checkoutDetails}
            </div>
        `;
    }

    async navigateToCheckout(checkoutId = null) {
        try {
            if (!this.currentPosition || !this.currentPosition.last_beacon) {
                this.showToast('Chưa xác định được vị trí hiện tại', 'warning');
                return;
            }

            // If no specific checkout, find the best one
            let endpoint = checkoutId ? `/api/navigation/route` : `/api/checkout/navigate`;
            
            if (checkoutId) {
                // Navigate to specific checkout
                const checkoutData = this.checkoutQueues[checkoutId];
                if (!checkoutData) {
                    this.showToast(`Không tìm thấy thông tin quầy ${checkoutId}`, 'error');
                    return;
                }

                const response = await fetch(`${this.apiBaseUrl}/api/navigation/route`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        start: this.currentPosition,
                        end: { x: checkoutData.position[0], y: checkoutData.position[1] }
                    })
                });

                if (response.ok) {
                    const routeData = await response.json();
                    this.displayRoute(routeData, `Quầy ${checkoutId}`);
                    this.showToast(`Đã tính toán đường đi đến quầy ${checkoutId}`, 'success');
                }
            } else {
                // Navigate to best checkout
                const response = await fetch(`${this.apiBaseUrl}/api/checkout/navigate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (response.ok) {
                    const data = await response.json();
                    this.displayRoute(data.route, `Quầy tối ưu: ${data.best_checkout.checkout_id}`);
                    this.showToast(data.recommendation, 'success');
                } else {
                    const errorData = await response.json();
                    this.showToast(errorData.message || 'Không thể tìm quầy thu ngân phù hợp', 'error');
                }
            }

        } catch (error) {
            console.error('Error navigating to checkout:', error);
            this.showToast('Lỗi khi tính toán đường đi đến quầy thu ngân', 'error');
        }
    }

    // ===== Map Rendering =====
    async loadMapData() {
        try {
            console.log('Loading map data...');
            const response = await fetch(`${this.apiBaseUrl}/api/map`);
            if (response.ok) {
                this.mapData = await response.json();
                console.log('Map data loaded:', this.mapData);
                
                // Load crowded areas data if available
                if (this.mapData.crowded_areas) {
                    console.log('Loading crowded areas from API:', this.mapData.crowded_areas);
                    this.crowdedAreas = this.mapData.crowded_areas;
                }
                
                // Load checkout queues data if available
                if (this.mapData.checkout_queues) {
                    console.log('Loading checkout queues from API:', this.mapData.checkout_queues);
                    this.checkoutQueues = this.mapData.checkout_queues;
                }
                
                this.renderMap();
                this.showToast('Đã tải bản đồ thành công', 'success');
            } else {
                console.error('Failed to load map data:', response.status);
                this.showToast('Không thể tải dữ liệu bản đồ', 'error');
            }
        } catch (error) {
            console.error('Error loading map data:', error);
            this.showToast('Không thể tải dữ liệu bản đồ', 'error');
        }
    }

    renderMap() {
        const mapGrid = document.getElementById('mapGrid');
        if (!mapGrid || !this.mapData) return;

        mapGrid.innerHTML = '';
        
        // Fix: Access grid correctly from map_layout
        const grid = this.mapData.map_layout ? this.mapData.map_layout.grid : this.mapData.grid;
        
        if (!grid) {
            console.error('No grid data found in map data');
            return;
        }
        
        for (let row = 0; row < grid.length; row++) {
            for (let col = 0; col < grid[row].length; col++) {
                const cell = document.createElement('div');
                cell.className = `map-cell ${this.getCellClass(grid[row][col])}`;
                cell.dataset.row = row;
                cell.dataset.col = col;
                cell.dataset.cellType = grid[row][col]; // Store original cell type
                cell.innerHTML = this.getCellContent(grid[row][col], row, col);
                
                // Thêm tooltip cho kệ hàng
                if (grid[row][col] === 1) {
                    const shelfInfo = this.findShelfAtPosition(row, col);
                    if (shelfInfo) {
                        const productsList = shelfInfo.products.slice(0, 3).join(', ');
                        const moreProducts = shelfInfo.products.length > 3 ? ` và ${shelfInfo.products.length - 3} sản phẩm khác` : '';
                        cell.title = `🏪 Kệ ${shelfInfo.id} - ${shelfInfo.category}\n📦 Sản phẩm: ${productsList}${moreProducts}\n👆 Click để xem chi tiết`;
                        cell.classList.add('shelf-clickable');
                    }
                }
                
                // Add click handler
                cell.addEventListener('click', () => this.handleCellClick(cell, row, col));
                
                mapGrid.appendChild(cell);
            }
        }

        // Update user position if available (from beacon or admin control)
        if (this.currentPosition && 
            (this.currentPosition.last_beacon || this.currentPosition.admin_controlled)) {
            this.updateMapPosition();
        }

        // Render crowded areas (always render regardless of user position)
        console.log('Rendering crowded areas:', this.crowdedAreas);
        this.renderCrowdedAreas();
        
        // Render checkout queues
        console.log('Rendering checkout queues:', this.checkoutQueues);
        this.renderCheckoutQueues();
        
        // Render priority products
        console.log('Rendering priority products:', this.priorityProducts);
        this.renderPriorityProducts();
    }

    // ===== Priority Products Management =====
    renderPriorityProducts() {
        // Hide priority products rendering on UI
        // Clear any existing priority indicators (just in case)
        document.querySelectorAll('.priority-indicator').forEach(el => el.remove());
        
        // Priority products are now only used for routing logic
        // No visual indicators on map
        console.log('Priority products loaded for routing (hidden from UI):', Object.keys(this.priorityProducts).length);
    }

    renderPriorityProduct(productId, productData) {
        // Disabled - no visual rendering
        console.log(`Priority product ${productId} available for routing optimization`);
    }

    updatePrioritySummary() {
        // Hide priority summary panel
        const prioritySummary = document.getElementById('prioritySummary');
        if (prioritySummary) {
            prioritySummary.style.display = 'none';
        }
    }

    showPriorityProductDetails(productId, productData) {
        // Disabled - no modal display for priority products
        console.log(`Priority product details for ${productId}: ${productData.product_name}`);
    }

    createPriorityProductDetailModal(productId, productData) {
        // Disabled - no modal creation
        return null;
    }

    async navigateToPriorityProduct(shelfId, productName) {
        // Close any modals
        document.querySelector('.priority-detail-modal')?.remove();
        
        if (!this.currentPosition || !this.currentPosition.last_beacon) {
            this.showToast('Chưa xác định được vị trí hiện tại', 'warning');
            return;
        }

        // Find the product in shelf info
        if (!this.mapData || !this.mapData.shelves_info || !this.mapData.shelves_info[shelfId]) {
            this.showToast(`Không tìm thấy kệ ${shelfId}`, 'error');
            return;
        }

        const shelfInfo = this.mapData.shelves_info[shelfId];
        const shelfCenterX = shelfInfo.position[0] + Math.floor(shelfInfo.size[0] / 2);
        const shelfCenterY = shelfInfo.position[1] + Math.floor(shelfInfo.size[1] / 2);

        try {
            await this.calculateRoute(
                this.currentPosition, 
                { x: shelfCenterX, y: shelfCenterY }, 
                `${productName} (Sản phẩm ưu tiên)`,
                false  // Normal routing, not forced priority
            );
            
            this.showToast(`Đã dẫn đường đến sản phẩm ưu tiên: ${productName}`, 'success');
        } catch (error) {
            console.error('Error navigating to priority product:', error);
            this.showToast(`Không thể dẫn đường đến ${productName}`, 'error');
        }
    }

    async calculateRouteWithPriority(targetShelfId = null) {
        if (!this.currentPosition || !this.currentPosition.last_beacon) {
            this.showToast('Chưa xác định được vị trí hiện tại', 'warning');
            return;
        }

        // If no target specified, use user's current navigation target or default to checkout
        let targetPosition = null;
        let targetName = 'Điểm đến';

        if (targetShelfId && this.mapData && this.mapData.shelves_info[targetShelfId]) {
            const shelfInfo = this.mapData.shelves_info[targetShelfId];
            targetPosition = {
                x: shelfInfo.position[0] + Math.floor(shelfInfo.size[0] / 2),
                y: shelfInfo.position[1] + Math.floor(shelfInfo.size[1] / 2)
            };
            targetName = `Kệ ${targetShelfId}`;
        } else if (this.routeEndPosition) {
            targetPosition = this.routeEndPosition;
            targetName = 'Điểm đến hiện tại';
        } else {
            // Default to nearest checkout
            targetPosition = { x: 18, y: 8 }; // Center between checkouts
            targetName = 'Quầy thu ngân';
        }

        try {
            await this.calculateRoute(
                this.currentPosition,
                targetPosition,
                `${targetName} (qua sản phẩm ưu tiên)`,
                true  // Force priority routing
            );
            
            this.showToast('Đã tính toán tuyến đường qua sản phẩm ưu tiên', 'success');
        } catch (error) {
            console.error('Error calculating priority route:', error);
            this.showToast('Không thể tính toán tuyến đường ưu tiên', 'error');
        }
    }

    // ===== Crowded Areas Management =====
    updateCrowdedArea(data) {
        if (data.area_id && data.area_data) {
            this.crowdedAreas[data.area_id] = data.area_data;
            this.renderCrowdedAreas();
            
            // Show notification for high crowd levels
            const crowdLevel = data.area_data.crowd_level;
            if (crowdLevel >= 4) {
                this.showToast(
                    `Cảnh báo: Khu vực ${data.area_id} đang rất đông (${data.area_data.people_count} người)`, 
                    'warning'
                );
            }
        }
    }

    renderCrowdedAreas() {
        // Clear previous crowd indicators
        document.querySelectorAll('.crowd-indicator').forEach(el => el.remove());

        // Render current crowded areas
        Object.entries(this.crowdedAreas).forEach(([areaId, areaData]) => {
            this.renderCrowdedArea(areaId, areaData);
        });

        // Update crowd summary
        this.updateCrowdSummary();
    }

    renderCrowdedArea(areaId, areaData) {
        const position = areaData.position;
        const crowdLevel = areaData.crowd_level;
        const peopleCount = areaData.people_count;
        const affectedPositions = areaData.affected_positions || [position]; // Fallback to center position

        console.log(`Rendering crowd area ${areaId} at position [${position[0]}, ${position[1]}] with ${peopleCount} people affecting ${affectedPositions.length} positions`);

        // Create crowd overlay for each affected position
        affectedPositions.forEach(([row, col]) => {
            const cell = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
            if (cell) {
                console.log(`Adding crowd indicator to cell [${row}, ${col}]`);
                const crowdIndicator = document.createElement('div');
                crowdIndicator.className = `crowd-indicator crowd-level-${crowdLevel}`;
                crowdIndicator.innerHTML = `
                    <div class="crowd-info">
                        <span class="people-count">${peopleCount}</span>
                        <span class="crowd-level">L${crowdLevel}</span>
                    </div>
                `;
                
                // Add tooltip
                crowdIndicator.title = `${areaData.description || areaId}\n${peopleCount} người - Mức độ ${crowdLevel}`;
                
                cell.appendChild(crowdIndicator);
                
                // Add click handler for crowd info
                crowdIndicator.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this.showCrowdAreaDetails(areaId, areaData);
                });
            } else {
                console.warn(`Cell not found for position [${row}, ${col}]`);
            }
        });
    }

    updateCrowdSummary() {
        const crowdSummary = document.getElementById('crowdSummary');
        if (!crowdSummary) return;

        const areas = Object.values(this.crowdedAreas);
        const totalPeople = areas.reduce((sum, area) => sum + area.people_count, 0);
        const highCrowdAreas = areas.filter(area => area.crowd_level >= 4).length;

        crowdSummary.innerHTML = `
            <div class="crowd-summary-content">
                <div class="crowd-stat">
                    <i class="fas fa-users"></i>
                    <span class="crowd-number">${totalPeople}</span>
                    <span class="crowd-label">Tổng người</span>
                </div>
                <div class="crowd-stat">
                    <i class="fas fa-exclamation-triangle"></i>
                    <span class="crowd-number">${highCrowdAreas}</span>
                    <span class="crowd-label">Vùng đông</span>
                </div>
                <div class="crowd-stat">
                    <i class="fas fa-eye"></i>
                    <span class="crowd-number">${areas.length}</span>
                    <span class="crowd-label">Khu vực</span>
                </div>
            </div>
        `;
    }

    showCrowdAreaDetails(areaId, areaData) {
        const modal = this.createCrowdDetailModal(areaId, areaData);
        document.body.appendChild(modal);
        
        // Show modal
        setTimeout(() => modal.classList.add('show'), 10);
    }

    createCrowdDetailModal(areaId, areaData) {
        const modal = document.createElement('div');
        modal.className = 'crowd-detail-modal';
        modal.innerHTML = `
            <div class="crowd-detail-content">
                <div class="crowd-detail-header">
                    <h3>${areaData.description || areaId}</h3>
                    <button class="close-btn" onclick="this.closest('.crowd-detail-modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="crowd-detail-body">
                    <div class="crowd-detail-stats">
                        <div class="stat-item">
                            <div class="stat-value">${areaData.people_count}</div>
                            <div class="stat-label">Số người</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value crowd-level-${areaData.crowd_level}">Mức ${areaData.crowd_level}</div>
                            <div class="stat-label">${this.getCrowdLevelDescription(areaData.crowd_level)}</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-value">${Math.round((areaData.confidence || 0.8) * 100)}%</div>
                            <div class="stat-label">Độ tin cậy</div>
                        </div>
                    </div>
                    <div class="crowd-detail-info">
                        <p><strong>Vị trí trung tâm:</strong> (${areaData.position[0]}, ${areaData.position[1]})</p>
                        <p><strong>Vùng ảnh hưởng:</strong> ${areaData.affected_positions ? areaData.affected_positions.length : 'N/A'} vị trí</p>
                        <p><strong>Cập nhật lần cuối:</strong> ${new Date(areaData.last_update).toLocaleTimeString()}</p>
                    </div>
                    <div class="crowd-detail-actions">
                        <button class="btn-avoid" onclick="app.avoidCrowdedArea('${areaId}')">
                            <i class="fas fa-route"></i> Tránh khu vực này
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        return modal;
    }

    getCrowdLevelDescription(level) {
        const descriptions = {
            0: "Trống",
            1: "Rất ít",
            2: "Ít", 
            3: "Vừa phải",
            4: "Đông",
            5: "Rất đông"
        };
        return descriptions[level] || "Không rõ";
    }

    avoidCrowdedArea(areaId) {
        // Close modal
        document.querySelector('.crowd-detail-modal')?.remove();
        
        // Add logic to avoid this area in route planning
        this.showToast(`Sẽ tránh khu vực ${areaId} khi dẫn đường`, 'info');
        
        // You can implement route replanning logic here
    }

    getCellClass(cellType) {
        const cellTypes = {
            0: 'cell-empty',
            1: 'cell-shelf',
            2: 'cell-obstacle',
            3: 'cell-beacon',
            4: 'cell-entrance',
            5: 'cell-checkout'
        };
        return cellTypes[cellType] || 'cell-empty';
    }

    getCellContent(cellType, row, col) {
        const icons = {
            1: this.getShelfIcon(row, col),
            2: '<i class="fas fa-times"></i>',
            3: '<i class="fas fa-broadcast-tower"></i>',
            4: '<i class="fas fa-door-open"></i>',
            5: '<i class="fas fa-cash-register"></i>'
        };
        return icons[cellType] || '';
    }

    getShelfIcon(row, col) {
        // Tìm kệ hàng tại vị trí này
        const shelfInfo = this.findShelfAtPosition(row, col);
        if (shelfInfo) {
            // Xác định icon dựa trên sản phẩm đầu tiên hoặc danh mục
            const firstProduct = shelfInfo.products[0]?.toLowerCase() || '';
            
            // Icon dựa trên sản phẩm cụ thể
            const productIcons = {
                'smartphone': '<i class="fas fa-mobile-alt" style="color: #667eea;"></i>',
                'laptop': '<i class="fas fa-laptop" style="color: #3b82f6;"></i>',
                'headphones': '<i class="fas fa-headphones" style="color: #8b5cf6;"></i>',
                'camera': '<i class="fas fa-camera" style="color: #f59e0b;"></i>',
                'gaming': '<i class="fas fa-gamepad" style="color: #10b981;"></i>',
                'tablet': '<i class="fas fa-tablet-alt" style="color: #667eea;"></i>',
                'smartwatch': '<i class="fas fa-clock" style="color: #ef4444;"></i>',
                'keyboard': '<i class="fas fa-keyboard" style="color: #6b7280;"></i>',
                'mouse': '<i class="fas fa-mouse" style="color: #6b7280;"></i>',
                'speaker': '<i class="fas fa-volume-up" style="color: #f59e0b;"></i>',
                'tv': '<i class="fas fa-tv" style="color: #1f2937;"></i>',
                'router': '<i class="fas fa-wifi" style="color: #3b82f6;"></i>',
                'charger': '<i class="fas fa-plug" style="color: #ef4444;"></i>',
                'cable': '<i class="fas fa-link" style="color: #6b7280;"></i>',
                'monitor': '<i class="fas fa-desktop" style="color: #1f2937;"></i>'
            };
            
            // Tìm icon phù hợp với sản phẩm
            for (const [keyword, icon] of Object.entries(productIcons)) {
                if (firstProduct.includes(keyword)) {
                    return icon;
                }
            }
            
            // Fallback với icon theo danh mục
            const categoryIcons = {
                'Electronics': '<i class="fas fa-tv" style="color: #667eea;"></i>',
                'Home Appliances': '<i class="fas fa-blender" style="color: #764ba2;"></i>',
                'Gaming': '<i class="fas fa-gamepad" style="color: #10b981;"></i>',
                'Computer': '<i class="fas fa-desktop" style="color: #3b82f6;"></i>',
                'Smart Home': '<i class="fas fa-home" style="color: #f59e0b;"></i>',
                'Accessories': '<i class="fas fa-plug" style="color: #8b5cf6;"></i>'
            };
            return categoryIcons[shelfInfo.category] || '<i class="fas fa-cube"></i>';
        }
        return '<i class="fas fa-cube"></i>';
    }

    findShelfAtPosition(row, col) {
        if (!this.mapData?.shelves_info) return null;
        
        for (const [shelfId, shelfInfo] of Object.entries(this.mapData.shelves_info)) {
            const [shelfX, shelfY] = shelfInfo.position;
            const [sizeX, sizeY] = shelfInfo.size;
            
            // Kiểm tra nếu vị trí (row, col) nằm trong kệ hàng
            if (row >= shelfX && row < shelfX + sizeX && 
                col >= shelfY && col < shelfY + sizeY) {
                return {
                    id: shelfId,
                    category: shelfInfo.category,
                    products: shelfInfo.products,
                    position: shelfInfo.position,
                    size: shelfInfo.size
                };
            }
        }
        return null;
    }

    handleCellClick(cell, row, col) {
        // Kiểm tra nếu là kệ hàng thì hiển thị thông tin sản phẩm
        const shelfInfo = this.findShelfAtPosition(row, col);
        if (shelfInfo) {
            this.showShelfProductInfo(shelfInfo, row, col);
        } else {
            // Hiển thị thông tin cell thông thường hoặc đặt làm đích đến
            this.showCellInfo(row, col);
        }
    }

    showShelfProductInfo(shelfInfo, row, col) {
        const modal = this.createShelfProductModal(shelfInfo, row, col);
        document.body.appendChild(modal);
        
        // Show modal với animation
        setTimeout(() => modal.classList.add('show'), 10);
    }

    createShelfProductModal(shelfInfo, row, col) {
        const modal = document.createElement('div');
        modal.className = 'shelf-product-modal';
        
        // Tạo danh sách sản phẩm
        const productsList = shelfInfo.products.map(product => `
            <div class="product-item">
                <i class="fas fa-box product-icon"></i>
                <span class="product-name">${product}</span>
                <button class="navigate-to-product-btn" onclick="app.navigateToPosition(${row}, ${col}, '${product}')">
                    <i class="fas fa-directions"></i>
                </button>
            </div>
        `).join('');

        modal.innerHTML = `
            <div class="shelf-product-content">
                <div class="shelf-product-header">
                    <div class="shelf-info-title">
                        ${this.getShelfIcon(row, col)}
                        <div class="shelf-details">
                            <h3>Kệ ${shelfInfo.id}</h3>
                            <span class="shelf-category">${shelfInfo.category}</span>
                        </div>
                    </div>
                    <button class="close-btn" onclick="this.closest('.shelf-product-modal').remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="shelf-product-body">
                    <div class="location-info">
                        <p><i class="fas fa-map-marker-alt"></i> Vị trí: (${row}, ${col})</p>
                        <p><i class="fas fa-th-large"></i> Kích thước: ${shelfInfo.size[0]}×${shelfInfo.size[1]}</p>
                    </div>
                    <div class="products-section">
                        <h4><i class="fas fa-shopping-basket"></i> Sản phẩm có sẵn (${shelfInfo.products.length})</h4>
                        <div class="products-list">
                            ${productsList}
                        </div>
                    </div>
                    <div class="shelf-actions">
                        <button class="btn-navigate" onclick="app.navigateToPosition(${row}, ${col}, 'Kệ ${shelfInfo.id}')">
                            <i class="fas fa-route"></i> Dẫn đường đến kệ này
                        </button>
                        <button class="btn-search-category" onclick="app.searchByCategory('${shelfInfo.category}')">
                            <i class="fas fa-search"></i> Tìm ${shelfInfo.category} khác
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        // Close on background click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
        
        return modal;
    }

    navigateToPosition(x, y, productName = '') {
        // Close modal first
        document.querySelector('.shelf-product-modal')?.remove();
        
        if (!this.currentPosition || !this.currentPosition.last_beacon) {
            this.showToast('Chưa xác định được vị trí hiện tại', 'warning');
            return;
        }

        this.calculateRoute(this.currentPosition, { x, y }, productName);
    }

    showCellInfo(row, col) {
        // Fix: Access grid correctly from map_layout
        const grid = this.mapData?.map_layout ? this.mapData.map_layout.grid : this.mapData?.grid;
        if (!grid) return;
        
        const cellType = grid[row][col];
        
        // Nếu là kệ hàng, hiển thị thông tin chi tiết sản phẩm
        if (cellType === 1) {
            const shelfInfo = this.findShelfAtPosition(row, col);
            if (shelfInfo) {
                const productsList = shelfInfo.products.join(', ');
                const detailedInfo = `📍 Vị trí: (${row}, ${col})\n🏪 Kệ ${shelfInfo.id} - ${shelfInfo.category}\n📦 Sản phẩm: ${productsList}\n📏 Kích thước: ${shelfInfo.size[0]}×${shelfInfo.size[1]}`;
                this.showToast(detailedInfo, 'info');
                return;
            }
        }
        
        let info = `Tọa độ: (${row}, ${col})`;
        
        switch (cellType) {
            case 0:
                info += '\nLoại: Lối đi';
                break;
            case 1:
                info += '\nLoại: Kệ hàng';
                break;
            case 2:
                info += '\nLoại: Vật cản';
                break;
            case 3:
                info += '\nLoại: Beacon';
                break;
            case 4:
                info += '\nLoại: Lối vào/ra';
                break;
        }
        
        this.showToast(info, 'info');
    }

    // ===== Category Management =====
    initializeCategories() {
        const categoryGrid = document.getElementById('categoryGrid');
        if (!categoryGrid) return;

        categoryGrid.innerHTML = this.categories.map(category => `
            <button class="category-item" onclick="app.searchByCategory('${category.name}')" 
                    style="background: linear-gradient(135deg, ${category.color}, ${category.color}88)">
                <i class="${category.icon}"></i>
                <span>${category.name}</span>
            </button>
        `).join('');
    }

    async searchByCategory(categoryName) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/navigation/products?category=${encodeURIComponent(categoryName)}`);
            if (response.ok) {
                const data = await response.json();
                this.displaySearchResults(data.results);
                this.showToast(`Tìm thấy ${data.total} sản phẩm trong danh mục ${categoryName}`, 'success');
            }
        } catch (error) {
            this.showToast('Lỗi khi tìm kiếm danh mục', 'error');
        }
    }

    // ===== Search & Navigation =====
    async searchProducts(query) {
        if (!query.trim()) {
            document.getElementById('searchResults').innerHTML = '';
            return;
        }

        try {
            const response = await fetch(`${this.apiBaseUrl}/api/navigation/products?q=${encodeURIComponent(query)}`);
            if (response.ok) {
                const data = await response.json();
                this.displaySearchResults(data.results);
            }
        } catch (error) {
            this.showToast('Lỗi khi tìm kiếm sản phẩm', 'error');
        }
    }

    displaySearchResults(results) {
        const searchResults = document.getElementById('searchResults');
        if (!searchResults) return;

        if (results.length === 0) {
            searchResults.innerHTML = '<div class="empty-state"><p>Không tìm thấy sản phẩm nào</p></div>';
            return;
        }

        searchResults.innerHTML = results.map(result => `
            <div class="search-result-item">
                <div class="search-result-info">
                    <div class="search-result-product">${result.product}</div>
                    <div class="search-result-details">Kệ ${result.shelf_id} - ${result.category}</div>
                </div>
                <button class="search-result-action" onclick="app.navigateToProduct('${result.shelf_id}', ${result.position[0]}, ${result.position[1]})">
                    Dẫn đường
                </button>
            </div>
        `).join('');
    }

    navigateToProduct(shelfId, x, y) {
        if (!this.currentPosition || !this.currentPosition.last_beacon) {
            this.showToast('Chưa xác định được vị trí hiện tại', 'warning');
            return;
        }

        this.calculateRoute(this.currentPosition, { x, y }, shelfId);
    }

    navigateToShelf(shelfId) {
        // Get shelf position from shelf data
        // This would need to be implemented based on your shelf data structure
        this.showToast(`Dẫn đường đến kệ ${shelfId}`, 'info');
    }

    async calculateRoute(start, end, destinationName = '', forcePriority = false) {
        try {
            const response = await fetch(`${this.apiBaseUrl}/api/navigation/route`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    start: start,
                    end: end,
                    force_priority: forcePriority
                })
            });

            if (response.ok) {
                const routeData = await response.json();
                
                // Check if route passes through crowded areas and show warning
                const crowdedPath = this.checkRouteForCrowds(routeData.path);
                if (crowdedPath.length > 0) {
                    this.showToast(`⚠️ Đường đi có ${crowdedPath.length} vùng đông người. Đã tối ưu để tránh khi có thể.`, 'warning');
                }
                
                // Show priority products info if any were visited
                if (routeData.priority_products_visited && routeData.priority_products_visited.length > 0) {
                    const priorityNames = routeData.priority_products_visited.map(p => p.product_name).join(', ');
                    this.showToast(`⭐ Tuyến đường qua ${routeData.total_priority_products} sản phẩm ưu tiên: ${priorityNames}`, 'info');
                }
                
                this.displayRoute(routeData, destinationName);
                this.showToast('Đã tính toán đường đi thành công', 'success');
            } else {
                this.showToast('Không thể tính toán đường đi', 'error');
            }
        } catch (error) {
            this.showToast('Lỗi khi tính toán đường đi', 'error');
        }
    }

    checkRouteForCrowds(path) {
        // Check if route passes through crowded areas
        const crowdedSteps = [];
        
        path.forEach((step, index) => {
            for (const [areaId, areaData] of Object.entries(this.crowdedAreas)) {
                if (areaData.affected_positions) {
                    for (const [x, y] of areaData.affected_positions) {
                        if (step.x === x && step.y === y) {
                            crowdedSteps.push({
                                step: index,
                                position: [x, y],
                                areaId: areaId,
                                crowdLevel: areaData.crowd_level
                            });
                        }
                    }
                }
            }
        });
        
        return crowdedSteps;
    }

    displayRoute(routeData, destinationName = '') {
        // Store route data
        this.currentRoute = routeData.path;
        this.routeStartPosition = routeData.start;
        this.routeEndPosition = routeData.end;

        // Show route section
        const routeSection = document.getElementById('routeSection');
        if (routeSection) {
            routeSection.style.display = 'block';
        }

        // Update route info
        const routeDistance = document.getElementById('routeDistance');
        const routeTime = document.getElementById('routeTime');
        
        if (routeDistance) {
            routeDistance.textContent = `${routeData.distance} bước`;
        }
        if (routeTime) {
            routeTime.textContent = `${Math.round(routeData.estimated_time / 60)} phút`;
        }

        // Visualize route on map
        this.visualizeRoute(routeData.path, routeData.start, routeData.end);

        // Generate and show directions
        this.displayDirections(routeData, destinationName);
    }

    visualizeRoute(path, start, end) {
        // Clear previous route
        this.clearRouteVisualization();

        // Mark start position
        const startCell = document.querySelector(`[data-row="${start.x}"][data-col="${start.y}"]`);
        if (startCell) {
            startCell.classList.add('route-start');
        }

        // Mark end position
        const endCell = document.querySelector(`[data-row="${end.x}"][data-col="${end.y}"]`);
        if (endCell) {
            endCell.classList.add('route-end');
        }

        // Mark path with crowd awareness
        const crowdedSteps = this.checkRouteForCrowds(path);
        const crowdedPositions = new Set(crowdedSteps.map(step => `${step.position[0]},${step.position[1]}`));

        path.forEach((point, index) => {
            if (index > 0 && index < path.length - 1) {
                const cell = document.querySelector(`[data-row="${point.x}"][data-col="${point.y}"]`);
                if (cell) {
                    cell.classList.add('cell-route');
                    
                    // Add special class for crowded route segments
                    if (crowdedPositions.has(`${point.x},${point.y}`)) {
                        cell.classList.add('route-crowded');
                        cell.title = `Đường đi (qua vùng đông người)`;
                    } else {
                        cell.title = `Đường đi`;
                    }
                }
            }
        });
    }

    displayDirections(routeData, destinationName = '') {
        const directionsSection = document.getElementById('directionsSection');
        const directionsList = document.getElementById('directionsList');
        
        if (!directionsSection || !directionsList) return;

        directionsSection.style.display = 'block';

        const directions = this.generateDirections(routeData.path);
        
        directionsList.innerHTML = directions.map((direction, index) => `
            <div class="direction-step">
                <strong>Bước ${index + 1}:</strong> ${direction}
            </div>
        `).join('');

        if (destinationName) {
            directionsList.innerHTML += `
                <div class="direction-step">
                    <strong>Đích đến:</strong> ${destinationName}
                </div>
            `;
        }
    }

    generateDirections(path) {
        if (path.length < 2) return ['Bạn đã ở đích đến'];

        const directions = [];
        
        for (let i = 0; i < path.length - 1; i++) {
            const current = path[i];
            const next = path[i + 1];
            
            const dx = next.x - current.x;
            const dy = next.y - current.y;
            
            if (dx > 0) directions.push('Đi xuống dưới');
            else if (dx < 0) directions.push('Đi lên trên');
            else if (dy > 0) directions.push('Đi sang phải');
            else if (dy < 0) directions.push('Đi sang trái');
        }

        directions.push('Bạn đã đến đích!');
        return directions;
    }

    clearRoute() {
        // Clear route data
        this.currentRoute = null;
        this.routeStartPosition = null;
        this.routeEndPosition = null;

        // Hide route sections
        const routeSection = document.getElementById('routeSection');
        const directionsSection = document.getElementById('directionsSection');
        
        if (routeSection) routeSection.style.display = 'none';
        if (directionsSection) directionsSection.style.display = 'none';

        // Clear route visualization
        this.clearRouteVisualization();

        // Clear search
        const productSearch = document.getElementById('productSearch');
        const searchResults = document.getElementById('searchResults');
        
        if (productSearch) productSearch.value = '';
        if (searchResults) searchResults.innerHTML = '';

        this.showToast('Đã xóa đường đi', 'info');
    }

    clearRouteVisualization() {
        document.querySelectorAll('.map-cell.cell-route, .map-cell.route-start, .map-cell.route-end, .map-cell.route-crowded').forEach(cell => {
            cell.classList.remove('cell-route', 'route-start', 'route-end', 'route-crowded');
            // Reset title if it was a route-related title
            if (cell.title && (cell.title.includes('Đường đi') || cell.title.includes('route'))) {
                cell.title = '';
            }
        });
    }

    // ===== Event Listeners =====
    setupEventListeners() {
        // Search functionality
        const productSearch = document.getElementById('productSearch');
        const searchBtn = document.getElementById('searchBtn');
        
        if (productSearch) {
            productSearch.addEventListener('input', (e) => {
                const query = e.target.value.trim();
                if (query.length >= 2) {
                    this.searchProducts(query);
                } else {
                    document.getElementById('searchResults').innerHTML = '';
                }
            });
            
            productSearch.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.searchProducts(e.target.value);
                }
            });
        }

        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                if (productSearch) {
                    this.searchProducts(productSearch.value);
                }
            });
        }

        // Route actions
        const clearRouteBtn = document.getElementById('clearRouteBtn');
        const startNavigationBtn = document.getElementById('startNavigationBtn');
        const checkoutNavigateBtn = document.getElementById('checkoutNavigateBtn');
        
        if (clearRouteBtn) {
            clearRouteBtn.addEventListener('click', () => this.clearRoute());
        }
        
        if (startNavigationBtn) {
            startNavigationBtn.addEventListener('click', () => {
                this.showToast('Bắt đầu dẫn đường!', 'success');
            });
        }
        
        if (checkoutNavigateBtn) {
            checkoutNavigateBtn.addEventListener('click', () => this.navigateToCheckout());
        }

        // Map controls
        const centerMapBtn = document.getElementById('centerMapBtn');
        const refreshPositionBtn = document.getElementById('refreshPositionBtn');
        const fullscreenBtn = document.getElementById('fullscreenBtn');
        
        if (centerMapBtn) {
            centerMapBtn.addEventListener('click', () => this.centerMapOnUser());
        }
        
        if (refreshPositionBtn) {
            refreshPositionBtn.addEventListener('click', () => {
                this.requestCurrentPosition();
                this.updatePositionFromAPI();
            });
        }
        
        if (fullscreenBtn) {
            fullscreenBtn.addEventListener('click', () => this.toggleFullscreen());
        }

        // Info panel
        const closeInfoBtn = document.getElementById('closeInfoBtn');
        if (closeInfoBtn) {
            closeInfoBtn.addEventListener('click', () => {
                document.getElementById('infoPanel').classList.remove('active');
            });
        }

        // Mobile navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const target = e.currentTarget.dataset.target;
                this.handleMobileNavigation(target);
            });
        });

        // Global keyboard listeners
        document.addEventListener('keydown', (e) => {
            // Close modals with Escape key
            if (e.key === 'Escape') {
                const modal = document.querySelector('.shelf-product-modal, .crowd-detail-modal');
                if (modal) {
                    modal.remove();
                }
            }
        });
    }

    setupMobileOptimizations() {
        if (this.isMobile) {
            // Add mobile-specific optimizations
            document.body.classList.add('mobile');
            
            // Touch optimizations
            document.addEventListener('touchstart', function() {}, { passive: true });
        }
    }

    handleMobileNavigation(target) {
        // Update active state
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.remove('active');
        });
        document.querySelector(`[data-target="${target}"]`).classList.add('active');

        // Handle navigation
        switch (target) {
            case 'search':
                // Show search panel
                break;
            case 'map':
                this.centerMapOnUser();
                break;
            case 'info':
                document.getElementById('infoPanel').classList.add('active');
                break;
        }
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            document.documentElement.requestFullscreen();
        } else {
            document.exitFullscreen();
        }
    }

    // ===== Toast Notifications =====
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;

        toastContainer.appendChild(toast);

        // Auto remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.navigationApp = new ModernIndoorNavigationApp();
    window.navigationApp.init();
    
    // Create global alias 'app' for backward compatibility
    window.app = window.navigationApp;
    
    // Add global debug helpers (minimal for production)
    window.debugNav = {
        getStatus: () => window.navigationApp.isConnected,
        updatePosition: () => window.navigationApp.updatePositionFromAPI(),
        centerMap: () => window.navigationApp.centerMapOnUser(),
        getCrowdedAreas: () => window.navigationApp.crowdedAreas,
        testCrowdDisplay: () => {
            // Test function to manually add crowd data with radius expansion
            window.navigationApp.crowdedAreas = {
                'test_zone_1': {
                    position: [5, 5],
                    size: [1, 1],
                    affected_positions: [[4,4],[4,5],[4,6],[5,4],[5,5],[5,6],[6,4],[6,5],[6,6]], // 3x3 grid around center
                    crowd_level: 3,
                    people_count: 8,
                    last_update: new Date().toISOString(),
                    description: 'Test Zone 1 - Expanded radius'
                }
            };
            window.navigationApp.renderCrowdedAreas();
            console.log('Test crowd data with expanded radius added and rendered');
        }
    };
});

// Export for compatibility
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModernIndoorNavigationApp;
}
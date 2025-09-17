// Indoor Navigation System - WebSocket Client
class IndoorNavigationApp {
    constructor() {
        this.socket = null;
        this.mapData = null;
        this.currentPosition = null;
        this.previousPosition = null;
        this.nearbyShelves = [];
        this.isConnected = false;
        this.userTrails = [];
        this.maxTrails = 10;
        this.isMobile = this.detectMobile();
        this.touchStartY = 0;
        this.touchEndY = 0;
        this.isPositionAnimating = false;
        this.positionInterpolation = null;
        this.previousValues = {
            rssi: null,
            distance: null,
            x: null,
            y: null
        };
        
        // Path animation properties
        this.isAnimatingPath = false;
        this.pathAnimationQueue = [];
        this.currentPathStep = 0;
        this.stepAnimationDuration = 600; // ms per step
        this.currentlyDisplayedPosition = null;
        this.animationStartTime = 0;
        this.healthCheckInterval = null;
        
        // Navigation properties
        this.currentRoute = null;
        this.routeStartPosition = null;
        this.routeEndPosition = null;
        
        this.init();
    }

    detectMobile() {
        return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) ||
               window.innerWidth <= 768;
    }

    init() {
        this.showLoadingOverlay();
        this.initializeWebSocket();
        this.setupEventListeners();
        this.setupNavigationControls();
        this.setupMobileOptimizations();
        this.updateConnectionStatus('offline', 'Đang kết nối...');
        this.startConnectionHealthCheck();
        
        // Load navigation from URL parameters if present
        this.loadNavigationFromURL();
        
        // Hide loading after a short delay
        setTimeout(() => this.hideLoadingOverlay(), 1000);
    }

    showLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'flex';
        }
    }

    hideLoadingOverlay() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.style.display = 'none';
        }
    }

    setupMobileOptimizations() {
        if (!this.isMobile) return;

        // Prevent zoom on double tap
        let lastTouchEnd = 0;
        document.addEventListener('touchend', function (event) {
            const now = (new Date()).getTime();
            if (now - lastTouchEnd <= 300) {
                event.preventDefault();
            }
            lastTouchEnd = now;
        }, false);

        // Prevent context menu on long press
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
        });

        // Add haptic feedback for touch interactions
        this.addHapticFeedback();

        // Optimize scroll behavior
        this.optimizeScrolling();
    }

    addHapticFeedback() {
        const addHaptic = (element) => {
            element.addEventListener('touchstart', () => {
                if (navigator.vibrate) {
                    navigator.vibrate(10); // Short vibration
                }
            });
        };

        // Add haptic feedback to control buttons
        document.querySelectorAll('.control-btn').forEach(addHaptic);
        
        // Add haptic feedback to map cells
        document.addEventListener('DOMContentLoaded', () => {
            setTimeout(() => {
                document.querySelectorAll('.map-cell').forEach(addHaptic);
            }, 1000);
        });
    }

    optimizeScrolling() {
        // Prevent bounce scroll on iOS
        document.body.addEventListener('touchmove', function(e) {
            if (e.target === document.body) {
                e.preventDefault();
            }
        }, { passive: false });

        // Smooth scroll to user position
        if ('scrollBehavior' in document.documentElement.style) {
            document.documentElement.style.scrollBehavior = 'smooth';
        }
    }

    // ===== WebSocket Management =====
    initializeWebSocket() {
        try {
            // Kết nối WebSocket
            this.socket = io();
            
            this.socket.on('connect', () => {
                console.log('🔌 Connected to server');
                this.isConnected = true;
                this.updateConnectionStatus('online', 'Đã kết nối');
                this.requestCurrentPosition();
                this.hideLoadingOverlay();
            });

            this.socket.on('disconnect', () => {
                console.log('🔌 Disconnected from server');
                this.isConnected = false;
                this.updateConnectionStatus('offline', 'Mất kết nối');
            });

            this.socket.on('map_data', (data) => {
                console.log('🗺️ Received map data:', data);
                this.mapData = data;
                this.renderMap();
            });

            this.socket.on('position_update', (data) => {
                console.log('📍 Position update:', data);
                this.updateUserPosition(data);
            });

            this.socket.on('connect_error', (error) => {
                console.error('❌ Connection error:', error);
                this.updateConnectionStatus('offline', 'Lỗi kết nối');
                this.hideLoadingOverlay();
            });

        } catch (error) {
            console.error('❌ WebSocket initialization error:', error);
            this.updateConnectionStatus('offline', 'Lỗi khởi tạo');
            this.hideLoadingOverlay();
        }
    }

    requestCurrentPosition() {
        if (this.socket && this.isConnected) {
            this.socket.emit('request_position');
        }
    }

    startConnectionHealthCheck() {
        this.healthCheckInterval = setInterval(() => {
            if (this.socket && !this.isConnected) {
                console.log('🔄 Attempting to reconnect...');
                this.socket.connect();
            }
            
            // Call API to update position every 3 seconds instead of relying on WebSocket events
            this.updatePositionFromAPI();
        }, 3000); // Changed from 10s to 3s to match server timing
    }

    async updatePositionFromAPI() {
        try {
            console.log('🔄 Calling position update API...');
            const response = await fetch('/api/position/update');
            const data = await response.json();
            
            if (data.status === 'success' && data.position_updated) {
                console.log('📍 Position update from API:', data);
                this.updateUserPosition({
                    position: data.position,
                    nearby_shelves: data.nearby_shelves || []
                });
            } else if (data.status === 'success' && !data.position_updated) {
                console.log('⚠️ No position update available:', data.message);
                // Still update with current position to refresh UI
                if (data.position) {
                    this.updateUserPosition({
                        position: data.position,
                        nearby_shelves: data.nearby_shelves || []
                    });
                }
            } else {
                console.error('❌ API error:', data.message);
            }
        } catch (error) {
            console.error('❌ Error calling position update API:', error);
            // Fallback to WebSocket request if API fails
            this.requestCurrentPosition();
        }
    }

    // ===== UI Updates =====
    updateConnectionStatus(status, message) {
        const statusIndicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        
        if (statusIndicator && statusText) {
            statusIndicator.className = `status-indicator ${status}`;
            statusText.textContent = message;
            
            // Add visual feedback for mobile
            if (this.isMobile && status === 'online') {
                statusIndicator.style.animation = 'mobile-pulse 1s ease-in-out';
                setTimeout(() => {
                    statusIndicator.style.animation = '';
                }, 1000);
            }
        }
    }

    updateUserPosition(data, forceUpdate = false) {
        try {
            // Store previous position for smooth transition
            this.previousPosition = this.currentPosition ? {...this.currentPosition} : null;
            let newPosition = data.position;
            
            // Safety check: ensure new position is not an obstacle
            if (this.mapData && this.mapData.map_layout && this.mapData.map_layout.grid) {
                if (this.isObstacle(newPosition, this.mapData.map_layout.grid)) {
                    console.warn(`⚠️ New position (${newPosition.x}, ${newPosition.y}) is an obstacle! Finding nearest walkable position.`);
                    const nearestWalkable = this.findNearestWalkablePosition(
                        newPosition, 
                        this.mapData.map_layout.grid, 
                        this.mapData.map_layout.width, 
                        this.mapData.map_layout.height
                    );
                    if (nearestWalkable) {
                        console.log(`🎯 Corrected to nearest walkable position: (${nearestWalkable.x}, ${nearestWalkable.y})`);
                        newPosition = nearestWalkable;
                    } else {
                        console.error('❌ Cannot place user in obstacle, keeping previous position');
                        return; // Don't update if no valid position found
                    }
                }
            }
            
            // If animation is stuck for more than 10 seconds, force update
            if (this.isAnimatingPath && (Date.now() - this.animationStartTime > 10000)) {
                console.warn('⚠️ Animation appears stuck - forcing update');
                this.isAnimatingPath = false;
                forceUpdate = true;
            }
            
            // Force update or first position
            if (forceUpdate || !this.previousPosition || !this.currentlyDisplayedPosition) {
                this.currentPosition = newPosition;
                this.currentlyDisplayedPosition = {...newPosition};
                this.nearbyShelves = data.nearby_shelves || [];
                
                this.updatePositionInfoWithAnimation(0);
                this.updateMapPositionDirectly();
                this.updateNearbyShelves();
                this.updateBeaconInfoWithAnimation(0);
                this.addUserTrail();
                return;
            }
            
            // Calculate movement distance and check if position has changed significantly
            let distance = 0;
            const hasPositionChanged = (
                this.currentlyDisplayedPosition.x !== newPosition.x || 
                this.currentlyDisplayedPosition.y !== newPosition.y
            );
            
            if (hasPositionChanged) {
                distance = Math.sqrt(
                    Math.pow(newPosition.x - this.currentlyDisplayedPosition.x, 2) + 
                    Math.pow(newPosition.y - this.currentlyDisplayedPosition.y, 2)
                );
                
                console.log(`📍 Position change: from (${this.currentlyDisplayedPosition.x}, ${this.currentlyDisplayedPosition.y}) to (${newPosition.x}, ${newPosition.y}), distance = ${distance.toFixed(2)} units`);
                
                // Calculate path from current displayed position to new position
                console.log(`🛤️ Calculating safe path avoiding obstacles (shelves and walls)...`);
                const path = this.calculatePath(this.currentlyDisplayedPosition, newPosition);
                
                if (path && path.length > 1) {
                    // Start animated movement along the path
                    this.startPathAnimation(path, newPosition, data.nearby_shelves || []);
                } else {
                    // Fallback to direct position update if no valid path
                    this.currentPosition = newPosition;
                    this.currentlyDisplayedPosition = {...newPosition};
                    this.nearbyShelves = data.nearby_shelves || [];
                    this.updatePositionInfoWithAnimation(distance);
                    this.updateMapPositionDirectly();
                    this.updateNearbyShelves();
                    this.updateBeaconInfoWithAnimation(distance);
                }
            } else {
                // Position hasn't changed, just update other info
                this.currentPosition = newPosition;
                this.nearbyShelves = data.nearby_shelves || [];
                this.updatePositionInfoWithAnimation(0);
                this.updateNearbyShelves();
                this.updateBeaconInfoWithAnimation(0);
            }
            
            this.addUserTrail();
            
            // Auto-center map on mobile when position updates
            if (this.isMobile && hasPositionChanged) {
                const totalAnimationTime = path ? path.length * this.stepAnimationDuration : 1000;
                setTimeout(() => this.centerMapOnUser(), totalAnimationTime + 300);
            }
        } catch (error) {
            console.error('❌ Error updating position:', error);
            // Emergency fallback - direct update on error
            if (data.position) {
                this.currentPosition = data.position;
                this.currentlyDisplayedPosition = {...data.position};
                this.nearbyShelves = data.nearby_shelves || [];
                this.updateMapPositionDirectly();
                this.updatePositionInfoWithAnimation(0);
                this.updateNearbyShelves();
                this.updateBeaconInfoWithAnimation(0);
            }
        }
    }

    calculatePath(start, end) {
        if (!this.mapData || !this.mapData.map_layout) return null;
        
        const grid = this.mapData.map_layout.grid;
        const width = this.mapData.map_layout.width;
        const height = this.mapData.map_layout.height;
        
        // Safety check: if destination is an obstacle, find nearest walkable cell
        if (this.isObstacle(end, grid)) {
            console.warn(`⚠️ Destination (${end.x}, ${end.y}) is an obstacle, finding nearest walkable position`);
            const nearestWalkable = this.findNearestWalkablePosition(end, grid, width, height);
            if (nearestWalkable) {
                console.log(`🎯 Using nearest walkable position: (${nearestWalkable.x}, ${nearestWalkable.y})`);
                end = nearestWalkable;
            } else {
                console.error('❌ No walkable position found near destination');
                return this.getDirectPath(start, end);
            }
        }
        
        // Simple A* pathfinding algorithm
        const openSet = [];
        const closedSet = new Set();
        const cameFrom = new Map();
        const gScore = new Map();
        const fScore = new Map();
        
        const startKey = `${start.x},${start.y}`;
        const endKey = `${end.x},${end.y}`;
        
        // Initialize start node
        openSet.push({x: start.x, y: start.y});
        gScore.set(startKey, 0);
        fScore.set(startKey, this.heuristic(start, end));
        
        while (openSet.length > 0) {
            // Find node with lowest fScore
            let current = openSet.reduce((lowest, node) => {
                const nodeKey = `${node.x},${node.y}`;
                const lowestKey = `${lowest.x},${lowest.y}`;
                return fScore.get(nodeKey) < fScore.get(lowestKey) ? node : lowest;
            });
            
            const currentKey = `${current.x},${current.y}`;
            
            // If we reached the goal
            if (currentKey === endKey) {
                return this.reconstructPath(cameFrom, current);
            }
            
            // Move current from open to closed set
            openSet.splice(openSet.indexOf(current), 1);
            closedSet.add(currentKey);
            
            // Check all neighbors
            const neighbors = this.getNeighbors(current, width, height);
            
            for (const neighbor of neighbors) {
                const neighborKey = `${neighbor.x},${neighbor.y}`;
                
                // Skip if in closed set or if it's an obstacle
                if (closedSet.has(neighborKey) || this.isObstacle(neighbor, grid)) {
                    continue;
                }
                
                const tentativeGScore = gScore.get(currentKey) + 1;
                
                // If not in open set, add it
                if (!openSet.some(node => `${node.x},${node.y}` === neighborKey)) {
                    openSet.push(neighbor);
                } else if (tentativeGScore >= gScore.get(neighborKey)) {
                    continue; // This path is not better
                }
                
                // This is the best path so far
                cameFrom.set(neighborKey, current);
                gScore.set(neighborKey, tentativeGScore);
                fScore.set(neighborKey, tentativeGScore + this.heuristic(neighbor, end));
            }
        }
        
        // No path found, return direct line path
        console.log('⚠️ No valid path found, using direct movement');
        return this.getDirectPath(start, end);
    }
    
    findNearestWalkablePosition(target, grid, width, height) {
        // BFS to find nearest walkable position
        const queue = [{x: target.x, y: target.y, distance: 0}];
        const visited = new Set([`${target.x},${target.y}`]);
        
        while (queue.length > 0) {
            const current = queue.shift();
            
            // If current position is walkable, return it
            if (!this.isObstacle(current, grid)) {
                return {x: current.x, y: current.y};
            }
            
            // Add neighbors to queue (expand search radius)
            const neighbors = this.getNeighbors(current, width, height);
            for (const neighbor of neighbors) {
                const key = `${neighbor.x},${neighbor.y}`;
                if (!visited.has(key)) {
                    visited.add(key);
                    queue.push({
                        x: neighbor.x, 
                        y: neighbor.y, 
                        distance: current.distance + 1
                    });
                }
            }
            
            // Limit search radius to prevent infinite loops
            if (current.distance > 10) {
                console.warn('⚠️ Search radius exceeded, no walkable position found');
                break;
            }
        }
        
        return null; // No walkable position found
    }

    heuristic(a, b) {
        // Manhattan distance
        return Math.abs(a.x - b.x) + Math.abs(a.y - b.y);
    }
    
    getNeighbors(node, width, height) {
        const neighbors = [];
        // Only use cardinal directions to prevent diagonal movement through obstacles
        const directions = [
            {x: 0, y: 1},   // Right
            {x: 0, y: -1},  // Left
            {x: 1, y: 0},   // Down
            {x: -1, y: 0}   // Up
            // Removed diagonal movements to prevent cutting through corners of obstacles
        ];
        
        for (const dir of directions) {
            const newX = node.x + dir.x;
            const newY = node.y + dir.y;
            
            if (newX >= 0 && newX < height && newY >= 0 && newY < width) {
                neighbors.push({x: newX, y: newY});
            }
        }
        
        return neighbors;
    }
    
    isObstacle(node, grid) {
        if (!grid[node.x] || grid[node.x][node.y] === undefined) return true;
        
        const cellType = grid[node.x][node.y];
        // Cell types: 0 = walkable, 1 = shelf (NOT walkable), 2 = obstacle (NOT walkable), 3 = beacon (walkable), 4 = entrance (walkable)
        // Updated: Both shelves and obstacles block movement to prevent going through walls and shelves
        return cellType === 1 || cellType === 2; // Shelves and obstacles block movement
    }
    
    reconstructPath(cameFrom, current) {
        const path = [current];
        let currentKey = `${current.x},${current.y}`;
        
        while (cameFrom.has(currentKey)) {
            current = cameFrom.get(currentKey);
            path.unshift(current);
            currentKey = `${current.x},${current.y}`;
        }
        
        console.log(`🛤️ Path calculated: ${path.length} steps`);
        return path;
    }
    
    getDirectPath(start, end) {
        // Improved fallback: create a path that avoids obstacles when possible
        const path = [];
        const dx = end.x - start.x;
        const dy = end.y - start.y;
        const steps = Math.max(Math.abs(dx), Math.abs(dy));
        
        // If no grid data available, fallback to simple path
        if (!this.mapData || !this.mapData.map_layout || !this.mapData.map_layout.grid) {
            for (let i = 0; i <= steps; i++) {
                const x = Math.round(start.x + (dx * i / steps));
                const y = Math.round(start.y + (dy * i / steps));
                path.push({x, y});
            }
            return path;
        }
        
        const grid = this.mapData.map_layout.grid;
        
        // Try to create a simple path, but validate each step
        for (let i = 0; i <= steps; i++) {
            const x = Math.round(start.x + (dx * i / steps));
            const y = Math.round(start.y + (dy * i / steps));
            const newNode = {x, y};
            
            // If this step would go through an obstacle, try to find an alternative
            if (this.isObstacle(newNode, grid)) {
                // Try adjacent cells (simple avoidance)
                const alternatives = [
                    {x: x + 1, y: y},
                    {x: x - 1, y: y},
                    {x: x, y: y + 1},
                    {x: x, y: y - 1}
                ];
                
                let foundAlternative = false;
                for (const alt of alternatives) {
                    if (!this.isObstacle(alt, grid)) {
                        path.push(alt);
                        foundAlternative = true;
                        break;
                    }
                }
                
                // If no alternative found, skip this step (teleport effect)
                if (!foundAlternative) {
                    console.warn(`⚠️ No valid path found, skipping obstacle at (${x}, ${y})`);
                    // Add the destination anyway to prevent getting stuck
                    if (i === steps) {
                        path.push(newNode);
                    }
                }
            } else {
                path.push(newNode);
            }
        }
        
        console.log(`🛤️ Direct path with obstacle avoidance: ${path.length} steps`);
        return path;
    }

    startPathAnimation(path, finalPosition, nearbyShelves) {
        if (this.isAnimatingPath) {
            console.log('🚫 Already animating, skipping new animation');
            return;
        }
        
        console.log(`🎬 Starting path animation with ${path.length} steps`);
        
        this.isAnimatingPath = true;
        this.animationStartTime = Date.now();
        this.pathAnimationQueue = path.slice(); // Copy the path
        this.currentPathStep = 0;
        this.currentPosition = finalPosition; // Set the final target position
        this.nearbyShelves = nearbyShelves;
        
        // Calculate step duration based on total distance
        const totalDistance = path.length;
        if (totalDistance > 8) {
            this.stepAnimationDuration = 400; // Faster for long distances
        } else if (totalDistance > 4) {
            this.stepAnimationDuration = 600; // Normal speed
        } else {
            this.stepAnimationDuration = 800; // Slower for short distances
        }
        
        console.log(`⏱️ Step duration: ${this.stepAnimationDuration}ms for ${totalDistance} steps`);
        
        // Start the animation
        this.animateNextStep();
    }
    
    animateNextStep() {
        if (!this.isAnimatingPath || this.currentPathStep >= this.pathAnimationQueue.length) {
            this.finishPathAnimation();
            return;
        }
        
        const currentStep = this.pathAnimationQueue[this.currentPathStep];
        console.log(`🚶 Step ${this.currentPathStep + 1}/${this.pathAnimationQueue.length}: (${currentStep.x}, ${currentStep.y})`);
        
        // Update the displayed position
        this.currentlyDisplayedPosition = {...currentStep};
        
        // Update map visually
        this.updateMapPositionDirectly();
        
        // Add to trail
        this.addStepToTrail(currentStep);
        
        // Update position info gradually
        this.updatePositionInfoGradually();
        
        // Move to next step
        this.currentPathStep++;
        
        // Schedule next step
        setTimeout(() => {
            this.animateNextStep();
        }, this.stepAnimationDuration);
    }
    
    finishPathAnimation() {
        console.log('✅ Path animation completed');
        
        this.isAnimatingPath = false;
        this.pathAnimationQueue = [];
        this.currentPathStep = 0;
        
        // Ensure we're at the final position
        if (this.currentPosition) {
            this.currentlyDisplayedPosition = {...this.currentPosition};
            this.updateMapPositionDirectly();
        }
        
        // Final updates
        this.updatePositionInfoWithAnimation(0);
        this.updateNearbyShelves();
        this.updateBeaconInfoWithAnimation(0);
        
        // Show completion notification on mobile
        if (this.isMobile) {
            this.showNotification('📍 Đã đến vị trí mới', 'success');
        }
    }
    
    updateMapPositionDirectly() {
        if (!this.currentlyDisplayedPosition || !this.mapData) return;
        
        try {
            // Remove old user position with more robust selection
            const oldUserCells = document.querySelectorAll('.cell-user');
            oldUserCells.forEach(cell => {
                cell.classList.remove('cell-user');
                cell.textContent = '';
                cell.title = '';
            });
            
            // Add new user position
            const { x, y } = this.currentlyDisplayedPosition;
            const cell = document.querySelector(`[data-row="${x}"][data-col="${y}"]`);
            
            if (cell) {
                cell.classList.add('cell-user');
                cell.textContent = '👤';
                cell.title = `Vị trí của bạn (${x}, ${y})`;
                
                // Add moving animation class during path animation
                if (this.isAnimatingPath) {
                    cell.classList.add('path-moving');
                    cell.style.transition = `all ${this.stepAnimationDuration * 0.8}ms ease-in-out`;
                } else {
                    cell.classList.remove('path-moving');
                    cell.style.transition = '';
                }
                
                console.log(`🗺️ Map position updated to (${x}, ${y})`);
            } else {
                console.warn(`⚠️ Could not find cell for position (${x}, ${y})`);
            }
        } catch (error) {
            console.error('❌ Error updating map position:', error);
        }
    }
    
    addStepToTrail(step) {
        // Add current step to trail
        this.userTrails.push({ 
            x: step.x, 
            y: step.y, 
            timestamp: Date.now(),
            isPathStep: true 
        });
        
        // Limit trail length
        if (this.userTrails.length > this.maxTrails) {
            this.userTrails.shift();
        }
        
        // Update trail visualization
        this.renderUserTrails();
    }
    
    updatePositionInfoGradually() {
        if (!this.currentlyDisplayedPosition || !this.currentPosition) return;
        
        const positionInfo = document.getElementById('currentPosition');
        const positionDetails = document.getElementById('positionDetails');
        
        if (positionInfo) {
            positionInfo.textContent = `📍 (${this.currentlyDisplayedPosition.x}, ${this.currentlyDisplayedPosition.y}) - Di chuyển...`;
        }
        
        if (positionDetails && this.currentPosition.last_beacon) {
            const pos = this.currentPosition;
            positionDetails.innerHTML = `
                <p><strong>🎯 Tọa độ hiện tại:</strong> (${this.currentlyDisplayedPosition.x}, ${this.currentlyDisplayedPosition.y})</p>
                <p><strong>🎯 Tọa độ đích:</strong> (${pos.x}, ${pos.y})</p>
                <p><strong>📡 Beacon:</strong> ${pos.last_beacon}</p>
                <p><strong>📏 Khoảng cách:</strong> ${pos.distance_to_beacon}m</p>
                <p><strong>📶 RSSI:</strong> ${pos.rssi} dBm</p>
                <p><strong>🚶 Trạng thái:</strong> <span style="color: #f39c12;">● Đang di chuyển</span></p>
            `;
        }
    }

    animatePositionChangeWithDuration(duration) {
        // Add moving animation to user cell with custom duration
        const userCells = document.querySelectorAll('.cell-user');
        userCells.forEach(cell => {
            cell.style.transition = `all ${duration}ms cubic-bezier(0.4, 0.0, 0.2, 1)`;
            cell.classList.add('position-transitioning');
            
            // Remove animation class after duration
            setTimeout(() => {
                cell.classList.remove('position-transitioning');
                cell.style.transition = ''; // Reset to default
            }, duration);
        });
    }

    animatePositionChange() {
        // Add moving animation to user cell
        const userCells = document.querySelectorAll('.cell-user');
        userCells.forEach(cell => {
            cell.classList.add('moving');
            setTimeout(() => {
                cell.classList.remove('moving');
            }, 2000);
        });
    }

    interpolateValue(startValue, endValue, progress) {
        if (startValue === null || endValue === null) return endValue;
        return startValue + (endValue - startValue) * progress;
    }

    animateValueChange(element, startValue, endValue, duration = 1000, formatter = null) {
        if (!element || startValue === endValue) return;
        
        const startTime = Date.now();
        const animate = () => {
            const elapsed = Date.now() - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            // Easing function for smooth animation
            const easedProgress = this.easeInOutCubic(progress);
            const currentValue = this.interpolateValue(startValue, endValue, easedProgress);
            
            // Update element content
            if (formatter) {
                element.textContent = formatter(currentValue);
            } else {
                element.textContent = currentValue.toFixed(2);
            }
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };
        
        requestAnimationFrame(animate);
    }

    easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
    }

    updatePositionInfoWithAnimation(distance = 0) {
        const positionInfo = document.getElementById('currentPosition');
        const positionDetails = document.getElementById('positionDetails');
        
        // Calculate animation duration based on distance
        const animationDuration = distance > 0 ? this.calculateAnimationDuration(distance) : 800;
        
        if (this.currentPosition && this.currentPosition.last_beacon) {
            const pos = this.currentPosition;
            
            if (positionInfo) {
                positionInfo.textContent = `📍 (${pos.x}, ${pos.y}) - ${pos.last_beacon}`;
            }
            
            if (positionDetails) {
                // Create elements for animated values
                const createAnimatedElement = (id, label, value, formatter) => {
                    return `<p><strong>${label}:</strong> <span class="position-value" id="${id}" style="transition: all ${animationDuration}ms cubic-bezier(0.4, 0.0, 0.2, 1);">${formatter ? formatter(value) : value}</span></p>`;
                };
                
                positionDetails.innerHTML = `
                    ${createAnimatedElement('coord-display', '🎯 Tọa độ', `(${pos.x}, ${pos.y})`)}
                    ${createAnimatedElement('beacon-display', '📡 Beacon', pos.last_beacon)}
                    ${createAnimatedElement('distance-display', '📏 Khoảng cách', pos.distance_to_beacon, (v) => `${v}m`)}
                    ${createAnimatedElement('rssi-display', '📶 RSSI', pos.rssi, (v) => `${Math.round(v)} dBm`)}
                    ${createAnimatedElement('time-display', '🕐 Cập nhật', new Date(pos.last_update).toLocaleTimeString())}
                `;
                
                // Animate value changes with custom duration
                this.animatePositionValues(animationDuration);
            }
        } else {
            if (positionInfo) {
                positionInfo.textContent = '📍 Vị trí: Chưa xác định';
            }
            if (positionDetails) {
                positionDetails.innerHTML = '<p>🔍 Đang tìm kiếm vị trí...</p>';
            }
        }
    }

    animatePositionValues(duration = 800) {
        if (!this.currentPosition || !this.previousPosition) return;
        
        const pos = this.currentPosition;
        const prevPos = this.previousPosition;
        
        // Animate distance change
        const distanceElement = document.getElementById('distance-display');
        if (distanceElement && prevPos.distance_to_beacon !== undefined) {
            const prevDistance = prevPos.distance_to_beacon || 0;
            const currentDistance = pos.distance_to_beacon || 0;
            
            // Add direction indicator with custom duration
            if (currentDistance > prevDistance) {
                distanceElement.classList.add('increasing');
                setTimeout(() => distanceElement.classList.remove('increasing'), duration);
            } else if (currentDistance < prevDistance) {
                distanceElement.classList.add('decreasing');
                setTimeout(() => distanceElement.classList.remove('decreasing'), duration);
            }
            
            // Animate value change with custom duration
            this.animateValueChange(
                distanceElement,
                prevDistance,
                currentDistance,
                duration,
                (value) => `${value.toFixed(2)}m`
            );
        }
        
        // Animate RSSI change
        const rssiElement = document.getElementById('rssi-display');
        if (rssiElement && prevPos.rssi !== undefined) {
            const prevRssi = prevPos.rssi || 0;
            const currentRssi = pos.rssi || 0;
            
            rssiElement.classList.add('updating');
            setTimeout(() => rssiElement.classList.remove('updating'), 1000);
            
            this.animateValueChange(
                rssiElement,
                prevRssi,
                currentRssi,
                800,
                (value) => `${Math.round(value)} dBm`
            );
        }
    }

    updatePositionInfo() {
        // Keep this method for backward compatibility
        this.updatePositionInfoWithAnimation();
    }

    updateNearbyShelves() {
        const nearbyShelves = document.getElementById('nearbyShelves');
        
        if (nearbyShelves) {
            if (this.nearbyShelves && this.nearbyShelves.length > 0) {
                nearbyShelves.innerHTML = this.nearbyShelves.map(shelf => `
                    <div class="shelf-item">
                        <h4>📦 ${shelf.id} - ${shelf.category}</h4>
                        <div class="distance">📏 Khoảng cách: ${shelf.distance}m</div>
                        <div class="products">🛍️ ${shelf.products.join(', ')}</div>
                    </div>
                `).join('');
            } else {
                nearbyShelves.innerHTML = '<p>📦 Không có kệ hàng gần đây</p>';
            }
        }
    }

    updateBeaconInfoWithAnimation(distance = 0) {
        const beaconInfo = document.getElementById('beaconInfo');
        
        // Calculate animation duration based on distance
        const animationDuration = distance > 0 ? this.calculateAnimationDuration(distance) : 800;
        
        if (beaconInfo && this.currentPosition && this.currentPosition.last_beacon) {
            const pos = this.currentPosition;
            const signalStrength = this.getSignalStrength(pos.rssi);
            const signalColor = this.getRSSIColor(pos.rssi);
            
            beaconInfo.innerHTML = `
                <p><strong>📡 Beacon ID:</strong> ${pos.last_beacon}</p>
                <p><strong>📶 Tín hiệu:</strong> <span class="rssi-value" style="background: ${signalColor}; transition: all ${animationDuration}ms cubic-bezier(0.4, 0.0, 0.2, 1);" id="beacon-rssi-display">${pos.rssi} dBm (${signalStrength})</span></p>
                <p><strong>📏 Khoảng cách:</strong> <span class="distance-value" style="transition: all ${animationDuration}ms cubic-bezier(0.4, 0.0, 0.2, 1);" id="beacon-distance-display">${pos.distance_to_beacon}m</span></p>
                <p><strong>🟢 Trạng thái:</strong> <span style="color: #27ae60;">● Kết nối</span></p>
            `;
            
            // Animate beacon values if there's a previous position
            if (this.previousPosition && this.previousPosition.rssi !== undefined) {
                const rssiDisplay = document.getElementById('beacon-rssi-display');
                const distanceDisplay = document.getElementById('beacon-distance-display');
                
                if (rssiDisplay) {
                    rssiDisplay.classList.add('updating');
                    setTimeout(() => rssiDisplay.classList.remove('updating'), 1000);
                }
                
                if (distanceDisplay) {
                    const prevDistance = this.previousPosition.distance_to_beacon || 0;
                    const currentDistance = pos.distance_to_beacon || 0;
                    
                    if (currentDistance > prevDistance) {
                        distanceDisplay.classList.add('increasing');
                        setTimeout(() => distanceDisplay.classList.remove('increasing'), 800);
                    } else if (currentDistance < prevDistance) {
                        distanceDisplay.classList.add('decreasing');
                        setTimeout(() => distanceDisplay.classList.remove('decreasing'), 800);
                    }
                }
            }
        } else {
            if (beaconInfo) {
                beaconInfo.innerHTML = '<p>🔴 Chưa kết nối beacon</p>';
            }
        }
    }

    updateBeaconInfo() {
        // Keep this method for backward compatibility
        this.updateBeaconInfoWithAnimation();
    }

    getSignalStrength(rssi) {
        if (rssi > -50) return 'Rất mạnh';
        if (rssi > -60) return 'Mạnh';
        if (rssi > -70) return 'Trung bình';
        if (rssi > -80) return 'Yếu';
        return 'Rất yếu';
    }

    getRSSIColor(rssi) {
        if (rssi > -50) return '#27ae60';
        if (rssi > -60) return '#f39c12';
        if (rssi > -70) return '#e67e22';
        return '#e74c3c';
    }

    centerMapOnUser() {
        if (!this.currentPosition) return;

        const { x, y } = this.currentPosition;
        const cell = document.querySelector(`[data-row="${x}"][data-col="${y}"]`);
        
        if (cell) {
            cell.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center', 
                inline: 'center' 
            });
        }
    }

    // ===== Map Rendering =====
    renderMap() {
        if (!this.mapData) return;

        const mapGrid = document.getElementById('mapGrid');
        if (!mapGrid) return;

        mapGrid.innerHTML = '';
        
        const { grid } = this.mapData.map_layout;
        const { width, height } = this.mapData.map_layout;

        // Adjust grid size for mobile
        const gridSize = this.isMobile ? 
            (window.innerWidth <= 360 ? 12 : window.innerWidth <= 480 ? 15 : 20) : 20;

        mapGrid.style.gridTemplateColumns = `repeat(${Math.min(width, gridSize)}, 1fr)`;
        mapGrid.style.gridTemplateRows = `repeat(${Math.min(height, gridSize)}, 1fr)`;

        // Tạo grid cells
        for (let row = 0; row < Math.min(height, gridSize); row++) {
            for (let col = 0; col < Math.min(width, gridSize); col++) {
                const cell = document.createElement('div');
                cell.className = 'map-cell';
                cell.dataset.row = row;
                cell.dataset.col = col;
                
                const cellType = grid[row] && grid[row][col] !== undefined ? grid[row][col] : 0;
                cell.classList.add(this.getCellClass(cellType));
                
                // Thêm nội dung cho cell
                const content = this.getCellContent(cellType, row, col);
                if (content) {
                    cell.textContent = content;
                }
                
                // Add touch events for mobile
                if (this.isMobile) {
                    this.addTouchEvents(cell);
                }
                
                mapGrid.appendChild(cell);
            }
        }

        // Render beacons
        this.renderBeacons();
        
        // Render current position if available
        if (this.currentPosition) {
            this.updateMapPosition();
        }
    }

    addTouchEvents(cell) {
        cell.addEventListener('touchstart', (e) => {
            e.preventDefault();
            cell.style.transform = 'scale(0.95)';
            cell.style.backgroundColor = 'rgba(102, 126, 234, 0.3)';
        });

        cell.addEventListener('touchend', (e) => {
            e.preventDefault();
            cell.style.transform = '';
            cell.style.backgroundColor = '';
        });
    }

    getCellClass(cellType) {
        switch (cellType) {
            case 0: return 'cell-empty';
            case 1: return 'cell-shelf';
            case 2: return 'cell-obstacle';
            case 3: return 'cell-empty'; // Treat beacon cells as empty to hide them
            case 4: return 'cell-entrance';
            case 5: return 'cell-checkout';
            default: return 'cell-empty';
        }
    }

    getCellContent(cellType, row, col) {
        // Beacon cells are hidden - don't render beacon content
        if (cellType === 3) { // Beacon
            return ''; // Return empty content to hide beacon
        }
        
        if (cellType === 1) { // Shelf
            // Tìm shelf tại vị trí này
            const shelf = Object.entries(this.mapData.shelves_info || {})
                .find(([id, data]) => {
                    const [shelfRow, shelfCol] = data.position;
                    const [sizeH, sizeW] = data.size;
                    return row >= shelfRow && row < shelfRow + sizeH && 
                           col >= shelfCol && col < shelfCol + sizeW;
                });
            return shelf ? shelf[0] : '';
        }
        
        if (cellType === 5) { // Checkout
            return '<i class="fas fa-cash-register"></i>';
        }
        
        return '';
    }

    renderBeacons() {
        // Beacons are hidden - don't render any beacon elements
        if (!this.mapData || !this.mapData.beacon_positions) return;

        // Comment out beacon rendering to hide beacons completely
        /*
        Object.entries(this.mapData.beacon_positions).forEach(([beaconId, beaconData]) => {
            const [row, col] = beaconData.position;
            const cell = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
            
            if (cell) {
                cell.classList.add('cell-beacon');
                cell.title = `${beaconId} - ${beaconData.area}`;
            }
        });
        */
    }

    updateMapPositionWithTransition(distance = 0) {
        if (!this.currentPosition || !this.mapData) return;

        // Calculate transition duration based on distance
        const transitionDuration = distance > 0 ? this.calculateAnimationDuration(distance) : 800;
        const fadeOutDuration = Math.min(transitionDuration * 0.3, 500); // 30% of total duration, max 500ms
        const fadeInDelay = fadeOutDuration * 0.5; // Start fading in halfway through fade out
        
        console.log(`🎬 Map transition: ${transitionDuration}ms (fadeOut: ${fadeOutDuration}ms, delay: ${fadeInDelay}ms)`);

        // Xóa vị trí cũ với fade out effect
        document.querySelectorAll('.cell-user').forEach(cell => {
            cell.style.transition = `opacity ${fadeOutDuration}ms ease-out, transform ${fadeOutDuration}ms ease-out`;
            cell.style.opacity = '0';
            cell.style.transform = 'scale(0.8)';
            
            setTimeout(() => {
                cell.classList.remove('cell-user');
                cell.style.transition = '';
                cell.style.opacity = '';
                cell.style.transform = '';
                cell.textContent = '';
            }, fadeOutDuration);
        });

        // Thêm vị trí mới với fade in effect
        setTimeout(() => {
            const { x, y } = this.currentPosition;
            const cell = document.querySelector(`[data-row="${x}"][data-col="${y}"]`);
            
            if (cell) {
                cell.classList.add('cell-user');
                cell.classList.add('position-updating');
                
                // Add distance-based animation class
                if (distance > 5) {
                    cell.classList.add('slow-transition');
                    console.log('🐌 Applying slow transition for long distance');
                } else if (distance > 2) {
                    cell.classList.add('medium-transition');
                    console.log('🚶 Applying medium transition for medium distance');
                } else if (distance > 0) {
                    cell.classList.add('fast-transition');
                    console.log('🏃 Applying fast transition for short distance');
                }
                
                cell.title = `Vị trí của bạn (${x}, ${y}) - Di chuyển: ${distance.toFixed(2)} ô`;
                cell.textContent = '👤';
                
                // Initial state for animation
                cell.style.opacity = '0';
                cell.style.transform = 'scale(0.5)';
                
                // Animate in with distance-based timing
                const fadeInDuration = Math.min(transitionDuration * 0.4, 800);
                setTimeout(() => {
                    cell.style.transition = `opacity ${fadeInDuration}ms ease-in, transform ${fadeInDuration}ms ease-in`;
                    cell.style.opacity = '1';
                    cell.style.transform = 'scale(1)';
                    
                    // Clean up classes after animation
                    setTimeout(() => {
                        cell.classList.remove('position-updating');
                        cell.classList.remove('slow-transition', 'medium-transition', 'fast-transition');
                        cell.style.transition = '';
                        cell.style.opacity = '';
                        cell.style.transform = '';
                    }, Math.max(fadeInDuration, 800));
                }, 100);
                
                // Add movement trail effect
                this.createMovementTrail(x, y);
            }
        }, this.hasSignificantPositionChange() ? 600 : 100);
    }

    createMovementTrail(x, y) {
        if (!this.previousPosition) return;
        
        const prevX = this.previousPosition.x;
        const prevY = this.previousPosition.y;
        
        // Create trail dots between previous and current position
        if (prevX !== x || prevY !== y) {
            const steps = Math.max(Math.abs(x - prevX), Math.abs(y - prevY));
            
            for (let i = 1; i <= steps; i++) {
                const trailX = prevX + Math.round((x - prevX) * (i / steps));
                const trailY = prevY + Math.round((y - prevY) * (i / steps));
                
                const trailCell = document.querySelector(`[data-row="${trailX}"][data-col="${trailY}"]`);
                if (trailCell && !trailCell.classList.contains('cell-user')) {
                    trailCell.classList.add('cell-trail');
                    trailCell.textContent = '•';
                    trailCell.style.opacity = (i / steps) * 0.6;
                    
                    // Remove trail after delay
                    setTimeout(() => {
                        trailCell.classList.remove('cell-trail');
                        trailCell.textContent = '';
                        trailCell.style.opacity = '';
                    }, 3000);
                }
            }
        }
    }

    updateMapPosition() {
        // Keep this method for backward compatibility
        this.updateMapPositionWithTransition();
    }

    addUserTrail() {
        if (!this.currentPosition) return;

        const { x, y } = this.currentPosition;
        
        // Check if position actually changed
        const lastTrail = this.userTrails[this.userTrails.length - 1];
        if (lastTrail && lastTrail.x === x && lastTrail.y === y) return;
        
        // Thêm trail mới
        this.userTrails.push({ x, y, timestamp: Date.now() });
        
        // Giới hạn số lượng trails
        if (this.userTrails.length > this.maxTrails) {
            this.userTrails.shift();
        }
        
        // Hiển thị trails trên map với smooth animation
        this.renderUserTrailsWithAnimation();
    }

    renderUserTrailsWithAnimation() {
        // Xóa trails cũ với fade out
        document.querySelectorAll('.cell-trail').forEach(cell => {
            if (!cell.classList.contains('cell-user')) {
                cell.style.transition = 'opacity 0.5s ease-out';
                cell.style.opacity = '0';
                setTimeout(() => {
                    cell.classList.remove('cell-trail', 'path-step');
                    cell.textContent = '';
                    cell.style.transition = '';
                    cell.style.opacity = '';
                }, 500);
            }
        });

        // Thêm trails mới với staggered animation (trừ vị trí hiện tại)
        setTimeout(() => {
            this.userTrails.slice(0, -1).forEach((trail, index) => {
                const cell = document.querySelector(`[data-row="${trail.x}"][data-col="${trail.y}"]`);
                if (cell && !cell.classList.contains('cell-user')) {
                    cell.classList.add('cell-trail');
                    
                    // Add path-step class if this is from path animation
                    if (trail.isPathStep) {
                        cell.classList.add('path-step');
                        cell.textContent = '→';
                    } else {
                        cell.textContent = '•';
                    }
                    
                    // Staggered fade in
                    cell.style.opacity = '0';
                    setTimeout(() => {
                        cell.style.transition = 'opacity 0.3s ease-in';
                        const opacity = trail.isPathStep ? 
                            ((index + 1) / this.userTrails.length * 0.7) : 
                            ((index + 1) / this.userTrails.length * 0.5);
                        cell.style.opacity = opacity.toString();
                        setTimeout(() => {
                            cell.style.transition = '';
                        }, 300);
                    }, index * 50); // Staggered timing
                }
            });
        }, 250);
    }

    renderUserTrails() {
        // Keep this method for backward compatibility
        this.renderUserTrailsWithAnimation();
    }

    // ===== Event Listeners =====
    setupEventListeners() {
        // Mobile control buttons
        const refreshBtn = document.getElementById('refreshPosition');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => {
                this.updatePositionFromAPI(); // Use API instead of WebSocket
                if (navigator.vibrate) navigator.vibrate(20);
            });
        }

        const centerBtn = document.getElementById('centerMap');
        if (centerBtn) {
            centerBtn.addEventListener('click', () => {
                this.centerMapOnUser();
                if (navigator.vibrate) navigator.vibrate(20);
            });
        }

        const infoBtn = document.getElementById('showInfo');
        if (infoBtn) {
            infoBtn.addEventListener('click', () => {
                this.showMobileInfo();
                if (navigator.vibrate) navigator.vibrate(20);
            });
        }

        // Click on map cells for info
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('map-cell')) {
                this.handleCellClick(e.target);
            }
        });

        // Touch events for map cells
        document.addEventListener('touchend', (e) => {
            if (e.target.classList.contains('map-cell')) {
                this.handleCellClick(e.target);
            }
        });

        // Reconnect on window focus
        window.addEventListener('focus', () => {
            if (!this.isConnected && this.socket) {
                this.socket.connect();
            }
        });

        // Handle orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.renderMap();
                this.centerMapOnUser();
            }, 500);
        });

        // Handle resize
        window.addEventListener('resize', () => {
            this.isMobile = this.detectMobile();
            setTimeout(() => {
                this.renderMap();
            }, 300);
        });

        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (this.healthCheckInterval) {
                clearInterval(this.healthCheckInterval);
            }
            if (this.socket) {
                this.socket.disconnect();
            }
        });
    }

    showMobileInfo() {
        const info = document.querySelector('.info-panel');
        if (info) {
            info.scrollIntoView({ behavior: 'smooth' });
        }
    }

    handleCellClick(cell) {
        const row = parseInt(cell.dataset.row);
        const col = parseInt(cell.dataset.col);
        
        console.log(`Clicked cell: (${row}, ${col})`);
        
        // Hiển thị thông tin chi tiết về cell
        this.showCellInfo(row, col);
    }

    showCellInfo(row, col) {
        if (!this.mapData) return;

        let info = `📍 Vị trí: (${row}, ${col})\n`;
        
        // Kiểm tra beacon
        const beacon = Object.entries(this.mapData.beacon_positions || {})
            .find(([id, data]) => data.position[0] === row && data.position[1] === col);
        
        if (beacon) {
            info += `📡 Beacon: ${beacon[0]} - ${beacon[1].area}`;
        }
        
        // Kiểm tra shelf
        const shelf = Object.entries(this.mapData.shelves_info || {})
            .find(([id, data]) => {
                const [shelfRow, shelfCol] = data.position;
                const [sizeH, sizeW] = data.size;
                return row >= shelfRow && row < shelfRow + sizeH && 
                       col >= shelfCol && col < shelfCol + sizeW;
            });
        
        if (shelf) {
            info += `📦 Kệ: ${shelf[0]} - ${shelf[1].category}\n🛍️ Sản phẩm: ${shelf[1].products.join(', ')}`;
        }
        
        // Kiểm tra landmark
        const landmark = Object.entries(this.mapData.landmarks || {})
            .find(([id, data]) => data.position[0] === row && data.position[1] === col);
        
        if (landmark) {
            info += `🏛️ Điểm: ${landmark[0]} - ${landmark[1].type}`;
        }
        
        if (info !== `📍 Vị trí: (${row}, ${col})\n`) {
            if (this.isMobile && 'showNotification' in window) {
                // Use notification API if available
                this.showNotification(info);
            } else {
                alert(info);
            }
        }
    }

    showNotification(message, type = 'info') {
        // Create a custom mobile notification với animation
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            left: 50%;
            transform: translateX(-50%) translateY(-100%);
            background: ${type === 'position' ? 'rgba(39, 174, 96, 0.95)' : type === 'success' ? 'rgba(39, 174, 96, 0.95)' : 'rgba(102, 126, 234, 0.95)'};
            color: white;
            padding: 12px 20px;
            border-radius: 25px;
            font-size: 0.9rem;
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            max-width: 90%;
            text-align: center;
            transition: transform 0.3s ease, opacity 0.3s ease;
            opacity: 0;
        `;
        notification.textContent = message;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.style.transform = 'translateX(-50%) translateY(0)';
            notification.style.opacity = '1';
        }, 100);
        
        // Animate out
        setTimeout(() => {
            notification.style.transform = 'translateX(-50%) translateY(-100%)';
            notification.style.opacity = '0';
            setTimeout(() => {
                if (document.body.contains(notification)) {
                    document.body.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }

    // Debug methods for troubleshooting
    forcePositionUpdate(data) {
        console.log('🔧 Force updating position:', data);
        this.updateUserPosition(data, true);
    }

    resetAnimation() {
        console.log('🔧 Resetting animation state');
        this.isAnimatingPath = false;
        this.pathAnimationQueue = [];
        this.currentPathStep = 0;
        this.animationStartTime = 0;
    }

    debugConnectionStatus() {
        return {
            isConnected: this.isConnected,
            hasSocket: !!this.socket,
            currentPosition: this.currentPosition,
            isAnimating: this.isAnimatingPath,
            animationStartTime: this.animationStartTime,
            timeSinceAnimationStart: this.animationStartTime ? Date.now() - this.animationStartTime : 0
        };
    }

    showPositionChangeNotification(oldPos, newPos, distance) {
        if (!oldPos || !newPos) return;
        
        const distanceChange = Math.abs((newPos.distance_to_beacon || 0) - (oldPos.distance_to_beacon || 0));
        const rssiChange = Math.abs((newPos.rssi || 0) - (oldPos.rssi || 0));
        const positionDistance = distance || 0;
        
        // Create more informative notification based on distance
        let message = '';
        if (positionDistance > 0) {
            if (positionDistance > 5) {
                message = `📍 Di chuyển xa ${positionDistance.toFixed(1)} ô - chuyển động chậm`;
            } else if (positionDistance > 2) {
                message = `📍 Di chuyển ${positionDistance.toFixed(1)} ô - tốc độ trung bình`;
            } else {
                message = `📍 Di chuyển ${positionDistance.toFixed(1)} ô - chuyển động nhanh`;
            }
        } else if (distanceChange > 1 || rssiChange > 10) {
            const direction = (newPos.distance_to_beacon || 0) > (oldPos.distance_to_beacon || 0) ? 'xa' : 'gần';
            message = `📍 Vị trí đã thay đổi - ${direction} hơn beacon`;
        }
        
        if (message) {
            this.showNotification(message, 'position');
        }
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Initializing Indoor Navigation App...');
    window.navigationApp = new IndoorNavigationApp();
    
    // Add global debug helpers
    window.debugNav = {
        getStatus: () => window.navigationApp.debugConnectionStatus(),
        forceUpdate: (data) => window.navigationApp.forcePositionUpdate(data),
        resetAnimation: () => window.navigationApp.resetAnimation(),
        requestPosition: () => window.navigationApp.requestCurrentPosition(),
        updateFromAPI: () => window.navigationApp.updatePositionFromAPI(),
        testAPI: async () => {
            const response = await fetch('/api/position/update');
            return await response.json();
        }
    };
    
    console.log('🛠️ Debug helpers available at window.debugNav');
});

// ===== Navigation Functions =====
IndoorNavigationApp.prototype.setupNavigationControls = function() {
    // Product search
    const productSearch = document.getElementById('productSearch');
    const searchBtn = document.getElementById('searchBtn');
    const searchResults = document.getElementById('searchResults');
    
    // Navigation controls
    const startX = document.getElementById('startX');
    const startY = document.getElementById('startY');
    const endX = document.getElementById('endX');
    const endY = document.getElementById('endY');
    const useCurrentBtn = document.getElementById('useCurrentBtn');
    const calculateRouteBtn = document.getElementById('calculateRouteBtn');
    const clearRouteBtn = document.getElementById('clearRouteBtn');
    
    // Load URL parameters if provided
    this.loadNavigationFromURL();
    
    // Search functionality
    const performSearch = () => {
        const query = productSearch.value.trim();
        if (query) {
            this.searchProducts(query);
        } else {
            searchResults.innerHTML = '';
        }
    };
    
    if (searchBtn) {
        searchBtn.addEventListener('click', performSearch);
    }
    
    if (productSearch) {
        productSearch.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                performSearch();
            }
        });
        
        // Auto-search as user types (with debounce)
        let searchTimeout;
        productSearch.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                if (productSearch.value.trim()) {
                    this.searchProducts(productSearch.value.trim());
                } else {
                    searchResults.innerHTML = '';
                }
            }, 500);
        });
    }
    
    // Use current position
    if (useCurrentBtn) {
        useCurrentBtn.addEventListener('click', () => {
            if (this.currentPosition) {
                startX.value = this.currentPosition.x;
                startY.value = this.currentPosition.y;
                this.showNotification('Đã sử dụng vị trí hiện tại', 'success');
            } else {
                this.showNotification('Vị trí hiện tại không khả dụng', 'error');
            }
        });
    }
    
    // Calculate route
    if (calculateRouteBtn) {
        calculateRouteBtn.addEventListener('click', () => {
            this.calculateRoute();
        });
    }
    
    // Clear route
    if (clearRouteBtn) {
        clearRouteBtn.addEventListener('click', () => {
            this.clearRoute();
        });
    }
};

IndoorNavigationApp.prototype.loadNavigationFromURL = function() {
    const urlParams = new URLSearchParams(window.location.search);
    
    const startX = urlParams.get('start_x');
    const startY = urlParams.get('start_y');
    const endX = urlParams.get('end_x');
    const endY = urlParams.get('end_y');
    const product = urlParams.get('product');
    const shelf = urlParams.get('shelf');
    
    // Fill form fields
    if (startX) document.getElementById('startX').value = startX;
    if (startY) document.getElementById('startY').value = startY;
    if (endX) document.getElementById('endX').value = endX;
    if (endY) document.getElementById('endY').value = endY;
    if (product) document.getElementById('productSearch').value = product;
    
    // Auto-calculate route if all parameters are provided
    if ((startX && startY && endX && endY) || product || shelf) {
        setTimeout(() => {
            if (product) {
                this.searchProducts(product, true);
            } else {
                this.calculateRoute();
            }
        }, 1000); // Wait for map to load
    }
};

IndoorNavigationApp.prototype.searchProducts = async function(query, autoNavigate = false) {
    try {
        const response = await fetch(`/api/navigation/products?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        if (data.status === 'success') {
            this.displaySearchResults(data.results, autoNavigate);
        } else {
            this.showNotification('Lỗi tìm kiếm sản phẩm', 'error');
        }
    } catch (error) {
        console.error('Error searching products:', error);
        this.showNotification('Lỗi kết nối khi tìm kiếm', 'error');
    }
};

IndoorNavigationApp.prototype.displaySearchResults = function(results, autoNavigate = false) {
    const searchResults = document.getElementById('searchResults');
    
    if (results.length === 0) {
        searchResults.innerHTML = '<div class="no-results">Không tìm thấy sản phẩm nào</div>';
        return;
    }
    
    searchResults.innerHTML = results.map(result => `
        <div class="search-result-item" data-shelf="${result.shelf_id}" data-x="${result.position[0]}" data-y="${result.position[1]}">
            <div class="search-result-info">
                <div class="search-result-product">${result.product}</div>
                <div class="search-result-details">Kệ ${result.shelf_id} - ${result.category}</div>
            </div>
            <button class="search-result-action" onclick="window.navigationApp.navigateToProduct('${result.shelf_id}', ${result.position[0]}, ${result.position[1]})">
                Dẫn đường
            </button>
        </div>
    `).join('');
    
    // Auto-navigate to first result if requested
    if (autoNavigate && results.length > 0) {
        const firstResult = results[0];
        this.navigateToProduct(firstResult.shelf_id, firstResult.position[0], firstResult.position[1]);
    }
};

IndoorNavigationApp.prototype.navigateToProduct = function(shelfId, x, y) {
    // Set destination coordinates
    document.getElementById('endX').value = x;
    document.getElementById('endY').value = y;
    
    // Use current position as start if available
    if (this.currentPosition) {
        document.getElementById('startX').value = this.currentPosition.x;
        document.getElementById('startY').value = this.currentPosition.y;
    }
    
    // Calculate route
    this.calculateRoute();
    
    this.showNotification(`Dẫn đường đến kệ ${shelfId}`, 'success');
};

IndoorNavigationApp.prototype.calculateRoute = async function() {
    const startX = parseInt(document.getElementById('startX').value);
    const startY = parseInt(document.getElementById('startY').value);
    const endX = parseInt(document.getElementById('endX').value);
    const endY = parseInt(document.getElementById('endY').value);
    
    if (isNaN(startX) || isNaN(startY) || isNaN(endX) || isNaN(endY)) {
        this.showNotification('Vui lòng nhập đầy đủ tọa độ', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/navigation/route', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                start: { x: startX, y: startY },
                end: { x: endX, y: endY }
            })
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            this.displayRoute(data);
            this.showNotification('Đã tính toán đường đi thành công!', 'success');
        } else {
            this.showNotification(data.message || 'Không thể tính toán đường đi', 'error');
        }
    } catch (error) {
        console.error('Error calculating route:', error);
        this.showNotification('Lỗi khi tính toán đường đi', 'error');
    }
};

IndoorNavigationApp.prototype.displayRoute = function(routeData) {
    // Store route data
    this.currentRoute = routeData.path;
    this.routeStartPosition = routeData.start;
    this.routeEndPosition = routeData.end;
    
    // Clear previous route visualization
    this.clearRouteVisualization();
    
    // Visualize route on map
    this.visualizeRoute(routeData.path, routeData.start, routeData.end);
    
    // Generate and display directions
    this.displayDirections(routeData);
    
    // Show directions section
    const directionsSection = document.getElementById('directionsSection');
    if (directionsSection) {
        directionsSection.style.display = 'block';
    }
};

IndoorNavigationApp.prototype.visualizeRoute = function(path, start, end) {
    // Mark start position
    const startCell = document.querySelector(`[data-row="${start.x}"][data-col="${start.y}"]`);
    if (startCell) {
        startCell.classList.add('route-start');
        startCell.textContent = '🏁';
        startCell.title = `Điểm bắt đầu (${start.x}, ${start.y})`;
    }
    
    // Mark end position
    const endCell = document.querySelector(`[data-row="${end.x}"][data-col="${end.y}"]`);
    if (endCell) {
        endCell.classList.add('route-end');
        endCell.textContent = '🎯';
        endCell.title = `Điểm đến (${end.x}, ${end.y})`;
    }
    
    // Mark path (excluding start and end)
    path.forEach((point, index) => {
        if (index > 0 && index < path.length - 1) {
            const cell = document.querySelector(`[data-row="${point.x}"][data-col="${point.y}"]`);
            if (cell) {
                cell.classList.add('route-path');
                cell.textContent = '→';
                cell.title = `Đường đi bước ${index}`;
            }
        }
    });
};

IndoorNavigationApp.prototype.displayDirections = function(routeData) {
    const directionsList = document.getElementById('directionsList');
    const routeInfo = document.getElementById('routeInfo');
    
    if (!directionsList || !routeInfo) return;
    
    // Generate step-by-step directions
    const directions = this.generateDirections(routeData.path);
    
    directionsList.innerHTML = directions.map((direction, index) => `
        <div class="direction-step">
            <strong>Bước ${index + 1}:</strong> ${direction}
        </div>
    `).join('');
    
    routeInfo.innerHTML = `
        <div class="route-info-item">
            <span>📏</span>
            <span>Khoảng cách: ${routeData.distance} bước</span>
        </div>
        <div class="route-info-item">
            <span>⏱️</span>
            <span>Thời gian ước tính: ${Math.round(routeData.estimated_time / 60)} phút</span>
        </div>
    `;
};

IndoorNavigationApp.prototype.generateDirections = function(path) {
    if (path.length < 2) {
        return ['Bạn đã ở đúng vị trí đích!'];
    }
    
    const directions = [];
    
    for (let i = 0; i < path.length - 1; i++) {
        const current = path[i];
        const next = path[i + 1];
        
        const dx = next.x - current.x;
        const dy = next.y - current.y;
        
        let direction = '';
        if (dx === 1) direction = 'Đi xuống';
        else if (dx === -1) direction = 'Đi lên';
        else if (dy === 1) direction = 'Đi sang phải';
        else if (dy === -1) direction = 'Đi sang trái';
        
        if (direction) {
            directions.push(`${direction} đến vị trí (${next.x}, ${next.y})`);
        }
    }
    
    directions.push('🎉 Bạn đã đến đích!');
    return directions;
};

IndoorNavigationApp.prototype.clearRoute = function() {
    // Clear route data
    this.currentRoute = null;
    this.routeStartPosition = null;
    this.routeEndPosition = null;
    
    // Clear form fields
    document.getElementById('startX').value = '';
    document.getElementById('startY').value = '';
    document.getElementById('endX').value = '';
    document.getElementById('endY').value = '';
    document.getElementById('productSearch').value = '';
    document.getElementById('searchResults').innerHTML = '';
    
    // Clear route visualization
    this.clearRouteVisualization();
    
    // Hide directions
    const directionsSection = document.getElementById('directionsSection');
    if (directionsSection) {
        directionsSection.style.display = 'none';
    }
    
    this.showNotification('Đã xóa đường đi', 'info');
};

IndoorNavigationApp.prototype.clearRouteVisualization = function() {
    // Remove route classes from all cells
    document.querySelectorAll('.route-path, .route-start, .route-end').forEach(cell => {
        cell.classList.remove('route-path', 'route-start', 'route-end');
        if (cell.textContent === '→' || cell.textContent === '🏁' || cell.textContent === '🎯') {
            cell.textContent = '';
        }
        // Reset title if it was a route-related title
        if (cell.title && (cell.title.includes('Điểm') || cell.title.includes('Đường đi'))) {
            cell.title = '';
        }
    });
};

// Export for debugging
if (typeof module !== 'undefined' && module.exports) {
    module.exports = IndoorNavigationApp;
}
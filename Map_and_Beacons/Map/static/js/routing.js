/**
 * Indoor routing system
 * Handles path finding between points on the indoor map
 */

class RoutingSystem {
    constructor(mapView) {
        this.mapView = mapView;
        this.map = mapView.map;
        this.routeLayer = null;
        this.routeFeature = null;
        this.startPoint = null;
        this.endPoint = null;
        this.waypoints = [];
        this.navigationActive = false;
        this.currentRoute = [];
        this.nextWaypointIndex = 0;
        
        // Navigation instructions
        this.instructions = [];
        this.currentInstructionIndex = 0;
        
        // Initialize the route layer
        this._initRouteLayer();
    }

    _initRouteLayer() {
        // Create vector source for route
        const routeSource = new ol.source.Vector();
        
        // Create route layer
        this.routeLayer = new ol.layer.Vector({
            source: routeSource,
            style: new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: '#ff6600',
                    width: 4,
                    lineDash: [0.5, 5]
                })
            }),
            zIndex: 10 // Make sure route is on top
        });
        
        // Add route layer to map
        this.map.addLayer(this.routeLayer);
    }

    // Set start point for routing
    setStartPoint(coordinate) {
        this.startPoint = coordinate;
        this._updateRouteDisplay();
        return this;
    }

    // Set end point for routing
    setEndPoint(coordinate) {
        this.endPoint = coordinate;
        this._updateRouteDisplay();
        this._calculateRoute();
        return this;
    }

    // Add a waypoint to the route
    addWaypoint(coordinate) {
        this.waypoints.push(coordinate);
        this._updateRouteDisplay();
        this._calculateRoute();
        return this;
    }

    // Clear all routing points
    clearRoute() {
        this.startPoint = null;
        this.endPoint = null;
        this.waypoints = [];
        this.routeLayer.getSource().clear();
        this.currentRoute = [];
        this.instructions = [];
        this.navigationActive = false;
        return this;
    }

    // Calculate the route between points
    _calculateRoute() {
        if (!this.startPoint || !this.endPoint) {
            return;
        }

        // Simplified pathfinding for indoor environment
        // Uses A* algorithm adapted for the indoor environment
        this.currentRoute = this._findPath(this.startPoint, this.endPoint);
        
        // Generate route instructions
        this._generateInstructions();
        
        // Show the calculated route
        this._displayRoute();
    }

    // A* pathfinding algorithm adapted for indoor environment
    _findPath(start, end) {
        // For this demo, we'll implement a simplified pathfinding
        // that avoids obstacles defined in the map
        
        // Get all shelves and obstacles from the map
        const obstacles = this._getObstacles();
        
        // Basic grid-based A* pathfinding
        const gridSize = 1.0; // 1 meter grid
        const maxX = 50;
        const maxY = 30;
        
        // Generate grid
        const grid = Array(Math.ceil(maxY/gridSize)).fill()
            .map(() => Array(Math.ceil(maxX/gridSize)).fill(1));
        
        // Mark obstacles in the grid
        obstacles.forEach(obstacle => {
            const coords = obstacle.getGeometry().getCoordinates()[0];
            coords.forEach(coord => {
                const x = Math.floor(coord[0] / gridSize);
                const y = Math.floor(coord[1] / gridSize);
                if (x >= 0 && x < grid[0].length && y >= 0 && y < grid.length) {
                    grid[y][x] = 0; // Mark as obstacle
                }
            });
        });
        
        // A* implementation for grid
        const openSet = [];
        const closedSet = new Set();
        const startX = Math.floor(start[0] / gridSize);
        const startY = Math.floor(start[1] / gridSize);
        const endX = Math.floor(end[0] / gridSize);
        const endY = Math.floor(end[1] / gridSize);
        
        openSet.push({
            x: startX,
            y: startY,
            g: 0,
            h: this._heuristic([startX, startY], [endX, endY]),
            parent: null
        });
        
        while (openSet.length > 0) {
            // Find node with lowest f score
            let currentIndex = 0;
            for (let i = 0; i < openSet.length; i++) {
                if (openSet[i].g + openSet[i].h < openSet[currentIndex].g + openSet[currentIndex].h) {
                    currentIndex = i;
                }
            }
            
            const current = openSet[currentIndex];
            
            // Check if we reached the end
            if (current.x === endX && current.y === endY) {
                // Reconstruct path
                const path = [];
                let temp = current;
                while (temp !== null) {
                    path.push([temp.x * gridSize + gridSize/2, temp.y * gridSize + gridSize/2]);
                    temp = temp.parent;
                }
                return path.reverse();
            }
            
            // Remove current from open set and add to closed set
            openSet.splice(currentIndex, 1);
            closedSet.add(`${current.x},${current.y}`);
            
            // Check neighbors
            const directions = [
                [0, 1], [1, 0], [0, -1], [-1, 0], // Cardinal directions
                [1, 1], [1, -1], [-1, -1], [-1, 1] // Diagonals
            ];
            
            for (const [dx, dy] of directions) {
                const newX = current.x + dx;
                const newY = current.y + dy;
                
                // Skip if out of bounds
                if (newX < 0 || newX >= grid[0].length || newY < 0 || newY >= grid.length) {
                    continue;
                }
                
                // Skip if it's an obstacle
                if (grid[newY][newX] === 0) {
                    continue;
                }
                
                // Skip if in closed set
                if (closedSet.has(`${newX},${newY}`)) {
                    continue;
                }
                
                // Calculate g score
                const diagonal = dx !== 0 && dy !== 0;
                const moveCost = diagonal ? 1.4 : 1.0;
                const g = current.g + moveCost;
                
                // Check if this path is better
                let inOpenSet = false;
                for (let i = 0; i < openSet.length; i++) {
                    if (openSet[i].x === newX && openSet[i].y === newY) {
                        inOpenSet = true;
                        if (g < openSet[i].g) {
                            openSet[i].g = g;
                            openSet[i].parent = current;
                        }
                        break;
                    }
                }
                
                if (!inOpenSet) {
                    openSet.push({
                        x: newX,
                        y: newY,
                        g: g,
                        h: this._heuristic([newX, newY], [endX, endY]),
                        parent: current
                    });
                }
            }
        }
        
        // No path found, return direct line
        return [start, end];
    }

    // Heuristic for A* (Manhattan distance)
    _heuristic(a, b) {
        return Math.abs(a[0] - b[0]) + Math.abs(a[1] - b[1]);
    }
    
    // Get all obstacles from the map
    _getObstacles() {
        const obstacles = [];
        this.map.getLayers().forEach(layer => {
            if (layer instanceof ol.layer.Vector && layer !== this.routeLayer && layer !== this.mapView.traceLayer) {
                layer.getSource().getFeatures().forEach(feature => {
                    const geometry = feature.getGeometry();
                    if (geometry instanceof ol.geom.Polygon) {
                        obstacles.push(feature);
                    }
                });
            }
        });
        return obstacles;
    }

    // Update markers for start, end, and waypoints
    _updateRouteDisplay() {
        // Clear existing route markers
        this.routeLayer.getSource().clear();
        
        // Add start marker if exists
        if (this.startPoint) {
            const startMarker = new ol.Feature({
                geometry: new ol.geom.Point(this.startPoint),
                name: 'Start'
            });
            startMarker.setStyle(new ol.style.Style({
                image: new ol.style.Circle({
                    radius: 6,
                    fill: new ol.style.Fill({ color: '#00ff00' }),
                    stroke: new ol.style.Stroke({ color: '#fff', width: 2 })
                }),
                text: new ol.style.Text({
                    text: 'Xuất phát',
                    offsetY: -15,
                    fill: new ol.style.Fill({ color: '#333' }),
                    stroke: new ol.style.Stroke({ color: '#fff', width: 3 })
                })
            }));
            this.routeLayer.getSource().addFeature(startMarker);
        }
        
        // Add end marker if exists
        if (this.endPoint) {
            const endMarker = new ol.Feature({
                geometry: new ol.geom.Point(this.endPoint),
                name: 'End'
            });
            endMarker.setStyle(new ol.style.Style({
                image: new ol.style.Circle({
                    radius: 6,
                    fill: new ol.style.Fill({ color: '#ff0000' }),
                    stroke: new ol.style.Stroke({ color: '#fff', width: 2 })
                }),
                text: new ol.style.Text({
                    text: 'Đích đến',
                    offsetY: -15,
                    fill: new ol.style.Fill({ color: '#333' }),
                    stroke: new ol.style.Stroke({ color: '#fff', width: 3 })
                })
            }));
            this.routeLayer.getSource().addFeature(endMarker);
        }
        
        // Add waypoint markers
        this.waypoints.forEach((waypoint, index) => {
            const waypointMarker = new ol.Feature({
                geometry: new ol.geom.Point(waypoint),
                name: `Waypoint ${index + 1}`
            });
            waypointMarker.setStyle(new ol.style.Style({
                image: new ol.style.Circle({
                    radius: 4,
                    fill: new ol.style.Fill({ color: '#ffcc00' }),
                    stroke: new ol.style.Stroke({ color: '#fff', width: 2 })
                }),
                text: new ol.style.Text({
                    text: `Trạm ${index + 1}`,
                    offsetY: -12,
                    fill: new ol.style.Fill({ color: '#333' }),
                    stroke: new ol.style.Stroke({ color: '#fff', width: 3 })
                })
            }));
            this.routeLayer.getSource().addFeature(waypointMarker);
        });
    }
    
    // Display the calculated route on the map
    _displayRoute() {
        if (this.currentRoute.length < 2) {
            return;
        }
        
        // Create a route feature
        this.routeFeature = new ol.Feature({
            geometry: new ol.geom.LineString(this.currentRoute)
        });
        
        this.routeLayer.getSource().addFeature(this.routeFeature);
    }
    
    // Generate navigation instructions based on the route
    _generateInstructions() {
        this.instructions = [];
        this.currentInstructionIndex = 0;
        
        if (this.currentRoute.length < 2) {
            return;
        }
        
        // Add starting instruction
        this.instructions.push({
            text: "Bắt đầu từ vị trí hiện tại",
            point: this.currentRoute[0],
            distance: 0
        });
        
        // Process route segments
        for (let i = 1; i < this.currentRoute.length - 1; i++) {
            const prevPoint = this.currentRoute[i - 1];
            const currentPoint = this.currentRoute[i];
            const nextPoint = this.currentRoute[i + 1];
            
            // Calculate directions
            const angle1 = Math.atan2(currentPoint[0] - prevPoint[0], currentPoint[1] - prevPoint[1]) * 180 / Math.PI;
            const angle2 = Math.atan2(nextPoint[0] - currentPoint[0], nextPoint[1] - currentPoint[1]) * 180 / Math.PI;
            let angleDiff = angle2 - angle1;
            
            // Normalize angle to -180 to 180
            while (angleDiff > 180) angleDiff -= 360;
            while (angleDiff < -180) angleDiff += 360;
            
            // Determine turn direction
            let direction = "";
            if (angleDiff > 20) {
                direction = "rẽ phải";
            } else if (angleDiff < -20) {
                direction = "rẽ trái";
            } else {
                direction = "đi thẳng";
            }
            
            // Find nearby POIs
            const nearbyPOI = this._findNearbyPOI(currentPoint, 3);
            
            // Create instruction
            let instructionText = `Tiếp tục ${direction}`;
            if (nearbyPOI) {
                instructionText += ` tại ${nearbyPOI.get('name')}`;
            }
            
            // Calculate distance from previous point
            const distance = this._calculateDistance(prevPoint, currentPoint);
            
            this.instructions.push({
                text: instructionText,
                point: currentPoint,
                distance: distance
            });
        }
        
        // Add final instruction
        const lastDistance = this._calculateDistance(
            this.currentRoute[this.currentRoute.length - 2], 
            this.currentRoute[this.currentRoute.length - 1]
        );
        
        this.instructions.push({
            text: "Đã đến đích",
            point: this.currentRoute[this.currentRoute.length - 1],
            distance: lastDistance
        });
    }
    
    // Find nearby POI for better instructions
    _findNearbyPOI(point, maxDistance) {
        let nearestPOI = null;
        let minDistance = maxDistance;
        
        this.map.getLayers().forEach(layer => {
            if (layer instanceof ol.layer.Vector && layer !== this.routeLayer && layer !== this.mapView.traceLayer) {
                layer.getSource().getFeatures().forEach(feature => {
                    if (feature.get('name') && feature.getGeometry() instanceof ol.geom.Point) {
                        const poiCoord = feature.getGeometry().getCoordinates();
                        const distance = this._calculateDistance(point, poiCoord);
                        
                        if (distance < minDistance) {
                            minDistance = distance;
                            nearestPOI = feature;
                        }
                    }
                });
            }
        });
        
        return nearestPOI;
    }
    
    // Calculate distance between two points
    _calculateDistance(p1, p2) {
        return Math.sqrt(Math.pow(p2[0] - p1[0], 2) + Math.pow(p2[1] - p1[1], 2));
    }
    
    // Start navigation along the calculated route
    startNavigation() {
        if (this.currentRoute.length < 2) {
            return false;
        }
        
        this.navigationActive = true;
        this.nextWaypointIndex = 1;  // Start with the first waypoint (index 0 is the starting position)
        this.currentInstructionIndex = 0;
        
        return true;
    }
    
    // Stop navigation
    stopNavigation() {
        this.navigationActive = false;
        return this;
    }
    
    // Check if user is close to the next waypoint
    updateNavigation(currentPosition) {
        if (!this.navigationActive || this.currentRoute.length < 2) {
            return null;
        }
        
        // Convert current position to array format
        const userPosition = [currentPosition.x, currentPosition.y];
        
        // Check distance to next waypoint
        const nextWaypoint = this.currentRoute[this.nextWaypointIndex];
        const distanceToWaypoint = this._calculateDistance(userPosition, nextWaypoint);
        
        // If we're close enough to the current waypoint, move to the next one
        if (distanceToWaypoint < 2.0) {  // 2 meter threshold
            this.nextWaypointIndex++;
            this.currentInstructionIndex++;
            
            // Check if we've reached the end
            if (this.nextWaypointIndex >= this.currentRoute.length) {
                this.navigationActive = false;
                return {
                    completed: true,
                    instruction: "Đã đến đích",
                    distance: 0
                };
            }
        }
        
        // Get current instruction
        const instruction = this.instructions[Math.min(this.currentInstructionIndex, this.instructions.length - 1)];
        
        // Get distance to end
        const distanceToEnd = this._calculateDistance(userPosition, this.currentRoute[this.currentRoute.length - 1]);
        
        return {
            completed: false,
            instruction: instruction.text,
            nextWaypoint: nextWaypoint,
            distanceToWaypoint: distanceToWaypoint,
            distanceToEnd: distanceToEnd
        };
    }
    
    // Get all instructions for the route
    getInstructions() {
        return this.instructions;
    }
}

export default RoutingSystem;

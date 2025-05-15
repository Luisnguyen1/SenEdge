/**
 * Indoor map implementation using OpenLayers
 */

import PositioningSystem from './positioning_system.js';
import RoutingSystem from './routing.js';
import POISystem from './poi_system.js';

class MapView {
    constructor(mapContainerId) {
        this.mapContainer = document.getElementById(mapContainerId);
        this.map = null;
        this.userMarker = null;
        this.positionSystem = new PositioningSystem();
        this.scale = 1; // pixels per meter
        this.trace = [];
        this.traceLayer = null;
        this.routingSystem = null;
        this.poiSystem = null;
        
        // Navigation status
        this.navigating = false;
        this.navigationInfo = null;
        this.navigationTimer = null;
        
        // Bind event handlers
        this.positionSystem.onPositionUpdate = this._handlePositionUpdate.bind(this);
        this.positionSystem.onHeadingUpdate = this._handleHeadingUpdate.bind(this);
        this.positionSystem.onStepDetected = this._handleStepDetected.bind(this);
    }    async initialize() {
        console.log('Initializing map view...');
        // Create custom projection for the floor plan
        const extent = [0, 0, 50, 30]; // Floor plan size in meters
        const projection = new ol.proj.Projection({
            code: 'floor-plan',
            units: 'm',
            extent: extent
        });

        // Create vector source for floor plan
        const floorPlanSource = new ol.source.Vector();
        console.log('Floor plan source created');
          // Add main walls with improved visibility
        const mainWalls = new ol.Feature({
            geometry: new ol.geom.Polygon([[
                [0, 0], [50, 0], [50, 30], [0, 30], [0, 0]
            ]])
        });
        mainWalls.setStyle(new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: '#333',
                width: 3
            }),
            fill: new ol.style.Fill({
                color: 'rgba(245, 245, 245, 0.9)'
            })
        }));
        floorPlanSource.addFeature(mainWalls);
        
        // Add grid for better visualization (10m grid)
        for (let x = 10; x < 50; x += 10) {
            const verticalLine = new ol.Feature({
                geometry: new ol.geom.LineString([[x, 0], [x, 30]])
            });
            verticalLine.setStyle(new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: 'rgba(200, 200, 200, 0.5)',
                    width: 1,
                    lineDash: [5, 5]
                })
            }));
            floorPlanSource.addFeature(verticalLine);
        }
        
        for (let y = 10; y < 30; y += 10) {
            const horizontalLine = new ol.Feature({
                geometry: new ol.geom.LineString([[0, y], [50, y]])
            });
            horizontalLine.setStyle(new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: 'rgba(200, 200, 200, 0.5)',
                    width: 1,
                    lineDash: [5, 5]
                })
            }));
            floorPlanSource.addFeature(horizontalLine);
        }// Add shelves with improved visualization
        const shelves = [
            {
                coords: [[5, 5], [15, 5], [15, 7], [5, 7]],
                name: 'Khu vực thực phẩm',
                color: '#8b4513'
            },
            {
                coords: [[20, 5], [30, 5], [30, 7], [20, 7]], 
                name: 'Khu vực đồ uống',
                color: '#9c6b30'
            },
            {
                coords: [[5, 15], [15, 15], [15, 17], [5, 17]], 
                name: 'Khu vực rau củ',
                color: '#6a994e'
            },
            {
                coords: [[20, 15], [30, 15], [30, 17], [20, 17]],
                name: 'Khu vực đồ gia dụng',
                color: '#7d4e57'
            },
            {
                coords: [[35, 5], [45, 5], [45, 7], [35, 7]],
                name: 'Khu vực điện tử',
                color: '#616161'
            },
        ];

        shelves.forEach((shelf, index) => {
            const shelfFeature = new ol.Feature({
                geometry: new ol.geom.Polygon([shelf.coords]),
                name: shelf.name
            });
            
            // Enhanced shelf styling with labels
            shelfFeature.setStyle(new ol.style.Style({
                stroke: new ol.style.Stroke({
                    color: '#5a3e2f',
                    width: 2
                }),
                fill: new ol.style.Fill({
                    color: shelf.color
                }),
                text: new ol.style.Text({
                    text: shelf.name,
                    font: '12px Arial',
                    fill: new ol.style.Fill({
                        color: '#fff'
                    }),
                    stroke: new ol.style.Stroke({
                        color: '#000',
                        width: 3
                    }),
                    overflow: true
                })
            }));
            floorPlanSource.addFeature(shelfFeature);
        });        // Add enhanced POIs with better visibility
        const pois = [
            { 
                coord: [45, 3], 
                name: 'Quầy thu ngân', 
                color: '#4CAF50',
                icon: '💰'
            },
            { 
                coord: [48, 28], 
                name: 'Nhà vệ sinh', 
                color: '#2196F3',
                icon: '🚻' 
            },
            { 
                coord: [2, 28], 
                name: 'Lối ra', 
                color: '#f44336',
                icon: '🚪' 
            },
            {
                coord: [35, 20],
                name: 'Khu vực khuyến mãi',
                color: '#E91E63',
                icon: '🏷️'
            }
        ];

        pois.forEach(poi => {
            const point = new ol.Feature({
                geometry: new ol.geom.Point(poi.coord),
                name: poi.name,
                isPOI: true,
                poiData: {
                    name: poi.name,
                    coordinates: poi.coord,
                    description: poi.name,
                    category: 'location'
                }
            });
            
            // Enhanced style for POI display
            point.setStyle([
                new ol.style.Style({
                    image: new ol.style.Circle({
                        radius: 12,
                        fill: new ol.style.Fill({
                            color: 'white'
                        }),
                        stroke: new ol.style.Stroke({
                            color: poi.color,
                            width: 3
                        })
                    }),
                }),
                new ol.style.Style({
                    text: new ol.style.Text({
                        text: poi.icon || '📍',
                        scale: 1.2,
                        offsetY: 1,
                        fill: new ol.style.Fill({
                            color: poi.color
                        })
                    })
                }),
                new ol.style.Style({
                    text: new ol.style.Text({
                        text: poi.name,
                        offsetY: -22,
                        font: 'bold 14px Roboto, Arial',
                        fill: new ol.style.Fill({
                            color: '#333'
                        }),
                        stroke: new ol.style.Stroke({
                            color: '#fff',
                            width: 4
                        }),
                        textAlign: 'center',
                        textBaseline: 'bottom'
                    })
                })
            ]);
            
            floorPlanSource.addFeature(point);
        });

        // Create user marker
        this.userMarker = new ol.Feature({
            geometry: new ol.geom.Point([25, 15]) // Start at center
        });
        this.userMarker.setStyle(new ol.style.Style({
            image: new ol.style.Circle({
                radius: 6,
                fill: new ol.style.Fill({ color: '#007bff' }),
                stroke: new ol.style.Stroke({ color: '#fff', width: 2 })
            })
        }));

        // Create trace layer
        this.traceLayer = new ol.layer.Vector({
            source: new ol.source.Vector({
                features: [this.userMarker]
            })
        });        // Create map with enhanced visibility
        console.log('Creating map with container:', this.mapContainer);
        this.map = new ol.Map({
            target: this.mapContainer,
            layers: [
                new ol.layer.Vector({
                    source: floorPlanSource,
                    style: new ol.style.Style({
                        fill: new ol.style.Fill({
                            color: 'rgba(255, 255, 255, 0.8)'
                        }),
                        stroke: new ol.style.Stroke({
                            color: '#333',
                            width: 2
                        })
                    })
                }),
                this.traceLayer
            ],            view: new ol.View({
                projection: projection,
                center: [25, 15],
                zoom: 2.5,
                maxZoom: 5,
                minZoom: 1,
                padding: [20, 20, 20, 20]
            }),
            controls: [
                new ol.control.Zoom(),
                new ol.control.ScaleLine(),
                new ol.control.ZoomSlider(),
                new ol.control.FullScreen()
            ]
        });
        
        // Log when map has been rendered
        this.map.once('rendercomplete', () => {
            console.log('Map render complete');
        });

        // Add popup for POIs
        const popupElement = document.createElement('div');
        popupElement.className = 'ol-popup';
        const popup = new ol.Overlay({
            element: popupElement,
            positioning: 'bottom-center',
            offset: [0, -10]
        });
        this.map.addOverlay(popup);

        // Show popup on hover
        this.map.on('pointermove', (e) => {
            const feature = this.map.forEachFeatureAtPixel(e.pixel, (feature) => {
                return feature;
            });
            
            if (feature && feature.get('name')) {
                popupElement.innerHTML = feature.get('name');
                popup.setPosition(e.coordinate);
                popupElement.style.display = 'block';
            } else {
                popupElement.style.display = 'none';
            }
        });        // Initialize routing system
        this.routingSystem = new RoutingSystem(this);
        
        // Initialize POI system
        this.poiSystem = new POISystem(this);
        
        // Set up navigation update timer
        this._setupNavigationUpdates();
        
        // Start tracking
        await this._requestSensorPermissions();
        this.positionSystem.startTracking();
    }

    async _requestSensorPermissions() {
        try {
            if ('DeviceMotionEvent' in window && typeof DeviceMotionEvent.requestPermission === 'function') {
                const motionPermission = await DeviceMotionEvent.requestPermission();
                console.log('Motion permission:', motionPermission);
            }
            
            if ('DeviceOrientationEvent' in window && typeof DeviceOrientationEvent.requestPermission === 'function') {
                const orientationPermission = await DeviceOrientationEvent.requestPermission();
                console.log('Orientation permission:', orientationPermission);
            }
        } catch (error) {
            console.error('Error requesting sensor permissions:', error);
        }
    }    _handlePositionUpdate(position) {
        console.log('Position update:', position);
        // Update marker position with enhanced visibility
        this.userMarker.getGeometry().setCoordinates([position.x, position.y]);
        
        // Apply a more visible style for the user marker
        this.userMarker.setStyle(new ol.style.Style({
            image: new ol.style.Circle({
                radius: 8,
                fill: new ol.style.Fill({ color: '#007bff' }),
                stroke: new ol.style.Stroke({ color: '#ffffff', width: 3 })
            })
        }));

        // Add to trace with limited history
        this.trace.push([position.x, position.y]);
        if (this.trace.length > 50) {
            // Limit the trace length to avoid performance issues
            this.trace = this.trace.slice(-50);
        }
        this._updateTrace();

        // Center map on user if needed
        this._centerMapOnUser(position.x, position.y);
        
        // Update navigation if active
        if (this.navigating && this.routingSystem) {
            const navUpdate = this.routingSystem.updateNavigation(position);
            
            if (navUpdate) {
                // If navigation completed
                if (navUpdate.completed) {
                    this.navigating = false;
                    
                    // Dispatch navigation completed event
                    const event = new CustomEvent('navigation-completed');
                    document.dispatchEvent(event);
                }
                
                // Update navigation info display
                this.navigationInfo = navUpdate;
                this._updateNavigationDisplay();
            }
        }
    }
    
    _setupNavigationUpdates() {
        // Listen for navigation start events
        document.addEventListener('navigation-started', (e) => {
            this.navigating = true;
            this.navigationInfo = {
                destination: e.detail.destination,
                instructions: e.detail.instructions,
                currentInstruction: e.detail.instructions[0],
                distanceToEnd: 0
            };
            
            // Show navigation UI
            this._showNavigationUI();
            this._updateNavigationDisplay();
        });
    }
    
    _showNavigationUI() {
        // Check if navigation panel exists, if not create it
        let navPanel = document.getElementById('navigationPanel');
        if (!navPanel) {
            navPanel = document.createElement('div');
            navPanel.id = 'navigationPanel';
            navPanel.className = 'navigation-panel';
            
            const content = `
                <div class="nav-header">
                    <h3>Đang điều hướng</h3>
                    <button id="stopNavBtn">Dừng</button>
                </div>
                <div class="nav-instruction" id="currentInstruction"></div>
                <div class="nav-distance" id="distanceInfo"></div>
            `;
            
            navPanel.innerHTML = content;
            document.body.appendChild(navPanel);
            
            // Add stop navigation handler
            document.getElementById('stopNavBtn').addEventListener('click', () => {
                this.stopNavigation();
            });
        }
        
        navPanel.style.display = 'block';
    }
    
    _updateNavigationDisplay() {
        if (!this.navigationInfo) return;
        
        const instructionElement = document.getElementById('currentInstruction');
        const distanceElement = document.getElementById('distanceInfo');
        
        if (instructionElement && distanceElement) {
            // Update instruction text
            if (this.navigationInfo.instruction) {
                instructionElement.textContent = this.navigationInfo.instruction;
            }
            
            // Update distance information
            if (this.navigationInfo.distanceToEnd !== undefined) {
                distanceElement.textContent = `Khoảng cách đến đích: ${this.navigationInfo.distanceToEnd.toFixed(1)}m`;
            }
        }
    }
    
    stopNavigation() {
        this.navigating = false;
        
        if (this.routingSystem) {
            this.routingSystem.stopNavigation();
        }
        
        // Hide navigation UI
        const navPanel = document.getElementById('navigationPanel');
        if (navPanel) {
            navPanel.style.display = 'none';
        }
        
        // Dispatch navigation stopped event
        const event = new CustomEvent('navigation-stopped');
        document.dispatchEvent(event);
    }

    _handleHeadingUpdate(heading) {
        // Update marker rotation based on heading
        const rotation = (heading * Math.PI) / 180;
        this.userMarker.setStyle(new ol.style.Style({
            image: new ol.style.Circle({
                radius: 6,
                fill: new ol.style.Fill({ color: '#007bff' }),
                stroke: new ol.style.Stroke({ color: '#fff', width: 2 })
            }),
            rotation: rotation
        }));
    }

    _handleStepDetected(stepCount, position) {
        // Update step count display if needed
        const stepCountElement = document.getElementById('stepCount');
        if (stepCountElement) {
            stepCountElement.textContent = stepCount;
        }
    }

    _updateTrace() {
        // Create a line feature for the trace
        const traceFeature = new ol.Feature({
            geometry: new ol.geom.LineString(this.trace)
        });
        traceFeature.setStyle(new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: '#007bff',
                width: 2
            })
        }));

        // Update trace layer
        this.traceLayer.getSource().clear();
        this.traceLayer.getSource().addFeatures([traceFeature, this.userMarker]);
    }

    _centerMapOnUser(x, y) {
        const view = this.map.getView();
        const extent = view.calculateExtent(this.map.getSize());
        
        // Only center if user is near the edge of the view
        const padding = 5; // meters from edge
        if (x < extent[0] + padding || x > extent[2] - padding ||
            y < extent[1] + padding || y > extent[3] - padding) {
            view.animate({
                center: [x, y],
                duration: 500
            });
        }
    }

    calibrate() {
        return this.positionSystem.calibrate();
    }

    clearTrace() {
        this.trace = [];
        this._updateTrace();
    }

    getCurrentPosition() {
        return this.positionSystem.getCurrentPosition();
    }
}

export function initMap(mapContainerId) {
    const mapView = new MapView(mapContainerId);
    return mapView;
}

export function updateUserPosition(mapView, position) {
    if (mapView && position) {
        mapView._handlePositionUpdate(position);
    }
}

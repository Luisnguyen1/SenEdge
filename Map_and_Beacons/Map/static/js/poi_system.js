/**
 * POI (Points of Interest) Information System
 * Provides detailed information about locations in the indoor map
 */

class POISystem {
    constructor(mapView) {
        this.mapView = mapView;
        this.map = mapView.map;
        this.poiList = [
            {
                id: 'checkout',
                name: 'Quầy thu ngân',
                coordinates: [45, 3],
                category: 'service',
                description: 'Khu vực thanh toán cho khách hàng.',
                icon: 'cash-register',
                services: ['Thanh toán', 'Hỗ trợ khách hàng', 'Đổi trả hàng']
            },
            {
                id: 'bathroom',
                name: 'Nhà vệ sinh',
                coordinates: [48, 28],
                category: 'facility',
                description: 'Nhà vệ sinh công cộng dành cho khách hàng.',
                icon: 'toilet',
                features: ['Phòng vệ sinh nam', 'Phòng vệ sinh nữ', 'Hỗ trợ người khuyết tật']
            },
            {
                id: 'exit',
                name: 'Lối ra',
                coordinates: [2, 28],
                category: 'navigation',
                description: 'Lối ra chính của cửa hàng.',
                icon: 'door-open',
                notes: 'Cửa ra vào tự động mở khi có người đến gần.'
            },
            {
                id: 'shelf1',
                name: 'Khu vực thực phẩm',
                coordinates: [10, 6],
                category: 'product',
                description: 'Khu vực trưng bày và bán thực phẩm.',
                icon: 'utensils',
                products: ['Thực phẩm khô', 'Đồ hộp', 'Gia vị', 'Bánh kẹo']
            },
            {
                id: 'shelf2',
                name: 'Khu vực đồ uống',
                coordinates: [25, 6],
                category: 'product',
                description: 'Khu vực trưng bày và bán đồ uống các loại.',
                icon: 'wine-bottle',
                products: ['Nước giải khát', 'Nước suối', 'Nước có ga', 'Đồ uống có cồn']
            },
            {
                id: 'shelf3',
                name: 'Khu vực rau củ',
                coordinates: [10, 16],
                category: 'product',
                description: 'Khu vực trưng bày và bán rau củ quả tươi.',
                icon: 'carrot',
                products: ['Rau xanh', 'Củ quả', 'Trái cây', 'Thảo mộc']
            },
            {
                id: 'shelf4',
                name: 'Khu vực đồ gia dụng',
                coordinates: [25, 16],
                category: 'product',
                description: 'Khu vực trưng bày và bán đồ dùng gia đình.',
                icon: 'home',
                products: ['Dụng cụ nhà bếp', 'Vật dụng phòng tắm', 'Vật dụng dọn dẹp', 'Đồ điện gia dụng nhỏ']
            },
            {
                id: 'shelf5',
                name: 'Khu vực điện tử',
                coordinates: [40, 6],
                category: 'product',
                description: 'Khu vực trưng bày và bán thiết bị điện tử.',
                icon: 'laptop',
                products: ['Điện thoại', 'Máy tính bảng', 'Phụ kiện điện tử', 'Pin và sạc']
            },
            {
                id: 'promotion1',
                name: 'Khu vực khuyến mãi',
                coordinates: [35, 20],
                category: 'promotion',
                description: 'Khu vực trưng bày sản phẩm đang khuyến mãi.',
                icon: 'tag',
                currentPromotions: ['Giảm giá 20% cho tất cả đồ uống', 'Mua 1 tặng 1 cho sản phẩm chăm sóc cá nhân']
            }
        ];

        // Initialize the POIs on the map
        this._initPOIs();
        this._setupPopups();
    }

    _initPOIs() {
        // Create POI layer if it doesn't exist
        let poiLayer = null;
        this.map.getLayers().forEach(layer => {
            if (layer.get('name') === 'poiLayer') {
                poiLayer = layer;
            }
        });

        if (!poiLayer) {
            poiLayer = new ol.layer.Vector({
                source: new ol.source.Vector(),
                name: 'poiLayer'
            });
            this.map.addLayer(poiLayer);
        }

        // Add POIs that don't already exist on the map
        this.poiList.forEach(poi => {
            // Check if POI already exists
            let poiExists = false;
            poiLayer.getSource().getFeatures().forEach(feature => {
                if (feature.get('id') === poi.id) {
                    poiExists = true;
                }
            });

            if (!poiExists) {
                const feature = new ol.Feature({
                    geometry: new ol.geom.Point(poi.coordinates),
                    id: poi.id,
                    name: poi.name,
                    category: poi.category,
                    description: poi.description,
                    icon: poi.icon,
                    ...poi
                });

                // Set icon style based on category
                let iconColor;
                switch (poi.category) {
                    case 'service':
                        iconColor = '#4CAF50';
                        break;
                    case 'facility':
                        iconColor = '#2196F3';
                        break;
                    case 'navigation':
                        iconColor = '#f44336';
                        break;
                    case 'product':
                        iconColor = '#8b4513';
                        break;
                    case 'promotion':
                        iconColor = '#E91E63';
                        break;
                    default:
                        iconColor = '#9C27B0';
                }

                feature.setStyle(new ol.style.Style({
                    image: new ol.style.Circle({
                        radius: 5,
                        fill: new ol.style.Fill({
                            color: iconColor
                        }),
                        stroke: new ol.style.Stroke({
                            color: '#fff',
                            width: 2
                        })
                    }),
                    text: new ol.style.Text({
                        text: poi.name,
                        offsetY: -15,
                        fill: new ol.style.Fill({
                            color: '#333'
                        }),
                        stroke: new ol.style.Stroke({
                            color: '#fff',
                            width: 3
                        })
                    })
                }));

                poiLayer.getSource().addFeature(feature);
            }
        });
    }

    _setupPopups() {
        // Create popup overlay for detailed POI information
        const popupElement = document.createElement('div');
        popupElement.className = 'poi-popup';
        document.body.appendChild(popupElement);

        const popup = new ol.Overlay({
            element: popupElement,
            positioning: 'bottom-center',
            offset: [0, -10],
            autoPan: true,
            autoPanAnimation: {
                duration: 250
            }
        });
        
        this.map.addOverlay(popup);

        // Handle click events on POIs
        this.map.on('click', (evt) => {
            const feature = this.map.forEachFeatureAtPixel(evt.pixel, (feature) => {
                return feature;
            });

            if (feature && feature.get('id')) {
                const poiId = feature.get('id');
                const poi = this.poiList.find(p => p.id === poiId);
                
                if (poi) {
                    this._showPOIDetails(poi, popup);
                }
            } else {
                popup.setPosition(undefined);
            }
        });
    }

    _showPOIDetails(poi, popup) {
        const popupElement = popup.getElement();
        
        // Build HTML content based on POI category
        let content = `
            <div class="poi-header">
                <h3>${poi.name}</h3>
                <span class="category">${this._getCategoryName(poi.category)}</span>
            </div>
            <p>${poi.description}</p>
        `;

        // Add category-specific information
        switch (poi.category) {
            case 'service':
                content += `<div class="services">
                    <h4>Dịch vụ:</h4>
                    <ul>
                        ${poi.services.map(service => `<li>${service}</li>`).join('')}
                    </ul>
                </div>`;
                break;
            case 'facility':
                content += `<div class="features">
                    <h4>Tiện ích:</h4>
                    <ul>
                        ${poi.features.map(feature => `<li>${feature}</li>`).join('')}
                    </ul>
                </div>`;
                break;
            case 'product':
                content += `<div class="products">
                    <h4>Sản phẩm:</h4>
                    <ul>
                        ${poi.products.map(product => `<li>${product}</li>`).join('')}
                    </ul>
                </div>`;
                break;
            case 'promotion':
                content += `<div class="promotions">
                    <h4>Khuyến mãi hiện tại:</h4>
                    <ul>
                        ${poi.currentPromotions.map(promo => `<li>${promo}</li>`).join('')}
                    </ul>
                </div>`;
                break;
        }

        // Add navigation button
        content += `
            <div class="poi-nav-buttons">
                <button onclick="window.navigateToPOI('${poi.id}')">Chỉ đường đến đây</button>
                <button onclick="window.hidePopup()">Đóng</button>
            </div>
        `;

        popupElement.innerHTML = content;
        popup.setPosition(poi.coordinates);

        // Add global functions for the buttons to work
        window.navigateToPOI = (poiId) => {
            const targetPoi = this.poiList.find(p => p.id === poiId);
            if (targetPoi && this.mapView.routingSystem) {
                // Get current user position
                const userPos = this.mapView.positionSystem.getCurrentPosition();
                
                // Clear existing route
                this.mapView.routingSystem.clearRoute();
                
                // Set start and end points
                this.mapView.routingSystem.setStartPoint([userPos.x, userPos.y]);
                this.mapView.routingSystem.setEndPoint(targetPoi.coordinates);
                
                // Start navigation
                this.mapView.routingSystem.startNavigation();
                
                // Hide popup
                popup.setPosition(undefined);
                
                // Show navigation instructions
                const event = new CustomEvent('navigation-started', { 
                    detail: { 
                        destination: targetPoi.name,
                        instructions: this.mapView.routingSystem.getInstructions() 
                    }
                });
                document.dispatchEvent(event);
            }
        };

        window.hidePopup = () => {
            popup.setPosition(undefined);
        };
    }

    _getCategoryName(category) {
        const categories = {
            'service': 'Dịch vụ',
            'facility': 'Tiện ích',
            'navigation': 'Điểm dẫn đường',
            'product': 'Khu vực sản phẩm',
            'promotion': 'Khuyến mãi'
        };
        
        return categories[category] || category;
    }

    // Get POI by ID
    getPOIById(id) {
        return this.poiList.find(poi => poi.id === id);
    }

    // Get all POIs of a specific category
    getPOIsByCategory(category) {
        return this.poiList.filter(poi => poi.category === category);
    }

    // Get all POIs
    getAllPOIs() {
        return [...this.poiList];
    }

    // Search POIs by name or description
    searchPOIs(query) {
        const lowerQuery = query.toLowerCase();
        return this.poiList.filter(poi => 
            poi.name.toLowerCase().includes(lowerQuery) || 
            poi.description.toLowerCase().includes(lowerQuery)
        );
    }
}

export default POISystem;

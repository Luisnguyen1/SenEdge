// app/static/js/map_view.js
// Indoor map implementation using OpenLayers (free and open source)
function initMap(containerId) {
    // Tạo bản đồ siêu thị với kích thước thực
    const extent = [0, 0, 50, 30]; // Kích thước siêu thị 50x30 mét
    const projection = new ol.proj.Projection({
        code: 'supermarket',
        units: 'm',
        extent: extent
    });

    // Tạo layer cho layout siêu thị
    const storeLayoutSource = new ol.source.Vector();
    
    // Thêm tường siêu thị
    const storeWalls = new ol.Feature({
        geometry: new ol.geom.Polygon([[
            [0, 0], [50, 0], [50, 30], [0, 30], [0, 0]
        ]])
    });
    storeWalls.setStyle(new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: '#333',
            width: 2
        }),
        fill: new ol.style.Fill({
            color: 'rgba(255, 255, 255, 0.5)'
        })
    }));
    storeLayoutSource.addFeature(storeWalls);

    // Thêm các kệ hàng
    const shelves = [
        [[5, 5], [15, 5], [15, 7], [5, 7]], // Kệ thực phẩm
        [[20, 5], [30, 5], [30, 7], [20, 7]], // Kệ đồ uống
        [[5, 15], [15, 15], [15, 17], [5, 17]], // Kệ rau củ
        [[20, 15], [30, 15], [30, 17], [20, 17]], // Kệ hóa phẩm
        [[35, 5], [45, 5], [45, 7], [35, 7]], // Kệ đồ gia dụng
    ];

    shelves.forEach((coords, index) => {
        const shelf = new ol.Feature({
            geometry: new ol.geom.Polygon([coords]),
            name: 'Kệ ' + (index + 1)
        });
        shelf.setStyle(new ol.style.Style({
            stroke: new ol.style.Stroke({
                color: '#5a3e2f',
                width: 1
            }),
            fill: new ol.style.Fill({
                color: '#8b4513'
            })
        }));
        storeLayoutSource.addFeature(shelf);
    });

    // Thêm các điểm quan trọng
    const pois = [
        { coord: [45, 3], name: 'Quầy thu ngân', color: '#4CAF50' },
        { coord: [48, 28], name: 'Nhà vệ sinh', color: '#2196F3' },
        { coord: [2, 28], name: 'Lối ra', color: '#f44336' }
    ];

    pois.forEach(poi => {
        const point = new ol.Feature({
            geometry: new ol.geom.Point(poi.coord),
            name: poi.name
        });
        point.setStyle(new ol.style.Style({
            image: new ol.style.Circle({
                radius: 5,
                fill: new ol.style.Fill({
                    color: poi.color
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
        storeLayoutSource.addFeature(point);
    });

    // Layer cho vị trí người dùng
    const userPosition = new ol.Feature({
        geometry: new ol.geom.Point([25, 15])
    });
    
    const userStyle = new ol.style.Style({
        image: new ol.style.Circle({
            radius: 6,
            fill: new ol.style.Fill({
                color: '#007bff'
            }),
            stroke: new ol.style.Stroke({
                color: '#fff',
                width: 2
            })
        })
    });
    userPosition.setStyle(userStyle);

    const userSource = new ol.source.Vector({
        features: [userPosition]
    });

    // Tạo map
    const map = new ol.Map({
        target: containerId,
        layers: [
            new ol.layer.Vector({
                source: storeLayoutSource
            }),
            new ol.layer.Vector({
                source: userSource
            })
        ],
        view: new ol.View({
            projection: projection,
            center: [25, 15],
            zoom: 2,
            maxZoom: 4,
            minZoom: 1
        }),
        controls: ol.control.defaults().extend([
            new ol.control.ScaleLine(),
            new ol.control.ZoomSlider()
        ])
    });

    // Thêm popup cho các điểm quan trọng
    const popup = new ol.Overlay({
        element: document.createElement('div'),
        positioning: 'bottom-center',
        offset: [0, -10]
    });
    popup.getElement().className = 'ol-popup';
    map.addOverlay(popup);

    // Hiện popup khi hover
    map.on('pointermove', function(e) {
        const feature = map.forEachFeatureAtPixel(e.pixel, function(feature) {
            return feature;
        });
        
        if (feature && feature.get('name')) {
            popup.getElement().innerHTML = feature.get('name');
            popup.setPosition(e.coordinate);
            popup.getElement().style.display = 'block';
        } else {
            popup.getElement().style.display = 'none';
        }
    });

    return {
        map: map,
        userFeature: userPosition
    };
}

function updateUserPosition(mapObj, position) {
    if (mapObj && mapObj.userFeature) {
        const point = new ol.geom.Point([position.x, position.y]);
        mapObj.userFeature.setGeometry(point);
        
        // Tự động di chuyển map theo người dùng
        mapObj.map.getView().animate({
            center: [position.x, position.y],
            duration: 500
        });
    }
}

export { initMap, updateUserPosition };
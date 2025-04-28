// Route drawing functionality using OpenLayers
let routeLayer = null;

function drawRoute(map, routeCoordinates) {
    // Xóa route cũ nếu có
    clearRoute(map);

    // Tạo feature cho đường đi
    const routeFeature = new ol.Feature({
        geometry: new ol.geom.LineString(routeCoordinates)
    });

    // Style cho đường đi
    const routeStyle = new ol.style.Style({
        stroke: new ol.style.Stroke({
            color: '#2196F3',
            width: 4
        })
    });
    routeFeature.setStyle(routeStyle);

    // Tạo layer mới cho route
    routeLayer = new ol.layer.Vector({
        source: new ol.source.Vector({
            features: [routeFeature]
        })
    });

    // Thêm điểm bắt đầu và kết thúc
    if (routeCoordinates.length > 0) {
        // Điểm bắt đầu
        const startPoint = new ol.Feature({
            geometry: new ol.geom.Point(routeCoordinates[0])
        });
        startPoint.setStyle(new ol.style.Style({
            image: new ol.style.Circle({
                radius: 7,
                fill: new ol.style.Fill({ color: '#4CAF50' }),
                stroke: new ol.style.Stroke({ color: '#fff', width: 2 })
            })
        }));

        // Điểm kết thúc
        const endPoint = new ol.Feature({
            geometry: new ol.geom.Point(routeCoordinates[routeCoordinates.length - 1])
        });
        endPoint.setStyle(new ol.style.Style({
            image: new ol.style.Circle({
                radius: 7,
                fill: new ol.style.Fill({ color: '#f44336' }),
                stroke: new ol.style.Stroke({ color: '#fff', width: 2 })
            })
        }));

        routeLayer.getSource().addFeature(startPoint);
        routeLayer.getSource().addFeature(endPoint);
    }

    // Thêm layer vào map
    map.addLayer(routeLayer);

    // Di chuyển view để nhìn thấy toàn bộ route
    const extent = routeLayer.getSource().getExtent();
    map.getView().fit(extent, {
        padding: [50, 50, 50, 50],
        duration: 1000
    });
}

function clearRoute(map) {
    if (routeLayer) {
        map.removeLayer(routeLayer);
        routeLayer = null;
    }
}

export { drawRoute, clearRoute };
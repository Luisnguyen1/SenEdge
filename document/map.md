# Dự án: Web‑based Indoor Navigation (BLE‑only)

## 1. Mục tiêu
Xây dựng ứng dụng web (PWA/SPA) cho phép người dùng định vị và dẫn đường trong siêu thị sử dụng **Web Bluetooth Scanning API** và **BLE beacons**.

## 2. Kiến trúc tổng quan

```mermaid
flowchart LR
  subgraph Browser (Client)
    A[BLE Scanner Module] --> B[Positioning Engine]
    B --> C[Map UI Module]
  end

  subgraph Backend (tuỳ chọn)
    D[API & WebSocket Server]
    E[PostGIS / Radio Map DB]
  end

  B -- optional --> D
  D --> C
```

- **Client**: PWA (HTTPS), chạy trên Chrome/Edge hỗ trợ Web BLE.
- **Backend**: Node.js + Express (tùy chọn, cho logging, radio‑map, routing).

## 3. Cấu trúc thư mục dự án (Client)

```
/src
 ├── components
 │    ├── BleScanner.js        # quản lý Web BLE Scan
 │    ├── PositioningEngine.js # trilateration & filter
 │    ├── MapView.js           # Mapbox GL JS / Leaflet
 │    └── RouteDrawer.js       # vẽ đường đi
 ├── hooks
 │    └── useBLEScan.js        # custom hook React cho BLE
 ├── utils
 │    ├── rssiToDistance.js    # hàm chuyển RSSI→distance
 │    ├── trilateration.js     # giải toạ độ
 │    └── kalmanFilter.js      # smoothing
 ├── assets
 │    └── maps
 ├── index.html
 ├── manifest.json             # PWA config
 ├── service-worker.js         # Workbox/service worker
 └── App.js

/public
 └── icons

/package.json
/webpack.config.js hoặc vite.config.js
```

## 4. Danh sách phần cứng

| Thiết bị           | Số lượng | Mô tả                                      |
|--------------------|---------:|---------------------------------------------|
| BG220-EK           | 100      | BLE iBeacon broadcaster (Bluetooth 5.2)      |
| (có sẵn)           |          |                                             |
| Smartphone/PC BLE  | tuỳ ý    | client hỗ trợ Web Bluetooth Scanning API    |
| Router/Wi-Fi       | 1        | chỉ để kết nối Internet/hosting PWA         |

> Chỉ cần **BG220-EK** và thiết bị client — phương án BLE‑only, không cần thêm gateway/server.

## 5. Sơ đồ luồng hoạt động chi tiết

1. **Khởi động PWA**
   - Service Worker đăng ký, cache static assets.
   - Người dùng cấp quyền Bluetooth.

2. **BLE Scanner Module**
   - Gọi `navigator.bluetooth.requestLEScan()` với filter UUID beacon.
   - Nhận `advertisementreceived`, lưu `{uuid, rssi, timestamp}` vào buffer.

3. **Positioning Engine**
   - Lấy N mẫu RSSI gần nhất cho mỗi beacon (window ~5–10 mẫu).
   - Tính distance = `10^((RSSI0 - rssi)/(10*n))`.
   - Chọn 3 beacon mạnh nhất, giải trilateration → (x, y).
   - Áp Kalman filter cho mượt mà.

4. **Map & UI Module**
   - Cập nhật GeoJSON source `userPosition` trên Mapbox GL JS.
   - Vẽ marker, optional: vòng bán kính sai số.
   - Nếu user yêu cầu dẫn đường đến kệ, client tính đường (A*/Dijkstra) trên graph local và vẽ path.

5. **(Tùy chọn) Logging & Analytics**
   - Đẩy vị trí/thời gian thực lên backend qua WebSocket.
   - Backend lưu log, phân tích coverage, heatmap.

## 6. Chi tiết từng module

### 6.1. BleScanner.js
```js
// Tham khảo Web Bluetooth Scanning API
export async function startScan(onAdvertisement) {
  const options = { acceptAllAdvertisements: true };
  const scan = await navigator.bluetooth.requestLEScan(options);
  navigator.bluetooth.addEventListener('advertisementreceived', event => {
    onAdvertisement({ uuid: event.uuid, rssi: event.rssi, t: Date.now() });
  });
}
```

### 6.2. PositioningEngine.js
```js
import { rssiToDistance } from '../utils/rssiToDistance';
import { trilaterate } from '../utils/trilateration';
import { KalmanFilter } from '../utils/kalmanFilter';

export function computePosition(adData) {
  // adData: [{uuid, rssi}]
  const beacons = adData.map(a => ({ ...a, d: rssiToDistance(a.rssi) }));
  const top3 = beacons.sort((a,b)=>a.d-b.d).slice(0,3);
  let { x, y } = trilaterate(top3);
  x = KalmanFilter('x').filter(x);
  y = KalmanFilter('y').filter(y);
  return { x, y };
}
```

### 6.3. MapView.js
```jsx
import mapboxgl from 'mapbox-gl';
export function initMap(containerId) {
  mapboxgl.accessToken = 'YOUR_TOKEN';
  const map = new mapboxgl.Map({ container: containerId, style: 'mapbox://styles/you/indoor', zoom: 18 });
  map.on('load', () => {
    map.addSource('user', { type: 'geojson', data: { type:'Point', coordinates: [0,0] } });
    map.addLayer({ id:'user-point', type:'circle', source:'user', paint:{'circle-radius':8} });
  });
  return map;
}

export function updateUserPosition(map, { x, y }) {
  const point = turf.point([x, y]);
  map.getSource('user').setData(point.geometry);
}
```

### 6.4. Service Worker & PWA
- Dùng Workbox để cache `index.html`, JS/CSS, Mapbox tiles.
- `manifest.json` khai báo icons, start_url, display.

---

**Với cấu trúc và luồng này**, bạn có thể triển khai POC trong 1–2 tuần, sau đó tối ưu và mở rộng. Nếu cần chi tiết code hoặc hướng dẫn triển khai cụ thể hơn, cho mình biết nhé!


// This file contains the JavaScript code for managing the Web Bluetooth scanning functionality.

async function startScan(onAdvertisement) {
    if (navigator.bluetooth && navigator.bluetooth.requestLEScan) {
        // Kiểm tra quyền vị trí nếu trình duyệt hỗ trợ
        if (navigator.permissions) {
            try {
                const status = await navigator.permissions.query({ name: 'geolocation' });
                if (status.state === 'denied') {
                    alert('Bạn cần cấp quyền vị trí cho trang web để sử dụng BLE scan. Vui lòng kiểm tra cài đặt trình duyệt.');
                    return;
                }
            } catch (e) {
                // Trình duyệt không hỗ trợ permissions cho geolocation
            }
        }
        // Yêu cầu quyền vị trí nếu chưa có
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                () => {},
                () => {
                    alert('Bạn cần cấp quyền vị trí cho trang web để sử dụng BLE scan.');
                }
            );
        }
        const options = { acceptAllAdvertisements: true };
        try {
            const scan = await navigator.bluetooth.requestLEScan(options);
            navigator.bluetooth.addEventListener('advertisementreceived', event => {
                onAdvertisement({ uuid: event.uuid, rssi: event.rssi, timestamp: Date.now() });
            });
        } catch (error) {
            console.error('Error starting BLE scan:', error);
        }
    } else {
        alert('Trình duyệt của bạn không hỗ trợ BLE scan (Web Bluetooth API)');
    }
}
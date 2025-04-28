// Hybrid positioning system that combines multiple positioning methods
class PositioningSystem {
    constructor() {
        this.currentPosition = null;
        this.lastQRPosition = null;
        this.sensors = {
            accelerometer: null,
            gyroscope: null,
            magnetometer: null
        };
        this.stepCount = 0;
        this.heading = 0;
    }

    async initialize() {
        // Initialize available positioning methods
        await this.initializeSensors();
        await this.initializeWiFi();
        await this.initializeBLE();
        this.initializeQRScanner();
    }

    async initializeSensors() {
        try {
            if ('DeviceOrientationEvent' in window && 'DeviceMotionEvent' in window) {
                // Request permission for iOS 13+ devices
                if (typeof DeviceOrientationEvent.requestPermission === 'function') {
                    const permission = await DeviceOrientationEvent.requestPermission();
                    if (permission === 'granted') {
                        this.enableSensors();
                    }
                } else {
                    this.enableSensors();
                }
            }
        } catch (error) {
            console.log('Sensors not available:', error);
        }
    }

    enableSensors() {
        window.addEventListener('devicemotion', this.handleMotion.bind(this));
        window.addEventListener('deviceorientation', this.handleOrientation.bind(this));
    }

    handleMotion(event) {
        // Step detection using accelerometer
        const acceleration = event.accelerationIncludingGravity;
        if (this.isStep(acceleration)) {
            this.stepCount++;
            this.updatePositionFromStep();
        }
    }

    handleOrientation(event) {
        // Update heading from compass
        this.heading = event.alpha || 0; // 0-360 degrees
    }

    isStep(acceleration) {
        // Simple step detection algorithm
        const magnitude = Math.sqrt(
            acceleration.x * acceleration.x +
            acceleration.y * acceleration.y +
            acceleration.z * acceleration.z
        );
        // Implement step detection logic here
        return this.detectStep(magnitude);
    }

    detectStep(magnitude) {
        // Implement your step detection algorithm
        // This is a simplified example
        const threshold = 12; // Adjust based on testing
        const minStepInterval = 250; // ms between steps
        
        if (magnitude > threshold && 
            (!this.lastStepTime || Date.now() - this.lastStepTime > minStepInterval)) {
            this.lastStepTime = Date.now();
            return true;
        }
        return false;
    }

    async initializeWiFi() {
        // Initialize WiFi scanning if available
        // Note: Web API doesn't provide direct WiFi scanning
        // This would need to be implemented server-side
        this.wifiAvailable = false;
        try {
            const response = await fetch('/api/wifi-support');
            this.wifiAvailable = await response.json();
        } catch (error) {
            console.log('WiFi positioning not available');
        }
    }

    async initializeBLE() {
        // Try to initialize BLE scanning
        if (navigator.bluetooth && navigator.bluetooth.requestLEScan) {
            try {
                await this.setupBLE();
            } catch (error) {
                console.log('BLE not available:', error);
            }
        }
    }

    initializeQRScanner() {
        // Initialize QR code scanner
        this.qrScanner = new QRScanner();
        this.qrScanner.onScan((result) => {
            this.handleQRCode(result);
        });
    }

    async setupBLE() {
        // Existing BLE setup code
        const options = { acceptAllAdvertisements: true };
        const scan = await navigator.bluetooth.requestLEScan(options);
        navigator.bluetooth.addEventListener('advertisementreceived', 
            this.handleBLEAdvertisement.bind(this)
        );
    }

    handleBLEAdvertisement(event) {
        // Process BLE beacon data
        const beaconData = {
            uuid: event.uuid,
            rssi: event.rssi,
            timestamp: Date.now()
        };
        this.updatePositionFromBLE(beaconData);
    }

    handleQRCode(qrData) {
        // Process QR code data (format: "POS:x,y")
        try {
            const [x, y] = qrData.split(':')[1].split(',').map(Number);
            this.lastQRPosition = { x, y };
            this.currentPosition = { x, y };
            this.stepCount = 0; // Reset step count at new QR scan
        } catch (error) {
            console.error('Invalid QR code format');
        }
    }

    updatePositionFromStep() {
        if (!this.currentPosition) return;

        // Update position based on step and heading
        const stepLength = 0.7; // Average step length in meters
        const dx = stepLength * Math.cos(this.heading * Math.PI / 180);
        const dy = stepLength * Math.sin(this.heading * Math.PI / 180);

        this.currentPosition.x += dx;
        this.currentPosition.y += dy;

        this.notifyPositionUpdate();
    }

    updatePositionFromBLE(beaconData) {
        // Update position using BLE beacon data if available
        // Implement your BLE positioning algorithm here
    }

    async updatePositionFromWiFi() {
        if (!this.wifiAvailable) return;
        
        try {
            const response = await fetch('/api/wifi-position');
            const position = await response.json();
            if (position) {
                this.currentPosition = position;
                this.notifyPositionUpdate();
            }
        } catch (error) {
            console.log('WiFi positioning failed:', error);
        }
    }

    notifyPositionUpdate() {
        // Notify subscribers of position update
        if (this.onPositionUpdate) {
            this.onPositionUpdate(this.currentPosition);
        }
    }

    getCurrentPosition() {
        return this.currentPosition;
    }

    onPositionUpdate(callback) {
        this.onPositionUpdate = callback;
    }
}

// Export the positioning system
export default PositioningSystem;

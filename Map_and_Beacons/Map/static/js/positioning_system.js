/**
 * Indoor Positioning System
 * Handles position tracking using beacons and sensor fusion
 */

class PositioningSystem {
    constructor() {
        this.currentPosition = { x: 25, y: 15 }; // Default starting position
        this.currentHeading = 0; // Default heading (north)
        this.stepCount = 0;
        this.beaconData = {};
        this.calibrationOffset = { x: 0, y: 0 };
        
        // Callbacks for events
        this.onPositionUpdate = null;
        this.onHeadingUpdate = null;
        this.onStepDetected = null;
        
        // Sensor data
        this._accelerometer = { x: 0, y: 0, z: 0 };
        this._gyroscope = { alpha: 0, beta: 0, gamma: 0 };
        this._lastAccelTimestamp = 0;
        this._isTracking = false;
    }

    startTracking() {
        if (this._isTracking) return;
        
        this._isTracking = true;
        
        // Start fetching beacon data
        this._startBeaconPolling();
        
        // Set up device motion event listeners if available
        if (window.DeviceMotionEvent) {
            window.addEventListener('devicemotion', this._handleMotion.bind(this));
        }
        
        // Set up device orientation event listeners if available
        if (window.DeviceOrientationEvent) {
            window.addEventListener('deviceorientation', this._handleOrientation.bind(this));
        }
        
        console.log('Position tracking started');
    }

    stopTracking() {
        this._isTracking = false;
        
        // Clear beacon polling interval
        if (this._beaconPollingInterval) {
            clearInterval(this._beaconPollingInterval);
        }
        
        // Remove event listeners
        window.removeEventListener('devicemotion', this._handleMotion);
        window.removeEventListener('deviceorientation', this._handleOrientation);
        
        console.log('Position tracking stopped');
    }

    _startBeaconPolling() {
        // Poll for beacon data every 2 seconds
        this._beaconPollingInterval = setInterval(async () => {
            try {
                const response = await fetch('/get_position');
                const data = await response.json();
                
                // Update beacon data
                this.beaconData = data.rssi_values || {};
                
                // Update position based on beacon triangulation
                if (data.position && data.position.x !== null && data.position.y !== null) {
                    this.currentPosition = {
                        x: data.position.x + this.calibrationOffset.x,
                        y: data.position.y + this.calibrationOffset.y
                    };
                    
                    // Notify listeners of position update
                    if (this.onPositionUpdate) {
                        this.onPositionUpdate(this.currentPosition);
                    }
                }
            } catch (error) {
                console.error('Error fetching beacon data:', error);
            }
        }, 2000);
    }

    _handleMotion(event) {
        // Update accelerometer data
        this._accelerometer = {
            x: event.accelerationIncludingGravity.x,
            y: event.accelerationIncludingGravity.y,
            z: event.accelerationIncludingGravity.z
        };
        
        // Step detection logic (simple threshold-based)
        this._detectSteps(event.timeStamp);
    }

    _detectSteps(timestamp) {
        // Simple step detection algorithm based on accelerometer z-axis
        const acceleration = Math.sqrt(
            Math.pow(this._accelerometer.x, 2) + 
            Math.pow(this._accelerometer.y, 2) + 
            Math.pow(this._accelerometer.z, 2)
        );
        
        const timeDiff = timestamp - this._lastAccelTimestamp;
        const STEP_THRESHOLD = 12; // Adjust based on testing
        const MIN_STEP_TIME = 300; // Minimum time between steps (ms)
        
        if (acceleration > STEP_THRESHOLD && timeDiff > MIN_STEP_TIME) {
            this.stepCount++;
            this._lastAccelTimestamp = timestamp;
            
            // Dead reckoning - update position based on step and heading
            // This is a simplified approach - in a real system, you'd use more sophisticated algorithms
            const stepLength = 0.7; // Average step length in meters
            const headingRad = (this.currentHeading * Math.PI) / 180;
            
            // Update position based on heading
            this.currentPosition.x += Math.sin(headingRad) * stepLength;
            this.currentPosition.y += Math.cos(headingRad) * stepLength;
            
            // Notify listeners
            if (this.onStepDetected) {
                this.onStepDetected(this.stepCount, this.currentPosition);
            }
            
            if (this.onPositionUpdate) {
                this.onPositionUpdate(this.currentPosition);
            }
        }
    }

    _handleOrientation(event) {
        // Update gyroscope data
        this._gyroscope = {
            alpha: event.alpha, // z-axis (0-360)
            beta: event.beta,   // x-axis (-180-180)
            gamma: event.gamma  // y-axis (-90-90)
        };
        
        // Update heading based on alpha (compass direction)
        if (event.alpha !== null) {
            this.currentHeading = event.alpha;
            
            // Notify listeners of heading update
            if (this.onHeadingUpdate) {
                this.onHeadingUpdate(this.currentHeading);
            }
        }
    }

    getCurrentPosition() {
        return { ...this.currentPosition };
    }

    getCurrentHeading() {
        return this.currentHeading;
    }

    calibrate() {
        // Use this to set the current position as a reference point
        this.calibrationOffset = { x: 0, y: 0 };
        
        return new Promise((resolve) => {
            fetch('/get_position')
                .then(response => response.json())
                .then(data => {
                    if (data.position && data.position.x !== null && data.position.y !== null) {
                        // Set calibration offset so that beacon position becomes our reference point
                        this.calibrationOffset = {
                            x: 25 - data.position.x, // Center the user at x=25
                            y: 15 - data.position.y  // Center the user at y=15
                        };
                        resolve(true);
                    } else {
                        resolve(false);
                    }
                })
                .catch(error => {
                    console.error('Calibration error:', error);
                    resolve(false);
                });
        });
    }
}

export default PositioningSystem;

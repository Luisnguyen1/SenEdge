# Indoor Positioning System using ESP32 Beacons

This project implements an indoor positioning system that determines a user's location based on WiFi signal strength (RSSI) measurements from multiple ESP32 beacons.

## System Architecture

1. **ESP32 Beacons**: Multiple ESP32 devices placed at known positions in the environment
2. **Web Server**: Flask-based server that coordinates the beacons and calculates user position
3. **Web Interface**: User interface for entering WiFi hotspot name and displaying position on a map

## Setup Instructions

### Server Setup

1. Navigate to the `Map` directory:
   ```
   cd Map_and_Beacons/Map
   ```

2. Install required Python packages:
   ```
   pip install flask
   ```

3. Run the server:
   ```
   python run.py
   ```

4. The server will start on port 5000. Open a web browser and navigate to:
   ```
   http://localhost:5000
   ```

### ESP32 Beacon Setup

You need to flash at least 3 ESP32 devices with the beacon code:

1. For each ESP32:
   - Open `ESP_beacons/src/main.cpp`
   - Edit the following configuration:
     - Update `ssid` and `password` with your local WiFi credentials
     - Set `serverUrl` to your server's IP address (e.g., "http://192.168.1.100:5000")
     - Set a unique `beaconId` for each beacon ("beacon1", "beacon2", "beacon3", etc.)

2. Build and upload the code to each ESP32 using PlatformIO:
   ```
   cd ESP_beacons
   platformio run --target upload
   ```

3. Place the beacons at known positions in your environment, matching the coordinates in the server code

4. Update the beacon positions in `Map/run.py`:
   ```python
   beacons = {
       "beacon1": {"x": 0, "y": 0},    # Position of beacon 1
       "beacon2": {"x": 10, "y": 0},   # Position of beacon 2
       "beacon3": {"x": 5, "y": 8},    # Position of beacon 3
   }
   ```

## Usage

1. Make sure the server is running and all beacons are powered on and connected to WiFi
2. On your smartphone or other device, create a WiFi hotspot
3. Open the web interface at `http://[server-ip]:5000`
4. Enter the name of your WiFi hotspot and click "Start Scanning"
5. The beacons will scan for your hotspot and send RSSI measurements to the server
6. The server will calculate your position using trilateration and display it on the map

## How It Works

1. The user enters their WiFi hotspot name in the web interface
2. The server instructs all beacons to scan for this specific hotspot
3. Each beacon measures the RSSI (signal strength) of the user's hotspot
4. Beacons send RSSI data to the server
5. The server converts RSSI values to estimated distances
6. Using trilateration, the server calculates the user's position
7. The position is displayed on the web interface map

## Troubleshooting

- If beacons cannot connect to WiFi, check the credentials in the code
- If the server cannot detect the beacons, check that they are on the same network
- For better accuracy, calibrate the RSSI-to-distance conversion parameters (RSSI0 and n)
- The more beacons you use, the more accurate the positioning will be
- For optimal results, place beacons at different angles around the area

## Map Display Troubleshooting

If the map is not displaying properly in the interface, check the following:

1. **HTML Structure**: Ensure the mobile_map.html file has the proper HTML structure and OpenLayers script is loaded correctly.

2. **CSS Styles**: The map container must have proper dimensions (width and height) for the map to be visible.

3. **Script Loading**: Make sure the OpenLayers library is loaded correctly before initializing the map.

4. **Map Initialization**: The map should be initialized after the DOM is fully loaded using:
   ```javascript
   mapView = initMap('map');
   await mapView.initialize();
   ```

5. **Console Errors**: Check the browser console for any JavaScript errors that might prevent the map from displaying.

Common issues include:
- Missing required OpenLayers CSS
- Map container not having an explicit height
- Module import errors
- Incorrect initialization sequence

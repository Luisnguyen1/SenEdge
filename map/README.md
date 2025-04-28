# Indoor Navigation Flask Project

## Overview
This project is a web-based indoor navigation application that utilizes Web Bluetooth Scanning API and BLE beacons to provide real-time positioning and navigation within indoor environments such as supermarkets.

## Features
- **Web Bluetooth Scanning**: Uses BLE beacons to determine user location.
- **Real-time Positioning**: Implements trilateration and Kalman filtering for accurate positioning.
- **Interactive Map**: Displays user location on a map and allows for route drawing.
- **Progressive Web App (PWA)**: Can be installed on devices for offline access.

## Project Structure
```
indoor-navigation-flask
├── app
│   ├── __init__.py
│   ├── routes.py
│   ├── static
│   │   ├── js
│   │   │   ├── ble_scanner.js
│   │   │   ├── positioning_engine.js
│   │   │   ├── map_view.js
│   │   │   └── route_drawer.js
│   │   └── css
│   │       └── style.css
│   ├── templates
│   │   └── index.html
│   ├── utils
│   │   ├── rssi_to_distance.py
│   │   ├── trilateration.py
│   │   └── kalman_filter.py
│   └── services
│       └── websocket.py
├── instance
│   └── config.py
├── requirements.txt
├── run.py
└── README.md
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd indoor-navigation-flask
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Running the Application
To start the Flask application, run:
```
python run.py
```
The application will be accessible at `http://localhost:5000`.

## Usage
- Open the application in a supported browser (Chrome/Edge).
- Grant Bluetooth permissions when prompted.
- The application will start scanning for BLE beacons and display the user's position on the map.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any suggestions or improvements.

## License
This project is licensed under the MIT License. See the LICENSE file for details.
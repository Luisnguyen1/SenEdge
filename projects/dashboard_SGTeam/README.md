# SenEdge Dashboard

A professional real-time dashboard for monitoring Chat Bot, Indo6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access dashboard**
   Open your browser and navigate to: `http://localhost:5000`

8. **Enable push notifications**
   - Login with credentials: `senedge` / `quyetthang`
   - Allow notification permission when prompted
   - Test notifications with: `python test_notifications.py`gation, and Security systems with 3D visualization using Flask and Three.js.

## Features

### 🤖 Chatbot Monitoring
- Real-time user activity tracking
- Conversation volume and session duration analytics
- Response time and intent recognition metrics
- Sentiment analysis visualization

### 🗺️ Indoor Navigation System
- Navigation request tracking and analytics
- Positioning accuracy monitoring
- Route completion rates
- Popular destinations and user flow analysis

### 🔒 Security System Integration
- Real-time security alert monitoring
- Access control and attempt tracking
- Glass break detection from edge devices
- Camera status and surveillance metrics
- **🔔 Real-time Push Notifications with Firebase**

### 🏢 3D Visualization
- Interactive 3D building view using Three.js
- Real-time user positions and camera locations
- Visual security system status
- Immersive navigation route visualization

### 📱 Push Notifications
- **Firebase Cloud Messaging integration**
- **Real-time glass break alerts**
- **Background notification support**
- **Cross-platform notification delivery**

## Technology Stack

- **Backend**: Python Flask with SQLite
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **3D Graphics**: Three.js
- **Charts**: Chart.js
- **Real-time Updates**: RESTful APIs with polling
- **Push Notifications**: Firebase Cloud Messaging
- **Database**: SQLite for development (easily upgradable to PostgreSQL)

## Installation

### Prerequisites
- Python 3.8+
- Modern web browser with WebGL support

### Setup Steps

1. **Clone or download the project**
   ```bash
   cd dashboard_SGTeam
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate virtual environment**
   
   Windows:
   ```bash
   venv\Scripts\activate
   ```
   
   macOS/Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure Firebase (for push notifications)**
   - Follow instructions in `FIREBASE_SETUP.md`
   - Update Firebase configuration in `app.py` and `dashboard.js`

6. **Run the application**
   ```bash
   python app.py
   ```

6. **Access dashboard**
   Open your browser and navigate to: `http://localhost:5000`

## API Documentation

### Endpoints Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/dashboard/overview` | GET | System overview and metrics |
| `/api/chatbot/metrics` | GET | Chatbot performance data |
| `/api/navigation/metrics` | GET | Navigation system data |
| `/api/security/metrics` | GET | Security system data |
| `/api/security/glass-break` | POST | **Glass break alerts from edge devices** |
| `/api/security/glass-break/events` | GET | Recent glass break events |
| `/api/register-fcm-token` | POST | **Register device for push notifications** |

### 🔴 Critical: Glass Break Alert API

**Endpoint**: `POST /api/security/glass-break`

**Purpose**: Receive glass break alerts from edge devices

**Request Format**:
```json
{
  "device_id": "EDGE_DEVICE_001",
  "location": "Building A - Floor 2 - Room 205",
  "severity": "high",
  "status": "active"
}
```

**Response**:
```json
{
  "status": "success",
  "message": "Glass break alert received and processed",
  "event_id": "EDGE_DEVICE_001"
}
```

**CURL Example**:
```bash
curl -X POST "http://localhost:5000/api/security/glass-break" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "EDGE_DEVICE_001",
    "location": "Building A - Floor 2 - Room 205",
    "severity": "high",
    "status": "active"
  }'
```

## External System Integration

### Integration Files
- `api_curl_commands.md` - Complete CURL command reference
- Ready-to-use Python scripts for each system
- Edge device integration examples

### Supported Systems
1. **Chatbot Systems** - Metrics and performance data
2. **Indoor Navigation** - Route tracking and accuracy
3. **Security Systems** - Alerts and access control
4. **Edge Devices** - Glass break detection sensors

## Dashboard Sections

### 1. Overview Dashboard
- System health status indicators
- Key performance metrics
- Real-time system overview chart
- Critical alerts summary

### 2. Chatbot Analytics
- User engagement metrics
- Response time analysis
- Intent recognition accuracy
- Sentiment analysis visualization

### 3. Navigation Monitoring
- Request volume tracking
- Accuracy and completion rates
- Popular routes analysis
- Duration statistics

### 4. Security Center
- Alert monitoring and management
- Access attempt tracking
- Camera system status
- Glass break event timeline

### 5. 3D Building View
- Interactive building visualization
- Real-time user positions
- Security camera locations
- Alert location mapping

## Code Architecture

### Backend Structure
```
app.py                 # Main Flask application
├── DatabaseManager    # SQLite database operations
├── MetricsGenerator   # Sample data generation
└── API Routes         # RESTful endpoints
```

### Frontend Structure
```
templates/dashboard.html    # Main dashboard interface
static/js/dashboard.js     # Dashboard management
├── DashboardManager      # Main controller class
├── Chart Management      # Chart.js integration
├── 3D Scene Setup        # Three.js visualization
└── Real-time Updates     # API polling and updates
```

## Customization

### Adding New Metrics
1. Add database table in `DatabaseManager.init_database()`
2. Create API endpoint in `app.py`
3. Add chart configuration in `dashboard.js`
4. Update HTML template with new section

### Modifying 3D Scene
- Edit `setup3DScene()` in `dashboard.js`
- Customize building layout in `createBuilding()`
- Add new interactive elements in Three.js scene

### Styling Changes
- Modify CSS variables in `dashboard.html`
- Update color schemes and animations
- Responsive design breakpoints

## Production Deployment

### Environment Configuration
```bash
export FLASK_ENV=production
export SECRET_KEY=your-production-secret-key
export DATABASE_URL=postgresql://user:pass@localhost/dashboard
```

### Recommended Setup
- Use PostgreSQL instead of SQLite
- Implement Redis for caching
- Add authentication middleware
- Set up SSL/HTTPS
- Configure reverse proxy (nginx)

### Security Considerations
- Add API authentication
- Implement rate limiting
- Validate all input data
- Use environment variables for secrets
- Enable CORS only for trusted domains

## Performance Optimization

### Backend Optimizations
- Database connection pooling
- Response caching with Redis
- Asynchronous processing for alerts
- Background tasks for data aggregation

### Frontend Optimizations
- Chart data pagination
- 3D scene level-of-detail
- Efficient API polling intervals
- Browser caching strategies

## Monitoring and Logging

### Application Monitoring
- Request/response logging
- Performance metrics tracking
- Error reporting and alerting
- Database query optimization

### System Health
- CPU and memory usage
- Database performance
- API response times
- WebSocket connection status

## Troubleshooting

### Common Issues

1. **Database not initializing**
   - Check file permissions
   - Verify SQLite installation
   - Review error logs

2. **3D scene not rendering**
   - Ensure WebGL support
   - Check browser console for errors
   - Verify Three.js CDN loading

3. **API calls failing**
   - Confirm Flask server is running
   - Check CORS configuration
   - Verify endpoint URLs

### Debug Mode
```bash
export FLASK_DEBUG=1
python app.py
```

## Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch
3. Make changes with tests
4. Submit pull request

### Code Standards
- Python PEP 8 compliance
- JavaScript ES6+ standards
- Comprehensive error handling
- Clear documentation

## License

This project is licensed under the MIT License. See LICENSE file for details.

## Support

For technical support or questions:
- Create an issue in the repository
- Email: support@senedge.dev
- Documentation: [Project Wiki]

---

**Dashboard Status**: ✅ Production Ready
**Last Updated**: September 1, 2025
**Version**: 1.0.0
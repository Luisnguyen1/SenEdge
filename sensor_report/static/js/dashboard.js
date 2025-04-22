document.addEventListener('DOMContentLoaded', function() {
    // Connect to WebSocket server
    const socket = io();
    const logsContainer = document.getElementById('logs-container');
    
    // Listen for sensor data updates
    socket.on('sensor_update', function(data) {
        document.getElementById('temperature-value').textContent = data.temperature + ' °C';
        document.getElementById('humidity-value').textContent = data.humidity + ' %';
        document.getElementById('pressure-value').textContent = data.pressure + ' hPa';
        document.getElementById('last-updated-time').textContent = data.last_updated;
    });
    
    // Listen for new log entries
    socket.on('new_log', function(logData) {
        // Clear the "No logs available yet" message if it exists
        const emptyLogs = document.querySelector('.empty-logs');
        if (emptyLogs) {
            emptyLogs.remove();
        }
        
        // Create log entry element
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry ${logData.method ? logData.method.toLowerCase() : ''}`;
        
        // Add timestamp
        const timestamp = document.createElement('div');
        timestamp.className = 'log-timestamp';
        timestamp.textContent = logData.timestamp;
        logEntry.appendChild(timestamp);
        
        // Add endpoint and method
        const endpoint = document.createElement('div');
        endpoint.className = 'log-endpoint';
        endpoint.textContent = `${logData.method || ''} ${logData.endpoint || ''}`;
        logEntry.appendChild(endpoint);
        
        // Add client IP
        const clientIp = document.createElement('div');
        clientIp.textContent = `Client IP: ${logData.client_ip || 'Unknown'}`;
        logEntry.appendChild(clientIp);
        
        // Add data if available
        if (logData.data) {
            const dataHeader = document.createElement('div');
            dataHeader.textContent = 'Request Data:';
            dataHeader.style.marginTop = '0.5rem';
            logEntry.appendChild(dataHeader);
            
            const dataContent = document.createElement('pre');
            dataContent.className = 'log-data';
            dataContent.textContent = JSON.stringify(logData.data, null, 2);
            logEntry.appendChild(dataContent);
        }
        
        // Add to logs container at the beginning
        logsContainer.insertBefore(logEntry, logsContainer.firstChild);
    });
    
    // Fetch initial logs
    fetch('/api/logs')
        .then(response => response.json())
        .then(logs => {
            if (logs.length > 0) {
                // Clear the "No logs available yet" message
                const emptyLogs = document.querySelector('.empty-logs');
                if (emptyLogs) {
                    emptyLogs.remove();
                }
                
                // Display logs in reverse order (newest first)
                logs.reverse().forEach(logData => {
                    // Create log entry element
                    const logEntry = document.createElement('div');
                    logEntry.className = `log-entry ${logData.method ? logData.method.toLowerCase() : ''}`;
                    
                    // Add timestamp
                    const timestamp = document.createElement('div');
                    timestamp.className = 'log-timestamp';
                    timestamp.textContent = logData.timestamp;
                    logEntry.appendChild(timestamp);
                    
                    // Add endpoint and method
                    const endpoint = document.createElement('div');
                    endpoint.className = 'log-endpoint';
                    endpoint.textContent = `${logData.method || ''} ${logData.endpoint || ''}`;
                    logEntry.appendChild(endpoint);
                    
                    // Add client IP
                    const clientIp = document.createElement('div');
                    clientIp.textContent = `Client IP: ${logData.client_ip || 'Unknown'}`;
                    logEntry.appendChild(clientIp);
                    
                    // Add data if available
                    if (logData.data) {
                        const dataHeader = document.createElement('div');
                        dataHeader.textContent = 'Request Data:';
                        dataHeader.style.marginTop = '0.5rem';
                        logEntry.appendChild(dataHeader);
                        
                        const dataContent = document.createElement('pre');
                        dataContent.className = 'log-data';
                        dataContent.textContent = JSON.stringify(logData.data, null, 2);
                        logEntry.appendChild(dataContent);
                    }
                    
                    // Add to logs container
                    logsContainer.appendChild(logEntry);
                });
            }
        })
        .catch(error => console.error('Error fetching logs:', error));
});

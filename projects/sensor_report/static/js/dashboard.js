document.addEventListener('DOMContentLoaded', function() {
    // Connect to WebSocket server
    const socket = io();
    const logsContainer = document.getElementById('logs-container');
    const deviceContainer = document.getElementById('device-container');
      // Function to show image modal
    function showImageModal(imageName, logData) {
        if (!imageName) return;
        
        // Extract information from the log entry if available
        const timestamp = logData ? logData.timestamp : '';
        const deviceId = logData ? logData.device_id || 'Unknown Device' : 'Unknown Device';
        
        // Create modal if it doesn't exist
        let imageModal = document.getElementById('image-modal');
        if (!imageModal) {
            imageModal = document.createElement('div');
            imageModal.id = 'image-modal';
            imageModal.className = 'image-modal';
            
            const modalContent = document.createElement('div');
            modalContent.className = 'modal-content';
              const modalHeader = document.createElement('div');
            modalHeader.className = 'modal-header';
            
            const modalTitle = document.createElement('div');
            modalTitle.className = 'modal-title';
            modalTitle.textContent = 'Image Viewer';
            
            const buttonsContainer = document.createElement('div');
            buttonsContainer.className = 'modal-buttons';
            
            const fullscreenBtn = document.createElement('span');
            fullscreenBtn.className = 'fullscreen-btn';
            fullscreenBtn.innerHTML = '⛶';
            fullscreenBtn.title = 'Fullscreen';
            fullscreenBtn.onclick = function() {
                if (modalImage.requestFullscreen) {
                    modalImage.requestFullscreen();
                } else if (modalImage.webkitRequestFullscreen) { /* Safari */
                    modalImage.webkitRequestFullscreen();
                } else if (modalImage.msRequestFullscreen) { /* IE11 */
                    modalImage.msRequestFullscreen();
                }
            };
            
            const closeBtn = document.createElement('span');
            closeBtn.className = 'close-modal';
            closeBtn.innerHTML = '&times;';
            closeBtn.title = 'Close';
            closeBtn.onclick = function() {
                imageModal.style.display = 'none';
            };
            
            buttonsContainer.appendChild(fullscreenBtn);
            buttonsContainer.appendChild(closeBtn);
            
            modalHeader.appendChild(modalTitle);
            modalHeader.appendChild(buttonsContainer);
              const modalImage = document.createElement('img');
            modalImage.id = 'modal-image';
            modalImage.alt = 'Detection Image';
            
            const imageInfo = document.createElement('div');
            imageInfo.className = 'image-info';
            imageInfo.id = 'modal-image-info';
              modalContent.appendChild(modalHeader);
            modalContent.appendChild(modalImage);
            modalContent.appendChild(imageInfo);
            imageModal.appendChild(modalContent);
            document.body.appendChild(imageModal);
            
            // Close modal when clicking outside the content
            window.onclick = function(event) {
                if (event.target === imageModal) {
                    imageModal.style.display = 'none';
                }
            };
        }
          // Set the image source and show the modal
        const modalImage = document.getElementById('modal-image');
        
        // Add loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'loading-indicator';
        loadingIndicator.textContent = 'Loading image...';
        
        const modalContent = document.querySelector('.modal-content');
        if (modalContent.querySelector('.loading-indicator')) {
            modalContent.querySelector('.loading-indicator').remove();
        }
        modalContent.appendChild(loadingIndicator);
        
        // Show the modal immediately
        imageModal.style.display = 'flex';
        
        // Set up image load event
        modalImage.onload = function() {
            // Remove loading indicator when image is loaded
            if (modalContent.querySelector('.loading-indicator')) {
                modalContent.querySelector('.loading-indicator').remove();
            }
        };
        
        modalImage.onerror = function() {
            // Show error message if image fails to load
            if (modalContent.querySelector('.loading-indicator')) {
                modalContent.querySelector('.loading-indicator').textContent = 'Failed to load image';
                modalContent.querySelector('.loading-indicator').className = 'loading-indicator error';
            }
        };
          // Set the image source after setting up event handlers
        modalImage.src = `/api/detections/${imageName}`;
        
        // Update image info in the modal
        const imageInfo = document.getElementById('modal-image-info');
        if (imageInfo) {
            let infoHTML = `<strong>Image:</strong> ${imageName}<br>`;
            
            if (timestamp) {
                infoHTML += `<strong>Timestamp:</strong> ${timestamp}<br>`;
            }
            
            if (deviceId) {
                infoHTML += `<strong>Device:</strong> ${deviceId}`;
            }
            
            imageInfo.innerHTML = infoHTML;
        }
    }
      // Event delegation for log entries with images
    logsContainer.addEventListener('click', function(event) {
        const logEntry = event.target.closest('.log-entry.has-image');
        if (logEntry) {
            const imageName = logEntry.getAttribute('data-image');
            if (imageName) {
                // Extract log data from the log entry DOM element
                const logData = {
                    timestamp: logEntry.querySelector('.log-timestamp')?.textContent || '',
                    endpoint: logEntry.querySelector('.log-endpoint')?.textContent || '',
                    device_id: logEntry.getAttribute('data-device-id') || 'Unknown Device'
                };
                
                showImageModal(imageName, logData);
            }
        }
    });
    
    // Listen for sensor data updates
    socket.on('sensor_update', function(data) {
        document.getElementById('temperature-value').textContent = data.temperature + ' °C';
        document.getElementById('humidity-value').textContent = data.humidity + ' %';
        document.getElementById('pressure-value').textContent = data.pressure + ' hPa';
        document.getElementById('last-updated-time').textContent = data.last_updated;
    });
    
    // Listen for device status updates
    socket.on('device_status', function(devices) {
        // Clear the "No devices connected yet" message if it exists
        const emptyDevices = deviceContainer.querySelector('.empty-devices');
        if (emptyDevices) {
            emptyDevices.remove();
        }
        
        // Update or add devices
        Object.entries(devices).forEach(([deviceId, status]) => {
            let deviceCard = document.getElementById(`device-${deviceId}`);
            
            if (!deviceCard) {
                // Create new device card if it doesn't exist
                deviceCard = document.createElement('div');
                deviceCard.className = 'device-card';
                deviceCard.id = `device-${deviceId}`;
                
                const icon = document.createElement('div');
                icon.className = 'device-icon';
                icon.textContent = '🖥️';
                
                const details = document.createElement('div');
                details.className = 'device-details';
                
                const title = document.createElement('h3');
                title.textContent = deviceId;
                
                const statusElem = document.createElement('p');
                statusElem.className = `device-status ${status.status}`;
                statusElem.id = `status-${deviceId}`;
                statusElem.textContent = `Status: ${status.status}`;
                
                const ipElem = document.createElement('p');
                ipElem.className = 'device-ip';
                ipElem.id = `ip-${deviceId}`;
                ipElem.textContent = `IP: ${status.ip}`;
                
                const lastSeenElem = document.createElement('p');
                lastSeenElem.className = 'device-last-seen';
                lastSeenElem.id = `last-seen-${deviceId}`;
                lastSeenElem.textContent = `Last seen: ${status.last_seen}`;
                
                details.appendChild(title);
                details.appendChild(statusElem);
                details.appendChild(ipElem);
                details.appendChild(lastSeenElem);
                
                deviceCard.appendChild(icon);
                deviceCard.appendChild(details);
                
                deviceContainer.appendChild(deviceCard);
            } else {
                // Update existing device card
                const statusElem = deviceCard.querySelector(`#status-${deviceId}`);
                statusElem.textContent = `Status: ${status.status}`;
                statusElem.className = `device-status ${status.status}`;
                
                const ipElem = deviceCard.querySelector(`#ip-${deviceId}`);
                ipElem.textContent = `IP: ${status.ip}`;
                
                const lastSeenElem = deviceCard.querySelector(`#last-seen-${deviceId}`);
                lastSeenElem.textContent = `Last seen: ${status.last_seen}`;
            }
        });
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
        logEntry.className = `log-entry ${logData.method ? logData.method.toLowerCase() : ''}`;        // Check if this log entry is related to an image
        const hasImage = logData.image || (logData.endpoint === '/api/person-detection' || logData.endpoint === '/api/camera-image');
        if (hasImage) {
            logEntry.classList.add('has-image');
            logEntry.setAttribute('data-image', logData.image || '');
            logEntry.style.cursor = 'pointer';
            
            // Store device ID if available
            if (logData.device_id) {
                logEntry.setAttribute('data-device-id', logData.device_id);
            }
            
            // Add visual indicator that this log entry has an image
            const imageIndicator = document.createElement('div');
            imageIndicator.className = 'image-indicator';
            imageIndicator.innerHTML = '📷 Click to view image';
            logEntry.appendChild(imageIndicator);
        }
        
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
                    logEntry.className = `log-entry ${logData.method ? logData.method.toLowerCase() : ''}`;                    // Check if this log entry is related to an image
                    const hasImage = logData.image || (logData.endpoint === '/api/person-detection' || logData.endpoint === '/api/camera-image');
                    if (hasImage) {
                        logEntry.classList.add('has-image');
                        logEntry.setAttribute('data-image', logData.image || '');
                        logEntry.style.cursor = 'pointer';
                        
                        // Store device ID if available
                        if (logData.device_id) {
                            logEntry.setAttribute('data-device-id', logData.device_id);
                        }
                        
                        // Add visual indicator that this log entry has an image
                        const imageIndicator = document.createElement('div');
                        imageIndicator.className = 'image-indicator';
                        imageIndicator.innerHTML = '📷 Click to view image';
                        logEntry.appendChild(imageIndicator);
                    }
                    
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

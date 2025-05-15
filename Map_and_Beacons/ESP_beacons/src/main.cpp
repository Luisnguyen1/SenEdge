#include "WiFi.h"
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <math.h>

// WiFi credentials for your local network
const char* ssid = "Phuong Uyen";      // Change to your WiFi SSID
const char* password = "manh123@123";  // Change to your WiFi password

// Server settings
const char* serverUrl = "http://192.168.1.188:5000";  // Change to your server IP

// ESP identifier - change this for each beacon
const char* beaconId = "beacon2";  // Change to "beacon1", "beacon2", "beacon3", etc.

// Scanning parameters
unsigned long lastScanTime = 0;
const unsigned long scanInterval = 5000;  // Scan every 5 seconds
String targetHotspot = "";
bool scanningActive = false;
void sendRssiToServer(int rssi);

void setup() {
  Serial.begin(115200);
  delay(1000);
  Serial.println("Indoor Positioning System Beacon Starting...");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

void checkForScanRequest() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected. Reconnecting...");
    WiFi.reconnect();
    delay(5000);
    return;
  }
  
  HTTPClient http;
  String url = String(serverUrl) + "/get_target_hotspot?beacon_id=" + beaconId;
  
  http.begin(url);
  int httpResponseCode = http.GET();
  
  if (httpResponseCode == 200) {
    String response = http.getString();
    
    // Parse JSON response
    DynamicJsonDocument doc(1024);
    DeserializationError error = deserializeJson(doc, response);
    
    if (!error) {
      bool active = doc["scan_active"];
      
      if (active) {
        String newTarget = doc["hotspot_name"].as<String>();
        
        if (newTarget != targetHotspot) {
          targetHotspot = newTarget;
          Serial.print("New target hotspot: ");
          Serial.println(targetHotspot);
        }
        
        scanningActive = true;
      } else {
        scanningActive = false;
      }
    } else {
      Serial.println("Failed to parse JSON response");
    }
  } else {
    Serial.print("Error checking for scan request: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void scanForHotspot() {
  if (!scanningActive || targetHotspot.length() == 0) {
    return;
  }
  
  Serial.println("Scanning for WiFi networks...");
  int n = WiFi.scanNetworks();
  
  if (n == 0) {
    Serial.println("No networks found");
  } else {
    bool found = false;
    
    for (int i = 0; i < n; ++i) {
      String foundSsid = WiFi.SSID(i);
      int rssi = WiFi.RSSI(i);
      
      if (foundSsid == targetHotspot) {
        found = true;
        Serial.print("Found target hotspot: ");
        Serial.print(targetHotspot);
        Serial.print(" with RSSI: ");
        Serial.print(rssi);
        Serial.println(" dBm");
        
        // Calculate distance (for display only)
        float RSSI0 = -45;  // RSSI at 1 meter (calibrate as needed)
        float n = 2.5;      // Path loss exponent (2-4 typically)
        float distance = pow(10.0, ((RSSI0 - rssi) / (10 * n)));
        
        Serial.print("Estimated distance: ");
        Serial.print(distance, 2);
        Serial.println(" meters");
        
        // Send RSSI to server
        sendRssiToServer(rssi);
        break;
      }
    }
    
    if (!found) {
      Serial.print("Target hotspot '");
      Serial.print(targetHotspot);
      Serial.println("' not found");
    }
  }
  
  // Free the memory used by WiFi scan
  WiFi.scanDelete();
}

void sendRssiToServer(int rssi) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected. Cannot send RSSI data.");
    return;
  }
  
  HTTPClient http;
  String url = String(serverUrl) + "/rssi";
  
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON payload
  DynamicJsonDocument doc(1024);
  doc["beacon_id"] = beaconId;
  doc["rssi"] = rssi;
  
  String payload;
  serializeJson(doc, payload);
  
  int httpResponseCode = http.POST(payload);
  
  if (httpResponseCode == 200) {
    Serial.println("RSSI data sent successfully");
  } else {
    Serial.print("Error sending RSSI data: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();
}

void loop() {
  unsigned long currentTime = millis();
  
  // Check for new scan requests
  checkForScanRequest();
  
  // Scan for hotspot at regular intervals
  if (currentTime - lastScanTime >= scanInterval) {
    lastScanTime = currentTime;
    scanForHotspot();
  }
  
  delay(1000);  // Small delay to prevent overwhelming the CPU
}

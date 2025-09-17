#include <Arduino.h>
#include "esp_camera.h"
#include <BLEDevice.h>
#include <BLEServer.h>
#include <BLEUtils.h>
#include <BLE2902.h>

// BLE UUIDs
#define SERVICE_UUID        "12345678-1234-1234-1234-1234567890ab"
#define CHARACTERISTIC_UUID "abcd1234-5678-90ab-cdef-1234567890ab"

// BLE state
BLECharacteristic *pCharacteristic;
bool deviceConnected = false;

// BLE Callbacks
class MyServerCallbacks : public BLEServerCallbacks {
  void onConnect(BLEServer* pServer) {
    deviceConnected = true;
    Serial.println("BLE client connected");
  }

  void onDisconnect(BLEServer* pServer) {
    deviceConnected = false;
    Serial.println("BLE client disconnected");
  }
};

// Khởi động camera với đúng pin của AI Thinker ESP32-CAM
void startCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = 5;
  config.pin_d1       = 18;
  config.pin_d2       = 19;
  config.pin_d3       = 21;
  config.pin_d4       = 36;
  config.pin_d5       = 39;
  config.pin_d6       = 34;
  config.pin_d7       = 35;
  config.pin_xclk     = 0;
  config.pin_pclk     = 22;
  config.pin_vsync    = 25;
  config.pin_href     = 23;
  config.pin_sscb_sda = 26;
  config.pin_sscb_scl = 27;
  config.pin_pwdn     = 32;
  config.pin_reset    = -1;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  config.frame_size   = FRAMESIZE_QQVGA;   // 160x120 (nhẹ cho BLE)
  config.jpeg_quality = 10;                // Chất lượng ảnh: thấp là tốt
  config.fb_count     = 1;

  // Khởi tạo camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  Serial.println("Camera init success");
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  startCamera();

  // BLE setup
  BLEDevice::init("ESP32-CAM");
  BLEServer *pServer = BLEDevice::createServer();
  pServer->setCallbacks(new MyServerCallbacks());

  BLEService *pService = pServer->createService(SERVICE_UUID);
  pCharacteristic = pService->createCharacteristic(
    CHARACTERISTIC_UUID,
    BLECharacteristic::PROPERTY_NOTIFY
  );
  pCharacteristic->addDescriptor(new BLE2902());
  pService->start();

  BLEAdvertising *pAdvertising = pServer->getAdvertising();
  pAdvertising->start();
  Serial.println("BLE advertising started");
}

void loop() {
  if (!deviceConnected) {
    delay(500);
    return;
  }

  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    delay(1000);
    return;
  }

  const size_t packetSize = 512; // tối đa (MTU tùy thiết bị, 20-512)
  size_t totalLen = fb->len;
  size_t offset = 0;

  Serial.printf("Sending image of %zu bytes\n", totalLen);

  while (offset < totalLen) {
    size_t len = min(packetSize, totalLen - offset);
    pCharacteristic->setValue(fb->buf + offset, len);
    pCharacteristic->notify();
    offset += len;
    delay(5);  // giảm nếu kết nối ổn
  }

  esp_camera_fb_return(fb);
  Serial.println("Image sent successfully");
  delay(5000); // Delay giữa các ảnh
}

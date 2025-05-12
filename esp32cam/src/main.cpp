#include <Arduino.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <esp_camera.h>
#include "soc/soc.h"
#include "soc/rtc_cntl_reg.h"

// TensorFlow Lite for person detection
#include <TensorFlowLite_ESP32.h>
#include "tensorflow/lite/micro/micro_mutable_op_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "person_detect_model_data.h"

// WiFi credentials - replace with your own
const char* ssid = "Phuong Uyen";
const char* password = "manh123@123";

// API endpoint for sending the image
const char* apiEndpoint = "http://192.168.1.188:7860/api/camera-image";

// Device identifier
const char* deviceId = "ESP32CAM-1";

// AI Thinker ESP32-CAM pin definition
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// TensorFlow Lite setup
class SerialTFLErrorReporter : public tflite::ErrorReporter {
public:
  virtual int Report(const char* format, va_list args) {
    char buffer[256];
    vsnprintf(buffer, sizeof(buffer), format, args);
    Serial.println(buffer);
    return 0;
  }
};

// TensorFlow model variables
tflite::ErrorReporter* error_reporter = new SerialTFLErrorReporter();
const tflite::Model* model = ::tflite::GetModel(g_person_detect_model_data);
const int tensor_arena_size = 81 * 1024;
uint8_t* tensor_arena;
tflite::MicroInterpreter* interpreter = NULL;
TfLiteTensor* input;

// Person detection parameters
constexpr int kNumCols = 96;
constexpr int kNumRows = 96;
constexpr int kPersonIndex = 1;
constexpr int kNotAPersonIndex = 2;
const float PersonScoreThreshold = 0.09;

// Declare functions
bool initCamera();
bool initTensorFlow();
bool detectPerson(camera_fb_t* fb);
bool sendPhotoToAPI(uint8_t *image_data, size_t image_size);

void setup() {
  // Disable brownout detector
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0);
  
  // Start serial communication
  Serial.begin(115200);
  Serial.println("ESP32 CAM starting...");
  
  // Initialize camera
  if (!initCamera()) {
    Serial.println("Camera initialization failed");
    return;
  }
  Serial.println("Camera initialized successfully");
  
  // Initialize TensorFlow Lite for person detection
  if (!initTensorFlow()) {
    Serial.println("TensorFlow initialization failed");
    return;
  }
  Serial.println("TensorFlow initialized successfully");
  
  // Connect to WiFi
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Attempting to reconnect...");
    WiFi.reconnect();
    delay(1000);
    return;
  }
  
  if (interpreter == NULL) {
    Serial.println("TensorFlow interpreter not initialized");
    delay(5000);
    return;
  }
  
  Serial.println("Taking photo for person detection...");
  
  // Take photo
  camera_fb_t *fb = esp_camera_fb_get();
  
  if (!fb) {
    Serial.println("Camera capture failed");
  } else {
    Serial.printf("Captured image: %uKB\n", fb->len / 1024);
    
    // Detect person in the image
    bool personDetected = detectPerson(fb);
    
    if (personDetected) {
      Serial.println("Person detected in image - sending to API");
      
      // Send photo to API only if a person is detected
      if (sendPhotoToAPI(fb->buf, fb->len)) {
        Serial.println("Photo sent successfully");
      } else {
        Serial.println("Failed to send photo");
      }
    } else {
      Serial.println("No person detected in image - skipping API upload");
    }
    
    // Return the frame buffer to be reused
    esp_camera_fb_return(fb);
  }
  
  // Wait 5 seconds before taking the next photo
  Serial.println("Waiting 5 seconds for next photo...");
  delay(5000);
}

bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  // Setup image quality and frame buffer count
  if (psramFound()) {
    config.frame_size = FRAMESIZE_VGA;  // FRAMESIZE_UXGA (1600x1200) for higher resolution
    config.jpeg_quality = 10;           // 0-63, lower is higher quality
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
  
  // Initialize the camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera initialization failed with error 0x%x", err);
    return false;
  }
  
  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    // Initial sensor settings
    s->set_brightness(s, 0);     // -2 to 2
    s->set_contrast(s, 0);       // -2 to 2
    s->set_saturation(s, 0);     // -2 to 2
    s->set_special_effect(s, 0); // 0 to 6 (0 - No Effect, 1 - Negative, 2 - Grayscale, 3 - Red Tint, 4 - Green Tint, 5 - Blue Tint, 6 - Sepia)
    s->set_whitebal(s, 1);       // 0 = disable , 1 = enable
    s->set_awb_gain(s, 1);       // 0 = disable , 1 = enable
    s->set_wb_mode(s, 0);        // 0 to 4 - if awb_gain enabled (0 - Auto, 1 - Sunny, 2 - Cloudy, 3 - Office, 4 - Home)
    s->set_exposure_ctrl(s, 1);  // 0 = disable , 1 = enable
    s->set_aec2(s, 0);           // 0 = disable , 1 = enable
    s->set_gain_ctrl(s, 1);      // 0 = disable , 1 = enable
    s->set_bpc(s, 0);            // 0 = disable , 1 = enable
    s->set_wpc(s, 1);            // 0 = disable , 1 = enable
    s->set_raw_gma(s, 1);        // 0 = disable , 1 = enable
    s->set_lenc(s, 1);           // 0 = disable , 1 = enable
    s->set_hmirror(s, 0);        // 0 = disable , 1 = enable
    s->set_vflip(s, 0);          // 0 = disable , 1 = enable
    s->set_dcw(s, 1);            // 0 = disable , 1 = enable
  }
  
  return true;
}

// Initialize TensorFlow Lite
bool initTensorFlow() {
  Serial.println(String("Preparing TFLite model version ") + model->version() + " ...");
  
  // Check version to make sure supported
  if (model->version() != TFLITE_SCHEMA_VERSION) {
    error_reporter->Report("Model provided is schema version %d not equal to supported version %d.",
                          model->version(), TFLITE_SCHEMA_VERSION);
    return false;
  }

  // Allocate memory for tensor_arena
  tensor_arena = (uint8_t *) heap_caps_malloc(tensor_arena_size, MALLOC_CAP_INTERNAL | MALLOC_CAP_8BIT);
  if (tensor_arena == NULL) {
    error_reporter->Report("heap_caps_malloc() failed");
    return false;
  }

  // Fill in only the operation implementations needed
  static tflite::MicroMutableOpResolver<5> micro_op_resolver;
  micro_op_resolver.AddAveragePool2D();
  micro_op_resolver.AddConv2D();
  micro_op_resolver.AddDepthwiseConv2D();
  micro_op_resolver.AddReshape();
  micro_op_resolver.AddSoftmax();

  // Build an interpreter to run the model with
  interpreter = new tflite::MicroInterpreter(model, micro_op_resolver, tensor_arena, tensor_arena_size, error_reporter);

  // Allocate memory from the tensor_arena for the model's tensors
  TfLiteStatus allocate_status = interpreter->AllocateTensors();
  if (allocate_status != kTfLiteOk) {
    error_reporter->Report("AllocateTensors() failed");
    return false;
  }
  
  // Obtain a pointer to the model's input tensor
  input = interpreter->input(0);
  
  Serial.println("TensorFlow model prepared successfully");
  return true;
}

// Process an image and detect if there is a person
bool detectPerson(camera_fb_t* fb) {
  // We need a grayscale image of kNumRows x kNumCols for the model
  camera_fb_t* resized_fb = NULL;
  bool person_detected = false;
  
  if (fb->format != PIXFORMAT_JPEG) {
    Serial.println("Camera not in JPEG format, cannot process");
    return false;
  }
  
  // Convert JPEG to grayscale 96x96 for TensorFlow input
  sensor_t * s = esp_camera_sensor_get();
  s->set_framesize(s, FRAMESIZE_96X96);
  s->set_pixformat(s, PIXFORMAT_GRAYSCALE);
  
  esp_camera_fb_return(fb);  // Release original frame buffer
  delay(100);  // Small delay for sensor to adjust
  
  // Get the new grayscale 96x96 frame
  resized_fb = esp_camera_fb_get();
  if (!resized_fb) {
    Serial.println("Failed to capture resized grayscale image");
    return false;
  }
  
  Serial.println("Running person detection on grayscale image");
  
  // Copy and convert the image data to TensorFlow input format
  // (signed 8-bit, 96x96)
  if (input->bytes != kNumRows * kNumCols) {
    Serial.printf("Model input size mismatch: model expects %d bytes, got %d bytes\n", 
                  kNumRows * kNumCols, input->bytes);
  } else {
    // Copy image data to TensorFlow input tensor and convert to signed int8
    const uint8_t* person_data = resized_fb->buf;
    for (int i = 0; i < input->bytes; ++i) {
      // Convert from uint8 to int8 for TensorFlow
      input->data.int8[i] = person_data[i] ^ 0x80;  // Convert by flipping the MSB
    }
    
    // Run the model on this input
    long detect_start_millis = millis();
    TfLiteStatus invoke_status = interpreter->Invoke();
    long detect_taken_millis = millis() - detect_start_millis;
    
    if (invoke_status != kTfLiteOk) {
      error_reporter->Report("Model Invoke failed");
    } else {
      // Process the inference (person detection) results
      TfLiteTensor* output = interpreter->output(0);
      int8_t person_score = output->data.int8[kPersonIndex];
      int8_t no_person_score = output->data.int8[kNotAPersonIndex];
      
      // Convert from quantized values to floating point probabilities
      float person_score_f = (person_score - output->params.zero_point) * output->params.scale;
      float no_person_score_f = (no_person_score - output->params.zero_point) * output->params.scale;
      
      Serial.printf("Person score: %.2f, No-person score: %.2f (took %ldms)\n", 
                    person_score_f, no_person_score_f, detect_taken_millis);
                    
      // Decide if a person is detected based on the threshold
      person_detected = (person_score_f > PersonScoreThreshold);
      
      if (person_detected) {
        Serial.printf("PERSON DETECTED with confidence: %.1f%%\n", person_score_f * 100);
      } else {
        Serial.printf("No person detected (confidence: %.1f%%)\n", person_score_f * 100);
      }
    }
  }
  
  // Release grayscale frame
  esp_camera_fb_return(resized_fb);
  
  // Set camera back to JPEG format for normal photos
  s->set_framesize(s, FRAMESIZE_VGA);
  s->set_pixformat(s, PIXFORMAT_JPEG);
  delay(100);  // Small delay for sensor to adjust
  
  return person_detected;
}

bool sendPhotoToAPI(uint8_t *image_data, size_t image_size) {
  HTTPClient http;
  bool success = false;
  
  Serial.print("Connecting to API: ");
  Serial.println(apiEndpoint);
  
  // Connect to the API endpoint
  http.begin(apiEndpoint);
  // Add headers
  http.addHeader("Content-Type", "image/jpeg");
  http.addHeader("Content-Disposition", "form-data; name=\"image\"; filename=\"esp32cam.jpg\"");
  http.addHeader("X-Device-ID", deviceId); // Add device identifier
  
  // Send the POST request with image data
  int httpResponseCode = http.POST(image_data, image_size);
  
  // Check response
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("HTTP Response code: " + String(httpResponseCode));
    Serial.println("Response: " + response);
    success = true;
  } else {
    Serial.print("Error on sending POST: ");
    Serial.println(httpResponseCode);
  }
  
  // Free resources
  http.end();
  
  return success;
}
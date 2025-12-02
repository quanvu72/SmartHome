/*
 * ESP32-CAM cho Smart Home System
 * Chức năng: Nhận lệnh chụp ảnh từ Raspberry Pi, sau đó gửi ảnh đến test_recieve.py
 * 
 * Workflow:
 * 1. Raspberry Pi gửi GET /capture
 * 2. ESP32 chụp ảnh
 * 3. ESP32 POST ảnh đến Raspberry Pi (test_recieve.py port 5000)
 * 4. ESP32 trả response cho Raspberry Pi
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>
#include <HTTPClient.h>

// ===== CÀI ĐẶT WIFI =====
const char* ssid = "Quân????";
const char* password = "qqqqqqqq";

// ===== CÀI ĐẶT RASPBERRY PI SERVER =====
const char* raspberryPiIP = "172.20.10.3";  // IP của Raspberry Pi
const int raspberryPiPort = 8080;            // Port của dashboard server
const char* uploadPath = "/upload";

// ===== CÀI ĐẶT WEB SERVER =====
WebServer server(80);

// ===== CAMERA PIN DEFINITION (AI-THINKER ESP32-CAM) =====
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

// LED Flash GPIO
#define LED_GPIO_NUM       4

// ===== BIẾN TOÀN CỤC =====
bool cameraInitialized = false;
unsigned long requestCount = 0;

// ===== KHỞI TẠO CAMERA =====
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
  
  // Cấu hình chất lượng ảnh
  if(psramFound()){
    config.frame_size = FRAMESIZE_UXGA;  // 1600x1200
    config.jpeg_quality = 10;
    config.fb_count = 2;
    Serial.println("PSRAM found - High quality mode");
  } else {
    config.frame_size = FRAMESIZE_SVGA;  // 800x600
    config.jpeg_quality = 12;
    config.fb_count = 1;
    Serial.println("No PSRAM - Standard quality mode");
  }

  // Khởi tạo camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return false;
  }

  // Cấu hình thêm cho camera sensor
  sensor_t * s = esp_camera_sensor_get();
  if (s != NULL) {
    s->set_brightness(s, 0);
    s->set_contrast(s, 0);
    s->set_saturation(s, 0);
    s->set_whitebal(s, 1);
    s->set_awb_gain(s, 1);
    s->set_exposure_ctrl(s, 1);
    s->set_gain_ctrl(s, 1);
  }

  Serial.println("Camera initialized successfully");
  return true;
}

// ===== HÀM GỬI ẢNH ĐẾN RASPBERRY PI =====
bool sendPhotoToRaspberryPi(camera_fb_t * fb) {
  if (!fb) {
    Serial.println("ERROR: No frame buffer provided");
    return false;
  }

  HTTPClient http;
  
  // URL đầy đủ của test_recieve.py trên Raspberry Pi
  String serverUrl = "http://" + String(raspberryPiIP) + ":" + String(raspberryPiPort) + String(uploadPath);
  
  Serial.println("\n--- Sending image to Raspberry Pi ---");
  Serial.print("URL: ");
  Serial.println(serverUrl);
  Serial.printf("Image size: %d bytes (%.2f KB)\n", fb->len, fb->len/1024.0);
  
  http.begin(serverUrl);
  http.addHeader("Content-Type", "image/jpeg");
  http.setTimeout(15000); // 15 second timeout
  
  // Gửi dữ liệu ảnh
  int httpResponseCode = http.POST(fb->buf, fb->len);
  
  if (httpResponseCode > 0) {
    Serial.printf("POST successful! HTTP code: %d\n", httpResponseCode);
    String response = http.getString();
    Serial.println("Response from Raspberry Pi:");
    Serial.println(response);
    http.end();
    return true;
  } else {
    Serial.printf("POST failed! Error: %s\n", http.errorToString(httpResponseCode).c_str());
    http.end();
    return false;
  }
}

// ===== HANDLER: CAPTURE IMAGE =====
void handleCapture() {
  Serial.println("\n╔════════════════════════════════════════════╗");
  Serial.println("║  CAPTURE REQUEST from Raspberry Pi        ║");
  Serial.println("╚════════════════════════════════════════════╝");
  requestCount++;
  
  if (!cameraInitialized) {
    Serial.println("❌ Camera not initialized");
    server.send(500, "application/json", "{\"success\":false,\"error\":\"Camera not initialized\"}");
    return;
  }
  
  // Bật LED flash
  digitalWrite(LED_GPIO_NUM, HIGH);
  delay(100);
  
  // Xóa buffer cũ để đảm bảo chụp ảnh mới
  camera_fb_t * fb_old = esp_camera_fb_get();
  if (fb_old) {
    esp_camera_fb_return(fb_old);
    Serial.println("🗑️  Cleared old frame buffer");
  }
  
  // Chụp ảnh mới
  Serial.println("📸 Capturing image...");
  camera_fb_t * fb = esp_camera_fb_get();
  
  // Tắt LED flash
  digitalWrite(LED_GPIO_NUM, LOW);
  
  if (!fb) {
    Serial.println("❌ Camera capture failed");
    server.send(500, "application/json", "{\"success\":false,\"error\":\"Camera capture failed\"}");
    return;
  }
  
  Serial.printf("✅ Image captured: %d bytes (%.2f KB)\n", fb->len, fb->len/1024.0);
  
  // Gửi ảnh đến Raspberry Pi (test_recieve.py)
  bool uploadSuccess = sendPhotoToRaspberryPi(fb);
  
  // Trả response cho Raspberry Pi
  if (uploadSuccess) {
    String jsonResponse = "{";
    jsonResponse += "\"success\":true,";
    jsonResponse += "\"message\":\"Image captured and sent to Raspberry Pi\",";
    jsonResponse += "\"size\":" + String(fb->len) + ",";
    jsonResponse += "\"uploaded_to\":\"" + String(raspberryPiIP) + ":" + String(raspberryPiPort) + "\"";
    jsonResponse += "}";
    
    server.send(200, "application/json", jsonResponse);
    Serial.println("✅ Response sent to Raspberry Pi");
  } else {
    server.send(500, "application/json", "{\"success\":false,\"error\":\"Failed to upload to Raspberry Pi\"}");
    Serial.println("❌ Failed to upload image");
  }
  
  // Giải phóng bộ nhớ
  esp_camera_fb_return(fb);
  Serial.println("╚════════════════════════════════════════════╝\n");
}

// ===== HANDLER: STATUS =====
void handleStatus() {
  String status = "{\n";
  status += "  \"status\": \"online\",\n";
  status += "  \"camera\": \"" + String(cameraInitialized ? "ready" : "not initialized") + "\",\n";
  status += "  \"wifi_rssi\": " + String(WiFi.RSSI()) + ",\n";
  status += "  \"requests\": " + String(requestCount) + ",\n";
  status += "  \"uptime\": " + String(millis() / 1000) + ",\n";
  status += "  \"free_heap\": " + String(ESP.getFreeHeap()) + "\n";
  status += "}";
  
  server.send(200, "application/json", status);
  Serial.println("Status check from: " + server.client().remoteIP().toString());
}

// ===== HANDLER: ROOT =====
void handleRoot() {
  String html = "<html><head><meta charset='UTF-8'><title>ESP32-CAM Smart Home</title></head>";
  html += "<body style='font-family: Arial; max-width: 600px; margin: 50px auto;'>";
  html += "<h1>🏠 ESP32-CAM Smart Home</h1>";
  html += "<p><strong>Status:</strong> Online ✅</p>";
  html += "<p><strong>Camera:</strong> " + String(cameraInitialized ? "Ready" : "Not Initialized") + "</p>";
  html += "<p><strong>WiFi:</strong> " + String(WiFi.SSID()) + " (" + String(WiFi.RSSI()) + " dBm)</p>";
  html += "<p><strong>IP:</strong> " + WiFi.localIP().toString() + "</p>";
  html += "<p><strong>Requests:</strong> " + String(requestCount) + "</p>";
  html += "<hr>";
  html += "<h3>📋 Configuration:</h3>";
  html += "<p><strong>Raspberry Pi:</strong> " + String(raspberryPiIP) + ":" + String(raspberryPiPort) + "</p>";
  html += "<p><strong>Upload endpoint:</strong> " + String(uploadPath) + "</p>";
  html += "<hr>";
  html += "<h3>API Endpoints:</h3>";
  html += "<ul>";
  html += "<li><a href='/capture'>/capture</a> - Chụp và gửi ảnh đến Raspberry Pi</li>";
  html += "<li><a href='/status'>/status</a> - Trạng thái hệ thống</li>";
  html += "</ul>";
  html += "<p style='color: #888; font-size: 12px;'>Mode: Capture → Send to Raspberry Pi (test_recieve.py)</p>";
  html += "</body></html>";
  
  server.send(200, "text/html", html);
}

// ===== HANDLER: NOT FOUND =====
void handleNotFound() {
  server.send(404, "text/plain", "404 Not Found");
}

// ===== SETUP =====
void setup() {
  Serial.begin(115200);
  
  // Setup LED Flash pin
  pinMode(LED_GPIO_NUM, OUTPUT);
  digitalWrite(LED_GPIO_NUM, LOW);
  
  // Khởi tạo camera
  Serial.println("\n📷 Initializing camera...");
  cameraInitialized = initCamera();
  
  if (!cameraInitialized) {
    Serial.println("❌ Camera initialization failed!");
  } else {
    Serial.println("✅ Camera ready");
  }
  
  // Kết nối WiFi với Static IP
  Serial.println("\n📡 Connecting to WiFi...");
  
  // Cấu hình Static IP
  IPAddress staticIP(172, 20, 10, 5);       // IP tĩnh cho ESP32
  IPAddress gateway(172, 20, 10, 1);         // Gateway của router
  IPAddress subnet(255, 255, 255, 0);        // Subnet mask
  IPAddress primaryDNS(8, 8, 8, 8);          // DNS Google
  IPAddress secondaryDNS(8, 8, 4, 4);        // DNS Google phụ
  
  // Áp dụng cấu hình Static IP
  if (!WiFi.config(staticIP, gateway, subnet, primaryDNS, secondaryDNS)) {
    Serial.println("⚠️  Failed to configure Static IP");
  }
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n✅ WiFi connected!");
    Serial.print("📍 ESP32 IP: ");
    Serial.println(WiFi.localIP());
    Serial.print("📶 Signal: ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println("\n❌ WiFi connection failed!");
    return;
  }
  
  // Hiển thị cấu hình
  Serial.println("\n⚙️  Configuration:");
  Serial.print("   Raspberry Pi IP: ");
  Serial.println(raspberryPiIP);
  Serial.print("   Raspberry Pi Port: ");
  Serial.println(raspberryPiPort);
  Serial.print("   Upload Path: ");
  Serial.println(uploadPath);
  
  // Setup HTTP routes
  server.on("/", HTTP_GET, handleRoot);
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/status", HTTP_GET, handleStatus);
  server.onNotFound(handleNotFound);
  
  // Khởi động server
  server.begin();
  Serial.println("\n✅ HTTP server started");
  Serial.println("╔═══════════════════════════════════════════╗");
  Serial.println("║  Ready to receive requests!               ║");
  Serial.print("║  Access: http://");
  Serial.print(WiFi.localIP());
  Serial.println("             ║");
  Serial.println("╚═══════════════════════════════════════════╝\n");
  
  // Test chụp ảnh và gửi khi khởi động
  Serial.println("🧪 STARTUP TEST: Capturing and sending test image...\n");
  delay(2000);
  
  // Xóa buffer cũ
  camera_fb_t * fb_old = esp_camera_fb_get();
  if (fb_old) {
    esp_camera_fb_return(fb_old);
  }
  
  digitalWrite(LED_GPIO_NUM, HIGH);
  delay(100);
  camera_fb_t * fb = esp_camera_fb_get();
  digitalWrite(LED_GPIO_NUM, LOW);
  
  if (fb) {
    Serial.printf("📸 Test image captured: %d bytes\n", fb->len);
    bool success = sendPhotoToRaspberryPi(fb);
    esp_camera_fb_return(fb);
    
    if (success) {
      Serial.println("✅ STARTUP TEST PASSED!\n");
    } else {
      Serial.println("⚠️  STARTUP TEST: Upload failed (check Raspberry Pi server)\n");
    }
  } else {
    Serial.println("❌ STARTUP TEST: Capture failed\n");
  }
}

// ===== LOOP =====
void loop() {
  // Xử lý HTTP requests từ Raspberry Pi
  server.handleClient();
  
  // Kiểm tra kết nối WiFi
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 30000) {
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi disconnected! Reconnecting...");
      WiFi.begin(ssid, password);
    }
    lastCheck = millis();
  }
}
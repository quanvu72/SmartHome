/*
 * ESP32-CAM HTTP Server cho Smart Home System
 * Chức năng: Nhận yêu cầu HTTP từ Raspberry Pi và chụp ảnh
 * 
 * Hardware: ESP32-CAM (AI-Thinker)
 * Camera: OV2640
 * 
 * Endpoints:
 * - GET /capture : Chụp ảnh và trả về image
 * - GET /status  : Kiểm tra trạng thái
 * - GET /info    : Lấy thông tin camera
 */

#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// ===== CÀI ĐẶT WIFI =====
const char* ssid = "YOUR_WIFI_SSID";           // Thay đổi tên WiFi
const char* password = "YOUR_WIFI_PASSWORD";   // Thay đổi mật khẩu WiFi

// ===== CÀI ĐẶT WEB SERVER =====
WebServer server(80);  // HTTP server trên port 80

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
  // Nếu có PSRAM: chất lượng cao
  // Nếu không có PSRAM: chất lượng thấp hơn
  if(psramFound()){
    config.frame_size = FRAMESIZE_UXGA;  // 1600x1200
    config.jpeg_quality = 10;             // 0-63, số thấp = chất lượng cao
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
    // Tùy chỉnh settings
    s->set_brightness(s, 0);     // -2 to 2
    s->set_contrast(s, 0);       // -2 to 2
    s->set_saturation(s, 0);     // -2 to 2
    s->set_special_effect(s, 0); // 0 to 6 (0 - No Effect)
    s->set_whitebal(s, 1);       // 0 = disable , 1 = enable
    s->set_awb_gain(s, 1);       // 0 = disable , 1 = enable
    s->set_wb_mode(s, 0);        // 0 to 4 - if awb_gain enabled
    s->set_exposure_ctrl(s, 1);  // 0 = disable , 1 = enable
    s->set_aec2(s, 0);           // 0 = disable , 1 = enable
    s->set_ae_level(s, 0);       // -2 to 2
    s->set_aec_value(s, 300);    // 0 to 1200
    s->set_gain_ctrl(s, 1);      // 0 = disable , 1 = enable
    s->set_agc_gain(s, 0);       // 0 to 30
    s->set_gainceiling(s, (gainceiling_t)0); // 0 to 6
    s->set_bpc(s, 0);            // 0 = disable , 1 = enable
    s->set_wpc(s, 1);            // 0 = disable , 1 = enable
    s->set_raw_gma(s, 1);        // 0 = disable , 1 = enable
    s->set_lenc(s, 1);           // 0 = disable , 1 = enable
    s->set_hmirror(s, 0);        // 0 = disable , 1 = enable
    s->set_vflip(s, 0);          // 0 = disable , 1 = enable
    s->set_dcw(s, 1);            // 0 = disable , 1 = enable
    s->set_colorbar(s, 0);       // 0 = disable , 1 = enable
  }

  Serial.println("Camera initialized successfully");
  return true;
}

// ===== KẾT NỐI WIFI =====
void connectWiFi() {
  Serial.println();
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.println("WiFi connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("Signal strength (RSSI): ");
    Serial.print(WiFi.RSSI());
    Serial.println(" dBm");
  } else {
    Serial.println();
    Serial.println("WiFi connection failed!");
  }
}

// ===== HANDLER: CAPTURE IMAGE =====
void handleCapture() {
  Serial.println("Received capture request");
  requestCount++;
  
  if (!cameraInitialized) {
    server.send(500, "text/plain", "Camera not initialized");
    return;
  }
  
  // Bật LED flash (optional)
  digitalWrite(LED_GPIO_NUM, HIGH);
  delay(100);  // Đợi LED sáng
  
  // Chụp ảnh
  camera_fb_t * fb = esp_camera_fb_get();
  
  // Tắt LED flash
  digitalWrite(LED_GPIO_NUM, LOW);
  
  if (!fb) {
    Serial.println("Camera capture failed");
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }
  
  Serial.printf("Image captured: %d bytes\n", fb->len);
  
  // Gửi ảnh về Raspberry Pi
  server.send(200, "image/jpeg", (const char *)fb->buf, fb->len);
  
  // Giải phóng bộ nhớ
  esp_camera_fb_return(fb);
  
  Serial.println("Image sent successfully");
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
}

// ===== HANDLER: INFO =====
void handleInfo() {
  sensor_t * s = esp_camera_sensor_get();
  
  String info = "{\n";
  info += "  \"device\": \"ESP32-CAM\",\n";
  info += "  \"camera_model\": \"OV2640\",\n";
  info += "  \"resolution\": \"" + String(s->status.framesize) + "\",\n";
  info += "  \"quality\": \"" + String(s->status.quality) + "\",\n";
  info += "  \"brightness\": \"" + String(s->status.brightness) + "\",\n";
  info += "  \"contrast\": \"" + String(s->status.contrast) + "\",\n";
  info += "  \"psram\": \"" + String(psramFound() ? "yes" : "no") + "\"\n";
  info += "}";
  
  server.send(200, "application/json", info);
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
  html += "<h3>API Endpoints:</h3>";
  html += "<ul>";
  html += "<li><a href='/capture' target='_blank'>/capture</a> - Chụp ảnh</li>";
  html += "<li><a href='/status' target='_blank'>/status</a> - Trạng thái hệ thống</li>";
  html += "<li><a href='/info' target='_blank'>/info</a> - Thông tin camera</li>";
  html += "</ul>";
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
  Serial.println();
  Serial.println("=================================");
  Serial.println("  ESP32-CAM Smart Home System");
  Serial.println("=================================");
  
  // Setup LED Flash pin
  pinMode(LED_GPIO_NUM, OUTPUT);
  digitalWrite(LED_GPIO_NUM, LOW);
  
  // Khởi tạo camera
  Serial.println("Initializing camera...");
  cameraInitialized = initCamera();
  
  if (!cameraInitialized) {
    Serial.println("Camera initialization failed!");
    Serial.println("System will continue but capture will not work");
  }
  
  // Kết nối WiFi
  connectWiFi();
  
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Cannot start server without WiFi");
    return;
  }
  
  // Setup HTTP routes
  server.on("/", HTTP_GET, handleRoot);
  server.on("/capture", HTTP_GET, handleCapture);
  server.on("/status", HTTP_GET, handleStatus);
  server.on("/info", HTTP_GET, handleInfo);
  server.onNotFound(handleNotFound);
  
  // Khởi động server
  server.begin();
  Serial.println("HTTP server started");
  Serial.println("=================================");
  Serial.print("Ready! Access at: http://");
  Serial.println(WiFi.localIP());
  Serial.println("=================================");
}

// ===== LOOP =====
void loop() {
  // Xử lý HTTP requests
  server.handleClient();
  
  // Kiểm tra kết nối WiFi
  static unsigned long lastCheck = 0;
  if (millis() - lastCheck > 30000) {  // Kiểm tra mỗi 30 giây
    if (WiFi.status() != WL_CONNECTED) {
      Serial.println("WiFi disconnected! Reconnecting...");
      connectWiFi();
    }
    lastCheck = millis();
  }
}

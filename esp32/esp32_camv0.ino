#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

// --- Cấu hình Wi-Fi ---
const char* ssid = "";
const char* password = "";

// --- Cấu hình Raspberry Pi Server ---
// Đặt IP tĩnh cho Raspberry Pi (hoặc dùng IP hiện tại của Pi)
const char* serverIp = "192.168.1.15"; // Thay thế bằng IP của Raspberry Pi
const int serverPort = 5000;            // Cổng mà Python server trên Pi đang lắng nghe
const char* serverPath = "/upload";     // Đường dẫn API nhận ảnh

// --- Cấu hình GPIO (Cảm biến cửa) ---
// Thay đổi GPIO nếu bạn dùng chân khác
const int DOOR_SENSOR_PIN = 13; // Ví dụ dùng GPIO 13
bool door_open_detected = false;

// --- Cấu hình Camera ---
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

// --- Hàm Khởi tạo Camera ---
void initCamera() {
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
  
  // Thiết lập độ phân giải (có thể thay đổi)
  config.frame_size = FRAMESIZE_VGA; // FRAMESIZE_VGA (640x480), FRAMESIZE_SVGA (800x600)
  config.jpeg_quality = 10; // Chất lượng (0-63, 0 là tốt nhất)
  config.fb_count = 1;

  // Khởi tạo camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }
}

// --- Hàm Gửi Ảnh qua HTTP POST ---
void sendPhoto() {
  camera_fb_t * fb = NULL;
  fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return;
  }

  Serial.printf("Captured image size: %zu bytes\n", fb->len);

  HTTPClient http;
  
  // URL đầy đủ của server trên Pi
  String serverUrl = "http://" + String(serverIp) + ":" + String(serverPort) + String(serverPath);
  http.begin(serverUrl);
  
  // Cài đặt Content-Type
  http.addHeader("Content-Type", "image/jpeg");
  
  Serial.print("Sending image to: ");
  Serial.println(serverUrl);

  // Gửi dữ liệu ảnh
  int httpResponseCode = http.POST(fb->buf, fb->len);
  
  if (httpResponseCode > 0) {
    Serial.printf("[HTTP] POST... code: %d\n", httpResponseCode);
    String response = http.getString();
    Serial.println(response);
  } else {
    Serial.printf("[HTTP] POST... failed, error: %s\n", http.errorToString(httpResponseCode).c_str());
  }
  
  http.end();
  esp_camera_fb_return(fb); // Trả lại bộ đệm
}

// --- Setup ---
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  // Khởi tạo GPIO cảm biến cửa (INPUT_PULLUP để đảm bảo tín hiệu)
  pinMode(DOOR_SENSOR_PIN, INPUT_PULLUP); 

  // --- Kết nối Wi-Fi ---
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // --- Khởi tạo Camera ---
  initCamera();
}

// --- Loop ---
void loop() {
  // Đọc trạng thái cảm biến. Giả sử cảm biến là NC (thường đóng). 
  // Cửa mở -> Tín hiệu LOW
  int doorState = digitalRead(DOOR_SENSOR_PIN);
  
  // Kiểm tra nếu cửa MỞ
  if (doorState == LOW) { 
    if (!door_open_detected) {
      Serial.println("!!! CUA MO DUOC PHAT HIEN !!!");
      
      // Chụp và gửi ảnh
      sendPhoto();
      
      // Đặt cờ để tránh chụp ảnh liên tục khi cửa vẫn mở
      door_open_detected = true;
      
      // Đợi 5 giây trước khi cho phép chụp lại (để tránh spam)
      // hoặc bạn có thể chỉ reset cờ khi cảm biến chuyển lại trạng thái đóng (HIGH)
      // delay(5000); 
    }
  } else {
    // Cửa đóng, reset cờ
    if (door_open_detected) {
      Serial.println("Cua da dong lai.");
      door_open_detected = false;
    }
  }
  
  // Chu kỳ kiểm tra ngắn
  delay(100); 
}
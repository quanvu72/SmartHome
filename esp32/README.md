# ESP32-CAM Setup Guide

## Cài Đặt Arduino IDE

1. **Tải Arduino IDE**
   - Download từ: https://www.arduino.cc/en/software
   - Cài đặt phiên bản mới nhất

2. **Thêm ESP32 Board Manager**
   - Mở Arduino IDE
   - File → Preferences
   - Thêm URL vào "Additional Board Manager URLs":
     ```
     https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
     ```
   - OK để lưu

3. **Cài Đặt ESP32 Board**
   - Tools → Board → Board Manager
   - Tìm "esp32"
   - Cài đặt "esp32 by Espressif Systems"

4. **Chọn Board**
   - Tools → Board → ESP32 Arduino → AI Thinker ESP32-CAM

## Upload Code Lên ESP32-CAM

### Phần Cứng Cần Thiết
- ESP32-CAM module
- FTDI Programmer (USB to Serial)
- Jumper wires (female-to-female)
- MicroUSB cable

### Kết Nối FTDI với ESP32-CAM

```
FTDI          ESP32-CAM
----          ---------
GND     →     GND
5V      →     5V
TX      →     UOR (RX)
RX      →     UOT (TX)

Để vào Programming Mode:
GPIO 0  →     GND (dùng jumper)
```

**⚠️ Lưu ý:** Kết nối GPIO 0 với GND chỉ khi upload code, sau đó gỡ jumper ra để chạy bình thường.

### Các Bước Upload

1. **Mở Code**
   - Mở file `camera_server.ino` trong Arduino IDE

2. **Chỉnh Sửa WiFi**
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```

3. **Cấu Hình Board**
   - Board: "AI Thinker ESP32-CAM"
   - Upload Speed: "115200"
   - Flash Frequency: "80MHz"
   - Flash Mode: "QIO"
   - Partition Scheme: "Huge APP (3MB No OTA/1MB SPIFFS)"
   - Port: Chọn COM port của FTDI

4. **Upload**
   - Kết nối GPIO 0 với GND
   - Nhấn nút RESET trên ESP32-CAM
   - Click nút Upload trong Arduino IDE
   - Đợi upload hoàn tất
   - Gỡ jumper GPIO 0 - GND
   - Nhấn RESET để chạy

5. **Kiểm Tra**
   - Mở Serial Monitor (115200 baud)
   - Nhấn RESET trên ESP32-CAM
   - Xem IP address được in ra

## Test ESP32-CAM

1. **Mở Serial Monitor**
   - Tools → Serial Monitor
   - Set baud rate: 115200
   - Nhấn RESET trên ESP32-CAM
   - Xem thông tin kết nối WiFi và IP

2. **Test qua Browser**
   - Mở browser
   - Truy cập: `http://<ESP32_IP>/`
   - Bạn sẽ thấy trang web status
   - Click vào `/capture` để test chụp ảnh

3. **Test API**
   ```bash
   # Test status
   curl http://<ESP32_IP>/status
   
   # Test capture (lưu ảnh)
   curl http://<ESP32_IP>/capture -o test.jpg
   ```

## Troubleshooting

### Không Upload Được

1. **Kiểm tra kết nối**
   - Đảm bảo GPIO 0 → GND khi upload
   - Kiểm tra TX-RX đã kết nối chéo chưa
   - Kiểm tra nguồn 5V đủ mạnh (ít nhất 500mA)

2. **Lỗi "Failed to connect"**
   - Nhấn giữ nút IO0 (GPIO 0) khi nhấn RESET
   - Thử giảm upload speed xuống 115200

3. **Brownout detector**
   - Nguồn không đủ mạnh
   - Dùng nguồn 5V/2A riêng cho ESP32-CAM

### Camera Không Hoạt Động

1. **Kiểm tra ribbon cable**
   - Đảm bảo camera module được cắm chắc chắn
   - Mặt xanh của ribbon cable hướng ra ngoài

2. **PSRAM error**
   - Một số board fake không có PSRAM
   - Code sẽ tự động chuyển sang chế độ thấp hơn

### WiFi Không Kết Nối

1. **Kiểm tra SSID và Password**
2. **Đảm bảo WiFi là 2.4GHz** (ESP32 không hỗ trợ 5GHz)
3. **Kiểm tra cường độ signal**

## Sơ Đồ Chân ESP32-CAM

```
                  ESP32-CAM
              ┌─────────────┐
       5V  ───┤             ├─── GND
      GND  ───┤   CAMERA    ├─── IO2
      IO12 ───┤   MODULE    ├─── IO4 (LED)
      IO13 ───┤             ├─── RX
      IO15 ───┤   AI-THINKER├─── TX
      IO14 ───┤             ├─── IO0
       GND ───┤             ├─── GND
      VCC  ───┤             ├─── 3.3V
              └─────────────┘
```

## Cải Tiến Code (Optional)

### Thêm Authentication
```cpp
// Trong setup()
server.on("/capture", HTTP_GET, [](){
  if(!server.authenticate("admin", "password")) {
    return server.requestAuthentication();
  }
  handleCapture();
});
```

### Thêm OTA Update
```cpp
#include <ArduinoOTA.h>

// Trong setup()
ArduinoOTA.begin();

// Trong loop()
ArduinoOTA.handle();
```

### Save ảnh lên SD Card
```cpp
#include "SD_MMC.h"

// Khởi tạo SD card
SD_MMC.begin();
```

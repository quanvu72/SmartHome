# Hệ Thống Quản Lý Nhà Thông Minh - Smart Home Management System

## Tổng Quan (Overview)
Hệ thống quản lý nhà thông minh sử dụng Raspberry Pi 5 để giám sát trạng thái cửa và tích hợp với ESP32 camera để chụp ảnh khi phát hiện cửa mở.

## Tính Năng (Features)
- ✅ Giám sát 2 cảm biến cửa (Door 1 và Door 2)
- ✅ Phát hiện trạng thái đóng/mở cửa real-time
- ✅ Tự động gửi yêu cầu chụp ảnh đến ESP32 qua HTTP
- ✅ Nhận và lưu ảnh từ ESP32
- ✅ Gửi thông báo đến web interface
- ✅ Log hệ thống chi tiết

## Kiến Trúc Hệ Thống (System Architecture)

```
┌─────────────────────────────────────────────────────────┐
│             Raspberry Pi 5 (Main Controller)            │
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │Door Sensor 1 │  │Door Sensor 2 │  │  GPIO Pins   │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘  │
│         │                  │                             │
│         └─────────┬────────┘                             │
│                   │                                      │
│         ┌─────────▼──────────┐                          │
│         │  door_sensor.py    │                          │
│         │  (Monitor Module)  │                          │
│         └─────────┬──────────┘                          │
│                   │                                      │
│         ┌─────────▼──────────┐                          │
│         │    main.py         │                          │
│         │  (Controller)      │                          │
│         └─────────┬──────────┘                          │
│                   │                                      │
│         ┌─────────▼──────────┐                          │
│         │ esp32_camera.py    │◄──HTTP──┐               │
│         │  (Camera Client)   │          │               │
│         └─────────┬──────────┘          │               │
│                   │                      │               │
│         ┌─────────▼──────────┐          │               │
│         │ web_notifier.py    │          │               │
│         │ (Web Interface)    │          │               │
│         └────────────────────┘          │               │
└─────────────────────────────────────────┼───────────────┘
                                          │
                              ┌───────────▼────────────┐
                              │      ESP32-CAM         │
                              │  (Camera Module)       │
                              │  - Capture Image       │
                              │  - HTTP Server         │
                              └────────────────────────┘
```

## Cấu Trúc Thư Mục (Directory Structure)

```
IoTDesign/
├── README.md                 # Tài liệu dự án
├── requirements.txt          # Python dependencies
├── config.json              # Cấu hình hệ thống
├── main.py                  # Main controller
├── modules/
│   ├── __init__.py
│   ├── door_sensor.py       # Module cảm biến cửa
│   ├── esp32_camera.py      # Module ESP32 camera client
│   └── web_notifier.py      # Module thông báo web
├── esp32/
│   └── camera_server.ino    # Code cho ESP32-CAM
├── logs/                    # Thư mục log files
└── images/                  # Thư mục lưu ảnh
```

## Yêu Cầu Phần Cứng (Hardware Requirements)

### Raspberry Pi 5
- Raspberry Pi 5 (2GB RAM trở lên)
- MicroSD Card (16GB+)
- Power Supply 5V/3A USB-C
- 2x Magnetic Door Sensors (Reed Switch)
- Jumper wires

### ESP32-CAM
- ESP32-CAM module
- OV2640 Camera
- FTDI Programmer (để upload code)
- Power Supply 5V

## Kết Nối Phần Cứng (Hardware Connection)

### Raspberry Pi GPIO Pins:
- **Door Sensor 1**: GPIO 17 (Physical Pin 11)
- **Door Sensor 2**: GPIO 27 (Physical Pin 13)
- **Ground**: Physical Pin 6, 9, 14, 20, 25, 30, 34, 39

### Cảm Biến Cửa (Door Sensor):
```
Reed Switch → Raspberry Pi
  ├─ Wire 1 → GPIO Pin (17 hoặc 27)
  └─ Wire 2 → Ground (GND)
```

## Cài Đặt (Installation)

### 1. Cài Đặt Raspberry Pi OS
```bash
# Cập nhật hệ thống
sudo apt update
sudo apt upgrade -y

# Cài đặt Python 3 và pip
sudo apt install python3 python3-pip python3-venv -y

# Cài đặt GPIO library
sudo apt install python3-rpi.gpio -y
```

### 2. Cài Đặt Project
```bash
# Clone hoặc tạo thư mục dự án
cd /home/pi/
mkdir -p IoTDesign
cd IoTDesign

# Tạo virtual environment (khuyên dùng)
python3 -m venv venv
source venv/bin/activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### 3. Cấu Hình
Chỉnh sửa file `config.json`:
```json
{
  "door_sensors": {
    "door1_pin": 17,
    "door2_pin": 27
  },
  "esp32": {
    "ip": "192.168.1.100",
    "port": 80
  },
  "web_server": {
    "url": "http://your-web-server.com/api/notification"
  }
}
```

## Chạy Hệ Thống (Running)

### Chạy Thủ Công (Manual)
```bash
# Kích hoạt virtual environment
source venv/bin/activate

# Chạy ứng dụng
python3 main.py
```

### Chạy Tự Động Khi Khởi Động (Auto-start on Boot)
Tạo systemd service:
```bash
sudo nano /etc/systemd/system/smarthome.service
```

Nội dung file:
```ini
[Unit]
Description=Smart Home Management System
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/IoTDesign
ExecStart=/home/pi/IoTDesign/venv/bin/python3 /home/pi/IoTDesign/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Kích hoạt service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable smarthome.service
sudo systemctl start smarthome.service
sudo systemctl status smarthome.service
```

## Cấu Hình ESP32-CAM

### 1. Upload Code
- Mở Arduino IDE
- Mở file `esp32/camera_server.ino`
- Chọn Board: "AI Thinker ESP32-CAM"
- Cấu hình WiFi SSID và Password
- Upload code

### 2. Kết Nối WiFi
ESP32-CAM sẽ tự động kết nối WiFi và in ra Serial Monitor địa chỉ IP.

### 3. Test Camera
Truy cập: `http://<ESP32_IP>/capture` để test chụp ảnh.

## API Endpoints

### ESP32-CAM
- `GET /capture` - Chụp ảnh và trả về image file

### Web Server (Tùy chỉnh)
- `POST /api/notification` - Nhận thông báo từ Raspberry Pi
  ```json
  {
    "door": "door1",
    "status": "open",
    "timestamp": "2025-11-18T10:30:00",
    "image_path": "/images/door1_20251118_103000.jpg"
  }
  ```

## Logs

Hệ thống ghi log vào:
- Console output
- File: `logs/smarthome.log`

Xem log realtime:
```bash
tail -f logs/smarthome.log
```

## Troubleshooting

### Lỗi GPIO Permission
```bash
sudo usermod -a -G gpio pi
# Sau đó logout và login lại
```

### ESP32 Không Phản Hồi
- Kiểm tra kết nối WiFi
- Ping ESP32: `ping <ESP32_IP>`
- Kiểm tra firewall
- Reset ESP32

### Cảm Biến Không Hoạt Động
- Kiểm tra kết nối GPIO
- Test GPIO: `gpio readall`
- Kiểm tra pull-up resistor trong code

## Bảo Mật (Security)

- ⚠️ Thay đổi default credentials
- ⚠️ Sử dụng HTTPS cho web API
- ⚠️ Giới hạn quyền truy cập GPIO
- ⚠️ Cập nhật hệ thống thường xuyên

## Tác Giả (Author)
Smart Home IoT Project

## License
MIT License

## Liên Hệ (Contact)
- Issues: Tạo issue trên GitHub repository
- Email: your-email@example.com

---
**Lưu Ý**: Đây là hệ thống demo. Cần bổ sung các tính năng bảo mật và xử lý lỗi chi tiết hơn cho môi trường production.

# 🌐 Web Dashboard Module

Module web dashboard để giám sát trạng thái cửa và hiển thị ảnh từ ESP32-CAM.

## 📁 Cấu trúc

```
web_dashboard/
├── dashboard_server.py      # Server chính (DashboardServer class)
├── run_dashboard.py         # Script chạy dashboard
├── templates/
│   └── dashboard.html       # Giao diện web
├── static/                  # Static files (nếu cần)
└── README.md               # File này
```

## 🎯 Tính năng

- ✅ Hiển thị trạng thái cửa realtime (Mở/Đóng)
- ✅ Hiển thị 6 ảnh mới nhất từ ESP32-CAM
- ✅ Auto refresh mỗi 5 giây
- ✅ Click ảnh để xem phóng to
- ✅ Responsive design (mobile-friendly)
- ✅ RESTful API endpoints
- ✅ Statistics dashboard
- ✅ Beautiful gradient UI

## 🚀 Cách chạy

### 1. Chạy Standalone

```bash
cd web_dashboard
python run_dashboard.py
```

### 2. Truy cập Dashboard

Mở browser:
```
http://localhost:8080
```

Hoặc từ máy khác trong mạng:
```
http://<raspberry-pi-ip>:8080
```

### 3. Import vào hệ thống chính

```python
from web_dashboard.dashboard_server import DashboardServer
import threading

# Chạy dashboard trong thread riêng
def start_dashboard():
    server = DashboardServer(
        host='0.0.0.0',
        port=8080,
        image_folder='images'
    )
    server.run(debug=False)

dashboard_thread = threading.Thread(target=start_dashboard, daemon=True)
dashboard_thread.start()
```

## 🔌 API Endpoints

### GET /
Dashboard UI - Giao diện chính

### GET /api/doors
Lấy trạng thái tất cả các cửa

**Response:**
```json
{
  "success": true,
  "doors": {
    "door1": {
      "status": "open",
      "last_updated": "2025-11-26 14:30:55",
      "pin": 17
    },
    "door2": {
      "status": "closed",
      "last_updated": "2025-11-26 14:30:55",
      "pin": 27
    }
  },
  "timestamp": "2025-11-26 14:30:55"
}
```

### POST /api/doors/update
Cập nhật trạng thái cửa (được gọi từ main.py)

**Request:**
```json
{
  "door": "door1",
  "status": "open"
}
```

**Response:**
```json
{
  "success": true,
  "door": "door1",
  "status": "open"
}
```

### GET /api/images
Lấy danh sách ảnh mới nhất

**Query Parameters:**
- `limit`: Số lượng ảnh (default: 10)

**Response:**
```json
{
  "success": true,
  "images": [
    {
      "filename": "esp32_20251126_143055.jpg",
      "size": 12345,
      "size_kb": "12.06",
      "timestamp": "2025-11-26 14:30:55",
      "mtime": 1732614655.123
    }
  ],
  "total": 6
}
```

### GET /api/images/<filename>
Lấy file ảnh

**Example:**
```
http://localhost:8080/api/images/esp32_20251126_143055.jpg
```

### GET /api/stats
Lấy thống kê hệ thống

**Response:**
```json
{
  "success": true,
  "stats": {
    "total_events": 10,
    "total_images": 25,
    "uptime_seconds": 3600,
    "uptime": "1:00:00"
  },
  "doors": { ... }
}
```

## 🎨 Giao diện

### Dashboard chính
- **3 cards**: Door 1, Door 2, Statistics
- **Màu sắc**: 
  - 🔴 Đỏ = Cửa mở
  - 🟢 Xanh = Cửa đóng
  - ⚪ Xám = Unknown
- **Auto-update**: Mỗi 5 giây

### Phần ảnh
- **Grid layout**: Responsive 3-4 cột
- **Hover effect**: Scale 1.05x
- **Click**: Xem ảnh fullscreen
- **Info**: Filename, timestamp, size

### Features
- ✅ Gradient background đẹp mắt
- ✅ Smooth animations
- ✅ Pulse effect khi cập nhật
- ✅ Modal fullscreen cho ảnh
- ✅ Floating refresh button
- ✅ Responsive mobile

## ⌨️ Keyboard Shortcuts

- `R`: Refresh dữ liệu thủ công
- `ESC`: Đóng modal ảnh

## 🔄 Auto Refresh

Dashboard tự động làm mới mỗi 5 giây:
- Trạng thái cửa
- Statistics
- Danh sách ảnh mới nhất

Tạm dừng khi tab không active (tiết kiệm tài nguyên).

## 📊 Statistics Tracking

Dashboard theo dõi:
- Tổng số sự kiện cửa mở
- Tổng số ảnh đã chụp
- Trạng thái hệ thống
- Thông tin ESP32-CAM
- Uptime server

## 🔗 Tích hợp với Main System

Để cập nhật trạng thái cửa từ `main.py`:

```python
import requests

def update_dashboard(door_name, status):
    """Gửi cập nhật đến dashboard"""
    try:
        requests.post('http://localhost:8080/api/doors/update', 
                     json={'door': door_name, 'status': status},
                     timeout=2)
    except:
        pass  # Dashboard không bắt buộc

# Trong callback cửa mở
update_dashboard('door1', 'open')
```

## 🌐 Network Configuration

**Default:**
- Host: `0.0.0.0` (all interfaces)
- Port: `8080`

**Access từ:**
- Local: `http://localhost:8080`
- LAN: `http://192.168.1.15:8080`
- Mobile: `http://192.168.1.15:8080`

## 📱 Mobile Support

Dashboard được tối ưu cho mobile:
- Responsive grid
- Touch-friendly buttons
- Readable font sizes
- Smooth scrolling

## 🎨 Customization

### Thay đổi màu sắc

Edit `templates/dashboard.html`:
```css
/* Background gradient */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* Door open color */
.door-status.open { background: #e74c3c; }

/* Door closed color */
.door-status.closed { background: #2ecc71; }
```

### Thay đổi refresh interval

Edit `templates/dashboard.html`:
```javascript
const AUTO_REFRESH_INTERVAL = 5000; // 5 seconds
```

### Thay đổi số ảnh hiển thị

Edit `run_dashboard.py` hoặc API call:
```
/api/images?limit=10
```

## 🐛 Troubleshooting

### Dashboard không load
```bash
# Kiểm tra server chạy chưa
ps aux | grep dashboard

# Kiểm tra port
netstat -ano | findstr :8080
```

### Ảnh không hiển thị
```bash
# Kiểm tra thư mục images
ls -la images/

# Kiểm tra permissions
chmod 755 images/
```

### Cửa hiển thị "Unknown"
- Main.py chưa gửi update
- Chưa có sự kiện cửa nào
- API endpoint không khả dụng

## 📝 Logging

Log được ghi vào:
```
logs/dashboard.log
```

Format:
```
2025-11-26 14:30:55,123 - __main__ - INFO - 📊 Cập nhật trạng thái: door1 = open
```

## 🔒 Security

- No authentication (LAN only)
- Read-only cho client
- Update API chỉ từ localhost (recommended)
- CORS không bật (same-origin only)

## 💡 Tips

1. **Performance**: Giảm refresh interval nếu cần
2. **Images**: Cleanup ảnh cũ định kỳ
3. **Mobile**: Dùng PWA cho mobile app experience
4. **Monitoring**: Check logs định kỳ
5. **Backup**: Backup database nếu thêm persistence

## 🚀 Production Deployment

```bash
# Dùng gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 dashboard_server:app

# Hoặc systemd service
sudo systemctl start dashboard
sudo systemctl enable dashboard
```

## 📚 Xem thêm

- [Main README](../README.md)
- [Image Receiver](../IMAGE_RECEIVER.md)
- [System Guide](../SYSTEM_GUIDE.md)

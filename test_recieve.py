"""
Test Server - Nhận ảnh từ ESP32-CAM
Server này lắng nghe ở port 5000 và nhận ảnh từ ESP32-CAM gửi lên
"""

from flask import Flask, request, jsonify
import os
from datetime import datetime
from pathlib import Path

app = Flask(__name__)

# Tạo thư mục lưu ảnh
UPLOAD_FOLDER = 'images'
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Endpoint nhận ảnh từ ESP32-CAM
    ESP32 sẽ POST ảnh với Content-Type: image/jpeg
    """
    try:
        # Lấy dữ liệu ảnh từ request body
        image_data = request.get_data()
        
        if not image_data:
            return jsonify({
                'success': False,
                'error': 'No image data received'
            }), 400
        
        # Tạo tên file với timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'esp32_door_{timestamp}.jpg'
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        
        # Lưu ảnh
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        file_size = len(image_data)
        
        print("="*60)
        print(f"✅ Đã nhận ảnh từ ESP32-CAM!")
        print(f"📁 File: {filename}")
        print(f"📍 Path: {filepath}")
        print(f"📏 Size: {file_size} bytes ({file_size/1024:.2f} KB)")
        print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)
        
        # Trả về response cho ESP32
        return jsonify({
            'success': True,
            'filename': filename,
            'size': file_size,
            'message': 'Image received successfully'
        }), 200
        
    except Exception as e:
        print(f"❌ Lỗi khi nhận ảnh: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/status', methods=['GET'])
def status():
    """
    Endpoint kiểm tra server có hoạt động không
    """
    # Đếm số ảnh trong thư mục
    image_count = len(list(Path(UPLOAD_FOLDER).glob('*.jpg')))
    
    return jsonify({
        'status': 'online',
        'server': 'ESP32 Image Receiver',
        'upload_folder': UPLOAD_FOLDER,
        'images_count': image_count
    }), 200


@app.route('/', methods=['GET'])
def home():
    """
    Trang chủ hiển thị thông tin server
    """
    image_count = len(list(Path(UPLOAD_FOLDER).glob('*.jpg')))
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>ESP32-CAM Image Receiver</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 50px auto;
                padding: 20px;
            }}
            h1 {{ color: #2c3e50; }}
            .status {{ 
                background: #2ecc71;
                color: white;
                padding: 10px;
                border-radius: 5px;
                display: inline-block;
            }}
            .info {{
                background: #ecf0f1;
                padding: 15px;
                border-radius: 5px;
                margin: 10px 0;
            }}
            .endpoint {{
                background: #34495e;
                color: white;
                padding: 10px;
                border-radius: 3px;
                margin: 5px 0;
                font-family: monospace;
            }}
        </style>
    </head>
    <body>
        <h1>🏠 ESP32-CAM Image Receiver Server</h1>
        <div class="status">✅ Server đang hoạt động</div>
        
        <div class="info">
            <h3>📊 Thông tin:</h3>
            <p><strong>Upload Folder:</strong> {UPLOAD_FOLDER}</p>
            <p><strong>Số ảnh đã nhận:</strong> {image_count}</p>
            <p><strong>Port:</strong> 5000</p>
        </div>
        
        <div class="info">
            <h3>🔌 API Endpoints:</h3>
            <div class="endpoint">POST /upload</div>
            <p>Nhận ảnh từ ESP32-CAM (Content-Type: image/jpeg)</p>
            
            <div class="endpoint">GET /status</div>
            <p>Kiểm tra trạng thái server</p>
        </div>
        
        <div class="info">
            <h3>⚙️ Cấu hình ESP32-CAM:</h3>
            <pre>
const char* serverIp = "192.168.1.15";  // IP của máy này
const int serverPort = 5000;
const char* serverPath = "/upload";
            </pre>
        </div>
        
        <div class="info">
            <h3>🧪 Test với curl:</h3>
            <pre>
# Test status
curl http://localhost:5000/status

# Test upload (nếu có file test.jpg)
curl -X POST http://localhost:5000/upload \\
  -H "Content-Type: image/jpeg" \\
  --data-binary @test.jpg
            </pre>
        </div>
    </body>
    </html>
    """
    return html


def main():
    """Main function"""
    print("="*60)
    print("🏠 ESP32-CAM Image Receiver Server")
    print("="*60)
    print()
    print("📁 Upload folder:", UPLOAD_FOLDER)
    print("🔌 Server port: 5000")
    print()
    print("⚙️  Cấu hình ESP32-CAM:")
    print("   - serverIp: (IP của máy này)")
    print("   - serverPort: 5000")
    print("   - serverPath: /upload")
    print()
    print("🌐 Endpoints:")
    print("   POST http://localhost:5000/upload  - Nhận ảnh")
    print("   GET  http://localhost:5000/status  - Status")
    print("   GET  http://localhost:5000/        - Web UI")
    print()
    print("="*60)
    print("🚀 Server đang chạy...")
    print("   Truy cập: http://localhost:5000")
    print("   Nhấn Ctrl+C để dừng")
    print("="*60)
    print()
    
    # Chạy Flask server
    # host='0.0.0.0' để cho phép truy cập từ mạng LAN
    app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Server đã dừng!")
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")

"""
Test Dashboard - Wrapper để chạy dashboard server
"""

from dashboard_server import DashboardServer
from pathlib import Path

if __name__ == '__main__':
    print("=" * 60)
    print("Smart Home Web Dashboard (Test Mode)")
    print("=" * 60)
    print()
    
    # Tạo thư mục logs
    Path('../logs').mkdir(parents=True, exist_ok=True)
    
    # Tạo và chạy server
    server = DashboardServer(
        host='0.0.0.0',
        port=8080,
        image_folder='../images',
        config_path='../config.json'
    )
    
    print("\nTips:")
    print("   - Mở browser: http://localhost:8080")
    print("   - Auto refresh: Mỗi 5 giây")
    print("   - Nhấn R: Refresh thủ công")
    print("   - Click ảnh: Xem phóng to")
    print()
    
    server.run(debug=False)

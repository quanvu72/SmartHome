"""
Smart Home Door Sensor System
Giám sát cảm biến MC-38 → Gửi lệnh ESP32 chụp ảnh → ESP32 gửi ảnh đến test_recieve.py
"""

import time
import requests
from datetime import datetime
from pathlib import Path

try:
    import RPi.GPIO as GPIO
    MOCK_MODE = False
    print("✅ RPi.GPIO available - Running on Raspberry Pi")
except ImportError:
    print("⚠️  RPi.GPIO not available - Running in SIMULATION MODE")
    MOCK_MODE = True
    
    class MockGPIO:
        BCM = "BCM"
        IN = "IN"
        PUD_UP = "PUD_UP"
        
        @staticmethod
        def setmode(mode):
            print(f"[MOCK] GPIO.setmode({mode})")
        
        @staticmethod
        def setup(pin, mode, pull_up_down=None):
            print(f"[MOCK] GPIO.setup(pin={pin}, mode={mode})")
        
        @staticmethod
        def input(pin):
            # Simulate door opening every 10 seconds
            import random
            return random.choice([0, 0, 0, 0, 1])  # 20% chance of open
        
        @staticmethod
        def cleanup():
            print("[MOCK] GPIO.cleanup()")
    
    GPIO = MockGPIO()

# ===== CẤU HÌNH =====
DOOR1_PIN = 17  # GPIO 17 - Door 1
DOOR2_PIN = 27  # GPIO 27 - Door 2

# ESP32-CAM Configuration
ESP32_IP = "192.168.1.13"  # IP của ESP32-CAM
ESP32_PORT = 80
ESP32_CAPTURE_URL = f"http://{ESP32_IP}:{ESP32_PORT}/capture"

# Note: Ảnh sẽ được lưu bởi test_recieve.py, không cần folder ở đây
# Image save folder (not used anymore - images saved by test_recieve.py)

# Trạng thái cửa
door_states = {
    'door1': None,
    'door2': None
}


def request_esp32_capture(door_name):
    """
    Gửi lệnh đến ESP32 để chụp ảnh
    ESP32 sẽ tự động gửi ảnh đến test_recieve.py
    
    Returns:
        dict: Thông tin response nếu thành công, None nếu thất bại
    """
    print(f"📸 Gửi lệnh chụp ảnh đến ESP32-CAM ({ESP32_IP})...")
    
    try:
        # Gửi GET request đến ESP32 /capture endpoint
        # ESP32 sẽ chụp ảnh và gửi đến test_recieve.py
        response = requests.get(ESP32_CAPTURE_URL, timeout=15)
        
        if response.status_code == 200:
            try:
                result = response.json()
                print("="*60)
                print(f"✅ ESP32 ĐÃ CHỤP VÀ GỬI ẢNH!")
                print(f"📤 ESP32 đã gửi ảnh đến test_recieve.py")
                print(f"🖥️  Server: {result.get('uploaded_to', 'N/A')}")
                print(f"📏 Size: {result.get('size', 0)} bytes")
                print("="*60)
                return result
            except:
                # Response không phải JSON, vẫn coi là thành công
                print("✅ ESP32 đã nhận lệnh chụp ảnh")
                return {'success': True}
        else:
            print(f"❌ ESP32 trả về lỗi: HTTP {response.status_code}")
            return None
            
    except requests.exceptions.Timeout:
        print("❌ Timeout khi kết nối ESP32-CAM")
        return None
    except requests.exceptions.ConnectionError:
        print(f"❌ Không thể kết nối ESP32-CAM tại {ESP32_IP}")
        print(f"   Kiểm tra: ping {ESP32_IP}")
        return None
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None


def check_esp32_connection():
    """Kiểm tra kết nối đến ESP32-CAM"""
    print(f"🔍 Kiểm tra kết nối ESP32-CAM tại {ESP32_IP}...")
    
    try:
        # Try to connect to ESP32 status endpoint
        response = requests.get(f"http://{ESP32_IP}:{ESP32_PORT}/status", timeout=3)
        if response.status_code == 200:
            print(f"✅ ESP32-CAM đã kết nối ({ESP32_IP})")
            return True
    except:
        pass
    
    print(f"⚠️  Không thể kết nối ESP32-CAM")
    print(f"   Kiểm tra:")
    print(f"   1. ESP32 đã bật và kết nối WiFi chưa?")
    print(f"   2. Ping test: ping {ESP32_IP}")
    print(f"   3. Browser test: http://{ESP32_IP}")
    return False


def monitor_door_sensors():
    """
    Giám sát cảm biến cửa và xử lý khi phát hiện cửa mở
    """
    print("\n" + "="*60)
    print("🏠 SMART HOME DOOR MONITORING SYSTEM")
    print("="*60)
    print("🚪 Door 1: GPIO {DOOR1_PIN}")
    print(f"🚪 Door 2: GPIO {DOOR2_PIN}")
    print(f"📷 ESP32-CAM: {ESP32_IP}")
    print(f"💾 Images saved by: test_recieve.py (port 5000)")
    
    if MOCK_MODE:
        print("\n⚠️  RUNNING IN MOCK MODE (Simulation)")
    
    print("\n" + "="*60)
    
    # Setup GPIO
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(DOOR1_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(DOOR2_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    
    # Đọc trạng thái ban đầu
    door_states['door1'] = 'open' if GPIO.input(DOOR1_PIN) == 1 else 'closed'
    door_states['door2'] = 'open' if GPIO.input(DOOR2_PIN) == 1 else 'closed'
    
    print(f"📊 Trạng thái ban đầu:")
    print(f"   Door 1: {door_states['door1'].upper()}")
    print(f"   Door 2: {door_states['door2'].upper()}")
    
    # Kiểm tra ESP32
    check_esp32_connection()
    
    print("\n🚀 Bắt đầu giám sát... (Nhấn Ctrl+C để dừng)")
    print("="*60 + "\n")
    
    try:
        while True:
            # Đọc trạng thái cảm biến
            state1 = GPIO.input(DOOR1_PIN)
            state2 = GPIO.input(DOOR2_PIN)
            
            current_state1 = 'open' if state1 == 1 else 'closed'
            current_state2 = 'open' if state2 == 1 else 'closed'
            
            # Kiểm tra Door 1
            if current_state1 == 'open' and door_states['door1'] != 'open':
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print("\n" + "🚨"*30)
                print(f"🚪 DOOR 1 MỞ! - {timestamp}")
                print("🚨"*30)
                
                # Gửi lệnh chụp ảnh đến ESP32
                result = request_esp32_capture('door1')
                
                if result:
                    print(f"✅ Workflow hoàn tất: Phát hiện cửa → ESP32 chụp → Gửi đến test_recieve.py")
                else:
                    print(f"⚠️  ESP32 không phản hồi")
                
                print()
                
            door_states['door1'] = current_state1
            
            # Kiểm tra Door 2
            if current_state2 == 'open' and door_states['door2'] != 'open':
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print("\n" + "🚨"*30)
                print(f"🚪 DOOR 2 MỞ! - {timestamp}")
                print("🚨"*30)
                
                # Gửi lệnh chụp ảnh đến ESP32
                result = request_esp32_capture('door2')
                
                if result:
                    print(f"✅ Workflow hoàn tất: Phát hiện cửa → ESP32 chụp → Gửi đến test_recieve.py")
                else:
                    print(f"⚠️  ESP32 không phản hồi")
                
                print()
                
            door_states['door2'] = current_state2
            
            # Hiển thị status
            status_icon1 = "🔓" if current_state1 == 'open' else "🔒"
            status_icon2 = "🔓" if current_state2 == 'open' else "🔒"
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] {status_icon1} Door1: {current_state1:6s} | {status_icon2} Door2: {current_state2:6s}", end='', flush=True)
            
            time.sleep(0.2)  # Check every 200ms
            
    except KeyboardInterrupt:
        print("\n\n🛑 Đang dừng hệ thống...")
    finally:
        GPIO.cleanup()
        print("✅ Đã cleanup GPIO")
        
        print(f"\n📊 Tổng kết:")
        print(f"   Tổng số lệnh chụp ảnh đã gửi: Xem log trên")
        print(f"   Ảnh được lưu bởi: test_recieve.py")
        print(f"   Kiểm tra: images/ folder trên Raspberry Pi")


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════╗
║     Smart Home Door Monitoring + ESP32-CAM System       ║
║     Raspberry Pi → ESP32 Camera Integration             ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    try:
        monitor_door_sensors()
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        GPIO.cleanup()

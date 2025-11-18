"""
Smart Home Management System - Main Controller
Hệ thống quản lý nhà thông minh với giám sát cảm biến cửa và ESP32-CAM
"""

import os
import sys
import json
import time
import signal
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict

# Import các module của hệ thống
from modules.door_sensor import DoorSensorMonitor
from modules.esp32_camera import ESP32CameraClient
from modules.web_notifier import WebNotifier, MockWebNotifier


class SmartHomeSystem:
    """
    Class chính điều khiển toàn bộ hệ thống Smart Home
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Khởi tạo Smart Home System
        
        Args:
            config_path: Đường dẫn đến file cấu hình
        """
        self.config_path = config_path
        self.config = self._load_config()
        self.running = False
        
        # Setup logging
        self._setup_logging()
        
        self.logger.info("=" * 60)
        self.logger.info("🏠 Smart Home Management System Starting...")
        self.logger.info("=" * 60)
        
        # Khởi tạo các module
        self.door_monitor = None
        self.camera_client = None
        self.web_notifier = None
        
        self._initialize_modules()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        self.start_time = datetime.now()
        
    def _load_config(self) -> Dict:
        """Load cấu hình từ file JSON"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ Đã load config từ {self.config_path}")
            return config
        except FileNotFoundError:
            print(f"⚠️  File config không tồn tại: {self.config_path}")
            print("Sử dụng cấu hình mặc định...")
            return self._default_config()
        except json.JSONDecodeError as e:
            print(f"❌ Lỗi parse JSON: {e}")
            sys.exit(1)
    
    def _default_config(self) -> Dict:
        """Trả về cấu hình mặc định"""
        return {
            "door_sensors": {
                "door1_pin": 17,
                "door2_pin": 27
            },
            "esp32": {
                "ip": "192.168.1.100",
                "port": 80,
                "timeout": 10
            },
            "web_server": {
                "url": "http://localhost:3000/api/notification",
                "timeout": 5,
                "retry_count": 3,
                "use_mock": True
            },
            "system": {
                "image_path": "images",
                "log_path": "logs",
                "log_level": "INFO",
                "cleanup_images_days": 7
            }
        }
    
    def _setup_logging(self):
        """Setup logging system"""
        log_config = self.config.get('system', {})
        log_path = Path(log_config.get('log_path', 'logs'))
        log_level = log_config.get('log_level', 'INFO')
        
        # Tạo thư mục logs
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Tạo log file với timestamp
        log_file = log_path / f"smarthome_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging đã được cấu hình: {log_file}")
    
    def _initialize_modules(self):
        """Khởi tạo tất cả các module"""
        try:
            # 1. Khởi tạo ESP32 Camera Client
            esp32_config = self.config.get('esp32', {})
            system_config = self.config.get('system', {})
            
            self.camera_client = ESP32CameraClient(
                esp32_ip=esp32_config.get('ip', '192.168.1.100'),
                esp32_port=esp32_config.get('port', 80),
                image_save_path=system_config.get('image_path', 'images'),
                timeout=esp32_config.get('timeout', 10)
            )
            
            # Kiểm tra kết nối ESP32
            if self.camera_client.check_connection():
                self.logger.info("✅ ESP32-CAM đã kết nối")
            else:
                self.logger.warning("⚠️  Không thể kết nối ESP32-CAM (sẽ thử lại sau)")
            
            # 2. Khởi tạo Web Notifier
            web_config = self.config.get('web_server', {})
            
            if web_config.get('use_mock', False):
                self.logger.info("Sử dụng Mock Web Notifier")
                self.web_notifier = MockWebNotifier()
            else:
                self.web_notifier = WebNotifier(
                    web_api_url=web_config.get('url', 'http://localhost:3000/api/notification'),
                    timeout=web_config.get('timeout', 5),
                    retry_count=web_config.get('retry_count', 3)
                )
            
            # 3. Khởi tạo Door Sensor Monitor (cuối cùng để bắt đầu monitoring)
            door_config = self.config.get('door_sensors', {})
            
            self.door_monitor = DoorSensorMonitor(
                door1_pin=door_config.get('door1_pin', 17),
                door2_pin=door_config.get('door2_pin', 27),
                callback=self._on_door_opened
            )
            
            self.logger.info("✅ Đã khởi tạo tất cả các module")
            
        except Exception as e:
            self.logger.error(f"❌ Lỗi khi khởi tạo modules: {e}")
            raise
    
    def _on_door_opened(self, event_data: Dict):
        """
        Callback khi phát hiện cửa được mở
        
        Args:
            event_data: Dictionary chứa thông tin sự kiện
        """
        door_name = event_data.get('door', 'unknown')
        timestamp = event_data.get('timestamp', '')
        
        self.logger.info(f"🚪 Phát hiện {door_name.upper()} được mở lúc {timestamp}")
        
        # 1. Gửi yêu cầu chụp ảnh đến ESP32
        self.logger.info(f"📸 Gửi yêu cầu chụp ảnh cho {door_name}...")
        
        image_result = self.camera_client.capture_image(door_name=door_name)
        
        if image_result and image_result.get('success'):
            self.logger.info(f"✅ Đã nhận ảnh: {image_result['filename']}")
            
            # 2. Chuẩn bị dữ liệu thông báo
            notification_data = {
                'door': door_name,
                'status': 'open',
                'timestamp': image_result['timestamp'],
                'image_filename': image_result['filename'],
                'image_path': image_result['image_path'],
                'image_size': image_result['size']
            }
            
            # 3. Gửi thông báo đến web
            self.logger.info("📤 Gửi thông báo đến web server...")
            
            if self.web_notifier.send_notification(notification_data):
                self.logger.info("✅ Đã gửi thông báo thành công")
            else:
                self.logger.error("❌ Không thể gửi thông báo đến web")
        else:
            error_msg = image_result.get('error', 'Unknown error') if image_result else 'No response'
            self.logger.error(f"❌ Không thể chụp ảnh: {error_msg}")
            
            # Vẫn gửi thông báo nhưng không có ảnh
            notification_data = {
                'door': door_name,
                'status': 'open',
                'timestamp': timestamp,
                'image_filename': None,
                'error': error_msg
            }
            self.web_notifier.send_notification(notification_data)
    
    def _signal_handler(self, signum, frame):
        """Xử lý signal để dừng hệ thống một cách graceful"""
        signal_name = signal.Signals(signum).name
        self.logger.info(f"\n🛑 Nhận signal {signal_name}. Đang dừng hệ thống...")
        self.stop()
    
    def start(self):
        """Khởi động hệ thống"""
        self.running = True
        
        self.logger.info("🚀 Hệ thống đã khởi động")
        self.logger.info("Đang giám sát cảm biến cửa...")
        
        # Hiển thị trạng thái ban đầu
        initial_states = self.door_monitor.get_door_states()
        self.logger.info(f"Trạng thái ban đầu: Door1={initial_states['door1']}, Door2={initial_states['door2']}")
        
        # Main loop
        try:
            heartbeat_interval = 300  # 5 phút
            last_heartbeat = time.time()
            cleanup_interval = 86400  # 24 giờ
            last_cleanup = time.time()
            
            while self.running:
                current_time = time.time()
                
                # Gửi heartbeat định kỳ
                if current_time - last_heartbeat >= heartbeat_interval:
                    self.web_notifier.send_heartbeat()
                    last_heartbeat = current_time
                
                # Cleanup ảnh cũ định kỳ
                if current_time - last_cleanup >= cleanup_interval:
                    cleanup_days = self.config.get('system', {}).get('cleanup_images_days', 7)
                    self.camera_client.cleanup_old_images(keep_days=cleanup_days)
                    last_cleanup = current_time
                
                # Hiển thị trạng thái
                states = self.door_monitor.get_door_states()
                uptime = datetime.now() - self.start_time
                
                self.logger.info(
                    f"📊 Status: Door1={states['door1']}, Door2={states['door2']}, "
                    f"Uptime={str(uptime).split('.')[0]}"
                )
                
                # Sleep 30 giây
                time.sleep(30)
                
        except KeyboardInterrupt:
            self.logger.info("\n🛑 Nhận Ctrl+C. Đang dừng hệ thống...")
        except Exception as e:
            self.logger.error(f"❌ Lỗi trong main loop: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Dừng hệ thống"""
        if not self.running:
            return
            
        self.running = False
        
        self.logger.info("Đang cleanup resources...")
        
        # Cleanup door monitor
        if self.door_monitor:
            self.door_monitor.cleanup()
        
        uptime = datetime.now() - self.start_time
        self.logger.info(f"Total uptime: {str(uptime).split('.')[0]}")
        self.logger.info("=" * 60)
        self.logger.info("🏠 Smart Home System đã dừng")
        self.logger.info("=" * 60)


def main():
    """Main entry point"""
    print("=" * 60)
    print("🏠 Smart Home Management System")
    print("   Raspberry Pi 5 + ESP32-CAM")
    print("=" * 60)
    print()
    
    # Kiểm tra config file
    config_file = "config.json"
    if not os.path.exists(config_file):
        print(f"⚠️  Config file không tồn tại: {config_file}")
        print("Tạo config mặc định...")
        
        # Tạo config mẫu
        default_config = {
            "door_sensors": {
                "door1_pin": 17,
                "door2_pin": 27
            },
            "esp32": {
                "ip": "192.168.1.100",
                "port": 80,
                "timeout": 10
            },
            "web_server": {
                "url": "http://localhost:3000/api/notification",
                "timeout": 5,
                "retry_count": 3,
                "use_mock": True
            },
            "system": {
                "image_path": "images",
                "log_path": "logs",
                "log_level": "INFO",
                "cleanup_images_days": 7
            }
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Đã tạo {config_file}")
        print()
    
    # Khởi tạo và chạy hệ thống
    try:
        system = SmartHomeSystem(config_path=config_file)
        system.start()
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Module ESP32 Camera Client
Gửi yêu cầu chụp ảnh đến ESP32-CAM và nhận ảnh qua HTTP
"""

import os
import logging
import requests
from typing import Optional, Dict
from datetime import datetime
from pathlib import Path


class ESP32CameraClient:
    """
    Client để giao tiếp với ESP32-CAM qua HTTP
    """
    
    def __init__(self, esp32_ip: str, esp32_port: int = 80, 
                 image_save_path: str = "images", timeout: int = 10):
        """
        Khởi tạo ESP32 Camera Client
        
        Args:
            esp32_ip: Địa chỉ IP của ESP32-CAM
            esp32_port: Port của ESP32-CAM HTTP server (mặc định 80)
            image_save_path: Đường dẫn lưu ảnh
            timeout: Timeout cho HTTP request (giây)
        """
        self.esp32_ip = esp32_ip
        self.esp32_port = esp32_port
        self.base_url = f"http://{esp32_ip}:{esp32_port}"
        self.image_save_path = Path(image_save_path)
        self.timeout = timeout
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Tạo thư mục lưu ảnh nếu chưa có
        self._create_image_directory()
        
        self.logger.info(f"Đã khởi tạo ESP32 Camera Client (URL: {self.base_url})")
    
    def _create_image_directory(self):
        """Tạo thư mục lưu ảnh"""
        try:
            self.image_save_path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Thư mục lưu ảnh: {self.image_save_path.absolute()}")
        except Exception as e:
            self.logger.error(f"Không thể tạo thư mục lưu ảnh: {e}")
            raise
    
    def check_connection(self) -> bool:
        """
        Kiểm tra kết nối đến ESP32-CAM
        
        Returns:
            True nếu kết nối thành công, False nếu không
        """
        try:
            response = requests.get(
                f"{self.base_url}/status",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.logger.info(f"Kết nối ESP32-CAM thành công: {self.esp32_ip}")
                return True
            else:
                self.logger.warning(f"ESP32-CAM phản hồi code: {response.status_code}")
                return False
                
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout khi kết nối ESP32-CAM: {self.esp32_ip}")
            return False
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Không thể kết nối ESP32-CAM: {self.esp32_ip}")
            return False
        except Exception as e:
            self.logger.error(f"Lỗi khi kiểm tra kết nối ESP32-CAM: {e}")
            return False
    
    def request_capture(self, door_name: str = "door") -> Optional[Dict[str, str]]:
        """
        Gửi lệnh chụp ảnh đến ESP32-CAM
        ESP32 sẽ tự động chụp và gửi ảnh đến test_recieve.py
        
        Args:
            door_name: Tên cửa (không sử dụng, chỉ để tương thích)
            
        Returns:
            Dictionary chứa thông tin response nếu thành công, None nếu thất bại
            {
                'success': True/False,
                'uploaded_to': 'http://192.168.1.15:5000/upload',
                'size': 12345,  # bytes
                'error': 'error message'  # nếu có lỗi
            }
        """
        try:
            self.logger.info(f"Gửi lệnh chụp ảnh đến ESP32-CAM ({door_name})...")
            
            # Gửi GET request đến endpoint /capture
            # ESP32 sẽ chụp ảnh và gửi đến test_recieve.py
            response = requests.get(
                f"{self.base_url}/capture",
                timeout=15  # Tăng timeout vì ESP32 cần thời gian chụp và upload
            )
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    self.logger.info(f"✅ ESP32 đã chụp và gửi ảnh")
                    self.logger.info(f"📤 Upload to: {result.get('uploaded_to', 'N/A')}")
                    self.logger.info(f"📏 Size: {result.get('size', 0)} bytes")
                    
                    return {
                        'success': True,
                        'uploaded_to': result.get('uploaded_to', 'N/A'),
                        'size': result.get('size', 0),
                        'door': door_name
                    }
                except:
                    # Response không phải JSON, vẫn coi là thành công
                    self.logger.info("✅ ESP32 đã nhận lệnh chụp ảnh")
                    return {
                        'success': True,
                        'door': door_name
                    }
            else:
                self.logger.error(f"ESP32-CAM trả về lỗi: {response.status_code}")
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}",
                    'door': door_name
                }
                
        except requests.exceptions.Timeout:
            self.logger.error(f"Timeout khi gửi lệnh đến ESP32-CAM")
            return {
                'success': False,
                'error': 'Timeout',
                'door': door_name
            }
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Không thể kết nối ESP32-CAM")
            return {
                'success': False,
                'error': 'Connection Error',
                'door': door_name
            }
        except Exception as e:
            self.logger.error(f"Lỗi khi gửi lệnh chụp: {e}")
            return {
                'success': False,
                'error': str(e),
                'door': door_name
            }
    
    def capture_image(self, door_name: str = "door") -> Optional[Dict[str, str]]:
        """
        [DEPRECATED] Method cũ - giữ lại để tương thích
        Sử dụng request_capture() thay thế
        
        Gửi yêu cầu chụp ảnh đến ESP32-CAM và lưu ảnh
        
        Args:
            door_name: Tên cửa để đặt tên file ảnh
            
        Returns:
            Dictionary chứa thông tin ảnh nếu thành công, None nếu thất bại
        """
        self.logger.warning("capture_image() is deprecated, use request_capture() instead")
        return self.request_capture(door_name)
    
    def get_camera_info(self) -> Optional[Dict]:
        """
        Lấy thông tin camera từ ESP32
        
        Returns:
            Dictionary chứa thông tin camera hoặc None
        """
        try:
            response = requests.get(
                f"{self.base_url}/info",
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.warning(f"Không thể lấy thông tin camera: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Lỗi khi lấy thông tin camera: {e}")
            return None
    
    def cleanup_old_images(self, keep_days: int = 7):
        """
        Xóa các ảnh cũ hơn số ngày chỉ định
        
        Args:
            keep_days: Số ngày giữ ảnh (mặc định 7 ngày)
        """
        try:
            current_time = datetime.now()
            deleted_count = 0
            
            for image_file in self.image_save_path.glob("*.jpg"):
                # Lấy thời gian sửa đổi file
                file_time = datetime.fromtimestamp(image_file.stat().st_mtime)
                age_days = (current_time - file_time).days
                
                if age_days > keep_days:
                    image_file.unlink()
                    deleted_count += 1
                    self.logger.info(f"Đã xóa ảnh cũ: {image_file.name} ({age_days} ngày)")
            
            if deleted_count > 0:
                self.logger.info(f"Đã xóa {deleted_count} ảnh cũ")
            
        except Exception as e:
            self.logger.error(f"Lỗi khi cleanup ảnh cũ: {e}")


if __name__ == "__main__":
    # Test module
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Tạo client
    client = ESP32CameraClient(
        esp32_ip="192.168.1.100",
        esp32_port=80
    )
    
    # Test kết nối
    print("Kiểm tra kết nối...")
    if client.check_connection():
        print("✅ Kết nối thành công!")
        
        # Test chụp ảnh
        print("\nChụp ảnh test...")
        result = client.capture_image(door_name="test_door")
        
        if result and result.get('success'):
            print(f"✅ Chụp ảnh thành công: {result['filename']}")
            print(f"   Đường dẫn: {result['image_path']}")
            print(f"   Kích thước: {result['size']} bytes")
        else:
            print(f"❌ Chụp ảnh thất bại: {result.get('error', 'Unknown error')}")
    else:
        print("❌ Không thể kết nối ESP32-CAM")

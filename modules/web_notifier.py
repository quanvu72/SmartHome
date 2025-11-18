"""
Module Web Notifier
Gửi thông báo đến web server khi có sự kiện cửa mở
"""

import logging
import requests
import json
from typing import Dict, Optional
from datetime import datetime


class WebNotifier:
    """
    Client để gửi thông báo đến web server
    """
    
    def __init__(self, web_api_url: str, timeout: int = 5, retry_count: int = 3):
        """
        Khởi tạo Web Notifier
        
        Args:
            web_api_url: URL của web API endpoint
            timeout: Timeout cho HTTP request (giây)
            retry_count: Số lần thử lại khi gửi thất bại
        """
        self.web_api_url = web_api_url
        self.timeout = timeout
        self.retry_count = retry_count
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"Đã khởi tạo Web Notifier (API: {web_api_url})")
    
    def send_notification(self, event_data: Dict) -> bool:
        """
        Gửi thông báo đến web server
        
        Args:
            event_data: Dictionary chứa thông tin sự kiện
            {
                'door': 'door1',
                'status': 'open',
                'timestamp': '2025-11-18 10:30:00',
                'image_path': '/path/to/image.jpg',
                'image_filename': 'door1_20251118_103000.jpg',
                'image_size': 12345
            }
            
        Returns:
            True nếu gửi thành công, False nếu thất bại
        """
        # Chuẩn bị payload
        payload = {
            'event_type': 'door_opened',
            'door': event_data.get('door', 'unknown'),
            'status': event_data.get('status', 'open'),
            'timestamp': event_data.get('timestamp', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            'image_filename': event_data.get('image_filename'),
            'image_path': event_data.get('image_path'),
            'image_size': event_data.get('image_size'),
            'device': 'raspberry_pi_5',
            'location': 'home'
        }
        
        # Thử gửi với retry
        for attempt in range(1, self.retry_count + 1):
            try:
                self.logger.info(f"Gửi thông báo đến web server (lần thử {attempt}/{self.retry_count})...")
                
                response = requests.post(
                    self.web_api_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=self.timeout
                )
                
                if response.status_code in [200, 201]:
                    self.logger.info(f"✅ Đã gửi thông báo thành công đến web server")
                    try:
                        response_data = response.json()
                        self.logger.debug(f"Response: {response_data}")
                    except:
                        pass
                    return True
                else:
                    self.logger.warning(
                        f"Web server trả về code {response.status_code}: {response.text[:200]}"
                    )
                    
                    # Không retry nếu lỗi client (4xx)
                    if 400 <= response.status_code < 500:
                        return False
                        
            except requests.exceptions.Timeout:
                self.logger.error(f"Timeout khi gửi thông báo (lần {attempt})")
            except requests.exceptions.ConnectionError:
                self.logger.error(f"Không thể kết nối web server (lần {attempt})")
            except Exception as e:
                self.logger.error(f"Lỗi khi gửi thông báo (lần {attempt}): {e}")
            
            # Đợi trước khi retry
            if attempt < self.retry_count:
                import time
                time.sleep(1)
        
        self.logger.error(f"❌ Không thể gửi thông báo sau {self.retry_count} lần thử")
        return False
    
    def send_heartbeat(self) -> bool:
        """
        Gửi heartbeat đến web server để báo hệ thống đang hoạt động
        
        Returns:
            True nếu gửi thành công, False nếu thất bại
        """
        payload = {
            'event_type': 'heartbeat',
            'device': 'raspberry_pi_5',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'status': 'online'
        }
        
        try:
            response = requests.post(
                self.web_api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                self.logger.debug("Heartbeat gửi thành công")
                return True
            else:
                self.logger.warning(f"Heartbeat failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Lỗi khi gửi heartbeat: {e}")
            return False
    
    def send_system_status(self, status_data: Dict) -> bool:
        """
        Gửi trạng thái hệ thống đến web server
        
        Args:
            status_data: Dictionary chứa thông tin trạng thái
            {
                'door1_status': 'closed',
                'door2_status': 'open',
                'esp32_connected': True,
                'uptime': 3600,
                'cpu_temp': 45.5
            }
            
        Returns:
            True nếu gửi thành công, False nếu thất bại
        """
        payload = {
            'event_type': 'system_status',
            'device': 'raspberry_pi_5',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data': status_data
        }
        
        try:
            response = requests.post(
                self.web_api_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                self.logger.info("Đã gửi trạng thái hệ thống")
                return True
            else:
                self.logger.warning(f"Gửi trạng thái thất bại: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Lỗi khi gửi trạng thái: {e}")
            return False
    
    def check_api_health(self) -> bool:
        """
        Kiểm tra web API có hoạt động không
        
        Returns:
            True nếu API hoạt động, False nếu không
        """
        try:
            # Thử gửi GET request đến base URL hoặc health endpoint
            health_url = self.web_api_url.replace('/notification', '/health')
            
            response = requests.get(
                health_url,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                self.logger.info("Web API đang hoạt động")
                return True
            else:
                self.logger.warning(f"Web API trả về code: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Không thể kết nối Web API: {e}")
            return False


class MockWebNotifier(WebNotifier):
    """
    Mock Web Notifier cho testing mà không cần web server thật
    """
    
    def __init__(self, **kwargs):
        super().__init__(web_api_url="http://mock-server.local/api", **kwargs)
        self.notifications = []
        self.logger.info("Sử dụng Mock Web Notifier (không gửi request thật)")
    
    def send_notification(self, event_data: Dict) -> bool:
        """Lưu notification vào list thay vì gửi HTTP"""
        self.notifications.append({
            'timestamp': datetime.now().isoformat(),
            'data': event_data
        })
        self.logger.info(f"📝 Mock: Đã lưu notification - {event_data.get('door')} {event_data.get('status')}")
        return True
    
    def send_heartbeat(self) -> bool:
        """Mock heartbeat"""
        self.logger.debug("Mock: Heartbeat")
        return True
    
    def send_system_status(self, status_data: Dict) -> bool:
        """Mock system status"""
        self.logger.info(f"Mock: System status - {status_data}")
        return True
    
    def check_api_health(self) -> bool:
        """Mock API health check"""
        return True
    
    def get_notifications(self) -> list:
        """Lấy danh sách notifications đã lưu"""
        return self.notifications.copy()


if __name__ == "__main__":
    # Test module
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Test với Mock Notifier
    print("=== Test Mock Web Notifier ===")
    mock_notifier = MockWebNotifier()
    
    test_event = {
        'door': 'door1',
        'status': 'open',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'image_filename': 'test_image.jpg',
        'image_path': '/images/test_image.jpg',
        'image_size': 12345
    }
    
    if mock_notifier.send_notification(test_event):
        print("✅ Mock notification gửi thành công")
    
    print(f"\nDanh sách notifications: {len(mock_notifier.get_notifications())}")
    
    # Test với real notifier (sẽ fail nếu không có server)
    print("\n=== Test Real Web Notifier ===")
    real_notifier = WebNotifier(
        web_api_url="http://localhost:3000/api/notification",
        retry_count=1
    )
    
    # Kiểm tra API health
    if real_notifier.check_api_health():
        print("✅ Web API đang hoạt động")
        real_notifier.send_notification(test_event)
    else:
        print("⚠️  Web API không khả dụng (điều này bình thường nếu chưa setup server)")

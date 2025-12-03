"""
Module Door Sensor Monitor
Giám sát trạng thái của 2 cảm biến cửa sử dụng GPIO trên Raspberry Pi
"""

import time
import logging
from typing import Callable, Dict
from datetime import datetime

try:
    import RPi.GPIO as GPIO
except ImportError:
    # Mock GPIO cho môi trường development không có Raspberry Pi
    class MockGPIO:
        BCM = "BCM"
        IN = "IN"
        PUD_UP = "PUD_UP"
        RISING = "RISING"
        FALLING = "FALLING"
        
        @staticmethod
        def setmode(mode):
            pass
        
        @staticmethod
        def setup(pin, mode, pull_up_down=None):
            pass
        
        @staticmethod
        def input(pin):
            return 1
        
        @staticmethod
        def add_event_detect(pin, edge, callback=None, bouncetime=None):
            pass
        
        @staticmethod
        def cleanup():
            pass
    
    GPIO = MockGPIO()
    logging.warning("RPi.GPIO không khả dụng. Sử dụng Mock GPIO cho development.")


class DoorSensorMonitor:
    """
    Class giám sát cảm biến cửa
    """
    
    def __init__(self, door1_pin: int, door2_pin: int, callback: Callable = None):
        """
        Khởi tạo Door Sensor Monitor
        
        Args:
            door1_pin: GPIO pin cho cảm biến cửa 1
            door2_pin: GPIO pin cho cảm biến cửa 2
            callback: Hàm callback khi phát hiện thay đổi trạng thái cửa
        """
        self.door1_pin = door1_pin
        self.door2_pin = door2_pin
        self.callback = callback
        
        # Trạng thái hiện tại của cửa
        self.door_states = {
            'door1': None,
            'door2': None
        }
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Setup GPIO
        self._setup_gpio()
        
        self.logger.info(f"Đã khởi tạo Door Sensor Monitor (Pin Door1: {door1_pin}, Pin Door2: {door2_pin})")
    
    def _setup_gpio(self):
        """Cấu hình GPIO pins"""
        try:
            # Sử dụng BCM numbering
            GPIO.setmode(GPIO.BCM)
            
            # Setup pins với pull-up resistor
            # Khi cửa đóng (magnet gần reed switch): GPIO = LOW (0)
            # Khi cửa mở (magnet xa reed switch): GPIO = HIGH (1)
            GPIO.setup(self.door1_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            GPIO.setup(self.door2_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            
            # Đọc trạng thái ban đầu
            self.door_states['door1'] = self._read_door_state(self.door1_pin)
            self.door_states['door2'] = self._read_door_state(self.door2_pin)
            
            self.logger.info(f"Trạng thái ban đầu - Door1: {self.door_states['door1']}, Door2: {self.door_states['door2']}")
            
            # Setup event detection với debouncing
            # GPIO.RISING: phát hiện khi GPIO chuyển từ LOW (0) sang HIGH (1)
            # Tức là khi cửa chuyển từ ĐÓNG sang MỞ
            # GPIO.FALLING: phát hiện khi GPIO chuyển từ HIGH (1) sang LOW (0)
            # Tức là khi cửa chuyển từ MỞ sang ĐÓNG
            GPIO.add_event_detect(
                self.door1_pin,
                GPIO.BOTH,  # Phát hiện cả mở và đóng (RISING + FALLING)
                callback=lambda channel: self._door_callback('door1', channel),
                bouncetime=500  # 500ms debounce để tránh nhiễu
            )
            
            GPIO.add_event_detect(
                self.door2_pin,
                GPIO.BOTH,  # Phát hiện cả mở và đóng
                callback=lambda channel: self._door_callback('door2', channel),
                bouncetime=500
            )
            
            self.logger.info("Đã setup event detection cho cả 2 cửa (phát hiện cả mở và đóng)")
            
        except Exception as e:
            self.logger.error(f"Lỗi khi setup GPIO: {e}")
            raise
    
    def _read_door_state(self, pin: int) -> str:
        """
        Đọc trạng thái cảm biến MC-38 từ GPIO pin
        
        MC-38 Reed Switch Logic:
        - GPIO HIGH (1) = mạch hở = magnet xa = Cửa MỞ
        - GPIO LOW (0) = mạch đóng = magnet gần = Cửa ĐÓNG
        
        Args:
            pin: GPIO pin number
            
        Returns:
            'open' hoặc 'closed'
        """
        state = GPIO.input(pin)
        # HIGH (1) = cửa mở, LOW (0) = cửa đóng (giống test_sensor.py)
        return 'open' if state == 1 else 'closed'
    
    def _door_callback(self, door_name: str, channel: int):
        """
        Callback khi phát hiện cửa mở (GPIO RISING: LOW -> HIGH)
        
        Args:
            door_name: Tên cửa ('door1' hoặc 'door2')
            channel: GPIO channel
        """
        # Đợi một chút để đảm bảo tín hiệu ổn định
        time.sleep(0.05)
        
        # Đọc trạng thái mới
        new_state = self._read_door_state(channel)
        old_state = self.door_states[door_name]
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        self.logger.info(f"[{timestamp}] {door_name.upper()} thay đổi: {old_state} -> {new_state}")
        
        # Cập nhật trạng thái
        self.door_states[door_name] = new_state
        
        # Gọi callback cho mọi thay đổi trạng thái
        event_data = {
            'door': door_name,
            'status': new_state,
            'timestamp': timestamp,
            'pin': channel
        }
        
        if new_state == 'open':
            self.logger.info(f"{door_name.upper()} được mở! Gọi callback...")
        else:
            self.logger.info(f"{door_name.upper()} được đóng! Gọi callback...")
        
        # Gọi callback
        if self.callback:
            try:
                self.callback(event_data)
            except Exception as e:
                self.logger.error(f"Lỗi khi gọi callback: {e}")
    
    def get_door_states(self) -> Dict[str, str]:
        """
        Lấy trạng thái hiện tại của tất cả các cửa
        
        Returns:
            Dictionary chứa trạng thái các cửa
        """
        # Đọc lại trạng thái hiện tại
        self.door_states['door1'] = self._read_door_state(self.door1_pin)
        self.door_states['door2'] = self._read_door_state(self.door2_pin)
        
        return self.door_states.copy()
    
    def cleanup(self):
        """Cleanup GPIO resources"""
        try:
            GPIO.cleanup()
            self.logger.info("Đã cleanup GPIO resources")
        except Exception as e:
            self.logger.error(f"Lỗi khi cleanup GPIO: {e}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.cleanup()


if __name__ == "__main__":
    # Test module
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def test_callback(event_data):
        print(f"Cửa được mở: {event_data}")
    
    # Test với GPIO pins mặc định
    with DoorSensorMonitor(door1_pin=17, door2_pin=27, callback=test_callback) as monitor:
        print("Đang giám sát cửa... Nhấn Ctrl+C để thoát")
        try:
            while True:
                states = monitor.get_door_states()
                print(f"Trạng thái: Door1={states['door1']}, Door2={states['door2']}")
                time.sleep(5)
        except KeyboardInterrupt:
            print("\nĐang dừng monitor...")

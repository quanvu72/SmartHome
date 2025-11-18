"""
Smart Home Management System - Modules Package
Chứa các module chính của hệ thống quản lý nhà thông minh
"""

__version__ = "1.0.0"
__author__ = "Smart Home IoT Project"

# Import các module chính
from .door_sensor import DoorSensorMonitor
from .esp32_camera import ESP32CameraClient
from .web_notifier import WebNotifier

__all__ = [
    'DoorSensorMonitor',
    'ESP32CameraClient',
    'WebNotifier'
]

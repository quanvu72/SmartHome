"""
Web Dashboard Server - Smart Home Monitoring
Hiển thị trạng thái cửa và ảnh mới nhất từ ESP32-CAM
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory, request, redirect, url_for, make_response
from typing import Dict, List, Optional

# Import authentication module
from web_dashboard.auth import AuthManager, login_required, admin_required

# Thêm parent directory vào path để import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Tạo thư mục logs nếu chưa có
Path('logs').mkdir(parents=True, exist_ok=True)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/dashboard.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class DashboardServer:
    """
    Flask server hiển thị dashboard giám sát smart home
    """
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080,
                 image_folder: str = 'images', config_path: str = 'config.json'):
        """
        Khởi tạo Dashboard Server
        
        Args:
            host: Host address
            port: Port number
            image_folder: Thư mục chứa ảnh
            config_path: Đường dẫn file config
        """
        self.host = host
        self.port = port
        self.image_folder = Path(image_folder)
        self.config_path = config_path
        
        # Load config
        self.config = self._load_config()
        
        # Trạng thái cửa (sẽ được cập nhật từ API)
        self.door_states = {
            'door1': {
                'status': 'unknown',
                'last_updated': None,
                'pin': self.config.get('door_sensors', {}).get('door1_pin', 17)
            },
            'door2': {
                'status': 'unknown',
                'last_updated': None,
                'pin': self.config.get('door_sensors', {}).get('door2_pin', 27)
            }
        }
        
        # Statistics
        self.stats = {
            'total_events': 0,
            'start_time': datetime.now()
        }
        
        # Camera settings
        self.camera_settings = {
            'mode': self.config.get('camera', {}).get('mode', 'auto')
        }
        
        # ESP32 connection status
        self.esp32_online = False
        self.last_esp32_check = None
        
        # Tạo Flask app
        template_folder = Path(__file__).parent / 'templates'
        static_folder = Path(__file__).parent / 'static'
        
        self.app = Flask(__name__,
                        template_folder=str(template_folder),
                        static_folder=str(static_folder))
        
        # Khoi tao Authentication Manager
        self.auth_manager = AuthManager(users_file='users.json')
        self.app.config['AUTH_MANAGER'] = self.auth_manager
        
        # Đăng ký routes
        self._register_routes()
        
        logger.info("Đã khởi tạo Dashboard Server")
        logger.info(f"  Host: {self.host}")
        logger.info(f"  Port: {self.port}")
        logger.info(f"  Image folder: {self.image_folder.absolute()}")
    
    def _load_config(self) -> Dict:
        """Load cấu hình từ file JSON"""
        try:
            config_file = Path(__file__).parent.parent / self.config_path
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"✅ Đã load config từ {config_file}")
            return config
        except FileNotFoundError:
            logger.warning("⚠️  Không tìm thấy config.json")
            return {}
        except Exception as e:
            logger.error(f"❌ Lỗi khi load config: {e}")
            return {}
    
    def _get_recent_images(self, limit: int = 10) -> List[Dict]:
        """
        Lấy danh sách ảnh mới nhất
        
        Args:
            limit: Số lượng ảnh tối đa
            
        Returns:
            List các dict chứa thông tin ảnh
        """
        try:
            image_path = Path(__file__).parent.parent / self.image_folder
            if not image_path.exists():
                return []
            
            # Lấy tất cả file .jpg
            images = list(image_path.glob('*.jpg'))
            
            # Sort theo thời gian sửa đổi (mới nhất trước)
            images.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            # Lấy thông tin chi tiết
            result = []
            for img in images[:limit]:
                stat = img.stat()
                result.append({
                    'filename': img.name,
                    'size': stat.st_size,
                    'size_kb': f"{stat.st_size / 1024:.2f}",
                    'timestamp': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                    'mtime': stat.st_mtime
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Lỗi khi lấy danh sách ảnh: {e}")
            return []
    
    def _register_routes(self):
        """Đăng ký các Flask routes"""
        
        @self.app.route('/login')
        def login():
            """Trang dang nhap"""
            return render_template('login.html')
        
        @self.app.route('/register')
        def register():
            """Trang dang ky tai khoan moi"""
            return render_template('register.html')
        
        @self.app.route('/change-password')
        @login_required
        def change_password_page():
            """Trang doi mat khau"""
            return render_template('change_password.html', user=request.user)
        
        @self.app.route('/users')
        @login_required
        def users_management():
            """Trang quan ly nguoi dung"""
            return render_template('users.html')
        
        @self.app.route('/logout')
        def logout():
            """Dang xuat nguoi dung"""
            session_token = request.cookies.get('session_token')
            if session_token:
                self.auth_manager.logout(session_token)
            
            response = make_response(redirect(url_for('login')))
            response.set_cookie('session_token', '', expires=0)
            return response
        
        @self.app.route('/')
        @login_required
        def index():
            """Trang chủ dashboard"""
            recent_images = self._get_recent_images(limit=6)
            user = request.user
            
            return render_template('dashboard.html',
                                 door_states=self.door_states,
                                 recent_images=recent_images,
                                 stats=self.stats,
                                 config=self.config,
                                 user=user)
        
        @self.app.route('/api/auth/login', methods=['POST'])
        def api_login():
            """API dang nhap"""
            try:
                data = request.get_json()
                username = data.get('username')
                password = data.get('password')
                
                if not username or not password:
                    return jsonify({
                        'success': False,
                        'error': 'Thieu username hoac password'
                    }), 400
                
                session_token = self.auth_manager.authenticate(username, password)
                
                if session_token:
                    logger.info(f"User {username} dang nhap thanh cong")
                    return jsonify({
                        'success': True,
                        'session_token': session_token,
                        'message': 'Dang nhap thanh cong'
                    })
                else:
                    logger.warning(f"Dang nhap that bai cho user {username}")
                    return jsonify({
                        'success': False,
                        'error': 'Sai username hoac password'
                    }), 401
                    
            except Exception as e:
                logger.error(f"Loi khi dang nhap: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/auth/register', methods=['POST'])
        def api_register():
            """API dang ky tai khoan moi"""
            try:
                data = request.get_json()
                username = data.get('username', '').strip()
                password = data.get('password', '')
                role = data.get('role', 'user')
                
                if not username or not password:
                    return jsonify({
                        'success': False,
                        'error': 'Thieu username hoac password'
                    }), 400
                
                if len(username) < 3 or len(username) > 20:
                    return jsonify({
                        'success': False,
                        'error': 'Username phai tu 3-20 ky tu'
                    }), 400
                
                if len(password) < 6:
                    return jsonify({
                        'success': False,
                        'error': 'Password phai toi thieu 6 ky tu'
                    }), 400
                
                if role not in ['user', 'admin']:
                    role = 'user'
                
                if self.auth_manager.add_user(username, password, role):
                    logger.info(f"Tao tai khoan moi: {username} ({role})")
                    return jsonify({
                        'success': True,
                        'message': 'Tao tai khoan thanh cong'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Username da ton tai'
                    }), 400
                    
            except Exception as e:
                logger.error(f"Loi khi dang ky: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/auth/change-password', methods=['POST'])
        @login_required
        def api_change_password():
            """API doi mat khau"""
            try:
                data = request.get_json()
                old_password = data.get('old_password', '')
                new_password = data.get('new_password', '')
                
                if not old_password or not new_password:
                    return jsonify({
                        'success': False,
                        'error': 'Thieu thong tin mat khau'
                    }), 400
                
                if len(new_password) < 6:
                    return jsonify({
                        'success': False,
                        'error': 'Mat khau moi phai toi thieu 6 ky tu'
                    }), 400
                
                username = request.user.get('username')
                if self.auth_manager.change_password(username, old_password, new_password):
                    logger.info(f"User {username} da doi mat khau thanh cong")
                    return jsonify({
                        'success': True,
                        'message': 'Doi mat khau thanh cong'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Mat khau cu khong dung'
                    }), 400
                    
            except Exception as e:
                logger.error(f"Loi khi doi mat khau: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/auth/users')
        @login_required
        def api_get_users():
            """API lay danh sach nguoi dung"""
            try:
                users = self.auth_manager.get_all_users()
                return jsonify({
                    'success': True,
                    'users': users,
                    'current_user': {
                        'username': request.user.get('username'),
                        'role': request.user.get('role')
                    }
                })
            except Exception as e:
                logger.error(f"Loi khi lay danh sach users: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/auth/users/<username>', methods=['DELETE'])
        @admin_required
        def api_delete_user(username):
            """API xoa nguoi dung - Chi admin moi co quyen"""
            try:
                if self.auth_manager.delete_user(username):
                    logger.info(f"Admin {request.user['username']} da xoa user: {username}")
                    return jsonify({
                        'success': True,
                        'message': f'Da xoa nguoi dung {username}'
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Khong the xoa user (khong ton tai hoac la admin)'
                    }), 400
            except Exception as e:
                logger.error(f"Loi khi xoa user: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/doors')
        @login_required
        def get_door_states():
            """API lấy trạng thái cửa"""
            return jsonify({
                'success': True,
                'doors': self.door_states,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            })
        
        @self.app.route('/api/doors/update', methods=['POST'])
        def update_door_state():
            """API cập nhật trạng thái cửa (được gọi từ main.py)"""
            try:
                data = request.get_json()
                door = data.get('door')
                status = data.get('status')
                
                if door in self.door_states:
                    self.door_states[door]['status'] = status
                    self.door_states[door]['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    self.stats['total_events'] += 1
                    
                    logger.info(f"📊 Cập nhật trạng thái: {door} = {status}")
                    
                    return jsonify({
                        'success': True,
                        'door': door,
                        'status': status
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid door name'
                    }), 400
                    
            except Exception as e:
                logger.error(f"Lỗi khi cập nhật trạng thái: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/images')
        @login_required
        def get_images():
            """API lấy danh sách ảnh mới nhất"""
            limit = int(request.args.get('limit', 10))
            images = self._get_recent_images(limit=limit)
            
            return jsonify({
                'success': True,
                'images': images,
                'total': len(images)
            })
        
        @self.app.route('/api/images/<filename>')
        @login_required
        def get_image(filename):
            """API lấy ảnh theo tên file"""
            try:
                image_path = Path(__file__).parent.parent / self.image_folder
                return send_from_directory(image_path, filename)
            except Exception as e:
                logger.error(f"Lỗi khi lấy ảnh {filename}: {e}")
                return jsonify({'error': 'Image not found'}), 404
        
        @self.app.route('/api/stats')
        @login_required
        def get_stats():
            """API lấy thống kê hệ thống"""
            uptime = datetime.now() - self.stats['start_time']
            
            image_path = Path(__file__).parent.parent / self.image_folder
            total_images = len(list(image_path.glob('*.jpg'))) if image_path.exists() else 0
            
            # Kiểm tra kết nối ESP32
            self._check_esp32_connection()
            
            return jsonify({
                'success': True,
                'stats': {
                    'total_events': self.stats['total_events'],
                    'total_images': total_images,
                    'uptime_seconds': int(uptime.total_seconds()),
                    'uptime': str(uptime).split('.')[0],
                    'esp32_online': self.esp32_online,
                    'esp32_ip': self.config.get('esp32', {}).get('ip', 'N/A')
                },
                'doors': self.door_states
            })
        
        @self.app.route('/api/camera/settings')
        @login_required
        def get_camera_settings():
            """API lay cai dat camera"""
            return jsonify({
                'success': True,
                'settings': self.camera_settings
            })
        
        @self.app.route('/api/camera/settings', methods=['POST'])
        @login_required
        def update_camera_settings():
            """API cap nhat cai dat camera"""
            try:
                data = request.get_json()
                
                if 'mode' in data:
                    mode = data['mode']
                    if mode in ['auto', 'manual']:
                        self.camera_settings['mode'] = mode
                        self._save_camera_setting('mode', mode)
                        logger.info(f"Camera mode updated: {mode}")
                        return jsonify({
                            'success': True,
                            'settings': self.camera_settings
                        })
                    else:
                        return jsonify({
                            'success': False,
                            'error': 'Invalid mode. Use "auto" or "manual"'
                        }), 400
                
                return jsonify({
                    'success': False,
                    'error': 'Missing mode parameter'
                }), 400
                
            except Exception as e:
                logger.error(f"Loi khi cap nhat camera settings: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/upload', methods=['POST'])
        def upload_image():
            """
            Endpoint nhan anh tu ESP32-CAM
            ESP32 se POST anh voi Content-Type: image/jpeg
            """
            try:
                # Lay du lieu anh tu request body
                image_data = request.get_data()
                
                if not image_data:
                    logger.warning("Khong nhan duoc du lieu anh tu ESP32")
                    return jsonify({
                        'success': False,
                        'error': 'No image data received'
                    }), 400
                
                # Tao thu muc images neu chua co
                self.image_folder.mkdir(parents=True, exist_ok=True)
                
                # Tao ten file voi timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'esp32_door_{timestamp}.jpg'
                filepath = self.image_folder / filename
                
                # Luu anh
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                file_size = len(image_data)
                
                logger.info("="*60)
                logger.info(f"✅ Da nhan anh tu ESP32-CAM!")
                logger.info(f"📁 File: {filename}")
                logger.info(f"📍 Path: {filepath}")
                logger.info(f"📏 Size: {file_size} bytes ({file_size/1024:.2f} KB)")
                logger.info(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info("="*60)
                
                # Cap nhat so luong anh
                self.stats['total_images'] = self.stats.get('total_images', 0) + 1
                
                # Tra ve response cho ESP32
                return jsonify({
                    'success': True,
                    'filename': filename,
                    'size': file_size,
                    'message': 'Image received successfully'
                }), 200
                
            except Exception as e:
                logger.error(f"❌ Loi khi nhan anh: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
        
        @self.app.route('/api/camera/capture', methods=['POST'])
        @login_required
        def manual_capture():
            """API chup anh thu cong"""
            try:
                # Import tai day de tranh circular import
                import requests
                
                esp32_ip = self.config.get('esp32', {}).get('ip', 'ESP32_IP_NOT_SET')
                if esp32_ip == 'ESP32_IP_NOT_SET':
                    return jsonify({
                        'success': False,
                        'error': 'ESP32 IP not configured'
                    }), 500
                
                # Gui yeu cau chup anh toi ESP32
                url = f"http://{esp32_ip}/capture"
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200:
                    logger.info("Manual capture thanh cong")
                    return jsonify({
                        'success': True,
                        'message': 'Chup anh thanh cong'
                    })
                else:
                    logger.error(f"ESP32 tra ve loi: {response.status_code}")
                    return jsonify({
                        'success': False,
                        'error': f'ESP32 error: {response.status_code}'
                    }), 500
                    
            except requests.Timeout:
                logger.error("Timeout khi chup anh")
                return jsonify({
                    'success': False,
                    'error': 'ESP32 timeout'
                }), 500
            except Exception as e:
                logger.error(f"Loi khi chup anh thu cong: {e}")
                return jsonify({
                    'success': False,
                    'error': str(e)
                }), 500
    
    def _save_camera_setting(self, key: str, value):
        """Luu cai dat camera vao config.json"""
        try:
            config_file = Path(__file__).parent.parent / self.config_path
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            if 'camera' not in config:
                config['camera'] = {}
            
            config['camera'][key] = value
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Da luu camera.{key} = {value} vao config")
        except Exception as e:
            logger.error(f"Loi khi luu camera setting: {e}")
    
    def _check_esp32_connection(self):
        """Kiem tra ket noi ESP32-CAM"""
        try:
            import requests
            from datetime import datetime, timedelta
            
            # Chi kiem tra neu da qua 5 giay tu lan check truoc
            now = datetime.now()
            if self.last_esp32_check:
                time_diff = (now - self.last_esp32_check).total_seconds()
                if time_diff < 5:
                    return
            
            self.last_esp32_check = now
            
            esp32_ip = self.config.get('esp32', {}).get('ip', '')
            if not esp32_ip:
                self.esp32_online = False
                return
            
            # Ping ESP32 voi timeout ngan
            url = f"http://{esp32_ip}/status"
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                self.esp32_online = True
            else:
                self.esp32_online = False
                
        except Exception:
            self.esp32_online = False
    
    def run(self, debug: bool = False):
        """
        Chạy Flask server
        
        Args:
            debug: Chế độ debug
        """
        logger.info("=" * 60)
        logger.info("🌐 Starting Web Dashboard Server")
        logger.info("=" * 60)
        logger.info(f"📍 Dashboard URL: http://{self.host}:{self.port}")
        logger.info(f"📁 Image folder: {self.image_folder.absolute()}")
        logger.info("=" * 60)
        logger.info("Endpoints:")
        logger.info(f"  - GET  /                    : Dashboard UI")
        logger.info(f"  - GET  /api/doors           : Trạng thái cửa")
        logger.info(f"  - POST /api/doors/update    : Cập nhật trạng thái")
        logger.info(f"  - GET  /api/images          : Danh sách ảnh")
        logger.info(f"  - GET  /api/images/<file>   : Lấy ảnh")
        logger.info(f"  - GET  /api/stats           : Thống kê")
        logger.info("=" * 60)
        logger.info("Nhấn Ctrl+C để dừng server\n")
        
        try:
            self.app.run(
                host=self.host,
                port=self.port,
                debug=debug,
                threaded=True
            )
        except KeyboardInterrupt:
            logger.info("\n🛑 Dừng dashboard server...")
        except Exception as e:
            logger.error(f"❌ Lỗi khi chạy server: {e}")
            raise


def main():
    """Main entry point"""
    print("=" * 60)
    print("🌐 Smart Home Web Dashboard")
    print("   Raspberry Pi 5 - ESP32-CAM")
    print("=" * 60)
    print()
    
    # Tạo thư mục logs nếu chưa có
    Path('logs').mkdir(parents=True, exist_ok=True)
    
    # Tạo và chạy server
    server = DashboardServer(
        host='0.0.0.0',
        port=8080,
        image_folder='images'
    )
    
    server.run(debug=False)


if __name__ == '__main__':
    main()

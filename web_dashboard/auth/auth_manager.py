"""
Authentication Manager - Quan ly xac thuc nguoi dung
"""

import json
import hashlib
import secrets
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime, timedelta


class AuthManager:
    """
    Quan ly xac thuc nguoi dung
    """
    
    def __init__(self, users_file: str = 'users.json'):
        """
        Khoi tao Auth Manager
        
        Args:
            users_file: Duong dan file luu thong tin nguoi dung
        """
        self.users_file = Path(__file__).parent.parent.parent / users_file
        self.users = self._load_users()
        self.sessions = {}  # session_token -> user_info
        self.session_timeout = timedelta(hours=24)
        
    def _load_users(self) -> Dict:
        """Load danh sach nguoi dung tu file"""
        try:
            if self.users_file.exists():
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Tao tai khoan mac dinh
                default_users = {
                    'admin': {
                        'password_hash': self._hash_password('admin123'),
                        'role': 'admin',
                        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                }
                self._save_users(default_users)
                return default_users
        except Exception as e:
            print(f"Loi khi load users: {e}")
            return {}
    
    def _save_users(self, users: Dict):
        """Luu danh sach nguoi dung vao file"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(users, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Loi khi save users: {e}")
    
    def _hash_password(self, password: str) -> str:
        """
        Hash mat khau bang SHA-256
        
        Args:
            password: Mat khau goc
            
        Returns:
            Mat khau da hash
        """
        return hashlib.sha256(password.encode()).hexdigest()
    
    def authenticate(self, username: str, password: str) -> Optional[str]:
        """
        Xac thuc nguoi dung
        
        Args:
            username: Ten dang nhap
            password: Mat khau
            
        Returns:
            Session token neu thanh cong, None neu that bai
        """
        if username not in self.users:
            return None
        
        user_data = self.users[username]
        password_hash = self._hash_password(password)
        
        if password_hash == user_data['password_hash']:
            # Tao session token
            session_token = secrets.token_hex(32)
            
            self.sessions[session_token] = {
                'username': username,
                'role': user_data.get('role', 'user'),
                'login_time': datetime.now(),
                'last_activity': datetime.now()
            }
            
            return session_token
        
        return None
    
    def validate_session(self, session_token: str) -> Optional[Dict]:
        """
        Kiem tra session co hop le khong
        
        Args:
            session_token: Token session
            
        Returns:
            Thong tin user neu session hop le, None neu khong
        """
        if session_token not in self.sessions:
            return None
        
        session = self.sessions[session_token]
        last_activity = session['last_activity']
        
        # Kiem tra timeout
        if datetime.now() - last_activity > self.session_timeout:
            del self.sessions[session_token]
            return None
        
        # Cap nhat last_activity
        session['last_activity'] = datetime.now()
        return session
    
    def logout(self, session_token: str):
        """
        Dang xuat nguoi dung
        
        Args:
            session_token: Token session can xoa
        """
        if session_token in self.sessions:
            del self.sessions[session_token]
    
    def add_user(self, username: str, password: str, role: str = 'user') -> bool:
        """
        Them nguoi dung moi
        
        Args:
            username: Ten dang nhap
            password: Mat khau
            role: Vai tro (admin/user)
            
        Returns:
            True neu thanh cong, False neu that bai
        """
        if username in self.users:
            return False
        
        self.users[username] = {
            'password_hash': self._hash_password(password),
            'role': role,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        self._save_users(self.users)
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """
        Doi mat khau
        
        Args:
            username: Ten dang nhap
            old_password: Mat khau cu
            new_password: Mat khau moi
            
        Returns:
            True neu thanh cong, False neu that bai
        """
        if username not in self.users:
            return False
        
        old_hash = self._hash_password(old_password)
        if old_hash != self.users[username]['password_hash']:
            return False
        
        self.users[username]['password_hash'] = self._hash_password(new_password)
        self.users[username]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self._save_users(self.users)
        return True
    
    def delete_user(self, username: str) -> bool:
        """
        Xoa nguoi dung
        
        Args:
            username: Ten dang nhap can xoa
            
        Returns:
            True neu thanh cong, False neu that bai
        """
        if username not in self.users or username == 'admin':
            return False
        
        del self.users[username]
        self._save_users(self.users)
        return True
    
    def get_all_users(self) -> Dict:
        """
        Lay danh sach tat ca nguoi dung (khong bao gom password hash)
        
        Returns:
            Dictionary chua thong tin nguoi dung
        """
        result = {}
        for username, data in self.users.items():
            result[username] = {
                'role': data.get('role', 'user'),
                'created_at': data.get('created_at', 'N/A'),
                'updated_at': data.get('updated_at', 'N/A')
            }
        return result

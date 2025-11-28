# Web Dashboard Authentication Module

Module xac thuc dang nhap cho web dashboard Smart Home System.

## Chuc nang

- Xac thuc nguoi dung bang username/password
- Quan ly session token
- Bao ve cac route voi decorator @login_required
- Luu tru thong tin nguoi dung trong file users.json

## Tai khoan mac dinh

- Username: `admin`
- Password: `admin123`
- Role: `admin`

## Su dung

### 1. Dang nhap

Truy cap: `http://localhost:8080/login`

### 2. Dang xuat

Click nut "Dang xuat" tren dashboard hoac truy cap: `http://localhost:8080/logout`

### 3. Them nguoi dung moi

```python
from web_dashboard.auth import AuthManager

auth = AuthManager()
auth.add_user('user1', 'password123', role='user')
```

### 4. Doi mat khau

```python
auth.change_password('admin', 'admin123', 'new_password')
```

### 5. Xoa nguoi dung

```python
auth.delete_user('user1')
```

## API Endpoints

### POST /api/auth/login
Dang nhap va nhan session token

Request:
```json
{
  "username": "admin",
  "password": "admin123"
}
```

Response:
```json
{
  "success": true,
  "session_token": "abc123...",
  "message": "Dang nhap thanh cong"
}
```

### GET /logout
Dang xuat va xoa session

## Bao mat

- Mat khau duoc hash bang SHA-256
- Session token duoc tao ngau nhien (32 bytes hex)
- Session het han sau 24 gio
- Tat ca cac route dashboard yeu cau xac thuc
- Cookie httpOnly de bao ve session token

## File cau truc

```
web_dashboard/
├── auth/
│   ├── __init__.py
│   ├── auth_manager.py      # Quan ly xac thuc
│   └── decorators.py         # Decorator @login_required
├── templates/
│   ├── login.html           # Trang dang nhap
│   └── dashboard.html       # Dashboard (can xac thuc)
└── dashboard_server.py      # Flask server
```

## Users file format

File `users.json` luu thong tin nguoi dung:

```json
{
  "admin": {
    "password_hash": "sha256_hash_here",
    "role": "admin",
    "created_at": "2025-11-27 10:00:00"
  },
  "user1": {
    "password_hash": "sha256_hash_here",
    "role": "user",
    "created_at": "2025-11-27 11:00:00"
  }
}
```

## Luu y

- Khong nen su dung tai khoan mac dinh trong moi truong production
- Doi mat khau admin ngay sau khi khoi tao
- Backup file users.json dinh ky
- Session timeout co the thay doi trong AuthManager.__init__()

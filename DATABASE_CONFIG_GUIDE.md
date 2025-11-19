# 🗄️ Hướng dẫn cấu hình Database từ .env

## ✅ Đã cấu hình xong!

Database URL hiện tại được đọc **TỰ ĐỘNG** từ file `.env` thay vì hardcode trong code.

## 🔧 Cách sử dụng

### Bước 1: Tạo file `.env`

```bash
cd cinema-booking-backend
cp .env.example .env
```

### Bước 2: Chỉnh sửa `.env`

Mở file `.env` và cấu hình DATABASE_URL phù hợp:

#### Option 1: PostgreSQL Local (Khuyên dùng cho dev)

```env
DATABASE_URL="postgresql+psycopg2://postgres:your_password@localhost:5432/cinema-booking"
```

#### Option 2: PostgreSQL Cloud (Neon)

```env
DATABASE_URL="postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require"
```

#### Option 3: Supabase

```env
DATABASE_URL="postgresql://postgres:pass@db.xxx.supabase.co:5432/postgres"
```

### Bước 3: Cấu hình các biến khác

```env
# JWT
SECRET_KEY="your-super-secret-key-change-in-production"
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
EMAIL_USERNAME=your-email@gmail.com
EMAIL_PASSWORD=your-app-password

# VNPay (giữ nguyên nếu dùng sandbox)
VNPAY_TMN_CODE="DL3ZO58E"
VNPAY_HASH_SECRET_KEY="54YH7V02ELC4KUAOF90RUI7R50S4JZ75"
```

## 🚀 Chạy Migration

Sau khi cấu hình `.env`, chạy các lệnh sau:

### 1. Tạo migration mới (nếu có thay đổi models)

```bash
alembic revision --autogenerate -m "your message"
```

### 2. Chạy migration

```bash
alembic upgrade head
```

### 3. Rollback (nếu cần)

```bash
alembic downgrade -1
```

## 📋 Kiểm tra cấu hình

### Test kết nối database

```python
# test_db_connection.py
from app.core.config import settings
from sqlalchemy import create_engine

try:
    engine = create_engine(settings.DATABASE_URL)
    connection = engine.connect()
    print("✅ Kết nối database thành công!")
    print(f"📍 Database URL: {settings.DATABASE_URL}")
    connection.close()
except Exception as e:
    print(f"❌ Lỗi kết nối: {e}")
```

Chạy test:
```bash
python test_db_connection.py
```

## 🔍 Cách hoạt động

### 1. File `app/core/config.py`

```python
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+psycopg2://..."  # Default value
    
    class Config:
        env_file = ".env"  # ← Đọc từ file .env

settings = Settings()
```

### 2. File `alembic/env.py` (ĐÃ CẬP NHẬT)

```python
from app.core.config import settings

# Override sqlalchemy.url từ .env
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

### 3. File `alembic.ini` (Không dùng nữa)

```ini
# NOTE: Giá trị này không còn được dùng
# Database URL được đọc từ .env qua env.py
sqlalchemy.url = driver://user:pass@localhost/dbname
```

## 🎯 Ưu điểm

✅ **Bảo mật**: Không commit database credentials lên Git  
✅ **Linh hoạt**: Dễ dàng chuyển đổi giữa dev/staging/prod  
✅ **Tập trung**: Tất cả config ở một chỗ (file `.env`)  
✅ **Đồng bộ**: FastAPI và Alembic dùng chung một DATABASE_URL  

## ⚠️ Lưu ý quan trọng

1. **KHÔNG commit file `.env`** lên Git
   ```bash
   # Đảm bảo .env có trong .gitignore
   echo ".env" >> .gitignore
   ```

2. **Thay đổi SECRET_KEY** trong production
   ```python
   # Generate random key
   import secrets
   print(secrets.token_urlsafe(32))
   ```

3. **Backup database** trước khi chạy migration
   ```bash
   pg_dump -U postgres cinema-booking > backup.sql
   ```

## 🐛 Troubleshooting

### Lỗi: "No such file or directory: '.env'"

**Giải pháp**: Tạo file `.env` từ `.env.example`
```bash
cp .env.example .env
```

### Lỗi: "database does not exist"

**Giải pháp**: Tạo database trước
```sql
CREATE DATABASE "cinema-booking";
```

### Lỗi: "password authentication failed"

**Giải pháp**: Kiểm tra lại username/password trong `.env`

### Lỗi: Alembic không thấy thay đổi models

**Giải pháp**: Đảm bảo import models trong `alembic/env.py`
```python
from app.models import *  # ← Phải có dòng này
```

## 📚 Tài liệu liên quan

- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html)
- [SQLAlchemy Engine](https://docs.sqlalchemy.org/en/20/core/engines.html)

## 🔐 Best Practices

### Development
```env
DATABASE_URL="postgresql+psycopg2://postgres:password@localhost:5432/cinema-booking-dev"
ACCESS_TOKEN_EXPIRE_MINUTES=60  # Lâu hơn để dev
```

### Staging
```env
DATABASE_URL="postgresql://user:pass@staging-db.com:5432/cinema-staging"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Production
```env
DATABASE_URL="postgresql://user:pass@prod-db.com:5432/cinema-prod?sslmode=require"
ACCESS_TOKEN_EXPIRE_MINUTES=15  # Ngắn hơn để bảo mật
SECRET_KEY="<random-generated-key>"  # ← Phải đổi!
```

---

**Cần trợ giúp?** Tạo issue hoặc liên hệ team dev! 🚀

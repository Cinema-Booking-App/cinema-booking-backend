# Hướng dẫn cài đặt môi trường

Các bước thực hiện:

**Tạo migration nếu cần thay đổi database:**
```bash
alembic revision --autogenerate -m "Tên migration"
```

**Nâng cấp database:**
```bash
alembic upgrade head
```

**Tạo môi trường ảo:**
```bash
python -m venv venv
```

**Kích hoạt môi trường ảo (Windows):**
```bash
venv\Scripts\activate
```

**Cài đặt các thư viện cần thiết:**
```bash
pip install -r requirements.txt
```

**Chạy chương trình:**
```bash
uvicorn app.main:app --reload
```

# 🗂️ Cấu trúc thư mục & file dự án (dạng cây)

```text
cinema-booking/
├── alembic/                    # Quản lý migration cơ sở dữ liệu
│   ├── env.py                  # Thiết lập môi trường cho Alembic
│   ├── script.py.mako          # Template cho các script migration
│   └── versions/               # Các script migration
├── app/                        # Thư mục chính của ứng dụng
│   ├── __init__.py
│   ├── main.py                 # Điểm vào của ứng dụng FastAPI
│   ├── api/                    # Các route và endpoint API
│   │   ├── __init__.py
│   │   ├── v1/                 # API phân theo phiên bản
│   │   │   ├── __init__.py
│   │   │   ├── movies.py       # Endpoint liên quan đến phim
│   │   │   ├── bookings.py     # Endpoint liên quan đến đặt vé
│   │   │   ├── theaters.py     # Endpoint liên quan đến rạp
│   │   │   ├── showtimes.py    # Endpoint liên quan đến lịch chiếu
│   │   │   └── users.py        # Endpoint liên quan đến người dùng
│   ├── core/                   # Cấu hình và tiện ích cốt lõi
│   │   ├── __init__.py
│   │   ├── config.py           # Cấu hình (biến môi trường)
│   │   ├── database.py         # Thiết lập kết nối cơ sở dữ liệu
│   │   ├── security.py         # Logic xác thực và phân quyền
│   │   └── middleware.py       # Middleware tùy chỉnh
│   ├── models/                 # Mô hình cơ sở dữ liệu (SQLAlchemy)
│   │   ├── __init__.py
│   │   ├── movie.py
│   │   ├── booking.py
│   │   ├── theater.py
│   │   ├── showtime.py
│   │   └── user.py
│   ├── schemas/                # Schema Pydantic cho xác thực request/response
│   │   ├── __init__.py
│   │   ├── movie.py
│   │   ├── booking.py
│   │   ├── theater.py
│   │   ├── showtime.py
│   │   └── user.py
│   ├── services/               # Logic nghiệp vụ
│   │   ├── __init__.py
│   │   ├── movie_service.py
│   │   ├── booking_service.py
│   │   ├── theater_service.py
│   │   ├── showtime_service.py
│   │   └── user_service.py
│   ├── utils/                  # Hàm tiện ích (logging, helpers)
│   │   ├── __init__.py
│   │   ├── logger.py
│   │   └── helpers.py
│   └── tests/                  # Unit test và integration test
│       ├── __init__.py
│       ├── test_movies.py
│       ├── test_bookings.py
│       ├── test_theaters.py
│       ├── test_showtimes.py
│       └── test_users.py
├── .env                        # Biến môi trường
├── .gitignore                  # File cấu hình Git
├── README.md                   # Tài liệu dự án
├── requirements.txt            # Danh sách thư viện phụ thuộc
├── docker-compose.yml          # Cấu hình Docker (tùy chọn)
└── Dockerfile                  # Cấu hình Docker cho ứng dụng (tùy chọn)
```

---

## 📁 Thư mục gốc
| Loại | Tên | Giải thích |
|------|-----|------------|
| 🗂️ | `alembic/` | Quản lý migration cơ sở dữ liệu |
| 🗂️ | `app/` | Thư mục chính của ứng dụng FastAPI |
| 📄 | `.env` | Biến môi trường (không commit lên git) |
| 📄 | `.gitignore` | Các file/thư mục bị loại trừ khỏi git |
| 📄 | `README.md` | Tài liệu hướng dẫn tổng quan dự án |
| 📄 | `requirements.txt` | Danh sách các thư viện Python cần cài đặt |
| 📄 | `docker-compose.yml` | Cấu hình Docker Compose để chạy nhiều service |
| 📄 | `Dockerfile` | Cấu hình Docker cho ứng dụng chính |

---

## 📁 alembic/
| Loại | Tên | Giải thích |
|------|-----|------------|
| 📄 | `env.py` | Thiết lập môi trường cho Alembic, dùng để migration database |
| 📄 | `script.py.mako` | Template cho các script migration |
| 🗂️ | `versions/` | Chứa các script migration được tạo ra khi thay đổi database |

---

## 📁 app/
| Loại | Tên | Giải thích |
|------|-----|------------|
| 📄 | `main.py` | Điểm vào của ứng dụng FastAPI |
| 🗂️ | `api/` | Chứa các route và endpoint API |
| 🗂️ | `core/` | Cấu hình và các tiện ích cốt lõi |
| 🗂️ | `models/` | Định nghĩa các mô hình cơ sở dữ liệu (SQLAlchemy) |
| 🗂️ | `schemas/` | Định nghĩa các schema Pydantic cho request/response |
| 🗂️ | `services/` | Chứa logic nghiệp vụ cho từng thực thể |
| 🗂️ | `utils/` | Các hàm tiện ích chung |
| 🗂️ | `tests/` | Chứa các file test cho từng module |

---

## 📄 Giải thích chi tiết từng file

### Thư mục gốc
- **.env**: Lưu các biến môi trường như thông tin kết nối database, secret key, ...
- **.gitignore**: Khai báo các file/thư mục không được đưa vào git (ví dụ: .env, __pycache__, ...).
- **README.md**: Tài liệu mô tả tổng quan dự án, hướng dẫn cài đặt và sử dụng.
- **requirements.txt**: Danh sách các thư viện Python cần thiết cho dự án.
- **docker-compose.yml**: Định nghĩa các service (app, db, ...) để chạy bằng Docker Compose.
- **Dockerfile**: Hướng dẫn Docker build image cho ứng dụng FastAPI.

### alembic/
- **env.py**: File cấu hình môi trường cho Alembic, xác định cách kết nối DB và chạy migration.
- **script.py.mako**: Template để Alembic sinh ra các file migration.
- **versions/**: Chứa các file migration (tự động sinh ra khi chạy lệnh alembic revision).

### app/
- **main.py**: Điểm khởi động ứng dụng FastAPI, khai báo app, include router, middleware, ...

#### app/api/
- **__init__.py**: Đánh dấu thư mục là package Python.
- **v1/**: Chứa các endpoint API phiên bản 1.
  - **__init__.py**: Đánh dấu là package.
  - **movies.py**: Định nghĩa các route liên quan đến phim (GET, POST, ...).
  - **bookings.py**: Định nghĩa các route liên quan đến đặt vé.
  - **theaters.py**: Định nghĩa các route liên quan đến rạp.
  - **showtimes.py**: Định nghĩa các route liên quan đến lịch chiếu.
  - **users.py**: Định nghĩa các route liên quan đến người dùng.

#### app/core/
- **__init__.py**: Đánh dấu là package.
- **config.py**: Đọc và quản lý các biến cấu hình (từ .env hoặc mặc định).
- **database.py**: Thiết lập kết nối SQLAlchemy, SessionLocal, Base.
- **security.py**: Xử lý xác thực, phân quyền, JWT, hash password, ...
- **middleware.py**: Định nghĩa các middleware tùy chỉnh (logging, CORS, ...).

#### app/models/
- **__init__.py**: Đánh dấu là package.
- **movie.py**: Định nghĩa model Movie (bảng phim).
- **booking.py**: Định nghĩa model Booking (bảng đặt vé).
- **theater.py**: Định nghĩa model Theater (bảng rạp).
- **showtime.py**: Định nghĩa model Showtime (bảng lịch chiếu).
- **user.py**: Định nghĩa model User (bảng người dùng).

#### app/schemas/
- **__init__.py**: Đánh dấu là package.
- **movie.py**: Định nghĩa schema Movie (Pydantic model cho request/response phim).
- **booking.py**: Định nghĩa schema Booking.
- **theater.py**: Định nghĩa schema Theater.
- **showtime.py**: Định nghĩa schema Showtime.
- **user.py**: Định nghĩa schema User.

#### app/services/
- **__init__.py**: Đánh dấu là package.
- **movie_service.py**: Xử lý logic nghiệp vụ liên quan đến phim.
- **booking_service.py**: Xử lý logic nghiệp vụ liên quan đến đặt vé.
- **theater_service.py**: Xử lý logic nghiệp vụ liên quan đến rạp.
- **showtime_service.py**: Xử lý logic nghiệp vụ liên quan đến lịch chiếu.
- **user_service.py**: Xử lý logic nghiệp vụ liên quan đến người dùng.

#### app/utils/
- **__init__.py**: Đánh dấu là package.
- **logger.py**: Cấu hình logging cho toàn bộ ứng dụng.
- **helpers.py**: Các hàm tiện ích dùng chung.

#### app/tests/
- **__init__.py**: Đánh dấu là package.
- **test_movies.py**: Unit test cho chức năng phim.
- **test_bookings.py**: Unit test cho chức năng đặt vé.
- **test_theaters.py**: Unit test cho chức năng rạp.
- **test_showtimes.py**: Unit test cho chức năng lịch chiếu.
- **test_users.py**: Unit test cho chức năng người dùng.

---

> **Lưu ý:**
> - Các file `__init__.py` giúp Python nhận diện thư mục là package/module.
> - Có thể mở rộng thêm các version API khác trong `app/api/` nếu cần. 
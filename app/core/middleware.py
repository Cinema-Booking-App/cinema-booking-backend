from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

def setup_middleware(app: FastAPI):
    # CORS chỉ định rõ domain frontend và local development
    allow_origins = [
        "https://ryon.website",
        "https://www.ryon.website",
        "http://localhost:3000",
        "http://127.0.0.1:3000",  # Next.js với 127.0.0.1
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:5500",    # Live Server default port
        "http://127.0.0.1:5500",    # Live Server với 127.0.0.1
        "http://localhost:8080",    # Vue.js default port
        "http://127.0.0.1:8080",
        "http://localhost:4200",    # Angular default port
        "http://127.0.0.1:4200",
        "http://localhost:5173",    # Vite default port
        "http://127.0.0.1:5173",
        "file://",                  # Cho phép mở file trực tiếp
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,  # không dùng "*" để bảo mật
        allow_credentials=True,       # cho phép cookie/auth
        allow_methods=["*"],          # GET, POST, PUT, DELETE
        allow_headers=["*"],          # tất cả headers
    )

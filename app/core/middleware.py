from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

def setup_middleware(app: FastAPI):
    # CORS chỉ định rõ domain frontend
    allow_origins = [
        "https://ryon.website",
        "https://www.ryon.website"
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,  # không dùng "*"
        allow_credentials=True,       # cho phép cookie/auth
        allow_methods=["*"],          # GET, POST, PUT, DELETE
        allow_headers=["*"],          # tất cả headers
    )

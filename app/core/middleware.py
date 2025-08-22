from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from app.core.config import settings

def setup_middleware(app: FastAPI):
    # Parse comma-separated origins from settings; fallback to '*' if empty and credentials False
    raw_origins = [o.strip() for o in (settings.CORS_ALLOW_ORIGINS or "").split(",") if o.strip()]
    allow_credentials = True if raw_origins else False
    allow_origins = raw_origins if raw_origins else ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )
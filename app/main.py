from fastapi import FastAPI
from app.api.v1 import auth, movies, users
# from app.core.database import Base, engine


app = FastAPI(title="Cinema Booking API", version="1.0.0")
# Tạo bảng cơ sở dữ liệu
# Base.metadata.create_all(bind=engine)

app.include_router(movies.router, prefix="/api/v1", tags=["Movies"])
app.include_router(users.router,  prefix="/api/v1",tags=["Users"])
app.include_router(auth.router,  prefix="/api/v1",tags=["Auth"])

@app.get("/")
async def root():
    return {"message": "Chào mừng đến với Cinema Booking API"}
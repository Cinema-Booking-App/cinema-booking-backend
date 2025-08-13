from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
import uvicorn
from app.core.middleware import setup_middleware
from app.utils.response import error_response
from app.api.v1 import auth, movies, reservations, rooms, seat_layouts, showtimes, theaters, tickets, users, promotions, combos, ranks

# from app.core.database import Base, engine

app = FastAPI(title="Cinema Booking API", version="1.0.0")
setup_middleware(app)
# Tạo bảng cơ sở dữ liệu
# Base.metadata.create_all(bind=engine)

app.include_router(movies.router, prefix="/api/v1", tags=["Movies"])
app.include_router(users.router,  prefix="/api/v1",tags=["Users"])
app.include_router(auth.router,  prefix="/api/v1",tags=["Auth"])
app.include_router(theaters.router,  prefix="/api/v1",tags=["Theaters"])
app.include_router(seat_layouts.router,  prefix="/api/v1",tags=["Seat Layouts"])
app.include_router(rooms.router,  prefix="/api/v1",tags=["Rooms"])
app.include_router(promotions.router, prefix="/api/v1", tags=["Promotions"])
app.include_router(showtimes.router,  prefix="/api/v1",tags=["Showtimes"])
app.include_router(reservations.router,  prefix="/api/v1",tags=["Reservations"])
app.include_router(tickets.router,  prefix="/api/v1",tags=["Tickets"])
app.include_router(combos.router, prefix="/api/v1", tags=["Combos"])
app.include_router(ranks.router, prefix="/api/v1", tags=["Ranks"])

@app.get("/")
async def root():
    return RedirectResponse(url="/docs")

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            exc.detail if isinstance(exc.detail, str) else str(exc.detail),
            code=exc.status_code
        ),
    )
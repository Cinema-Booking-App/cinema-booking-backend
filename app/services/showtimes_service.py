<<<<<<< HEAD
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.showtimes import Showtimes
from app.schemas.showtimes import ShowtimesCreate, ShowtimesUpdate, ShowtimesResponse

def get_all_showtimes(db: Session):
    try:
        showtimes = db.query(Showtimes).all()
        return [ShowtimesResponse.from_orm(s) for s in showtimes]
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")

def get_showtime_by_id(db: Session, showtime_id: int):
    showtime = db.query(Showtimes).filter(Showtimes.showtime_id == showtime_id).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    return ShowtimesResponse.from_orm(showtime)

def create_showtime(db: Session, showtime_in: ShowtimesCreate):
    showtime = Showtimes(**showtime_in.dict())
    db.add(showtime)
    db.commit()
    db.refresh(showtime)
    return ShowtimesResponse.from_orm(showtime)

def update_showtime(db: Session, showtime_id: int, showtime_in: ShowtimesUpdate):
    showtime = db.query(Showtimes).filter(Showtimes.showtime_id == showtime_id).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    for field, value in showtime_in.dict(exclude_unset=True).items():
        setattr(showtime, field, value)
    db.commit()
    db.refresh(showtime)
    return ShowtimesResponse.from_orm(showtime)

def delete_showtime(db: Session, showtime_id: int):
    showtime = db.query(Showtimes).filter(Showtimes.showtime_id == showtime_id).first()
    if not showtime:
        raise HTTPException(status_code=404, detail="Showtime not found")
    db.delete(showtime)
    db.commit()
    return {"msg": "Showtime deleted successfully"} 
=======
from sqlalchemy.orm import Session
from app.models.theaters import Theaters
from app.models.showtimes import Showtimes
from fastapi import HTTPException
from  app.models.rooms import Rooms
from app.schemas.showtimes import ShowtimesCreate

# Danh sách xuất chiếu trong rạp
def get_showtimes_by_theater(db: Session,theater_id: int):
    theater = db.query(Theaters).filter(Theaters.theater_id == theater_id).first()
    if not theater:
        raise HTTPException(status_code=404, detail="Theater not found")
    # Lấy danh sách id phòng của rạp đó
    rooms = db.query(Rooms).filter(Rooms.theater_id == theater_id).all()
    # Lấy danh sách xuất chiếu theo id phòng
    showtimes = db.query(Showtimes).filter(Showtimes.room_id.in_([
        room.room_id for room in rooms
    ])).all()
    return showtimes

def create_showtime(db: Session, showtime_in : ShowtimesCreate):
    showtime = Showtimes(
        movie_id=showtime_in.movie_id,
        room_id=showtime_in.room_id,
        show_datetime=showtime_in.show_datetime,
        format=showtime_in.format,
        ticket_price=showtime_in.ticket_price,
        status=showtime_in.status,
        available_seats=showtime_in.available_seats,
        language=showtime_in.language
    )
    db.add(showtime)
    db.commit()
    db.refresh(showtime)
    return showtime
>>>>>>> e06283a8d15f65a28d59c517e70b5ceb178f84f9

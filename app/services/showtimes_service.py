from sqlalchemy.orm import Session
from app.models.theaters import Theaters
from app.models.showtimes import Showtimes
from fastapi import HTTPException
from  app.models.rooms import Rooms
from app.schemas.showtimes import ShowtimesCreate, ShowtimesResponse

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
    return [ShowtimesResponse.from_orm(showtime) for showtime in showtimes]

def create_showtime(db: Session, showtime_in : ShowtimesCreate):
    try:
        showtime = Showtimes(**showtime_in.dict( exclude_unset=True))
        # Kiểm tra xem rạp có tồn tại không
        theater = db.query(Theaters).filter(Theaters.theater_id == showtime_in.theater_id).first()
        if not theater:
            raise HTTPException(status_code=404, detail="Theater not found")
        # Kiểm tra xem phòng có tồn tại không
        room = db.query(Rooms).filter(Rooms.room_id == showtime_in.room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        # Kiểm tra xem xuất chiếu đã tồn tại chưa
        existing_showtime = db.query(Showtimes).filter(
            Showtimes.room_id == showtime_in.room_id,
            Showtimes.start_time == showtime_in.start_time
        ).first()
        if existing_showtime:
            raise HTTPException(status_code=400, detail="Showtime already exists for this room at the specified time")
        db.add(showtime)
        db.commit()
        db.refresh(showtime)
        return ShowtimesResponse.from_orm(showtime)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
# Xóa xuất chiếu theo id
def delete_showtime(db: Session, showtime_id: int):
    try:
        showtime = db.query(Showtimes).filter(Showtimes.showtime_id == showtime_id).first()
        if not showtime:
            raise HTTPException(status_code=404, detail="Showtime not found")
        db.delete(showtime)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
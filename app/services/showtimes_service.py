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
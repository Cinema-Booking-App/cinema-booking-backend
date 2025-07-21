
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.seat_type import SeatType
from app.schemas.seat_type import SeatTypeResponse

# Lấy tất cả các loại ghế
def get_all_seat_types(db: Session):
    seat_types = db.query(SeatType).all()
    return [SeatTypeResponse.from_orm(seat_type) for seat_type in seat_types]

# Lấy thông tin loại ghế theo ID
def get_seat_type_by_id(db: Session, seat_type_id: int):
    seat_type = db.query(SeatType).filter(SeatType.seat_type_id == seat_type_id).first()
    if not seat_type:
        raise HTTPException(status_code=404, detail="Seat type not found")
    return SeatTypeResponse.from_orm(seat_type)

# Tạo loại ghế
def create_seat_type(db: Session, seat_type_in: SeatTypeResponse):
    try:
        db_seat_type = SeatType(**seat_type_in.dict())
        db.add(db_seat_type)
        db.commit()
        db.refresh(db_seat_type)
        return db_seat_type
    except Exception as e:
            db.rollback()
            raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")

# Xóa loại ghế
def delete_seat_type(db: Session, seat_type_id: int):
    try:
        seat_type = db.query(SeatType).filter(SeatType.seat_type_id == seat_type_id).first()
        if not seat_type:
            raise HTTPException(status_code=404, detail="Seat type not found")
        db.delete(seat_type)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")

# Cập nhật thông tin loại ghế
def update_seat_type(db: Session, seat_type_id: int, seat_type_in: SeatTypeResponse):
    try:
        seat_type = db.query(SeatType).filter(SeatType.seat_type_id == seat_type_id).first()
        if not seat_type:
            raise HTTPException(status_code=404, detail="Seat type not found")
        updated_seat_type = seat_type_in.dict(exclude_unset=True)
        for key, value in updated_seat_type.items():
            setattr(seat_type, key, value)
        db.commit()
        db.refresh(seat_type)
        return seat_type
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")
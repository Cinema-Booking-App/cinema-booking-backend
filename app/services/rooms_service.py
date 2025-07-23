from fastapi import HTTPException
from app.schemas.rooms import RoomCreate, RoomResponse
from sqlalchemy.orm import Session
from app.models.rooms import Rooms
from app.models.theaters import Theaters
# Lấy thông tin phòng theo ID
def get_room_by_id(db: Session, room_id: int):
    room = db.query(Rooms).filter(Rooms.room_id == room_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    return RoomResponse.from_orm(room)

# Lấy tất cả các phòng trong rạp
def get_all_rooms(db: Session):
    try:
        rooms = db.query(Rooms).all()
        if not rooms:
            return []
        return [RoomResponse.from_orm(room) for room in rooms]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
    
# Lấy danh sách phòng theo ID của rạp
def get_rooms_by_theater_id(db: Session, theater_id: int):
    try:
        theater = db.query(Theaters).filter(Theaters.theater_id == theater_id).first()
        if not theater:
            raise HTTPException(status_code=404, detail="Theater not found")
        
        rooms = db.query(Rooms).filter(Rooms.theater_id == theater_id).all()
        if not rooms:
            return []
        return [RoomResponse.from_orm(room) for room in rooms]
    except Exception as e :
        raise HTTPException(status_code=500, detail=f"{str(e)}")

# Thêm phòng cho rạp
def create_room_to_theater(db: Session, theater_id: int, room_in: RoomCreate):
    try:
        #Kiểm tra rạp có tồn tại không
        theater = db.query(Theaters).filter(Theaters.theater_id == theater_id).first()
        if not theater:
            raise HTTPException(status_code=404, detail="Theater not found")
        room = Rooms(
            theater_id = theater_id,
            room_name = room_in.room_name,
            layout_id = room_in.layout_id,
        )
        db.add(room)
        db.commit()
        db.refresh(room)
        return RoomResponse.from_orm(room)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")
    
# Xóa phòng theo ID
def delete_room(db: Session, room_id: int):
    try:
        room = db.query(Rooms).filter(Rooms.room_id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        db.delete(room)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")

# Cập nhật thông tin phòng
def update_room(db: Session, room_id: int, room_in: RoomCreate):
    try:
        room = db.query(Rooms).filter(Rooms.room_id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        updated_room = room_in.dict(exclude_unset=True)
        for key, value in updated_room.items():
            setattr(room, key, value)
        db.commit()
        db.refresh(room)
        return room
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")

# 
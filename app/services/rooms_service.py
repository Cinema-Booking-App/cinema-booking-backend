from hmac import new
from fastapi import HTTPException
from app.models.seat_layouts import SeatLayouts
from app.models.seat_templates import SeatTemplates
from app.models.seats import Seats
from app.schemas.rooms import RoomCreate, RoomResponse
from sqlalchemy.orm import Session
from app.models.rooms import Rooms
from app.models.theaters import Theaters
from app.schemas.seats import SeatsResponse
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
        seat_layout = db.query(SeatLayouts).filter(SeatLayouts.layout_id == room_in.layout_id).first()
        if not seat_layout:
            raise HTTPException(status_code=404, detail="Seat layout not found")
        existing_room = db.query(Rooms).filter(Rooms.room_name == room_in.room_name, Rooms.theater_id == theater_id).first()
        if existing_room:
            raise HTTPException(status_code=400, detail="Room already exists")
        
        room = Rooms(
             theater_id=theater_id,
             room_name=room_in.room_name,
             layout_id=room_in.layout_id,
             )
        db.add(room)
        db.flush()
        seat_templates = db.query(SeatTemplates).filter(SeatTemplates.layout_id == room.layout_id).all()
        if not seat_templates:
            raise HTTPException(status_code=404, detail="No seat templates found for this layout")
        
        seat_create =[]
        for template in seat_templates:
            new_seat = Seats(
                room_id=room.room_id, 
                seat_type=template.seat_type,
                seat_code=template.seat_code, 
                is_available=template.is_active, 
                is_edge=template.is_edge,
                row_number=template.row_number,
                column_number=template.column_number
            )
            seat_create.append(new_seat)
        db.add_all(seat_create)
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

# Lấy danh sách ghế trong phòng
def get_seats_in_room(db: Session, room_id: int):
    try : 
        room = db.query(Rooms).filter(Rooms.room_id == room_id).first()
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")
        
        seats = db.query(Seats).filter(Seats.room_id == room_id).all()
        if not seats:
            return []
        return [SeatsResponse.from_orm(seat) for seat in seats]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{str(e)}")
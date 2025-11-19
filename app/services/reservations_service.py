from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from typing import List
import asyncio

from app.models.seat_reservations import SeatReservations
from app.models.seats import Seats
from app.models.showtimes import Showtimes
from app.schemas.reservations import SeatReservationsCreate, SeatReservationsResponse


#Lấy danh sách các ghế đã đặt
def get_reserved_seats(showtime_id: int, db: Session):
    try:
        showtime = db.query(Showtimes).filter(Showtimes.showtime_id == showtime_id).first()
        if not showtime:
            raise HTTPException(status_code=404, detail="Showtime not found")
        # Lấy danh sách các ghế đã đặt cho showtime cụ thể
        reserved_seats = db.query(SeatReservations).filter(
            SeatReservations.showtime_id == showtime_id,
            SeatReservations.status.in_(["confirmed", "pending"])
        ).all()
        
        return [SeatReservationsResponse.from_orm(reservation) for reservation in reserved_seats]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
# Tạo một hàm để tạo đặt chỗ
def create_reserved_seats(reservation_in : SeatReservationsCreate , db : Session):
    try:
        showtime = db.query(Showtimes).filter(Showtimes.showtime_id == reservation_in.showtime_id).first()
        seat = db.query(Seats).filter(Seats.seat_id == reservation_in.seat_id).first()
        if not showtime:
            raise HTTPException(status_code=404 , detail="Showtime not found")
        if not seat:
            raise HTTPException(status_code=404 , detail="Seat not found")
        existing_reservation = db.query(SeatReservations).filter(
            SeatReservations.showtime_id == reservation_in.showtime_id,
            SeatReservations.seat_id == reservation_in.seat_id,
            or_(
                SeatReservations.status == 'confirmed',
                and_(
                    SeatReservations.status == 'pending',
                    SeatReservations.expires_at > datetime.now(timezone.utc)
                )
            )
        ).first()
        if existing_reservation:
            if existing_reservation.status == 'confirmed':
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT, 
                    detail=f"Seat {reservation_in.seat_id} for showtime {reservation_in.showtime_id} is already confirmed."
                )
            elif existing_reservation.status == 'pending':
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Seat {reservation_in.seat_id} for showtime {reservation_in.showtime_id} is temporarily reserved and not yet expired."
                )
            
        current_utc_time = datetime.now(timezone.utc)
        calculated_expires_at = current_utc_time + timedelta(minutes=10)

        db_reservation = SeatReservations(
            seat_id=reservation_in.seat_id,
            showtime_id=reservation_in.showtime_id,
            user_id=reservation_in.user_id,
            session_id=reservation_in.session_id,
            expires_at=calculated_expires_at,
            status="pending"
        )

        db.add(db_reservation)
        db.commit()
        db.refresh(db_reservation) 

        # Gửi thông báo WebSocket realtime (không chặn luong chính)
        try:
            from app.core.websocket_manager import websocket_manager
            # Tạo task bất đồng bộ để thông báo ghế đã được đặt
            asyncio.create_task(
                websocket_manager.send_seat_reserved(
                    showtime_id=reservation_in.showtime_id,  # Suất chiếu
                    seat_ids=[reservation_in.seat_id],       # Danh sách ghế được đặt
                    user_session=reservation_in.session_id or ""  # Session người đặt
                )
            )
        except Exception as ws_error:
            # Không làm thất bại việc đặt ghế nếu WebSocket gặp lỗi
            print(f"Thông báo WebSocket thất bại: {ws_error}")

        return SeatReservationsResponse.from_orm(db_reservation)
    except Exception as e :
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,detail= e)


# Tạo nhiều reservations cùng lúc
async def create_multiple_reserved_seats(reservations_in: List[SeatReservationsCreate], db: Session):
    try:
        created_reservations = []
        seat_ids = []
        showtime_id = None
        user_session = None
        
        for reservation_in in reservations_in:
            showtime = db.query(Showtimes).filter(Showtimes.showtime_id == reservation_in.showtime_id).first()
            seat = db.query(Seats).filter(Seats.seat_id == reservation_in.seat_id).first()
            
            if not showtime:
                raise HTTPException(status_code=404, detail="Showtime not found")
            if not seat:
                raise HTTPException(status_code=404, detail="Seat not found")
                
            # Check existing reservations
            existing_reservation = db.query(SeatReservations).filter(
                SeatReservations.showtime_id == reservation_in.showtime_id,
                SeatReservations.seat_id == reservation_in.seat_id,
                or_(
                    SeatReservations.status == 'confirmed',
                    and_(
                        SeatReservations.status == 'pending',
                        SeatReservations.expires_at > datetime.now(timezone.utc)
                    )
                )
            ).first()
            
            if existing_reservation:
                if existing_reservation.status == 'confirmed':
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Seat {reservation_in.seat_id} is already confirmed."
                    )
                elif existing_reservation.status == 'pending':
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Seat {reservation_in.seat_id} is temporarily reserved."
                    )
            
            current_utc_time = datetime.now(timezone.utc)
            calculated_expires_at = current_utc_time + timedelta(minutes=10)

            db_reservation = SeatReservations(
                seat_id=reservation_in.seat_id,
                showtime_id=reservation_in.showtime_id,
                user_id=reservation_in.user_id,
                session_id=reservation_in.session_id,
                expires_at=calculated_expires_at,
                status="pending"
            )

            db.add(db_reservation)
            seat_ids.append(reservation_in.seat_id)
            showtime_id = reservation_in.showtime_id
            user_session = reservation_in.session_id or ""
            
        db.commit()
        
        # Gửi thông báo WebSocket cho tất cả ghế được đặt cùng lúc
        try:
            from app.core.websocket_manager import websocket_manager
            # Thông báo realtime đến tất cả client đang xem suất chiếu này
            await websocket_manager.send_seat_reserved(
                showtime_id=showtime_id,    # Suất chiếu
                seat_ids=seat_ids,          # Danh sách tất cả ghế vừa được đặt
                user_session=user_session   # Session người đặt
            )
        except Exception as ws_error:
            print(f"Thông báo WebSocket đặt nhiều ghế thất bại: {ws_error}")
        
        # Refresh and return all created reservations
        for reservation in created_reservations:
            db.refresh(reservation)
            
        return [SeatReservationsResponse.from_orm(res) for res in created_reservations]
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

# Giải phóng ghế (hủy reservation)
async def cancel_seat_reservations(showtime_id: int, seat_ids: List[int], session_id: str, db: Session):
    try:
        # Validate showtime exists
        showtime = db.query(Showtimes).filter(Showtimes.showtime_id == showtime_id).first()
        if not showtime:
            raise HTTPException(status_code=404, detail="Showtime not found")
        
        # Find reservations to cancel (chỉ pending và của session này)
        reservations_to_cancel = db.query(SeatReservations).filter(
            SeatReservations.showtime_id == showtime_id,
            SeatReservations.seat_id.in_(seat_ids),
            SeatReservations.session_id == session_id,
            SeatReservations.status == 'pending'
        ).all()
        
        if not reservations_to_cancel:
            # Trả về thành công nhưng không có gì để hủy
            return {
                "success": True,
                "message": "No pending reservations found to cancel",
                "cancelled_seats": []
            }
        
        cancelled_seat_ids = []
        seat_codes = []
        
        for reservation in reservations_to_cancel:
            # Lấy seat_code để gửi WebSocket
            seat = db.query(Seats).filter(Seats.seat_id == reservation.seat_id).first()
            if seat:
                seat_codes.append(seat.seat_code)
            
            cancelled_seat_ids.append(reservation.seat_id)
            db.delete(reservation)
        
        db.commit()
        
        # Gửi thông báo WebSocket về việc giải phóng ghế
        try:
            from app.core.websocket_manager import websocket_manager
            # Thông báo realtime rằng các ghế đã được giải phóng
            await websocket_manager.send_seat_released(
                showtime_id=showtime_id,
                seat_ids=cancelled_seat_ids
            )
            print(f"✅ WebSocket thông báo giải phóng {len(cancelled_seat_ids)} ghế cho showtime {showtime_id}")
        except Exception as ws_error:
            print(f"❌ Thông báo WebSocket giải phóng ghế thất bại: {ws_error}")
        
        # Lấy room_id từ showtime để frontend có thể invalidate seats cache
        room_id = showtime.room_id if showtime else None
        
        return {
            "success": True,
            "message": f"Successfully cancelled {len(cancelled_seat_ids)} seat reservations",
            "cancelled_seats": cancelled_seat_ids,
            "seat_codes": seat_codes,
            "showtime_id": showtime_id,
            "session_id": session_id,
            "room_id": room_id
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

#Xóa đặt chỗ tự động khi hết hạn  
async def delete_expired_reservations(db: Session):
    try:
        current_time = datetime.now(timezone.utc)
        expired_reservations = db.query(SeatReservations).filter(
            SeatReservations.status == 'pending',
            SeatReservations.expires_at < current_time
        ).all()

        # Nhóm các ghế theo suất chiếu để gửi thông báo WebSocket hiệu quả
        showtime_seat_map = {}
        for reservation in expired_reservations:
            showtime_id = reservation.showtime_id
            # Tạo map: showtime_id -> danh sách seat_id hết hạn
            if showtime_id not in showtime_seat_map:
                showtime_seat_map[showtime_id] = []
            showtime_seat_map[showtime_id].append(reservation.seat_id)
            db.delete(reservation)  # Xóa reservation hết hạn

        db.commit()
        
        # Gửi thông báo WebSocket cho các ghế được giải phóng do hết hạn
        try:
            from app.core.websocket_manager import websocket_manager
            # Gửi thông báo cho từng suất chiếu
            for showtime_id, seat_ids in showtime_seat_map.items():
                await websocket_manager.send_seat_released(
                    showtime_id=showtime_id,  # Suất chiếu
                    seat_ids=seat_ids         # Danh sách ghế hết hạn được giải phóng
                )
        except Exception as ws_error:
            print(f"Thông báo WebSocket ghế hết hạn thất bại: {ws_error}")
            
        return len(expired_reservations)
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
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

        # Send WebSocket notification (non-blocking)
        try:
            from app.core.websocket_manager import websocket_manager
            asyncio.create_task(
                websocket_manager.send_seat_reserved(
                    showtime_id=reservation_in.showtime_id,
                    seat_ids=[reservation_in.seat_id],
                    user_session=reservation_in.session_id or ""
                )
            )
        except Exception as ws_error:
            # Don't fail the reservation if WebSocket fails
            print(f"WebSocket notification failed: {ws_error}")

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
        
        # Send WebSocket notification for all seats
        try:
            from app.core.websocket_manager import websocket_manager
            await websocket_manager.send_seat_reserved(
                showtime_id=showtime_id,
                seat_ids=seat_ids,
                user_session=user_session
            )
        except Exception as ws_error:
            print(f"WebSocket notification failed: {ws_error}")
        
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
        reservations_to_cancel = db.query(SeatReservations).filter(
            SeatReservations.showtime_id == showtime_id,
            SeatReservations.seat_id.in_(seat_ids),
            SeatReservations.session_id == session_id,
            SeatReservations.status == 'pending'
        ).all()
        
        if not reservations_to_cancel:
            raise HTTPException(status_code=404, detail="No pending reservations found")
        
        cancelled_seat_ids = []
        for reservation in reservations_to_cancel:
            cancelled_seat_ids.append(reservation.seat_id)
            db.delete(reservation)
        
        db.commit()
        
        # Send WebSocket notification
        try:
            from app.core.websocket_manager import websocket_manager
            await websocket_manager.send_seat_released(
                showtime_id=showtime_id,
                seat_ids=cancelled_seat_ids
            )
        except Exception as ws_error:
            print(f"WebSocket notification failed: {ws_error}")
        
        return {"cancelled_seats": cancelled_seat_ids}
        
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

        # Group by showtime for efficient WebSocket notifications
        showtime_seat_map = {}
        for reservation in expired_reservations:
            showtime_id = reservation.showtime_id
            if showtime_id not in showtime_seat_map:
                showtime_seat_map[showtime_id] = []
            showtime_seat_map[showtime_id].append(reservation.seat_id)
            db.delete(reservation)

        db.commit()
        
        # Send WebSocket notifications for released seats
        try:
            from app.core.websocket_manager import websocket_manager
            for showtime_id, seat_ids in showtime_seat_map.items():
                await websocket_manager.send_seat_released(
                    showtime_id=showtime_id,
                    seat_ids=seat_ids
                )
        except Exception as ws_error:
            print(f"WebSocket notification failed: {ws_error}")
            
        return len(expired_reservations)
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
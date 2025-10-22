from datetime import datetime
from fastapi import HTTPException,status
from sqlalchemy import  func
from app.models.seat_reservations import SeatReservations
from app.models.seat_templates import SeatTypeEnum
from app.models.seats import Seats
from app.models.showtimes import Showtimes
from app.models.transactions import TransactionStatus, Transaction
from app.schemas.tickets import (
    TicketsCreate,
    TicketsResponse,
    TicketQRResponse,
    TicketVerifyRequest,
    TicketVerifyResponse,
)
from sqlalchemy.orm import Session
from app.models.tickets import Tickets
from app.core.token_utils import create_token
from datetime import timedelta
from jose import jwt, JWTError
from app.core.config import settings


def get_all_bookings(db: Session):
    """Return bookings grouped by booking_code with summary fields suitable for admin/print views."""
    try:
        tickets = db.query(Tickets).all()
        grouped = {}
        for t in tickets:
            code = getattr(t, 'booking_code', None) or 'NO_CODE'
            if code not in grouped:
                grouped[code] = {
                    'code': code,
                    'tickets': [],
                    'customer': None,
                    'phone': None,
                    'email': None,
                    'movie': None,
                    'showtime': None,
                    'date': None,
                    'status': None,
                    'printed': False,
                    'received': False,
                    'refunded': False,
                    'qr': code,
                }
            # seat code/type
            seat_code = getattr(t.seat, 'seat_code', None)
            seat_type = getattr(t.seat, 'seat_type', None)
            grouped[code]['tickets'].append({
                'ticket_id': t.ticket_id,
                'seat': seat_code,
                'type': str(seat_type) if seat_type else None,
                'price': float(t.price) if t.price is not None else None,
            })
            # populate customer/email/phone if available from user
            if t.user:
                grouped[code]['customer'] = t.user.full_name
                grouped[code]['email'] = t.user.email
                grouped[code]['phone'] = t.user.phone
            # showtime/movie
            if t.showtime and t.showtime.movie:
                grouped[code]['movie'] = t.showtime.movie.title
                # format showtime
                try:
                    dt = t.showtime.show_datetime
                    room = getattr(t.showtime.room, 'room_name', None)
                    grouped[code]['showtime'] = f"{dt.strftime('%H:%M')} - {room}" if dt else None
                    grouped[code]['date'] = dt.strftime('%Y-%m-%d') if dt else None
                except Exception:
                    pass
            # status inference: if any ticket is refunded/cancelled
            if str(t.status) == 'cancelled':
                grouped[code]['refunded'] = True

        # Convert to list
        result = []
        for code, item in grouped.items():
            # compute seats string
            seats = [ti['seat'] for ti in item['tickets'] if ti.get('seat')]
            item['seats'] = ', '.join(seats)
            # status aggregation
            item['status'] = 'Đã thanh toán' if any(True for ti in item['tickets']) else 'unknown'
            result.append(item)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def get_booking_by_code(db: Session, booking_code: str):
    try:
        tickets = db.query(Tickets).filter(Tickets.booking_code == booking_code).all()
        if not tickets:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Booking not found')
        # reuse grouping logic but only for one code
        grouped = {
            'code': booking_code,
            'tickets': [],
            'customer': None,
            'phone': None,
            'email': None,
            'movie': None,
            'showtime': None,
            'date': None,
            'status': None,
            'printed': False,
            'received': False,
            'refunded': False,
            'qr': booking_code,
        }
        for t in tickets:
            seat_code = getattr(t.seat, 'seat_code', None)
            seat_type = getattr(t.seat, 'seat_type', None)
            grouped['tickets'].append({
                'ticket_id': t.ticket_id,
                'seat': seat_code,
                'type': str(seat_type) if seat_type else None,
                'price': float(t.price) if t.price is not None else None,
            })
            if t.user:
                grouped['customer'] = t.user.full_name
                grouped['email'] = t.user.email
                grouped['phone'] = t.user.phone
            if t.showtime and t.showtime.movie:
                try:
                    dt = t.showtime.show_datetime
                    room = getattr(t.showtime.room, 'room_name', None)
                    grouped['showtime'] = f"{dt.strftime('%H:%M')} - {room}" if dt else None
                    grouped['date'] = dt.strftime('%Y-%m-%d') if dt else None
                    grouped['movie'] = t.showtime.movie.title
                except Exception:
                    pass
            if str(t.status) == 'cancelled':
                grouped['refunded'] = True
        grouped['seats'] = ', '.join([ti['seat'] for ti in grouped['tickets'] if ti.get('seat')])
        grouped['status'] = 'Đã thanh toán'
        return grouped
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


# Nhân viên tạo vé trực tiếp tại quầy
def create_ticket_directly(db : Session, ticket_in : TicketsCreate):
    try:
        # Kiểm tra xem ghế đã được đặt hay chưa
        existing_ticket = db.query(Tickets).filter(
            Tickets.showtime_id == ticket_in.showtime_id,
            Tickets.seat_id == ticket_in.seat_id,
            Tickets.status != 'cancelled'
        ).first()
        if existing_ticket:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat already booked for this showtime.")
        
        # Kiểm tra xem ghế đã đặt chỗ hay chưa
        reversed_seat = db.query(SeatReservations).filter(
            SeatReservations.showtime_id == ticket_in.showtime_id,
            SeatReservations.seat_id == ticket_in.seat_id,
            SeatReservations.status == 'pending',
            SeatReservations.expires_at > func.now()
        ).first()
        if reversed_seat:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Seat is reserved and cannot be booked directly.")
        
        showtime = db.query(Showtimes).filter(
            Showtimes.showtime_id == ticket_in.showtime_id,
            Showtimes.status == 'active'
        ).first()
        seat = db.query(Seats).filter(
            Seats.seat_id == ticket_in.seat_id
        ).first()
        # Tính giá vé dựa trên loại ghế
        base_price = float(showtime.ticket_price)
        if seat.seat_type == SeatTypeEnum.vip:
            base_price *= 1.5
        elif seat.seat_type == SeatTypeEnum.couple:
            base_price *= 2

        db_transaction = Transaction(
            user_id=ticket_in.user_id,
            staff_user_id=ticket_in.user_id,
            # staff_user_id=staff_user_id, # Nhân viên thực hiện giao dịch
            promotion_id=ticket_in.promotion_id,
            total_amount=base_price,
            payment_method='cash',  # Mặc định tiền mặt khi tạo tại quầy
            status=TransactionStatus.success,  # Mặc định thành công khi tạo trực tiếp
            transaction_time=datetime.now()
        )
        db.add(db_transaction)
        db.flush()  # Để lấy transaction_id
        db_ticket = Tickets(
            user_id=ticket_in.user_id,
            showtime_id=ticket_in.showtime_id,
            seat_id=ticket_in.seat_id,
            promotion_id=ticket_in.promotion_id,
            price= base_price,
            status='confirmed',
            transaction_id=db_transaction.transaction_id
        )
        db.add(db_ticket)
        db.flush() 
        db.commit()
        db.refresh(db_transaction)
        db.refresh(db_ticket)
         # Chuẩn bị dữ liệu response
        response_data = {
            "ticket_id": db_ticket.ticket_id,
            "user_id": db_ticket.user_id,
            "showtime_id": db_ticket.showtime_id,
            "seat_id": db_ticket.seat_id,
            "promotion_id": db_ticket.promotion_id,
            "price": db_ticket.price,
            "booking_time": db_ticket.booking_time,
            "status": db_ticket.status,
            "cancelled_at": db_ticket.cancelled_at,
            "seat_code": seat.seat_code,
            "seat_type": seat.seat_type
        }

        return TicketsResponse(**response_data)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def generate_ticket_qr(db: Session, ticket_id: int) -> TicketQRResponse:
    ticket = db.query(Tickets).filter(Tickets.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if str(ticket.status) != 'confirmed':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket is not confirmed")
    payload = {"ticket_id": ticket.ticket_id, "showtime_id": ticket.showtime_id, "type": "ticket_qr"}
    token = create_token(payload, expires_delta=timedelta(hours=12), token_type="qr")
    return TicketQRResponse(ticket_id=ticket.ticket_id, qr_token=token)


def verify_ticket_qr(db: Session, verify_in: TicketVerifyRequest) -> TicketVerifyResponse:
    try:
        decoded = jwt.decode(verify_in.qr_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid QR token")
    if decoded.get("type") != "qr" or decoded.get("ticket_id") is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid QR payload")
    ticket_id = int(decoded["ticket_id"])
    ticket = db.query(Tickets).filter(Tickets.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found")
    if str(ticket.status) != 'confirmed':
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Ticket is not valid for entry")
    # Idempotent: if already validated, return current state
    if ticket.validated_at:
        return TicketVerifyResponse(ticket_id=ticket.ticket_id, validated=True, validated_at=ticket.validated_at, status=str(ticket.status))
    ticket.validated_at = datetime.now()
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return TicketVerifyResponse(ticket_id=ticket.ticket_id, validated=True, validated_at=ticket.validated_at, status=str(ticket.status))
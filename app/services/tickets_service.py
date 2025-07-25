from datetime import datetime
from fastapi import HTTPException,status
from sqlalchemy import  func
from app.models.seat_reservations import SeatReservations
from app.models.seat_templates import SeatTypeEnum
from app.models.seats import Seats
from app.models.showtimes import Showtimes
from app.models.transactions import TransactionStatus, TransactionTickets, Transactions
from app.schemas.tickets import TicketsCreate, TicketsResponse
from sqlalchemy.orm import Session
from app.models.tickets import Tickets
# Nhân viên tạo vé trực tiếp tại quầy
# Phần chưa hoàn thiện là chưa giải quyết trường hợp đặt nhiều vé và lưu và tổng thanh toán vẫn đang lưu từng cái 
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

        db_transaction = Transactions(
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
            status='confirmed'
        )
        db.add(db_ticket)
        db.flush()  # Để lấy ticket_id

           # 6. Liên kết giao dịch và vé
        db_transaction_ticket = TransactionTickets(
            transaction_id=db_transaction.transaction_id,
            ticket_id=db_ticket.ticket_id
        )
        db.add(db_transaction_ticket)
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
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
import uuid
import random
import string
import traceback
import unicodedata  # <--- Mới thêm: Để xử lý tiếng Việt

from app.services.email_service import EmailService
from app.models.users import Users
from app.models.showtimes import Showtimes
from app.models.movies import Movies
from app.models.seats import Seats
from app.core.config import settings
from app.payments.vnpay import VNPay
from app.models.payments import Payment, PaymentStatusEnum, PaymentMethodEnum, VNPayPayment
from app.models.seat_reservations import SeatReservations
from app.models.tickets import Tickets
from app.models.transactions import Transaction, TransactionStatus
from app.schemas.payments import (
    PaymentRequest,
    PaymentResponse,
    PaymentResult,
    PaymentStatus,
    PaymentMethod
)

class PaymentService:
    """Service xử lý thanh toán"""
    
    def __init__(self):
        self.vnpay = VNPay()

    # --- HELPER: BỎ DẤU TIẾNG VIỆT ---
    def remove_accents(self, input_str: str) -> str:
        if not input_str:
            return ""
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        only_ascii = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
        return "".join(c for c in only_ascii if c.isalnum() or c == " ")

    def create_payment(self, db: Session, request: PaymentRequest, client_ip: str, user_id: Optional[int] = None):
        print("\n================ PAYMENT START ================\n")
        try:
            order_id = str(uuid.uuid4())
            reservations = db.query(SeatReservations).filter(
                SeatReservations.session_id == request.session_id,
                SeatReservations.status == 'pending'
            ).all()

            if not reservations:
                raise ValueError("Không tìm thấy reservation hợp lệ")
            
            if user_id is None:
                raise ValueError("Người dùng chưa được xác định")
            
            # Tính tổng tiền
            total_amount = 0
            for reservation in reservations:
                ticket_price = self.calculate_ticket_price(db, reservation.seat_id, reservation.showtime_id)
                total_amount += ticket_price
            
            # Chuẩn hóa payment_method
            try:
                if isinstance(request.payment_method, str):
                    payment_method = PaymentMethodEnum(request.payment_method)
                else:
                    payment_method = PaymentMethodEnum(request.payment_method.value)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid payment_method: {request.payment_method}")

            # Tạo Payment
            if payment_method == PaymentMethodEnum.VNPAY:
                payment = VNPayPayment(
                    order_id=order_id,
                    amount=total_amount,
                    payment_method=payment_method,
                    payment_status=PaymentStatusEnum.PENDING,
                    order_desc=request.order_desc,
                    client_ip=client_ip,
                    vnp_txn_ref=order_id,
                    user_id=user_id
                )
            else:
                payment = Payment(
                    order_id=order_id,
                    user_id=user_id,
                    amount=total_amount,
                    payment_method=payment_method,
                    payment_status=PaymentStatusEnum.PENDING,
                    order_desc=request.order_desc,
                    client_ip=client_ip
                )
            
            db.add(payment)
            db.flush() # Dùng flush để lấy ID nhưng chưa commit hẳn
            
            # Update Reservation
            db.query(SeatReservations).filter(
                SeatReservations.session_id == request.session_id,
                SeatReservations.status == 'pending'
            ).update({SeatReservations.payment_id: payment.payment_id}, synchronize_session=False)
            
            # Tạo Transaction
            transaction = Transaction(
                user_id=user_id,
                staff_user_id=None,
                promotion_id=None,
                total_amount=total_amount,
                payment_method=payment_method.value,
                status=TransactionStatus.pending,
                transaction_time=datetime.utcnow(),
                payment_id=payment.payment_id
            )
            db.add(transaction)
            
            # Tạo URL thanh toán
            if payment_method == PaymentMethodEnum.VNPAY:
                payment.payment_url = self.create_vnpay_url(request, client_ip, total_amount, order_id)
            elif payment_method == PaymentMethodEnum.MOMO:
                payment.payment_url = None # Chưa implement
            elif payment_method == PaymentMethodEnum.CASH:
                payment.payment_url = None
                
            db.commit()
            db.refresh(payment)
            
            return PaymentResponse(
                payment_url=payment.payment_url,
                order_id=order_id,
                amount=payment.amount,
                payment_method=PaymentMethod(payment.payment_method.value),
                payment_status=PaymentStatus(payment.payment_status.value)
            )
        except Exception as e:
            db.rollback()
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))

    def create_vnpay_url(self, payment_request: PaymentRequest, client_ip: str, amount: int, order_id: str) -> str:
        """Tạo URL thanh toán VNPay"""
        try:
            # Xử lý chuỗi an toàn
            clean_order_desc = self.remove_accents(payment_request.order_desc)
            clean_order_desc = clean_order_desc[:50] if clean_order_desc else f"Thanh toan {order_id}"

            self.vnpay.set_request_data(
                vnp_Version='2.1.0',
                vnp_Command='pay',
                vnp_TmnCode=settings.VNPAY_TMN_CODE,
                vnp_Amount=int(amount * 100),
                vnp_CurrCode='VND',
                vnp_TxnRef=order_id,
                vnp_OrderInfo=clean_order_desc,
                vnp_OrderType='other',
                vnp_Locale=payment_request.language or 'vn',
                vnp_CreateDate=datetime.now().strftime('%Y%m%d%H%M%S'),
                vnp_IpAddr=client_ip,
                vnp_ReturnUrl=settings.VNPAY_RETURN_URL
            )
            
            return self.vnpay.get_payment_url(
                settings.VNPAY_PAYMENT_URL,
                settings.VNPAY_HASH_SECRET_KEY
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create payment URL: {str(e)}")
    
    def handle_vnpay_callback(self, db: Session, callback_data: Dict[str, Any]) -> PaymentResult:
        """Xử lý callback: Chỉ xác thực chữ ký, KHÔNG cập nhật status DB tại đây để tránh conflict"""
        try:
            self.vnpay.set_response_data(callback_data)
            is_valid = self.vnpay.validate_response(settings.VNPAY_HASH_SECRET_KEY)
            
            order_id = callback_data.get('vnp_TxnRef')
            amount = int(callback_data.get('vnp_Amount', 0)) // 100
            response_code = callback_data.get('vnp_ResponseCode')
            transaction_no = callback_data.get('vnp_TransactionNo')

            if not is_valid:
                return PaymentResult(
                    success=False,
                    order_id=order_id,
                    message="Invalid signature",
                    payment_method=PaymentMethod.VNPAY,
                    payment_status=PaymentStatus.FAILED
                )
            
            success = (response_code == '00')
            
            return PaymentResult(
                success=success,
                order_id=order_id,
                transaction_id=transaction_no,
                amount=amount,
                message="Success" if success else f"Failed: {response_code}",
                payment_method=PaymentMethod.VNPAY,
                payment_status=PaymentStatus.SUCCESS if success else PaymentStatus.FAILED
            )
            
        except Exception as e:
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Callback error: {str(e)}")

    def update_payment_status(self, db: Session, order_id: str, payment_result: PaymentResult) -> Dict[str, Any]:
        """Hàm quan trọng: Cập nhật trạng thái và TẠO VÉ (Atomic)"""
        try:
            # 1. Tìm payment
            payment = self.get_payment_by_order_id(db, order_id)
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")
            
            # Nếu đã xử lý rồi
            if payment.payment_status == PaymentStatusEnum.SUCCESS:
                # Tìm booking code cũ để trả về
                trans = db.query(Transaction).filter_by(payment_id=payment.payment_id).first()
                ticket = db.query(Tickets).filter_by(transaction_id=trans.transaction_id).first() if trans else None
                return {
                    "status": "success",
                    "booking_code": ticket.booking_code if ticket else "PROCESSED",
                    "message": "Already processed"
                }

            # Cập nhật thông tin VNPay (nhưng chưa commit status success)
            vnpay_payment = db.query(VNPayPayment).filter_by(payment_id=payment.payment_id).first()
            if vnpay_payment and payment_result.transaction_id:
                vnpay_payment.vnp_transaction_no = payment_result.transaction_id
            
            # 2. Nếu thanh toán thất bại
            if not payment_result.success:
                payment.payment_status = PaymentStatusEnum.FAILED
                if vnpay_payment: vnpay_payment.payment_status = PaymentStatusEnum.FAILED
                
                trans = db.query(Transaction).filter_by(payment_id=payment.payment_id).first()
                if trans: trans.status = TransactionStatus.failed
                
                db.commit()
                return {"status": "failed", "message": "Payment failed from gateway"}

            # 3. Nếu thanh toán thành công -> TẠO VÉ
            try:
                # Gọi hàm tạo vé và gửi mail
                success_data = self.process_successful_payment(db, order_id, payment_result)
                
                # Cập nhật Payment & Transaction thành công SAU KHI tạo vé xong
                payment.payment_status = PaymentStatusEnum.SUCCESS
                if vnpay_payment: vnpay_payment.payment_status = PaymentStatusEnum.SUCCESS
                
                if success_data.get("transaction_id"):
                    payment.transaction_id = success_data["transaction_id"]
                
                db.commit() # <--- COMMIT CUỐI CÙNG
                
                return {
                    "status": "success",
                    "payment_status": "SUCCESS",
                    **success_data
                }
                
            except Exception as logic_error:
                db.rollback() # Rollback nếu tạo vé lỗi
                print(f"CRITICAL: Payment success but ticket generation failed: {logic_error}")
                raise HTTPException(status_code=500, detail="Payment charged but failed to generate ticket.")

        except Exception as e:
            db.rollback()
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))

    def process_successful_payment(self, db: Session, order_id: str, payment_result: PaymentResult) -> Dict[str, Any]:
        """Logic tạo vé và gửi mail"""
        # Lấy payment & user
        payment = self.get_payment_by_order_id(db, order_id)
        user = db.query(Users).filter(Users.user_id == payment.user_id).first()
        transaction = db.query(Transaction).filter(Transaction.payment_id == payment.payment_id).first()
        
        reservations = db.query(SeatReservations).filter(
            SeatReservations.payment_id == payment.payment_id,
            SeatReservations.status == 'pending'
        ).all()

        if not reservations:
            # Có thể đã xử lý rồi hoặc lỗi
            check_ticket = db.query(Tickets).filter(Tickets.transaction_id == transaction.transaction_id).first()
            if check_ticket:
                return {
                    "transaction_id": transaction.transaction_id,
                    "booking_code": check_ticket.booking_code
                }
            raise HTTPException(status_code=404, detail="No pending reservations found")

        # Tạo Booking Code
        booking_code = f"BK{datetime.now().strftime('%Y%m%d')}{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"

        created_tickets = []
        for reservation in reservations:
            # Kiểm tra hết hạn (Optional: Có thể bỏ qua nếu đã thanh toán thành công để user không bị mất tiền)
            # current_time = datetime.utcnow()
            # if reservation.expires_at < current_time: ...

            price = self.calculate_ticket_price(db, reservation.seat_id, reservation.showtime_id)
            
            ticket = Tickets(
                user_id=user.user_id,
                showtime_id=reservation.showtime_id,
                seat_id=reservation.seat_id,
                price=price,
                status='confirmed',
                transaction_id=transaction.transaction_id,
                booking_code=booking_code
            )
            db.add(ticket)
            
            reservation.status = "confirmed"
            reservation.transaction_id = transaction.transaction_id
        
        transaction.status = TransactionStatus.success
        transaction.payment_ref_code = payment_result.transaction_id
        
        db.flush() # Lưu tạm để check lỗi

        # --- GỬI EMAIL (QUAN TRỌNG: BỌC TRY EXCEPT ĐỂ KHÔNG CHẾT APP NẾU GỬI LỖI) ---
        try:
            self.send_booking_email(db, reservations, user, booking_code)
        except Exception as e:
            print(f"WARNING: Failed to send email for {booking_code}. Error: {e}")
            # Không raise exception ở đây để vé vẫn được tạo

        return {
            "transaction_id": transaction.transaction_id,
            "booking_code": booking_code,
            "message": "Tickets created successfully"
        }

    def send_booking_email(self, db: Session, reservations: list, user: Users, booking_code: str):
        """Hàm gửi email tách riêng"""
        seats_list = []
        movie_title = 'Unknown'
        showtime_str = 'Unknown'

        for res in reservations:
            seat = db.query(Seats).filter(Seats.seat_id == res.seat_id).first()
            seats_list.append(seat.seat_code if seat else str(res.seat_id))
            
            # Lấy thông tin phim từ vé đầu tiên
            if movie_title == 'Unknown':
                st = db.query(Showtimes).filter(Showtimes.showtime_id == res.showtime_id).first()
                if st:
                    if st.movie: movie_title = st.movie.title
                    else: 
                        mv = db.query(Movies).filter(Movies.movie_id == st.movie_id).first()
                        movie_title = mv.title if mv else 'Unknown'
                    
                    dt = st.show_datetime
                    showtime_str = dt.strftime('%Y-%m-%d %H:%M') if dt else str(st.start_time)

        ticket_info = {
            'booking_id': booking_code,
            'customer_name': user.full_name or user.name or 'Customer',
            'movie_name': movie_title,
            'showtime': showtime_str,
            'seats': seats_list
        }
        
        # Lấy config email
        email_service = EmailService(
            smtp_server=settings.EMAIL_HOST,
            smtp_port=settings.EMAIL_PORT,
            username=settings.EMAIL_USERNAME,
            password=settings.EMAIL_PASSWORD,
            sender_name=settings.EMAIL_SENDER_NAME
        )
        email_service.send_ticket_email(to_email=user.email, ticket_info=ticket_info)

    def calculate_ticket_price(self, db: Session, seat_id: int, showtime_id: int) -> int:
        """Tính giá vé"""
        from app.models.seats import Seats
        from app.models.showtimes import Showtimes
        from app.models.seat_templates import SeatTypeEnum
        
        seat = db.query(Seats).filter(Seats.seat_id == seat_id).first()
        showtime = db.query(Showtimes).filter(Showtimes.showtime_id == showtime_id).first()
        
        if not seat or not showtime:
            raise HTTPException(status_code=404, detail="Seat or Showtime not found")
        
        price = float(showtime.ticket_price)
        if seat.seat_type == SeatTypeEnum.vip: price *= 1.5
        elif seat.seat_type == SeatTypeEnum.couple: price *= 2.0
            
        return int(price)

    def get_payment_by_order_id(self, db: Session, order_id: str) -> Optional[Payment]:
        return db.query(Payment).filter(Payment.order_id == order_id).first()
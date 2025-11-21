from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
import uuid
import random
import string
import traceback
import unicodedata
import qrcode
import base64
from io import BytesIO
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
            db.flush()
            
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
                payment.payment_url = None
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
        """
        Hàm quan trọng: Cập nhật trạng thái và TẠO VÉ (Atomic)
        
        LOGIC:
        1. Kiểm tra payment đã xử lý chưa
        2. VALIDATE reservations TRƯỚC KHI cho phép payment success
        3. Chỉ cập nhật payment success SAU KHI tạo vé thành công
        """
        try:
            # 1. Tìm payment
            payment = self.get_payment_by_order_id(db, order_id)
            if not payment:
                raise HTTPException(status_code=404, detail="Payment not found")
            
            # Nếu đã xử lý rồi
            if payment.payment_status == PaymentStatusEnum.SUCCESS:
                trans = db.query(Transaction).filter_by(payment_id=payment.payment_id).first()
                ticket = db.query(Tickets).filter_by(transaction_id=trans.transaction_id).first() if trans else None
                return {
                    "status": "success",
                    "booking_code": ticket.booking_code if ticket else "PROCESSED",
                    "message": "Already processed"
                }

            # 2. Xử lý thanh toán thất bại
            if not payment_result.success:
                payment.payment_status = PaymentStatusEnum.FAILED
                
                # Cập nhật VNPay payment nếu có
                vnpay_payment = db.query(VNPayPayment).filter_by(payment_id=payment.payment_id).first()
                if vnpay_payment:
                    vnpay_payment.payment_status = PaymentStatusEnum.FAILED
                
                # Cập nhật transaction
                trans = db.query(Transaction).filter_by(payment_id=payment.payment_id).first()
                if trans:
                    trans.status = TransactionStatus.failed
                
                db.commit()
                return {
                    "status": "failed",
                    "payment_status": payment.payment_status.value,
                    "order_id": order_id,
                    "message": "Payment failed from gateway"
                }
            
            # 3. Thanh toán thành công - VALIDATE reservations TRƯỚC KHI commit payment success
            reservations = db.query(SeatReservations).filter(
                SeatReservations.payment_id == payment.payment_id,
                SeatReservations.status == 'pending'
            ).all()
            
            if not reservations:
                # KHÔNG có reservations → KHÔNG CHO PHÉP payment thành công
                payment.payment_status = PaymentStatusEnum.FAILED
                db.commit()
                raise HTTPException(
                    status_code=400,
                    detail="Cannot process payment: No valid reservations found. Payment has been marked as FAILED."
                )
            
            # Kiểm tra reservations có còn hạn không
            current_time = datetime.now(timezone.utc)
            expired_reservations = []
            
            for res in reservations:
                expires_at = res.expires_at
                # Đảm bảo expires_at là timezone-aware
                if not hasattr(expires_at, 'tzinfo') or expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                elif expires_at.tzinfo != timezone.utc:
                    expires_at = expires_at.astimezone(timezone.utc)
                
                if expires_at < current_time:
                    expired_reservations.append(res.reservation_id)
            
            if expired_reservations:
                # Có reservations hết hạn → KHÔNG CHO PHÉP payment thành công
                payment.payment_status = PaymentStatusEnum.FAILED
                db.commit()
                raise HTTPException(
                    status_code=400,
                    detail=f"{len(expired_reservations)} reservation(s) have expired. Cannot process payment. Payment has been marked as FAILED."
                )
            
            # 4. Có reservations hợp lệ → Cập nhật VNPay transaction number trước
            vnpay_payment = db.query(VNPayPayment).filter_by(payment_id=payment.payment_id).first()
            if vnpay_payment and payment_result.transaction_id:
                vnpay_payment.vnp_transaction_no = payment_result.transaction_id
                db.commit()
            
            # 5. Tạo tickets (trong một transaction riêng để đảm bảo atomic)
            success_result = self.process_successful_payment(db, order_id, payment_result)
            
            # 6. CHỈ CẬP NHẬT payment success SAU KHI tạo vé thành công
            payment.payment_status = PaymentStatusEnum.SUCCESS
            if vnpay_payment:
                vnpay_payment.payment_status = PaymentStatusEnum.SUCCESS
            if success_result.get("transaction_id"):
                payment.transaction_id = success_result["transaction_id"]
            
            db.commit()
            
            return {
                "status": "success",
                "payment_status": payment.payment_status.value,
                "order_id": order_id,
                "vnp_transaction_no": getattr(payment, 'vnp_transaction_no', None),
                **success_result
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            db.rollback()
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))

    def process_successful_payment(self, db: Session, order_id: str, payment_result: PaymentResult) -> Dict[str, Any]:
        """
        Xử lý sau khi thanh toán thành công - tạo ticket và cập nhật reservation
        
        LƯU Ý: Method này CHỈ được gọi SAU KHI đã validate reservations trong update_payment_status
        """
        try:
            # 0. Lấy payment để biết payment_id
            payment = self.get_payment_by_order_id(db, order_id)
            if not payment:
                raise HTTPException(status_code=404, detail=f"Payment not found for order_id: {order_id}")
            
            # Get user information
            user = db.query(Users).filter(Users.user_id == payment.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail=f"User not found for payment")

            # Get transaction
            transaction = db.query(Transaction).filter(
                Transaction.payment_id == payment.payment_id
            ).first()
            if not transaction:
                raise HTTPException(status_code=404, detail=f"Transaction not found for payment_id: {payment.payment_id}")

            # Get reservations (đã được validate ở update_payment_status)
            reservations = db.query(SeatReservations).filter(
                SeatReservations.payment_id == payment.payment_id,
                SeatReservations.status == 'pending'
            ).all()

            if not reservations:
                raise HTTPException(
                    status_code=500,
                    detail=f"CRITICAL: No pending reservations found for payment_id: {payment.payment_id}"
                )

            created_tickets = []
            reservation_ids = []

            # Sinh booking_code duy nhất cho đơn đặt vé này
            def generate_booking_code():
                now = datetime.now()
                rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                return f"BK{now.strftime('%Y%m%d')}{rand}"
            
            booking_code = generate_booking_code()

            # Thu thập thông tin để gửi email
            seats_list = []
            movie_title = 'Unknown'
            showtime_str = 'Unknown'

            for reservation in reservations:
                reservation_ids.append(reservation.reservation_id)

                # Tính giá vé chính xác
                correct_price = self.calculate_ticket_price(
                    db,
                    reservation.seat_id,
                    reservation.showtime_id
                )

                # Lấy thông tin ghế trước khi tạo QR code
                seat = db.query(Seats).filter(Seats.seat_id == reservation.seat_id).first()
                seat_code = seat.seat_code if seat else f"seat_{reservation.seat_id}"
                seats_list.append(seat_code)

                # Tạo Ticket với booking_code
                ticket_user_id = reservation.user_id or transaction.user_id or getattr(payment, 'user_id', None)
                # Chuỗi QR code payload cho từng vé (có thể tuỳ chỉnh thêm thông tin nếu muốn)
                qr_code_payload = f"Mã đặt vé: {booking_code}\nKhách hàng: {user.full_name or user.name or 'Customer'}\nPhim: {movie_title}\nSuất chiếu: {showtime_str}\nGhế: {seat_code}"

                qr = qrcode.QRCode(
                    version=1,
                    error_correction=qrcode.constants.ERROR_CORRECT_L,
                    box_size=10,
                    border=4,
                )
                qr.add_data(qr_code_payload)
                qr.make(fit=True)
                img = qr.make_image(fill_color="black", back_color="white")
                buf = BytesIO()
                img.save(buf, format="PNG")
                qr_code_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")
                db_ticket = Tickets(
                    user_id=ticket_user_id,
                    showtime_id=reservation.showtime_id,
                    seat_id=reservation.seat_id,
                    promotion_id=None,
                    price=correct_price,
                    status='confirmed',
                    transaction_id=transaction.transaction_id,
                    booking_code=booking_code,
                    qr_code=qr_code_base64
                )
                db.add(db_ticket)
                db.flush()

                # Cập nhật reservation
                reservation.status = "confirmed"
                reservation.transaction_id = transaction.transaction_id
                created_tickets.append(db_ticket.ticket_id)

                # ...đã chuyển lên trên...

                # Lấy thông tin phim/suất chiếu từ reservation đầu tiên
                if movie_title == 'Unknown' or showtime_str == 'Unknown':
                    st = db.query(Showtimes).filter(Showtimes.showtime_id == reservation.showtime_id).first()
                    if st:
                        # Lấy tên phim
                        if hasattr(st, 'movie') and getattr(st, 'movie') is not None:
                            movie_title = getattr(st.movie, 'title', 'Unknown')
                        else:
                            mv = db.query(Movies).filter(Movies.movie_id == getattr(st, 'movie_id', None)).first()
                            movie_title = mv.title if mv else 'Unknown'

                        # Lấy thời gian chiếu
                        dt = getattr(st, 'show_datetime', None)
                        if dt is not None:
                            try:
                                showtime_str = dt.strftime('%Y-%m-%d %H:%M')
                            except Exception:
                                showtime_str = str(dt)
                        else:
                            if hasattr(st, 'start_time'):
                                showtime_str = str(getattr(st, 'start_time'))
                            elif hasattr(st, 'show_time'):
                                showtime_str = str(getattr(st, 'show_time'))
                            else:
                                showtime_str = 'Unknown'

            # Cập nhật transaction
            transaction.status = TransactionStatus.success
            transaction.payment_ref_code = payment_result.transaction_id
            db.commit()

            # --- GỬI EMAIL (BỌC TRY-EXCEPT ĐỂ KHÔNG CRASH NẾU LỖI) ---
            try:
                self.send_booking_email(
                    user=user,
                    booking_code=booking_code,
                    movie_title=movie_title,
                    showtime_str=showtime_str,
                    seats_list=seats_list
                )
            except Exception as email_error:
                print(f"WARNING: Failed to send email for {booking_code}. Error: {email_error}")
                print(traceback.format_exc())
                # Không raise exception - vé đã tạo thành công

            return {
                "transaction_id": transaction.transaction_id,
                "booking_code": booking_code,
                "message": "Tickets created successfully"
            }
            
        except HTTPException:
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=str(e))

    def send_booking_email(self, user: Users, booking_code: str, movie_title: str, 
                          showtime_str: str, seats_list: list):
        """
        Hàm gửi email tách riêng - không cần db session vì chỉ gửi email
        
        Raises:
            Exception: Nếu gửi email thất bại
        """
        ticket_info = {
            'booking_id': booking_code,
            'customer_name': user.full_name or user.name or 'Customer',
            'movie_name': movie_title,
            'showtime': showtime_str,
            'seats': seats_list
        }
        
        email_service = EmailService(
            smtp_server=settings.EMAIL_HOST,
            smtp_port=settings.EMAIL_PORT,
            username=settings.EMAIL_USERNAME,
            password=settings.EMAIL_PASSWORD,
            sender_name=settings.EMAIL_SENDER_NAME
        )
        
        email_service.send_ticket_email(to_email=user.email, ticket_info=ticket_info)

    def calculate_ticket_price(self, db: Session, seat_id: int, showtime_id: int) -> int:
        """Tính giá vé dựa trên loại ghế và giá suất chiếu"""
        from app.models.seats import Seats
        from app.models.showtimes import Showtimes
        from app.models.seat_templates import SeatTypeEnum
        
        seat = db.query(Seats).filter(Seats.seat_id == seat_id).first()
        showtime = db.query(Showtimes).filter(Showtimes.showtime_id == showtime_id).first()
        
        if not seat or not showtime:
            raise HTTPException(status_code=404, detail="Seat or Showtime not found")
        
        price = float(showtime.ticket_price)
        
        # Áp dụng hệ số nhân theo loại ghế
        if seat.seat_type == SeatTypeEnum.vip:
            price *= 1.5
        elif seat.seat_type == SeatTypeEnum.couple:
            price *= 2.0
            
        return int(price)

    def get_payment_by_order_id(self, db: Session, order_id: str) -> Optional[Payment]:
        """Lấy payment theo order_id"""
        return db.query(Payment).filter(Payment.order_id == order_id).first()
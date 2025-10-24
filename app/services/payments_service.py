from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
import uuid
import random, string
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

    def create_payment(self, db: Session, request: PaymentRequest, client_ip: str,user_id: Optional[int] = None):
        order_id = str(uuid.uuid4())
        reservations = db.query(SeatReservations).filter(
            SeatReservations.session_id == request.session_id,
            SeatReservations.status == 'pending'
        ).all()
        if not reservations:
            raise ValueError("Không tìm thấy reservation hợp lệ với session_id đã cho")
        
        if user_id is None:
            raise ValueError("Người dùng chưa được xác định")
        
        # Tính tổng số tiền từ các reservation
        total_amount = 0
        for reservation in reservations:
            ticket_price = self.calculate_ticket_price(db, reservation.seat_id, reservation.showtime_id)
            total_amount += ticket_price
        
        # Chuẩn hóa payment_method về PaymentMethodEnum
        try:
            if isinstance(request.payment_method, str):
                payment_method = PaymentMethodEnum(request.payment_method)
            else:
                payment_method = PaymentMethodEnum(request.payment_method.value)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid payment_method: {request.payment_method}")
        if payment_method  == PaymentMethodEnum.VNPAY:
            payment = VNPayPayment(
                order_id=order_id,
                amount=total_amount,
                payment_method=payment_method,
                payment_status=PaymentStatusEnum.PENDING,
                order_desc=request.order_desc,
                client_ip=client_ip,
                vnp_txn_ref=order_id,
                user_id=user_id  # Thêm user_id vào đây
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
        db.commit()
        db.refresh(payment)
        
        # Gán payment_id cho các ghế đã chọn
        db.query(SeatReservations).filter(
            SeatReservations.session_id == request.session_id,
            SeatReservations.status == 'pending'
        ).update({SeatReservations.payment_id: payment.payment_id}, synchronize_session=False)
        db.commit()
        
        # Tạo transaction khởi tạo (log)
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
        db.commit()
        db.refresh(transaction)

        # Sử dụng payment_method enum đã convert (PaymentMethodEnum)
        if payment_method == PaymentMethodEnum.VNPAY:
            payment.payment_url = self.create_vnpay_url(request, client_ip, total_amount, order_id)
        elif payment_method == PaymentMethodEnum.MOMO:
            payment.payment_url = self.create_momo_url(request, client_ip) if hasattr(self, 'create_momo_url') else None
        elif payment_method == PaymentMethodEnum.CASH:
            payment.payment_url = None
            
        db.commit()
        db.refresh(payment)
        
        # Convert enum to schema enum for response
        response_payment_method = PaymentMethod(payment.payment_method.value)
        response_payment_status = PaymentStatus(payment.payment_status.value)
        
        return PaymentResponse(
            payment_url=payment.payment_url,
            order_id=order_id,
            amount=payment.amount,
            payment_method=response_payment_method,
            payment_status=response_payment_status
)

    """Tạo URL thanh toán VNPay và trả về chuỗi URL."""
    def create_vnpay_url(self, payment_request: PaymentRequest, client_ip: str, amount: int, order_id : str) -> str:
        try:
            # Set VNPay request data
            self.vnpay.set_request_data(
                vnp_Version='2.1.0',
                vnp_Command='pay',
                vnp_TmnCode=settings.VNPAY_TMN_CODE,
                vnp_Amount=amount * 100,
                vnp_CurrCode='VND',
                vnp_TxnRef=order_id,
                vnp_OrderInfo=payment_request.order_desc,
                vnp_OrderType='other',
                vnp_Locale=payment_request.language,
                vnp_CreateDate=datetime.now().strftime('%Y%m%d%H%M%S'),
                vnp_IpAddr=client_ip,
                vnp_ReturnUrl=settings.VNPAY_RETURN_URL
            )
            
            # Generate payment URL
            payment_url = self.vnpay.get_payment_url(
                settings.VNPAY_PAYMENT_URL,
                settings.VNPAY_HASH_SECRET_KEY
            )
            
            return payment_url
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create payment URL: {str(e)}")
    
    def handle_vnpay_callback(self,db: Session, callback_data: Dict[str, Any]) -> PaymentResult:
        """Xử lý callback từ VNPay"""
        try:
            # Set response data for validation
            self.vnpay.set_response_data(callback_data)
            
            # Validate signature
            is_valid = self.vnpay.validate_response(settings.VNPAY_HASH_SECRET_KEY)
            
            if not is_valid:
                return PaymentResult(
                    success=False,
                    order_id=callback_data.get('vnp_TxnRef', ''),
                    message="Invalid signature",
                    payment_method=PaymentMethod.VNPAY,
                    payment_status=PaymentStatus.FAILED
                )
            
            order_id = callback_data.get('vnp_TxnRef')
            amount = int(callback_data.get('vnp_Amount', 0)) // 100
            response_code = callback_data.get('vnp_ResponseCode')
            transaction_id = callback_data.get('vnp_TransactionNo')
            bank_code = callback_data.get('vnp_BankCode')
            card_type = callback_data.get('vnp_CardType')
            pay_date_str = callback_data.get('vnp_PayDate')
            pay_date = None
            if pay_date_str:
                try:
                    pay_date = datetime.strptime(pay_date_str, "%Y%m%d%H%M%S")
                except ValueError:
                    pay_date = None  # hoặc log lỗi nếu cần
                
            # Check payment status
            if response_code == '00':
                status_schema = PaymentStatus.SUCCESS
                status_model = PaymentStatusEnum.SUCCESS
                message = "Payment successful"
                success = True
            else:
                status_schema = PaymentStatus.FAILED
                status_model = PaymentStatusEnum.FAILED
                message = f"Payment failed with code: {response_code}"
                success = False
            # Cập nhật database
            payment = db.query(Payment).filter_by(order_id=order_id).first()
            if not payment:
                raise HTTPException(status_code=404, detail=f"Payment record {order_id} not found")

            payment.vnp_transaction_no = transaction_id
            payment.amount = amount
            payment.payment_status = status_model
            db.commit()

            # Bước 1: Lấy payment_id từ Payment
            vnpay_payment = db.query(VNPayPayment).filter(
                VNPayPayment.order_id == order_id
            ).first()
            if not vnpay_payment:
                raise HTTPException(status_code=404, detail="Payment not found")

           # Update VNPayPayment với đầy đủ thông tin
            vnpay_payment.vnp_transaction_no = transaction_id
            vnpay_payment.vnp_response_code = response_code
            vnpay_payment.vnp_bank_code = bank_code
            vnpay_payment.vnp_card_type = card_type
            vnpay_payment.vnp_pay_date = pay_date
            vnpay_payment.amount = amount
            vnpay_payment.payment_status = status_model
            
            db.commit()
            db.refresh(vnpay_payment)

            return PaymentResult(
                success=success,
                order_id=order_id,
                transaction_id=transaction_id,
                amount=amount,
                message=message,
                payment_method=PaymentMethod.VNPAY,
                payment_status=status_schema
            )
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to process callback: {str(e)}")
    
    
    def update_payment_status(
        self,
        db: Session,
        order_id: str,
        payment_result: PaymentResult
    ) -> Dict[str, Any]:
        """Cập nhật trạng thái thanh toán và xử lý logic tiếp theo"""
        try:
            # 1. Tìm payment record
            payment = self.get_payment_by_order_id(db, order_id)
            if not payment:
                raise HTTPException(status_code=404, detail=f"Payment not found for order_id: {order_id}")
            

            payment.payment_status = PaymentStatusEnum.SUCCESS if payment_result.success else PaymentStatusEnum.FAILED
            db.commit()

            # Nếu là thanh toán VNPay, cập nhật trường vnp_transaction_no ở VNPayPayment
            vnpay_payment = db.query(VNPayPayment).filter_by(payment_id=payment.payment_id).first()
            if vnpay_payment:
                vnpay_payment.vnp_transaction_no = payment_result.transaction_id
                db.commit()
            
            
            # 3. Nếu thanh toán thành công, xử lý tạo transaction và ticket
            if payment_result.success:
                success_result = self.process_successful_payment(db, order_id, payment_result)
                
                # 4. Sau khi tạo transaction thành công, mới cập nhật payment.transaction_id
                if success_result.get("transaction_id"):
                    payment.transaction_id = success_result["transaction_id"]
                    db.commit()
                
                return {
                    "status": "success",
                    "payment_status": payment.payment_status.value,
                    "order_id": order_id,
                    "vnp_transaction_no": payment.vnp_transaction_no,
                    **success_result
                }
            else:
                return {
                    "status": "failed",
                    "payment_status": payment.payment_status.value,
                    "order_id": order_id,
                    "vnp_transaction_no": payment.vnp_transaction_no,
                    "message": "Payment failed"
                }
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update payment status: {str(e)}")
    
    def get_payment_by_order_id(self, db: Session, order_id: str) -> Optional[Payment]:
        """Lấy thông tin thanh toán theo order ID"""
        return db.query(Payment).filter(Payment.order_id == order_id).first()
    
        """Xử lý sau khi thanh toán thành công - tạo ticket và cập nhật reservation"""

    def process_successful_payment(self, db: Session, order_id: str, payment_result: PaymentResult) -> Dict[str, Any]:
        try:
            # 0. Lấy payment để biết payment_id
            payment = self.get_payment_by_order_id(db, order_id)
            if not payment:
                raise HTTPException(status_code=404, detail=f"Payment not found for order_id: {order_id}")
            # Get user information
            user = db.query(Users).filter(Users.user_id == payment.user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail=f"User not found for payment")

            transaction = db.query(Transaction).filter(
                Transaction.payment_id == payment.payment_id
            ).first()
            if not transaction:
                raise HTTPException(status_code=404, detail=f"Transaction not found for payment_id: {payment.payment_id}")

            reservations = db.query(SeatReservations).filter(
                SeatReservations.payment_id == payment.payment_id,
                SeatReservations.status == 'pending'
            ).all()

            if not reservations:
                raise HTTPException(status_code=404, detail=f"No pending reservations found for payment_id: {payment.payment_id}")

            created_tickets = []
            reservation_ids = []

            # Sinh booking_code duy nhất cho đơn đặt vé này
            def generate_booking_code():
                # Ví dụ: BK20251021A1
                now = datetime.now()
                rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=2))
                return f"BK{now.strftime('%Y%m%d')}{rand}"
            booking_code = generate_booking_code()

            for reservation in reservations:
                reservation_ids.append(reservation.reservation_id)

                # Kiểm tra thời hạn reservation
                current_time = datetime.utcnow()
                expires_at = reservation.expires_at
                if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo:
                    expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)

                if expires_at < current_time:
                    raise HTTPException(status_code=400, detail=f"Reservation {reservation.reservation_id} has expired")

                # Tính giá vé
                correct_price = self.calculate_ticket_price(
                    db,
                    reservation.seat_id,
                    reservation.showtime_id
                )

                # Tạo Ticket với booking_code
                # Determine user_id: prefer reservation.user_id, then transaction.user_id, then payment.user_id
                ticket_user_id = reservation.user_id or transaction.user_id or getattr(payment, 'user_id', None)
                db_ticket = Tickets(
                    user_id=ticket_user_id,
                    showtime_id=reservation.showtime_id,
                    seat_id=reservation.seat_id,
                    promotion_id=None,
                    price=correct_price,
                    status='confirmed',
                    transaction_id=transaction.transaction_id,
                    booking_code=booking_code
                )
                db.add(db_ticket)
                db.flush() # Lấy ticket_id

                # Cập nhật reservation
                reservation.status = "confirmed"
                reservation.transaction_id = transaction.transaction_id
                created_tickets.append(db_ticket.ticket_id)

            transaction.status = TransactionStatus.success
            transaction.payment_ref_code = payment_result.transaction_id
            db.commit()

            # Gửi 1 email tổng hợp cho toàn bộ booking (nhiều ghế trong cùng 1 email)
            seats_list = []
            movie_title = 'Unknown'
            showtime_str = 'Unknown'

            # gather seat codes and determine movie/showtime from first reservation/ticket
            for reservation in reservations:
                seat = db.query(Seats).filter(Seats.seat_id == reservation.seat_id).first()
                seat_code = seat.seat_code if seat else f"seat_{reservation.seat_id}"
                seats_list.append(seat_code)

                # grab showtime/movie from first
                if movie_title == 'Unknown' or showtime_str == 'Unknown':
                    st = db.query(Showtimes).filter(Showtimes.showtime_id == reservation.showtime_id).first()
                    if st:
                        if hasattr(st, 'movie') and getattr(st, 'movie') is not None:
                            movie_title = getattr(st.movie, 'title', 'Unknown')
                        else:
                            mv = db.query(Movies).filter(Movies.movie_id == getattr(st, 'movie_id', None)).first()
                            movie_title = mv.title if mv else 'Unknown'

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

            ticket_info = {
                'booking_id': booking_code,
                'customer_name': getattr(user, 'full_name', getattr(user, 'name', 'Customer')),
                'movie_name': movie_title,
                'showtime': showtime_str,
                'seats': seats_list
            }

            smtp_host = getattr(settings, 'EMAIL_HOST', getattr(settings, 'SMTP_SERVER', None))
            smtp_port = getattr(settings, 'EMAIL_PORT', getattr(settings, 'SMTP_PORT', None))
            smtp_user = getattr(settings, 'EMAIL_USERNAME', getattr(settings, 'SMTP_USERNAME', None))
            smtp_pass = getattr(settings, 'EMAIL_PASSWORD', getattr(settings, 'SMTP_PASSWORD', None))
            sender_name = getattr(settings, 'EMAIL_SENDER_NAME', 'CinePlus')

            email_service = EmailService(
                smtp_server=smtp_host,
                smtp_port=smtp_port,
                username=smtp_user,
                password=smtp_pass,
                sender_name=sender_name
            )

            email_sent = email_service.send_ticket_email(
                to_email=getattr(user, 'email', None),
                ticket_info=ticket_info
            )

            if not email_sent:
                print(f"Warning: Failed to send booking email for booking {booking_code}")

            return {
                "transaction_id": transaction.transaction_id,
                "vnp_transaction_no": payment_result.transaction_id,
                "status": "success",
                "message": "Payment processed successfully and tickets created",
                "booking_code": booking_code
            }

        except HTTPException:
            # propagate HTTPException (đã chuẩn bị message cho user)
            db.rollback()
            raise
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to process successful payment: {str(e)}")
 
        # Thêm method calculate_ticket_price bị thiếu
    def calculate_ticket_price(self, db: Session, seat_id: int, showtime_id: int) -> int:
        """Tính giá vé dựa trên loại ghế và suất chiếu"""
        try:
            # Import ở đây để tránh circular import
            from app.models.seats import Seats
            from app.models.showtimes import Showtimes
            from app.models.seat_templates import SeatTypeEnum
            
            # Lấy thông tin ghế và loại ghế
            seat = db.query(Seats).filter(Seats.seat_id == seat_id).first()
            if not seat:
                raise HTTPException(status_code=404, detail=f"Seat {seat_id} not found")
            
            # Lấy thông tin suất chiếu để có giá cơ bản
            showtime = db.query(Showtimes).filter(Showtimes.showtime_id == showtime_id).first()  
            if not showtime:
                raise HTTPException(status_code=404, detail=f"Showtime {showtime_id} not found")
            
            # Lấy giá cơ bản từ showtime (sử dụng ticket_price)
            base_price = float(showtime.ticket_price)
            
            # Tính phụ phí theo loại ghế (tương tự logic trong tickets_service)
            if seat.seat_type == SeatTypeEnum.vip:
                base_price *= 1.5  # VIP tăng 50%
            elif seat.seat_type == SeatTypeEnum.couple:
                base_price *= 2.0  # Couple tăng 100%
            # regular giữ nguyên giá base
            
            return int(base_price)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to calculate ticket price: {str(e)}")
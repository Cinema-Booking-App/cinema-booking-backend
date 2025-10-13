from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime, timezone
import uuid

from app.core.config import settings
from app.payments.vnpay import VNPay
from app.models.payments import Payment, PaymentStatusEnum, PaymentMethodEnum
from app.models.seat_reservations import SeatReservations
from app.models.tickets import Tickets
from app.models.transactions import Transaction, TransactionTickets, TransactionStatus
from app.schemas.payments import (
    PaymentRequest,
    PaymentResponse,
    VNPayCallback,
    PaymentResult,
    PaymentStatus,
    PaymentMethod
)


class PaymentService:
    """Service xử lý thanh toán"""
    
    def __init__(self):
        self.vnpay = VNPay()

    def create_payment(self, db: Session, request: PaymentRequest, client_ip: str):
        order_id = str(uuid.uuid4())
        reservations = db.query(SeatReservations).filter(
            SeatReservations.session_id == request.session_id,
            SeatReservations.status == 'pending'
        ).all()
        if not reservations:
            raise ValueError("Không tìm thấy reservation hợp lệ với session_id đã cho")
        # Tính tổng số tiền từ các reservation
        total_amount = 0
        for reservation in reservations:
            ticket_price = self.calculate_ticket_price(db, reservation.seat_id, reservation.showtime_id)
            total_amount += ticket_price
        
        # Đảm bảo payment_method là Enum
        payment_method = request.payment_method
        if isinstance(payment_method, str):
            try:
                payment_method = PaymentMethodEnum(payment_method)
            except Exception:
                raise HTTPException(status_code=400, detail=f"Invalid payment_method: {payment_method}")

        payment = Payment(
            order_id=order_id,
            amount=total_amount,
            payment_method=payment_method,
            payment_status=PaymentStatusEnum.PENDING,
            order_desc=request.order_desc,
            client_ip=client_ip
        )
        db.add(payment)
        db.commit()
        
        # Gán payment_id cho các ghế đã chọn
        db.query(SeatReservations).filter(
            SeatReservations.session_id == request.session_id,
            SeatReservations.status == 'pending'
        ).update({SeatReservations.payment_id: payment.payment_id}, synchronize_session=False)
        db.commit()
        
        # Tạo transaction khởi tạo (log)
        transaction = Transaction(
            user_id=None,
            staff_user_id=None,
            promotion_id=None,
            total_amount=total_amount,
            payment_method=payment_method.value,
            status=TransactionStatus.pending,
            transaction_time=datetime.utcnow()
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        if request.payment_method == PaymentMethod.VNPAY:
            payment.payment_url = self.create_vnpay_url(request, client_ip, total_amount, order_id)
        elif request.payment_method == "MOMO":
            payment.payment_url = self.create_momo_url(request, client_ip)
        elif request.payment_method == "CASH":
            payment.payment_url = None
            
        db.commit()
#         db.refresh(payment)
        return PaymentResponse(
            payment_url=payment.payment_url,
            order_id=order_id,
            amount=payment.amount,
            payment_method=payment.payment_method,
            payment_status=payment.payment_status
)

    def create_vnpay_url(self, payment_request: PaymentRequest, client_ip: str, amount: int, order_id : str) -> PaymentResponse:
        """Tạo URL thanh toán VNPay"""
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
    
    def handle_vnpay_callback(self, callback_data: Dict[str, Any]) -> PaymentResult:
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
            
            # Check payment status
            if response_code == '00':
                status = PaymentStatus.SUCCESS
                message = "Payment successful"
                success = True
            else:
                status = PaymentStatus.FAILED
                message = f"Payment failed with code: {response_code}"
                success = False
            
            return PaymentResult(
                success=success,
                order_id=order_id,
                transaction_id=transaction_id,
                amount=amount,
                message=message,
                payment_method=PaymentMethod.VNPAY,
                payment_status=status
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
            
            # 2. Sửa lỗi: dùng transaction_id thay vì transaction_no
            payment.payment_status = PaymentStatusEnum.SUCCESS if payment_result.success else PaymentStatusEnum.FAILED
            payment.vnp_transaction_no = payment_result.transaction_id  # Sửa từ transaction_no thành transaction_id
            
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
    
    def create_payment_from_reservation(
        self, 
        db: Session, 
        reservation_id: int,
        client_ip: str
    ) -> Dict[str, Any]:
        """Tạo thanh toán từ reservation với giá chính xác"""
        try:
            # Import ở đây để tránh circular import
            from app.models.seat_reservations import SeatReservations
            from app.models.showtimes import Showtimes
            from app.models.seats import Seats
            
            # Lấy thông tin reservation
            reservation = db.query(SeatReservations).filter(
                SeatReservations.reservation_id == reservation_id
            ).first()
            
            if not reservation:
                raise HTTPException(status_code=404, detail="Reservation not found")
            
            if reservation.status != "pending":
                raise HTTPException(status_code=400, detail="Reservation is not in pending status")
            
            # Kiểm tra reservation còn hạn
            current_time = datetime.utcnow()
            expires_at = reservation.expires_at
            
            # Xử lý timezone
            if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo:
                expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
            
            if expires_at < current_time:
                raise HTTPException(status_code=400, detail="Reservation has expired")
            
            # Lấy thông tin để tính giá vé
            showtime = db.query(Showtimes).filter(
                Showtimes.showtime_id == reservation.showtime_id
            ).first()
            
            seat = db.query(Seats).filter(
                Seats.seat_id == reservation.seat_id
            ).first()
            
            if not showtime or not seat:
                raise HTTPException(status_code=404, detail="Showtime or seat not found")
            
            # Tính giá vé chính xác theo loại ghế
            ticket_price = self.calculate_ticket_price(
                db, 
                reservation.seat_id, 
                reservation.showtime_id
            )
            
            # Tạo order description
            order_desc = f"Thanh toan ve xem phim - Ghe {seat.seat_code} - Suat {showtime.showtime_id}"
            
            # Tạo PaymentRequest
            payment_request = PaymentRequest(
                order_id=str(reservation_id),
                amount=ticket_price,
                order_desc=order_desc,
                language="vn"
            )
            
            # Tạo bản ghi thanh toán
            self.create_payment_record(
                db=db,
                order_id=payment_request.order_id,
                amount=payment_request.amount,
                payment_method="vnpay",
                order_desc=payment_request.order_desc,
                client_ip=client_ip,
                user_id=reservation.user_id
            )
            
            # Tạo URL thanh toán VNPay
            payment_response = self.create_vnpay_payment_url(payment_request, client_ip)
            
            return {
                "payment_url": payment_response.payment_url,
                "order_id": payment_response.order_id,
                "reservation_id": reservation_id,
                "amount": ticket_price,
                "seat_code": seat.seat_code,
                "showtime_id": showtime.showtime_id,
                "expires_at": reservation.expires_at,
                "message": "Payment URL created successfully"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to create payment from reservation: {str(e)}")
    
    def process_successful_payment(self, db: Session, order_id: str, payment_result: PaymentResult) -> Dict[str, Any]:
        """Xử lý sau khi thanh toán thành công - tạo ticket và cập nhật reservation"""
        try:
            # 1. Tìm reservation theo order_id
            reservation = db.query(SeatReservations).filter(
                SeatReservations.reservation_id == int(order_id)
            ).first()
            
            if not reservation:
                raise HTTPException(status_code=404, detail=f"Reservation not found for order_id: {order_id}")
            
            # 2. Kiểm tra reservation
            if reservation.status not in ["pending"]:
                raise HTTPException(status_code=400, detail=f"Reservation {order_id} is not in pending status")
            
            # 3. Sửa lỗi timezone - chuyển tất cả về UTC
            current_time = datetime.utcnow()
            expires_at = reservation.expires_at
            
            # Chuyển expires_at về UTC nếu cần
            if hasattr(expires_at, 'tzinfo') and expires_at.tzinfo:
                expires_at = expires_at.astimezone(timezone.utc).replace(tzinfo=None)
            
            if expires_at < current_time:
                raise HTTPException(status_code=400, detail=f"Reservation {order_id} has expired")
            
            # 4. Tính giá vé chính xác
            correct_price = self.calculate_ticket_price(
                db, 
                reservation.seat_id, 
                reservation.showtime_id
            )
            
            # 5. Tạo Transaction
            db_transaction = Transaction(
                user_id=reservation.user_id,
                staff_user_id=reservation.user_id,
                promotion_id=None,
                total_amount=correct_price,
                payment_method='vnpay',
                status=TransactionStatus.success,
                transaction_time=datetime.utcnow()  # Sử dụng UTC
            )
            db.add(db_transaction)
            db.flush()
            
            # 6. Tạo Ticket
            db_ticket = Tickets(
                user_id=reservation.user_id,
                showtime_id=reservation.showtime_id,
                seat_id=reservation.seat_id,
                promotion_id=None,
                price=correct_price,
                status='confirmed'
            )
            db.add(db_ticket)
            db.flush()
            
            # 7. Liên kết Transaction và Ticket
            db_transaction_ticket = TransactionTickets(
                transaction_id=db_transaction.transaction_id,
                ticket_id=db_ticket.ticket_id
            )
            db.add(db_transaction_ticket)
            
            # 8. Cập nhật reservation
            reservation.status = "confirmed"
            reservation.transaction_id = db_transaction.transaction_id
            
            # 9. Commit tất cả
            db.commit()
            db.refresh(db_transaction)
            db.refresh(db_ticket)
            db.refresh(reservation)
            
            return {
                "reservation_id": reservation.reservation_id,
                "transaction_id": db_transaction.transaction_id,
                "ticket_id": db_ticket.ticket_id,
                "ticket_price": correct_price,
                "vnp_transaction_no": payment_result.transaction_id,
                "status": "success",
                "message": "Payment processed successfully and ticket created"
            }
            
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
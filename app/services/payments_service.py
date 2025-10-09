from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime

from app.core.config import settings
from app.payments.vnpay import VNPay
from app.models.payments import Payment, PaymentStatusEnum, PaymentMethodEnum
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
    
    def create_vnpay_payment_url(self, payment_request: PaymentRequest, client_ip: str) -> PaymentResponse:
        """Tạo URL thanh toán VNPay"""
        try:
            # Set VNPay request data
            self.vnpay.set_request_data(
                vnp_Version='2.1.0',
                vnp_Command='pay',
                vnp_TmnCode=settings.VNPAY_TMN_CODE,
                vnp_Amount=payment_request.amount * 100,  # VNPay yêu cầu amount * 100
                vnp_CurrCode='VND',
                vnp_TxnRef=payment_request.order_id,
                vnp_OrderInfo=payment_request.order_desc,
                vnp_OrderType='other',
                vnp_Locale=payment_request.language,
                vnp_CreateDate=datetime.now().strftime('%Y%m%d%H%M%S'),
                vnp_IpAddr=client_ip,
                vnp_ReturnUrl=settings.VNPAY_RETURN_URL
            )
            
            if payment_request.bank_code:
                self.vnpay.set_request_data(vnp_BankCode=payment_request.bank_code)
            
            # Generate payment URL
            payment_url = self.vnpay.get_payment_url(
                settings.VNPAY_PAYMENT_URL,
                settings.VNPAY_HASH_SECRET_KEY
            )
            
            return PaymentResponse(
                payment_url=payment_url,
                order_id=payment_request.order_id
            )
            
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
    
    def create_payment_record(
        self, 
        db: Session,
        order_id: str,
        amount: int,
        payment_method: str,
        order_desc: str,
        client_ip: str,
        user_id: Optional[int] = None
    ) -> Payment:
        """Tạo bản ghi thanh toán trong database"""
        try:
            payment = Payment(
                order_id=order_id,
                amount=amount,
                payment_method=PaymentMethodEnum(payment_method),
                payment_status=PaymentStatusEnum.PENDING,
                order_desc=order_desc,
                client_ip=client_ip
            )
            
            db.add(payment)
            db.commit()
            db.refresh(payment)
            
            return payment
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to create payment record: {str(e)}")
    
    def update_payment_status(
        self,
        db: Session,
        order_id: str,
        payment_result: PaymentResult
    ) -> Optional[Payment]:
        """Cập nhật trạng thái thanh toán"""
        try:
            payment = db.query(Payment).filter(Payment.order_id == order_id).first()
            
            if not payment:
                return None
            
            # Update payment status
            if payment_result.payment_status == PaymentStatus.SUCCESS:
                payment.payment_status = PaymentStatusEnum.SUCCESS
            elif payment_result.payment_status == PaymentStatus.FAILED:
                payment.payment_status = PaymentStatusEnum.FAILED
            elif payment_result.payment_status == PaymentStatus.CANCELLED:
                payment.payment_status = PaymentStatusEnum.CANCELLED
            
            # Update VNPay specific fields
            if payment_result.transaction_id:
                payment.transaction_id = payment_result.transaction_id
                payment.vnp_transaction_no = payment_result.transaction_id
            
            db.commit()
            db.refresh(payment)
            
            return payment
            
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to update payment status: {str(e)}")
    
    def get_payment_by_order_id(self, db: Session, order_id: str) -> Optional[Payment]:
        """Lấy thông tin thanh toán theo order ID"""
        return db.query(Payment).filter(Payment.order_id == order_id).first()
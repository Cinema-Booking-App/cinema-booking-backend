from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.payments_service import PaymentService
from app.schemas.payments import PaymentRequest
from app.utils.response import success_response
from app.core.security import get_current_active_user
from app.models.users import Users
from typing import Optional
from datetime import datetime
from app.models.payments import VNPayPayment, PaymentStatusEnum
router = APIRouter()
payment_service = PaymentService()

# Tạo thanh toán
@router.post("/create")
async def create_vnpay_payment(
    payment_request: PaymentRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_active_user),
):
    try:
        client_ip = request.client.host
        payment = payment_service.create_payment(db, payment_request, client_ip, user_id=current_user.user_id)
        return success_response(payment)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment: {e}")


@router.get("/vnpay/return")
async def vnpay_return_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle VNPay return callback (when user returns from VNPay)
    """
    try:
        # Get query parameters
        query_params = dict(request.query_params)
        print("🔍 VNPay Return Params:", query_params)

        # Process return callback
        payment_result = payment_service.handle_vnpay_callback(db, query_params)
        print("🔍 Payment Result:", payment_result)

        # Update payment status and process ticket creation
        result = payment_service.update_payment_status(db, payment_result.order_id, payment_result)
        print("🔍 Update Payment Result:", result)
        print("========== END VNPay RETURN ==============")
        return success_response(result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/vnpay/ipn")
async def vnpay_ipn_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle VNPay IPN (Instant Payment Notification) callback
    This endpoint is called by VNPay to notify payment status
    """
    try:
        # Get query parameters (VNPay sends data as query parameters)
        query_params = dict(request.query_params)
     
        payment_result = payment_service.handle_vnpay_callback(db, query_params)
        
        # Update payment status and process ticket creation
        result = payment_service.update_payment_status(db, payment_result.order_id, payment_result)
        
        # Return response to VNPay
        if payment_result.success:
            return JSONResponse(
                content={'RspCode': '00', 'Message': 'Confirm Success'},
                status_code=200
            )
        else:
            return JSONResponse(
                content={'RspCode': '99', 'Message': 'Unknow error'},
                status_code=200
            )
            
    except HTTPException:
        raise
    except Exception as e:
        # Always return success to VNPay to avoid retry
        return JSONResponse(
            content={'RspCode': '99', 'Message': 'Unknow error'},
            status_code=200
        )


# TODO: Implement query và refund endpoints sau khi cần thiết


@router.get("/payment-status/{order_id}")
async def get_payment_status(
    order_id: str,
    db: Session = Depends(get_db)
):
    """
    Get payment status for an order
    """
    try:
        # Get payment status from database
        payment = payment_service.get_payment_by_order_id(db, order_id)
        
        if not payment:
            raise HTTPException(status_code=404, detail="Payment not found")
        
        return {
            "order_id": order_id,
            "status": payment.payment_status.value,
            "amount": payment.amount,
            "payment_method": payment.payment_method.value,
            "transaction_id": payment.transaction_id,
            "created_at": payment.created_at,
            "updated_at": payment.updated_at,
            "message": "Payment status retrieved successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/vnpay/history")
async def vnpay_history(
    page: int = 1,
    limit: int = 50,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    order_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Users = Depends(get_current_active_user),
):
    """
    Get paginated VNPay payment history from DB. Non-admin users only see their own records.
    """
    try:
        # Authorization: determine if current user is admin by role name
        is_admin = False
        try:
            is_admin = any((r.role_name or '').lower() == 'admin' for r in getattr(current_user, 'roles', []) )
        except Exception:
            is_admin = False

        # Non-admins can only view their own payments
        if user_id and not is_admin and user_id != current_user.user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        query = db.query(VNPayPayment)

        # apply ownership restriction for non-admins
        if not is_admin:
            query = query.filter(VNPayPayment.user_id == current_user.user_id)
        else:
            if user_id:
                query = query.filter(VNPayPayment.user_id == user_id)

        if order_id:
            query = query.filter(VNPayPayment.order_id.ilike(f"%{order_id}%"))

        if status:
            # Expect status like SUCCESS / FAILED / PENDING
            try:
                status_enum = PaymentStatusEnum[status]
                query = query.filter(VNPayPayment.payment_status == status_enum)
            except KeyError:
                raise HTTPException(status_code=400, detail="Invalid status")

        # date filters: try parse ISO strings and filter by vnp_pay_date if present, else created_at
        def parse_dt(s: Optional[str]):
            if not s:
                return None
            try:
                return datetime.fromisoformat(s)
            except Exception:
                return None

        start_dt = parse_dt(start_date)
        end_dt = parse_dt(end_date)
        if start_dt:
            # vnp_pay_date stored as string in model; try compare on created_at fallback
            try:
                query = query.filter(VNPayPayment.vnp_pay_date >= start_dt)
            except Exception:
                query = query.filter(VNPayPayment.created_at >= start_dt)
        if end_dt:
            try:
                query = query.filter(VNPayPayment.vnp_pay_date <= end_dt)
            except Exception:
                query = query.filter(VNPayPayment.created_at <= end_dt)

        total = query.count()
        # enforce sensible limits
        if limit <= 0:
            limit = 50
        if limit > 500:
            limit = 500

        items = query.order_by(VNPayPayment.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

        # Map items to serializable dicts
        result_items = []
        for it in items:
            # VNPayPayment fields
            result_items.append({
                'payment_id': getattr(it, 'payment_id', None),
                'order_id': getattr(it, 'order_id', None),
                'vnp_txn_ref': getattr(it, 'vnp_txn_ref', None),
                'vnp_transaction_no': getattr(it, 'vnp_transaction_no', None),
                'vnp_bank_code': getattr(it, 'vnp_bank_code', None),
                'vnp_card_type': getattr(it, 'vnp_card_type', None),
                'vnp_pay_date': getattr(it, 'vnp_pay_date', None),
                'vnp_response_code': getattr(it, 'vnp_response_code', None),
                'amount': getattr(it, 'amount', None),
                'payment_status': getattr(getattr(it, 'payment_status', None), 'value', None),
                'user_id': getattr(it, 'user_id', None),
                'created_at': getattr(it, 'created_at', None),
                'updated_at': getattr(it, 'updated_at', None),
            })

        response = {
            'items': result_items,
            'page': page,
            'limit': limit,
            'total': total,
            'total_pages': (total + limit - 1) // limit if total and limit else 0
        }

        return success_response(response)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# API endpoints đã được đơn giản hóa và tối ưu cho MVP
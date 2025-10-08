import hashlib
import hmac
import time
from urllib.parse import urlencode
from typing import Dict
from fastapi import HTTPException
from ..schemas.models import PaymentResponse, ReturnResponse, IPNResponse

class VNPayService:
    # Danh sách ngân hàng được VNPay hỗ trợ
    SUPPORTED_BANKS = {
        "NCB": "Ngân hàng NCB",
        "AGRIBANK": "Ngân hàng Agribank", 
        "SCB": "Ngân hàng SCB",
        "SACOMBANK": "Ngân hàng SacomBank",
        "EXIMBANK": "Ngân hàng EximBank",
        "MSBANK": "Ngân hàng MS",
        "NAMABANK": "Ngân hàng NamA",
        "VNMART": "Ví điện tử VnMart",
        "VIETINBANK": "Ngân hàng Vietinbank",
        "VNBANK": "Ngân hàng VietinBank",  # Alias cho VietinBank
        "VIETCOMBANK": "Ngân hàng VCB",
        "HDBANK": "Ngân hàng HDBank",
        "DONGABANK": "Ngân hàng Dong A",
        "TPBANK": "Ngân hàng TPBank",
        "OJB": "Ngân hàng OceanBank",
        "BIDV": "Ngân hàng BIDV",
        "TECHCOMBANK": "Ngân hàng Techcombank",
        "VPBANK": "Ngân hàng VPBank",
        "MBBANK": "Ngân hàng MB",
        "ACB": "Ngân hàng ACB",
        "OCB": "Ngân hàng OCB",
        "IVB": "Ngân hàng IVB",
        "VNPAYQR": "VNPay QR",  # VNPay QR Code
        "VISA": "Thanh toán qua VISA/MASTER",
        "MASTERCARD": "Thanh toán qua MasterCard",
        "JCB": "Thanh toán qua JCB",
        "UPI": "Thanh toán UPI",
        "VNPAY": "Ví VNPay"
    }

    def __init__(self, tmn_code: str, hash_secret: str, endpoint: str):
        self.tmn_code = tmn_code
        self.hash_secret = hash_secret
        self.endpoint = endpoint

    def get_supported_banks(self) -> Dict:
        """Lấy danh sách ngân hàng được hỗ trợ."""
        return self.SUPPORTED_BANKS

    def create_payment_url(self, request: Dict, return_url: str) -> PaymentResponse:
        """Tạo URL thanh toán VNPay."""
        try:
            # Validate bank code nếu có
            bank_code = request.get("bank_code", "").strip().upper()
            if bank_code and bank_code not in self.SUPPORTED_BANKS:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Ngân hàng thanh toán không được hỗ trợ. Mã ngân hàng: {bank_code}. "
                           f"Các ngân hàng hỗ trợ: {', '.join(self.SUPPORTED_BANKS.keys())}"
                )
        
            # Chỉ validate nếu bank_code KHÔNG RỖNG
            if bank_code and bank_code not in self.SUPPORTED_BANKS:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Bank code không hợp lệ: {bank_code}"
                )
            # Debug logging
            print(f"Creating payment with TMN_CODE: {self.tmn_code}")
            print(f"Bank code: {bank_code if bank_code else 'None (all banks)'}")
            print(f"Endpoint: {self.endpoint}")

            params = {
                "vnp_Version": "2.1.0",
                "vnp_Command": "pay",
                "vnp_TmnCode": self.tmn_code,
                "vnp_Amount": request["amount"],
                "vnp_CurrCode": "VND",
                "vnp_TxnRef": request["order_id"],
                "vnp_OrderInfo": request["order_info"],
                "vnp_OrderType": "other",
                "vnp_Locale": request.get("locale", "vn"),
                "vnp_ReturnUrl": return_url,
                "vnp_IpAddr": request.get("ip_addr", "127.0.0.1"),
                "vnp_CreateDate": time.strftime("%Y%m%d%H%M%S"),
                "vnp_ExpireDate": time.strftime("%Y%m%d%H%M%S", time.localtime(time.time() + 15 * 60)),
            }
            # Thêm bank code nếu có và đã được validate
            if bank_code:
                params["vnp_BankCode"] = bank_code

            # Tạo chữ ký HMAC-SHA512 theo chuẩn VNPay
            querystring = urlencode(sorted(params.items()))
            secure_hash = hmac.new(
                self.hash_secret.encode('utf-8'),
                querystring.encode('utf-8'),
                hashlib.sha512
            ).hexdigest()
            params["vnp_SecureHash"] = secure_hash

            payment_url = f"{self.endpoint}?{urlencode(params)}"
            return PaymentResponse(
                success=True,
                message="Tạo URL thanh toán thành công",
                pay_url=payment_url,
                order_id=request["order_id"]
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Lỗi tạo URL thanh toán: {str(e)}")

    def verify_return(self, params: Dict) -> ReturnResponse:
        """Xác thực chữ ký và xử lý phản hồi từ Return URL."""
        # Tạo bản copy để không thay đổi dict gốc
        params_copy = params.copy()
        secure_hash = params_copy.pop("vnp_SecureHash", None)
        
        # Debug logging
        print(f"Verifying return with params: {params_copy}")
        print(f"Received secure hash: {secure_hash}")
        
        # Tạo query string theo thứ tự alphabet (VNPay yêu cầu)
        # VNPay sử dụng standard URL encoding
        querystring = urlencode(sorted(params_copy.items()))
        print(f"Query string for verification: {querystring}")
        
        expected_hash = hmac.new(
            self.hash_secret.encode('utf-8'),
            querystring.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        print(f"Expected hash: {expected_hash}")

        if secure_hash != expected_hash:
            raise HTTPException(status_code=400, detail="Chữ ký không hợp lệ")

        response_code = params.get("vnp_ResponseCode")
        transaction_status = params.get("vnp_TransactionStatus")
        order_id = params.get("vnp_TxnRef")
        amount = int(params.get("vnp_Amount", 0)) / 100

        # Kiểm tra transaction status trước
        if transaction_status == "02":
            return ReturnResponse(
                status="failed", 
                message="Giao dịch thất bại hoặc bị hủy",
                order_id=order_id,
                error_desc="Transaction status: 02 - Failed/Cancelled"
            )

        if response_code == "00" and transaction_status == "00":
            return ReturnResponse(
                status="success",
                message=f"Thanh toán thành công! Số tiền: {amount} VND, Đơn hàng: {order_id}",
                order_id=order_id,
                transaction_no=params.get("vnp_TransactionNo")
            )
        return ReturnResponse(
            status="failed",
            message=f"Thanh toán thất bại. Mã lỗi: {response_code}, Transaction status: {transaction_status}",
            order_id=order_id,
            error_desc=params.get("vnp_ResponseMessage")
        )

    def verify_ipn(self, params: Dict) -> IPNResponse:
        """Xác thực chữ ký và xử lý IPN từ VNPay."""
        secure_hash = params.pop("vnp_SecureHash", None)
        querystring = urlencode(sorted(params.items()))
        expected_hash = hmac.new(
            self.hash_secret.encode('utf-8'),
            querystring.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

        if secure_hash != expected_hash:
            return IPNResponse(RspCode="97", Message="Chữ ký không hợp lệ")

        response_code = params.get("vnp_ResponseCode")
        order_id = params.get("vnp_TxnRef")
        amount = int(params.get("vnp_Amount", 0)) / 100

        if response_code == "00":
            # Cập nhật database hoặc logic kinh doanh
            print(f"IPN: Thanh toán thành công - Order ID: {order_id}, Amount: {amount} VND")
        else:
            print(f"IPN: Thanh toán thất bại - Order ID: {order_id}, Code: {response_code}")

        return IPNResponse(RspCode="00", Message="Xác nhận thành công")
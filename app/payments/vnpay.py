import hashlib
import hmac
import urllib.parse
from typing import Dict, Any


class VNPay:
    def __init__(self):
        # Dữ liệu request gửi đến VNPay
        self.request_data: Dict[str, Any] = {}
        # Dữ liệu response nhận từ VNPay  
        self.response_data: Dict[str, Any] = {}
# Tạo URL thanh toán VNPay
    def get_payment_url(self, vnpay_payment_url: str, secret_key: str) -> str:
        """
        1. Sắp xếp tham số theo thứ tự alphabet
        2. Tạo query string với URL encoding đặc biệt
        3. Tính hash HMAC SHA512 cho bảo mật
        4. Ghép thành URL hoàn chỉnh
        """
        # Sắp xếp parameters theo alphabet (yêu cầu của VNPay)
        input_data = sorted(self.request_data.items())
        query_string = ''
        seq = 0
        
        # Tạo query string với format đặc biệt của VNPay
        for key, val in input_data:
            if seq == 1:
                query_string = query_string + "&" + key + '=' + urllib.parse.quote_plus(str(val))
            else:
                seq = 1
                query_string = key + '=' + urllib.parse.quote_plus(str(val))

        # Tạo hash signature để bảo mật
        hash_value = self._hmacsha512(secret_key, query_string)
        return vnpay_payment_url + "?" + query_string + '&vnp_SecureHash=' + hash_value

# Xác thực chữ ký phản hồi từ VNPay
    def validate_response(self, secret_key: str, debug: bool = False) -> bool:
        """
        VNPay gửi kèm hash signature để đảm bảo tính toàn vẹn của dữ liệu.
        Function này sẽ tính lại hash và so sánh với hash được gửi kèm.
        """
        # Kiểm tra có hash signature không
        if 'vnp_SecureHash' not in self.response_data:
            if debug:
                print("DEBUG: vnp_SecureHash not found in response data")
            return False
            
        vnp_secure_hash = self.response_data['vnp_SecureHash']
        if debug:
            print(f"DEBUG: Received hash: {vnp_secure_hash}")
        
        # Remove hash params for validation
        response_data_copy = self.response_data.copy()
        if 'vnp_SecureHash' in response_data_copy:
            response_data_copy.pop('vnp_SecureHash')
        if 'vnp_SecureHashType' in response_data_copy:
            response_data_copy.pop('vnp_SecureHashType')

        # Filter only VNPay parameters
        vnp_params = {}
        for key, val in response_data_copy.items():
            if str(key).startswith('vnp_'):
                vnp_params[key] = val
        
        if debug:
            print(f"DEBUG: VNPay parameters: {vnp_params}")

        input_data = sorted(vnp_params.items())
        has_data = ''
        seq = 0
        
        for key, val in input_data:
            if seq == 1:
                has_data = has_data + "&" + str(key) + '=' + urllib.parse.quote_plus(str(val))
            else:
                seq = 1
                has_data = str(key) + '=' + urllib.parse.quote_plus(str(val))
                    
        if debug:
            print(f"DEBUG: Hash data string: {has_data}")
            print(f"DEBUG: Secret key length: {len(secret_key)}")
            
        # Tính hash và so sánh với hash từ VNPay
        hash_value = self._hmacsha512(secret_key, has_data)
        
        if debug:
            print(f"DEBUG: Calculated hash: {hash_value}")
            print(f"DEBUG: Hash match: {vnp_secure_hash.lower() == hash_value.lower()}")
            
        return vnp_secure_hash.lower() == hash_value.lower()

    @staticmethod
    def _hmacsha512(key: str, data: str) -> str:
        """Tạo hash HMAC SHA512 theo chuẩn VNPay"""
        byte_key = key.encode('utf-8')
        byte_data = data.encode('utf-8')
        return hmac.new(byte_key, byte_data, hashlib.sha512).hexdigest()

    def set_request_data(self, **kwargs) -> None:
        """Lưu dữ liệu request để gửi VNPay"""
        for key, value in kwargs.items():
            self.request_data[key] = value

    def set_response_data(self, data: Dict[str, Any]) -> None:
        """Lưu dữ liệu response từ VNPay"""
        self.response_data = data

    @staticmethod
    def get_client_ip(request) -> str:
        """Lấy IP address của client từ request"""
        x_forwarded_for = getattr(request.headers, 'x-forwarded-for', None)
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = getattr(request.client, 'host', '127.0.0.1')
        return ip
from pydantic import BaseModel, Field

class PaymentRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Số tiền thanh toán (VND, nhân 100, ví dụ: 1000000 cho 10.000 VND)")
    order_id: str = Field(..., min_length=1, max_length=50, description="ID đơn hàng duy nhất")
    order_info: str = Field(..., min_length=1, max_length=100, description="Mô tả đơn hàng")
    locale: str = Field(default="vn", pattern="^(vn|en)$", description="Ngôn ngữ: vn (Việt Nam) hoặc en (English)")
    bank_code: str = Field(default="", max_length=20, description="Mã ngân hàng, để trống nếu khách chọn")

class PaymentResponse(BaseModel):
    success: bool
    message: str
    pay_url: str | None = None
    order_id: str | None = None

class ReturnResponse(BaseModel):
    status: str
    message: str
    order_id: str | None = None
    transaction_no: str | None = None
    error_desc: str | None = None

class IPNResponse(BaseModel):
    RspCode: str
    Message: str
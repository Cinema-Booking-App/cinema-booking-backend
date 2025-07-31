from typing import List, TypeVar, Generic
from pydantic import BaseModel

# Định nghĩa TypeVar để biểu thị kiểu dữ liệu của các mục trong danh sách
T = TypeVar("T")

    # Schema tổng quát cho phản hồi phân trang.
class PaginatedResponse(BaseModel, Generic[T]):
    total: int
    skip: int
    limit: int
    items: List[T] # Trường dữ liệu chung cho danh sách các mục
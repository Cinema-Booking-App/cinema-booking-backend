from typing import Optional, List
from pydantic import BaseModel

class SeatLayoutBase(BaseModel):
    layout_name: str
    description: Optional[str] = None
    total_rows: int
    total_columns: int
    aisle_positions: Optional[str] = None



class SeatLayoutResponse(SeatLayoutBase):
    layout_id: int

    class Config:
        from_attributes = True

class SeatTemplateResponse(BaseModel):
    template_id: int
    row_number: int
    column_number: int
    seat_code: str
    seat_type : str
    is_edge: Optional[bool] = False
    is_active: Optional[bool] = True

    class Config:
        from_attributes = True

class SeatLayoutWithTemplatesResponse(SeatLayoutResponse):
    seat_templates: List[SeatTemplateResponse]

    class Config:
        from_attributes = True

class SeatTemplateCreate(BaseModel):
    row_number: int
    column_number: int
    seat_code: str
    seat_type: str
    is_edge: Optional[bool] = False
    is_active: Optional[bool] = True

# Schema tạo layout kèm danh sách seat_templates
class SeatLayoutWithTemplatesCreate(SeatLayoutBase):
    seat_templates: List[SeatTemplateCreate] = []
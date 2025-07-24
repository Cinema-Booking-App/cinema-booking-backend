from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload
from typing import List, Set, Tuple
from app.models.seat_layouts import SeatLayouts 
from app.models.seat_templates import SeatTemplates ,SeatTypeEnum
from app.schemas.seat_layouts import SeatLayoutWithTemplatesCreate


def get_all_seat_layouts(db: Session):
    seat_layouts = db.query(SeatLayouts).all()
    return seat_layouts

def get_seat_layout_by_id(db: Session, layout_id: int):
    try:
        # Sử dụng selectinload để eager load (nạp trước) danh sách seat_templates liên quan đến layout này
        # Điều này giúp khi trả về layout, trường seat_templates đã có sẵn dữ liệu, tránh lazy loading gây lỗi hoặc chậm
        seat_layout = db.query(SeatLayouts)\
            .options(selectinload(SeatLayouts.seat_templates))\
            .filter(SeatLayouts.layout_id == layout_id).first()
        if not seat_layout:
            raise HTTPException(status_code=404, detail="Seat layout not found")
        return seat_layout
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Tạo layout ghế với danh sách mẫu ghế
def create_seat_layout_with_templates(db: Session, layout_in: SeatLayoutWithTemplatesCreate):
    try:
        layout_name = db.query(SeatLayouts).filter(SeatLayouts.layout_name == layout_in.layout_name).first()
        if layout_name:
            raise HTTPException(status_code=400, detail="Layout name already exists")
        if layout_in.total_rows <= 0 or layout_in.total_columns <= 0:
            raise HTTPException(status_code=400, detail="Invalid total rows or columns")
        layout = SeatLayouts(
            layout_name=layout_in.layout_name,
            total_rows=layout_in.total_rows,
            total_columns=layout_in.total_columns,
            aisle_positions=layout_in.aisle_positions
        )
        db.add(layout)
        db.flush() # Đảm bảo rằng layout đã được thêm vào cơ sở dữ liệu
        if not layout_in.seat_templates:
            seat_templates = generate_default_seat_templates(
                layout_id=layout.layout_id,
                total_rows=layout_in.total_rows,
                total_columns=layout_in.total_columns
            )
            for seat_template in seat_templates:
                db.add(seat_template)

        else:
            for seat_template_data in layout_in.seat_templates:
                seat_template = SeatTemplates(
                    layout_id=layout.layout_id,
                    row_number=seat_template_data.row_number,
                    column_number=seat_template_data.column_number,
                    seat_code=seat_template_data.seat_code,
                    seat_type=SeatTypeEnum(seat_template_data.seat_type), 
                    is_edge=seat_template_data.is_edge,
                    is_active=seat_template_data.is_active
                )
                db.add(seat_template)
        db.commit()
        db.refresh(layout)
        return layout
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")

def delete_seat_layout(db: Session, layout_id: int):
    try:
        seat_layout = db.query(SeatLayouts).filter(SeatLayouts.layout_id == layout_id).first()
        if not seat_layout:
            raise HTTPException(status_code=404, detail="Seat layout not found")
        db.delete(seat_layout)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")
    

# Tự động tạo template cho layout mới
#-> tại sao List[SeatTemplate] tồn tại . vì đây là 1 list có kiểu dữ liệu là SeatTemplate . nếu không có thì sẽ lỗi : 
def generate_default_seat_templates(layout_id: int , total_rows: int, total_columns: int, exclude_positions: Set[Tuple[int, int]] = None) -> List[SeatTemplates]:
    
    # Hàm này sẽ tạo ra các mẫu ghế mặc định dựa trên số hàng và cột
    seat_templates = [] 
    except_positions = exclude_positions or set()  # Nếu không có thì rỗng
    for row in range(1, total_rows + 1):
        for column in range(1, total_columns + 1):
            if (row, column) in except_positions:
                continue
            else:
                seat_code = f"{chr(64 + row)}{column}" # Ví dụ: "A1", "B2", "C3"... 
                is_edge = (row == 1 or row == total_rows or column == 1 or column == total_columns) # Kiểm tra xem ghế có phải là ghế cạnh hay không
                seat_template = SeatTemplates(
                    layout_id=layout_id,
                    row_number=row, 
                    column_number=column,
                    seat_code=seat_code,
                    is_edge=is_edge,
                    is_active=True,
                    seat_type = SeatTypeEnum.regular.value  # Mặc định là ghế thường
                )
                seat_templates.append(seat_template)
    
    return seat_templates



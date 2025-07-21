
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.models.seat_layout import SeatLayout
from app.models.seat_template import SeatTemplate
from app.schemas.seat_layout import SeatLayoutWithTemplatesCreate, SeatLayoutWithTemplatesResponse


def get_all_seat_layouts(db: Session):
    seat_layouts = db.query(SeatLayout).all()
    return seat_layouts

def get_seat_layout_by_id(db: Session, layout_id: int):
    try:
        # Sử dụng selectinload để eager load (nạp trước) danh sách seat_templates liên quan đến layout này
        # Điều này giúp khi trả về layout, trường seat_templates đã có sẵn dữ liệu, tránh lazy loading gây lỗi hoặc chậm
        seat_layout = db.query(SeatLayout)\
            .options(selectinload(SeatLayout.seat_templates))\
            .filter(SeatLayout.layout_id == layout_id).first()
        if not seat_layout:
            raise HTTPException(status_code=404, detail="Seat layout not found")
        return seat_layout
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Tạo layout ghế với danh sách mẫu ghế
def create_seat_layout_with_templates(db: Session, layout_in: SeatLayoutWithTemplatesCreate):
    try:
        layout = SeatLayout(
            layout_name=layout_in.layout_name,
            total_rows=layout_in.total_rows,
            total_columns=layout_in.total_columns,
            aisle_positions=layout_in.aisle_positions
        )
        db.add(layout)
        db.flush() # Đảm bảo rằng layout đã được thêm vào cơ sở dữ liệu
        for seat_template_data in layout_in.seat_templates:
            seat_template = SeatTemplate(
                layout_id=layout.layout_id,
                row_number=seat_template_data.row_number,
                column_number=seat_template_data.column_number,
                seat_code=seat_template_data.seat_code,
                seat_type_id=seat_template_data.seat_type_id,
                is_edge=seat_template_data.is_edge,
                is_active=seat_template_data.is_active
            )
            db.add(seat_template)
        db.commit()
        db.refresh(layout)

        return layout
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")

def delete_seat_layout(db: Session, layout_id: int):
    try:
        seat_layout = db.query(SeatLayout).filter(SeatLayout.layout_id == layout_id).first()
        if not seat_layout:
            raise HTTPException(status_code=404, detail="Seat layout not found")
        db.delete(seat_layout)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Lỗi dữ liệu: {str(e)}")
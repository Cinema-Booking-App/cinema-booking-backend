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
# def generate_default_seat_templates(layout_id: int , total_rows: int, total_columns: int, exclude_positions: Set[Tuple[int, int]] = None) -> List[SeatTemplates]:
    
#     # Hàm này sẽ tạo ra các mẫu ghế mặc định dựa trên số hàng và cột
#     seat_templates = [] 
#     except_positions = exclude_positions or set()  # Nếu không có thì rỗng
#     for row in range(1, total_rows + 1):
#         for column in range(1, total_columns + 1):
#             if (row, column) in except_positions:
#                 continue
#             else:
#                 seat_code = f"{chr(64 + row)}{column}" # Ví dụ: "A1", "B2", "C3"... 
#                 is_edge = (row == 1 or row == total_rows or column == 1 or column == total_columns) # Kiểm tra xem ghế có phải là ghế cạnh hay không
#                 seat_template = SeatTemplates(
#                     layout_id=layout_id,
#                     row_number=row, 
#                     column_number=column,
#                     seat_code=seat_code,
#                     is_edge=is_edge,
#                     is_active=True,
#                     seat_type = SeatTypeEnum.regular.value  # Mặc định là ghế thường
#                 )
#                 seat_templates.append(seat_template)
    
#     return seat_templates

def generate_default_seat_templates(
    layout_id: int,
    total_rows: int,
    total_columns: int,
    exclude_positions: Set[Tuple[int, int]] = None
) -> List[SeatTemplates]:
    """
    Hàm này tạo ra các mẫu ghế mặc định với các loại ghế khác nhau
    dựa trên vị trí hàng:
    - 20% hàng đầu: ghế Standard
    - 20% hàng cuối: ghế Double (ghế đôi)
    - Các hàng còn lại ở giữa: ghế VIP
    """
    seat_templates = []
    excluded_positions = exclude_positions or set()

    # Tính toán ngưỡng cho từng loại ghế
    # Ít nhất 1 hàng cho mỗi loại nếu tổng số hàng đủ lớn
    num_standard_rows = max(1, int(total_rows * 0.2)) if total_rows > 0 else 0
    num_double_rows = max(1, int(total_rows * 0.2)) if total_rows > 0 else 0

    # Đảm bảo tổng số hàng không vượt quá total_rows khi tính VIP
    # VIP sẽ là phần còn lại sau khi đã phân bổ Standard và Double
    if total_rows > 0:
        if num_standard_rows + num_double_rows >= total_rows:
            # Nếu tổng Standard và Double đã chiếm hết hoặc vượt quá,
            # phân bổ lại cho hợp lý (ví dụ: chia đều hoặc ưu tiên Standard/Double)
            # Ở đây ta sẽ điều chỉnh để VIP vẫn có nếu có chỗ
            num_standard_rows = int(total_rows * 0.2)
            num_double_rows = int(total_rows * 0.2)
            if num_standard_rows + num_double_rows >= total_rows:
                 # Nếu vẫn vượt quá, ta ưu tiên standard và double
                 if total_rows >= 2: # Ít nhất 1 standard, 1 double
                     num_standard_rows = 1
                     num_double_rows = 1
                 else: # Chỉ có 1 hàng
                     num_standard_rows = 1
                     num_double_rows = 0 # Không có ghế đôi
        
        start_vip_row = num_standard_rows + 1
        end_vip_row = total_rows - num_double_rows
    else: # Trường hợp total_rows = 0
        start_vip_row = 1
        end_vip_row = 0 # Không có hàng VIP


    # Sử dụng một tập hợp để theo dõi các cột đã được chiếm bởi ghế đôi
    # để tránh tạo ghế đơn trên cùng vị trí đó.
    occupied_by_double = set()

    for row_num in range(1, total_rows + 1):
        # Xác định loại ghế cho hàng hiện tại
        if row_num <= num_standard_rows:
            current_seat_type = SeatTypeEnum.regular
        elif row_num > end_vip_row: # Hàng cuối
            current_seat_type = SeatTypeEnum.couple
        else: # Hàng giữa
            current_seat_type = SeatTypeEnum.vip

        # Reset occupied_by_double cho mỗi hàng mới
        occupied_by_double = set()

        for col_num in range(1, total_columns + 1):
            # Nếu vị trí này đã bị chiếm bởi một ghế đôi trước đó, bỏ qua
            if (row_num, col_num) in excluded_positions or (row_num, col_num) in occupied_by_double:
                continue

            # Xử lý logic cho ghế đôi
            if current_seat_type == SeatTypeEnum.couple:
                # Ghế đôi cần 2 cột. Kiểm tra xem có đủ chỗ không
                if col_num + 1 <= total_columns and (row_num, col_num + 1) not in excluded_positions:
                    seat_code = f"{chr(64 + row_num)}{col_num}-{col_num+1}" # Ví dụ: "A1-2"
                    # Đánh dấu cột kế tiếp đã bị chiếm để không tạo ghế ở đó
                    occupied_by_double.add((row_num, col_num + 1))
                    # Tạo ghế đôi tại vị trí col_num
                    seat_template = SeatTemplates(
                        layout_id=layout_id,
                        row_number=row_num,
                        column_number=col_num,
                        seat_code=seat_code,
                        seat_type=SeatTypeEnum.couple,
                        is_edge=(row_num == 1 or row_num == total_rows or col_num == 1 or col_num + 1 == total_columns),
                        is_active=True,
                    )
                    seat_templates.append(seat_template)
            else:
                # Ghế thường hoặc VIP (chỉ chiếm 1 cột)
                seat_code = f"{chr(64 + row_num)}{col_num}"
                seat_template = SeatTemplates(
                    layout_id=layout_id,
                    row_number=row_num,
                    column_number=col_num,
                    seat_code=seat_code,
                    seat_type=current_seat_type,
                    is_edge=(row_num == 1 or row_num == total_rows or col_num == 1 or col_num == total_columns),
                    is_active=True,
                )
                seat_templates.append(seat_template)
    
    return seat_templates

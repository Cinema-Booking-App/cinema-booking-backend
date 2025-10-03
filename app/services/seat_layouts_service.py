from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload
from typing import List, Set, Tuple
from app.models.seat_layouts import SeatLayouts
from app.models.seat_templates import SeatTemplates, SeatTypeEnum
from app.schemas.seat_layouts import SeatLayoutWithTemplatesCreate, SeatTemplateUpdate


def get_all_seat_layouts(db: Session):
    seat_layouts = db.query(SeatLayouts).all()
    return seat_layouts


def get_seat_layout_by_id(db: Session, layout_id: int):
    try:
        # Sử dụng selectinload để eager load (nạp trước) danh sách seat_templates liên quan đến layout này
        # Điều này giúp khi trả về layout, trường seat_templates đã có sẵn dữ liệu, tránh lazy loading gây lỗi hoặc chậm
        seat_layout = (
            db.query(SeatLayouts)
            .options(selectinload(SeatLayouts.seat_templates))
            .filter(SeatLayouts.layout_id == layout_id)
            .first()
        )
        if not seat_layout:
            raise HTTPException(status_code=404, detail="Seat layout not found")
        return seat_layout
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Tạo layout ghế với danh sách mẫu ghế
def create_seat_layout_with_templates(
    db: Session, layout_in: SeatLayoutWithTemplatesCreate
):
    try:
        layout_name = (
            db.query(SeatLayouts)
            .filter(SeatLayouts.layout_name == layout_in.layout_name)
            .first()
        )
        if layout_name:
            raise HTTPException(status_code=400, detail="Layout name already exists")
        if layout_in.total_rows <= 0 or layout_in.total_columns <= 0:
            raise HTTPException(status_code=400, detail="Invalid total rows or columns")
        layout = SeatLayouts(
            layout_name=layout_in.layout_name,
            total_rows=layout_in.total_rows,
            total_columns=layout_in.total_columns,
            aisle_positions=layout_in.aisle_positions,
        )
        db.add(layout)
        db.flush()  # Đảm bảo rằng layout đã được thêm vào cơ sở dữ liệu
        if not layout_in.seat_templates:
            seat_templates = generate_default_seat_templates(
                layout_id=layout.layout_id,
                total_rows=layout_in.total_rows,
                total_columns=layout_in.total_columns,
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
                    is_active=seat_template_data.is_active,
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
        seat_layout = (
            db.query(SeatLayouts).filter(SeatLayouts.layout_id == layout_id).first()
        )
        if not seat_layout:
            raise HTTPException(status_code=404, detail="Seat layout not found")
        db.delete(seat_layout)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"{str(e)}")


# Cập nhật loại ghế trong mảng seat_template trong layout theo template id
def update_seats_in_layout(
    db: Session, layout_id: int, updates: List[SeatTemplateUpdate]
):
    # Cập nhật các ghế trong layout cụ thể bằng template_id.
    try:
        # Kiểm tra xem layout và truy cập seat_templates
        layout = (
            db.query(SeatLayouts)
            .options(selectinload(SeatLayouts.seat_templates))
            .filter(SeatLayouts.layout_id == layout_id)
            .first()
        )

        if not layout:
            raise HTTPException(
                status_code=404, detail=f"Layout với ID {layout_id} không tìm thấy."
            )

        updated_count = 0

        # Tạo một dictionary để dễ dàng tìm kiếm ghế theo template_id
        seat_templates_map = {seat.template_id: seat for seat in layout.seat_templates}

        # Bước 2: Lặp qua từng bản cập nhật được gửi từ frontend
        for update_item in updates:
            # Tìm ghế trong layout đã load
            seat_to_update = seat_templates_map.get(update_item.template_id)

            if seat_to_update:
                # Cập nhật các trường nếu chúng được cung cấp trong payload
                if update_item.seat_type is not None:
                    # Đảm bảo giá trị của seat_type là hợp lệ với Enum
                    try:
                        seat_to_update.seat_type = SeatTypeEnum(update_item.seat_type)
                    except ValueError:
                        print(
                            f"Giá trị seat_type '{update_item.seat_type}' không hợp lệ cho template_id '{update_item.template_id}'. Bỏ qua cập nhật loại ghế này."
                        )
                        continue  # Bỏ qua cập nhật seat_type cho ghế này
                updated_count += 1
            else:
                print(
                    f"Ghế với template_id '{update_item.template_id}' không tìm thấy trong layout {layout_id}. Bỏ qua."
                )
        db.commit()
        # db.refresh(layout)

        return {
            "message": f"Đã cập nhật thành công {updated_count} ghế.",
            "updated_seats_count": updated_count,
        }

    except HTTPException as e:
        db.rollback()  # Hoàn tác các thay đổi nếu có HTTPException
        raise e  # Ném lại lỗi để FastAPI xử lý
    except Exception as e:
        db.rollback()  # Luôn hoàn tác nếu có lỗi bất ngờ
        raise HTTPException(
            status_code=500, detail=f"Đã xảy ra lỗi khi cập nhật ghế: {str(e)}"
        )


# Tự động tạo template cho layout mới
# -> tại sao List[SeatTemplate] tồn tại . vì đây là 1 list có kiểu dữ liệu là SeatTemplate . nếu không có thì sẽ lỗi :
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
    exclude_positions: Set[Tuple[int, int]] = None,
) -> List[SeatTemplates]:
    """
    Hàm này tạo ra các mẫu ghế mặc định với các loại ghế khác nhau
    dựa trên vị trí hàng:
    - 50% hàng đầu: ghế Standard
    - 30% hàng giữa: ghế VIP
    - 20% hàng cuối: ghế Double (ghế đôi)
    """
    seat_templates = []
    excluded_positions = exclude_positions or set()

    # --- Dòng bạn cần sửa ---
    # Tính toán ngưỡng cho từng loại ghế với tỷ lệ mới
    num_standard_rows = int(total_rows * 0.5)
    num_double_rows = int(total_rows * 0.2)
    # --- Kết thúc phần sửa ---

    # Đảm bảo tổng số hàng không vượt quá total_rows khi tính VIP
    if total_rows > 0:
        if num_standard_rows + num_double_rows >= total_rows:
            # Điều chỉnh lại phân bổ nếu tổng vượt quá total_rows
            if total_rows > 2:
                # Ưu tiên ghế thường và ghế đôi, VIP sẽ là phần còn lại nếu có
                num_standard_rows = int(total_rows * 0.5)
                num_double_rows = int(total_rows * 0.2)
            else:
                num_standard_rows = total_rows
                num_double_rows = 0

        end_vip_row = total_rows - num_double_rows
    else:
        end_vip_row = 0

    # Sử dụng một tập hợp để theo dõi các cột đã được chiếm bởi ghế đôi
    occupied_by_double = set()

    for row_num in range(1, total_rows + 1):
        # Xác định loại ghế cho hàng hiện tại
        if row_num <= num_standard_rows:
            current_seat_type = SeatTypeEnum.regular
        elif row_num > end_vip_row:  # Hàng cuối
            current_seat_type = SeatTypeEnum.couple
        else:  # Hàng giữa
            current_seat_type = SeatTypeEnum.vip

        # Reset occupied_by_double cho mỗi hàng mới
        occupied_by_double = set()

        for col_num in range(1, total_columns + 1):
            if (row_num, col_num) in excluded_positions or (
                row_num,
                col_num,
            ) in occupied_by_double:
                continue

            if current_seat_type == SeatTypeEnum.couple:
                if (
                    col_num + 1 <= total_columns
                    and (row_num, col_num + 1) not in excluded_positions
                ):
                    seat_code = (
                        f"{chr(64 + row_num)}{col_num}-{col_num+1}"
                    )
                    occupied_by_double.add((row_num, col_num + 1))
                    seat_template = SeatTemplates(
                        layout_id=layout_id,
                        row_number=row_num,
                        column_number=col_num,
                        seat_code=seat_code,
                        seat_type=SeatTypeEnum.couple,
                        is_edge=(
                            row_num == 1
                            or row_num == total_rows
                            or col_num == 1
                            or col_num + 1 == total_columns
                        ),
                        is_active=True,
                    )
                    seat_templates.append(seat_template)
            else:
                seat_code = f"{chr(64 + row_num)}{col_num}"
                seat_template = SeatTemplates(
                    layout_id=layout_id,
                    row_number=row_num,
                    column_number=col_num,
                    seat_code=seat_code,
                    seat_type=current_seat_type,
                    is_edge=(
                        row_num == 1
                        or row_num == total_rows
                        or col_num == 1
                        or col_num == total_columns
                    ),
                    is_active=True,
                )
                seat_templates.append(seat_template)

    return seat_templates

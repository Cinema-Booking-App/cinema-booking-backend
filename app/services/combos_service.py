from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload
from app.models.combos import Combos, ComboItems, ComboDishes
from app.schemas.combos import ComboCreate, ComboUpdate, ComboResponse, ComboItemResponse, DishCreate, DishResponse
from sqlalchemy.exc import SQLAlchemyError

def create_dish(db: Session, dish_data: DishCreate):
    try:
        # Kiểm tra trùng dish_name
        existing_dish = db.query(ComboDishes).filter(ComboDishes.dish_name == dish_data.dish_name).first()
        if existing_dish:
            raise HTTPException(status_code=400, detail="Dish name đã tồn tại.")

        new_dish = ComboDishes(
            dish_name=dish_data.dish_name,
            description=dish_data.description
        )
        db.add(new_dish)
        db.commit()
        db.refresh(new_dish)
        return DishResponse(
            dish_id=new_dish.dish_id,
            dish_name=new_dish.dish_name,
            description=new_dish.description
        )
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating dish: {str(e)}")

def create_combo(db: Session, combo_data: ComboCreate):
    try:
        # Kiểm tra trùng combo_name
        existing_combo = db.query(Combos).filter(Combos.combo_name == combo_data.combo_name).first()
        if existing_combo:
            raise HTTPException(status_code=400, detail="Combo name đã tồn tại.")

        # Kiểm tra dish_id hợp lệ
        for item in combo_data.items:
            dish = db.query(ComboDishes).filter(ComboDishes.dish_id == item.dish_id).first()
            if not dish:
                raise HTTPException(status_code=400, detail=f"Dish ID {item.dish_id} không tồn tại.")

        # Tạo combo mới
        new_combo = Combos(
            combo_name=combo_data.combo_name,
            description=combo_data.description,
            price=combo_data.price,
            image_url=combo_data.image_url,
            status=combo_data.status
        )
        db.add(new_combo)
        db.flush()  # Lấy combo_id

        # Tạo các item trong combo
        for item in combo_data.items:
            db_item = ComboItems(
                combo_id=new_combo.combo_id,
                dish_id=item.dish_id,
                quantity=item.quantity,
            )
            db.add(db_item)

        db.commit()
        db.refresh(new_combo)

        # Truy vấn items với join để lấy dish_name và description
        items = (db.query(ComboItems)
                 .join(ComboDishes, ComboItems.dish_id == ComboDishes.dish_id)
                 .filter(ComboItems.combo_id == new_combo.combo_id)
                 .all())

        return ComboResponse(
            combo_id=new_combo.combo_id,
            combo_name=new_combo.combo_name,
            description=new_combo.description,
            price=new_combo.price,
            image_url=new_combo.image_url,
            status=new_combo.status,
            created_at=new_combo.created_at,
            items=[
                ComboItemResponse(
                    item_id=item.item_id,
                    dish_id=item.dish_id,
                    quantity=item.quantity,
                    dish_name=item.dish.dish_name,
                    description=item.dish.description
                ) for item in items
            ]
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating combo: {str(e)}")

def get_combo_by_id(db: Session, combo_id: int):
    # Sử dụng joinedload để lấy items và dishes trong cùng một truy vấn
    combo = (db.query(Combos)
             .options(joinedload(Combos.items).joinedload(ComboItems.dish))
             .filter(Combos.combo_id == combo_id)
             .first())
    if not combo:
        raise HTTPException(status_code=404, detail="Không tìm thấy combo có ID này.")

    return ComboResponse(
        combo_id=combo.combo_id,
        combo_name=combo.combo_name,
        description=combo.description,
        price=combo.price,
        image_url=combo.image_url,
        status=combo.status,
        created_at=combo.created_at,
        items=[
            ComboItemResponse(
                item_id=item.item_id,
                dish_id=item.dish_id,
                quantity=item.quantity,
                dish_name=item.dish.dish_name,
                description=item.dish.description
            ) for item in combo.items
        ]
    )

def get_all_combos(db: Session):
    # Sử dụng joinedload để lấy tất cả combos, items và dishes trong một truy vấn
    combos = (db.query(Combos)
              .options(joinedload(Combos.items).joinedload(ComboItems.dish))
              .all())
    result = []
    for combo in combos:
        result.append(
            ComboResponse(
                combo_id=combo.combo_id,
                combo_name=combo.combo_name,
                description=combo.description,
                price=combo.price,
                image_url=combo.image_url,
                status=combo.status,
                created_at=combo.created_at,
                items=[
                    ComboItemResponse(
                        item_id=item.item_id,
                        dish_id=item.dish_id,
                        quantity=item.quantity,
                        dish_name=item.dish.dish_name,
                        description=item.dish.description
                    ) for item in combo.items
                ]
            )
        )
    return result

def update_combo(db: Session, combo_id: int, combo_data: ComboUpdate):
    try:
        combo = db.query(Combos).filter(Combos.combo_id == combo_id).first()
        if not combo:
            raise HTTPException(status_code=404, detail="Không tìm thấy combo cần cập nhật.")

        # Kiểm tra trùng combo_name (trừ combo hiện tại)
        existing_combo = db.query(Combos).filter(Combos.combo_name == combo_data.combo_name, Combos.combo_id != combo_id).first()
        if existing_combo:
            raise HTTPException(status_code=400, detail="Combo name đã tồn tại.")

        # Cập nhật thông tin combo
        combo.combo_name = combo_data.combo_name
        combo.description = combo_data.description
        combo.price = combo_data.price
        combo.image_url = combo_data.image_url
        if combo_data.status is not None:
            combo.status = combo_data.status

        # Cập nhật items nếu có
        if combo_data.items is not None:
            # Kiểm tra dish_id hợp lệ
            for item in combo_data.items:
                dish = db.query(ComboDishes).filter(ComboDishes.dish_id == item.dish_id).first()
                if not dish:
                    raise HTTPException(status_code=400, detail=f"Dish ID {item.dish_id} không tồn tại.")
            
            # Xóa items cũ
            db.query(ComboItems).filter(ComboItems.combo_id == combo_id).delete()
            # Thêm items mới
            for item in combo_data.items:
                db.add(ComboItems(
                    combo_id=combo_id,
                    dish_id=item.dish_id,
                    quantity=item.quantity
                ))

        db.commit()
        db.refresh(combo)

        # Truy vấn lại items với join để lấy dish_name và description
        items = (db.query(ComboItems)
                 .join(ComboDishes, ComboItems.dish_id == ComboDishes.dish_id)
                 .filter(ComboItems.combo_id == combo_id)
                 .all())
        return ComboResponse(
            combo_id=combo.combo_id,
            combo_name=combo.combo_name,
            description=combo.description,
            price=combo.price,
            image_url=combo.image_url,
            status=combo.status,
            created_at=combo.created_at,
            items=[
                ComboItemResponse(
                    item_id=item.item_id,
                    dish_id=item.dish_id,
                    quantity=item.quantity,
                    dish_name=item.dish.dish_name,
                    description=item.dish.description
                ) for item in items
            ]
        )

    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating combo: {str(e)}")

def delete_combo(db: Session, combo_id: int):
    try:
        combo = db.query(Combos).filter(Combos.combo_id == combo_id).first()
        if not combo:
            raise HTTPException(status_code=404, detail="Không tìm thấy combo cần xóa.")
        db.delete(combo)
        db.commit()
        return True
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting combo: {str(e)}")
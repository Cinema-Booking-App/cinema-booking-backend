# app/services/combos_service.py

from sqlalchemy.orm import Session
from app.models.combos import Combos, Combo_items
from app.schemas.combos import ComboCreate, ComboUpdate


def create_combo(db: Session, combo_data: ComboCreate):
    new_combo = Combos(
        combo_name=combo_data.combo_name,
        description=combo_data.description,
        price=combo_data.price,
        status=combo_data.status,
    )
    db.add(new_combo)
    db.flush()  # Lấy combo_id để tạo item liên kết

    for item in combo_data.items:
        db_item = Combo_items(
            combo_id=new_combo.combo_id,
            item_name=item.item_name,
            quantity=item.quantity,
        )
        db.add(db_item)

    db.commit()
    db.refresh(new_combo)
    return new_combo


def get_combo_by_id(db: Session, combo_id: int):
    return db.query(Combos).filter(Combos.combo_id == combo_id).first()


def get_all_combos(db: Session):
    return db.query(Combos).all()


def update_combo(db: Session, combo_id: int, combo_data: ComboUpdate):
    combo = db.query(Combos).filter(Combos.combo_id == combo_id).first()
    if not combo:
        return None

    combo.combo_name = combo_data.combo_name
    combo.description = combo_data.description
    combo.price = combo_data.price
    combo.status = combo_data.status

    if combo_data.items is not None:
        db.query(Combo_items).filter(Combo_items.combo_id == combo_id).delete()
        for item in combo_data.items:
            db.add(Combo_items(
                combo_id=combo_id,
                item_name=item.item_name,
                quantity=item.quantity
            ))

    db.commit()
    db.refresh(combo)
    return combo


def delete_combo(db: Session, combo_id: int):
    combo = db.query(Combos).filter(Combos.combo_id == combo_id).first()
    if not combo:
        return False

    db.delete(combo)  # sẽ xóa luôn combo_items nếu cascade đã thiết lập
    db.commit()
    return True

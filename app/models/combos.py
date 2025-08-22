from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, Enum, DateTime, func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
# Enum trạng thái combo
class ComboStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    deleted = "deleted"


# Bảng ComboDishes
class ComboDish(Base):
    __tablename__ = 'combo_dishes'

    dish_id = Column(Integer, primary_key=True, autoincrement=True)
    dish_name = Column(String, nullable=False)
    description = Column(Text)

    # Quan hệ với ComboItem
    combo_items = relationship("ComboItem", back_populates="dish")


# Bảng Combos
class Combo(Base):
    __tablename__ = 'combos'

    combo_id = Column(Integer, primary_key=True, autoincrement=True)
    combo_name = Column(String(255), unique=True, nullable=False)
    description = Column(Text)
    price = Column(Numeric(10, 2), nullable=False)
    image_url = Column(String(255))
    status = Column(Enum(ComboStatusEnum), default=ComboStatusEnum.active)

    # Quan hệ với ComboItem
    combo_items = relationship("ComboItem", back_populates="combo")


# Bảng ComboItems (Bảng trung gian)
class ComboItem(Base):
    __tablename__ = 'combo_items'

    item_id = Column(Integer, primary_key=True, autoincrement=True)
    combo_id = Column(Integer, ForeignKey('combos.combo_id'), nullable=False)
    dish_id = Column(Integer, ForeignKey('combo_dishes.dish_id'), nullable=False)
    quantity = Column(Integer, nullable=False)

    # Quan hệ tới Combo và ComboDish
    combo = relationship("Combo", back_populates="combo_items")
    dish = relationship("ComboDish", back_populates="combo_items")

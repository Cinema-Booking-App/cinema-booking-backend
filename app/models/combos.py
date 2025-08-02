from sqlalchemy import Integer, Column, String, Text, Numeric, Enum, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime
import enum

class ComboStatusEnum(str, enum.Enum):
    active = "active"
    inactive = "inactive"
    deleted = "deleted"

class Combos(Base):
    __tablename__ = "combos"

    combo_id = Column(Integer, primary_key=True, index=True)
    combo_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric, nullable=False)
    image_url = Column(Text, nullable=True)
    status = Column(Enum(ComboStatusEnum, name="combo_status"), default=ComboStatusEnum.active, server_default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("ComboItems", back_populates="combo", cascade="all, delete-orphan")


# Bảng combo_dishes
class ComboDishes(Base):
    __tablename__ = "combo_dishes"

    dish_id = Column(Integer, primary_key=True, index=True)
    dish_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Quan hệ đến combo_items
    items = relationship("ComboItems", back_populates="dish", cascade="all, delete-orphan")
    

# Bảng combo_items (trung gian combo - món ăn)
class ComboItems(Base):
    __tablename__ = "combo_items"

    item_id = Column(Integer, primary_key=True, index=True)
    combo_id = Column(Integer, ForeignKey("combos.combo_id"), nullable=False, index=True)
    dish_id = Column(Integer, ForeignKey("combo_dishes.dish_id"), nullable=True, index=True)
    quantity = Column(Integer, nullable=False)

    # Quan hệ đến combos
    combo = relationship("Combos", back_populates="items")

    # Quan hệ đến combo_dishes
    dish = relationship("ComboDishes", back_populates="items")

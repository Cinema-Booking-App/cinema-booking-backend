from sqlalchemy import Integer, Column, String, Text, Numeric, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum

class ComboStatusEnum(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"

class Combos(Base):
    __tablename__ = "combos"

    combo_id = Column(Integer, primary_key=True, index=True)
    combo_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Numeric, nullable=False)
    status: ComboStatusEnum = ComboStatusEnum.ACTIVE

    items = relationship("Combo_items", back_populates="combo", cascade="all, delete-orphan")


class Combo_items(Base):
    __tablename__ = "combo_items"

    item_id = Column(Integer, primary_key=True, index=True)
    combo_id = Column(Integer, ForeignKey("combos.combo_id"), nullable=False)
    item_name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)

    combo = relationship("Combos", back_populates="items")

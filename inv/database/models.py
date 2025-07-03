"""SQLAlchemy models for streetwear inventory"""

from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP, ForeignKey
from sqlalchemy.types import DECIMAL
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Location(Base):
    __tablename__ = 'locations'
    
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False)
    location_type = Column(String(50))
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_date = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    items = relationship("Item", back_populates="location")


class Consigner(Base):
    __tablename__ = 'consigners'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    email = Column(String(200))
    default_split_percentage = Column(Integer, default=70)
    created_date = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    items = relationship("Item", back_populates="consigner")


class Item(Base):
    __tablename__ = 'items'
    
    id = Column(Integer, primary_key=True)
    sku = Column(String(10), nullable=False)
    variant_id = Column(Integer, default=1)
    brand = Column(String(100), nullable=False)
    model = Column(String(200), nullable=False)
    size = Column(String(20), nullable=False)
    color = Column(String(100), nullable=False)
    condition = Column(String(10), nullable=False)  # CHECK constraint handled at application level
    box_status = Column(String(10), nullable=False)  # CHECK constraint handled at application level
    current_price = Column(DECIMAL(10, 2), nullable=False)
    purchase_price = Column(DECIMAL(10, 2), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.id'))
    date_added = Column(TIMESTAMP, default=func.current_timestamp())
    notes = Column(Text)
    status = Column(String(20), default='available')  # CHECK constraint handled at application level
    
    # Consignment fields
    ownership_type = Column(String(20), default='owned')  # CHECK constraint handled at application level
    consigner_id = Column(Integer, ForeignKey('consigners.id'))
    split_percentage = Column(Integer)
    
    # Sale tracking
    sold_price = Column(DECIMAL(10, 2))
    sold_platform = Column(String(50))
    sold_date = Column(TIMESTAMP)
    
    # Relationships
    location = relationship("Location", back_populates="items")
    consigner = relationship("Consigner", back_populates="items")
    photos = relationship("Photo", back_populates="item", cascade="all, delete-orphan")
    
    __table_args__ = (
        {'sqlite_autoincrement': True}
    )


class Photo(Base):
    __tablename__ = 'photos'
    
    id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey('items.id', ondelete='CASCADE'), nullable=False)
    file_path = Column(String(500), nullable=False)
    photo_type = Column(String(20))
    display_order = Column(Integer, default=1)
    created_date = Column(TIMESTAMP, default=func.current_timestamp())
    
    # Relationships
    item = relationship("Item", back_populates="photos")
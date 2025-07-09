from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()


class RoomType(Base):
    __tablename__ = "room_types"
    
    id = Column(String(50), primary_key=True)  # Используем ID из TravelLine API
    name = Column(String(255), nullable=False)
    description = Column(Text)
    size_value = Column(Float)
    category_code = Column(String(100))
    category_name = Column(String(255))
    position = Column(Integer)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    images = relationship("RoomTypeImage", back_populates="room_type", cascade="all, delete-orphan")
    amenities = relationship("Amenity", back_populates="room_type", cascade="all, delete-orphan")
    address = relationship("Address", back_populates="room_type", uselist=False, cascade="all, delete-orphan")
    occupancy = relationship("Occupancy", back_populates="room_type", uselist=False, cascade="all, delete-orphan")
    placements = relationship("Placement", back_populates="room_type", cascade="all, delete-orphan")


class RoomTypeImage(Base):
    __tablename__ = "room_type_images"
    
    id = Column(Integer, primary_key=True, index=True)
    room_type_id = Column(String(50), ForeignKey("room_types.id"), nullable=False)  # Изменяем тип на String
    url = Column(String(1024), nullable=False)
    position = Column(Integer)
    
    # Relationship
    room_type = relationship("RoomType", back_populates="images")


class Amenity(Base):
    __tablename__ = "amenities"
    
    id = Column(Integer, primary_key=True, index=True)
    room_type_id = Column(String(50), ForeignKey("room_types.id"), nullable=False)  # Изменяем тип на String
    code = Column(String(100), nullable=False)
    
    # Relationship
    room_type = relationship("RoomType", back_populates="amenities")


class Address(Base):
    __tablename__ = "addresses"
    
    id = Column(Integer, primary_key=True, index=True)
    room_type_id = Column(String(50), ForeignKey("room_types.id"), nullable=False, unique=True)  # Изменяем тип на String
    postal_code = Column(String(50))
    country_code = Column(String(10))
    region = Column(String(255))
    region_id = Column(String(50))
    city_name = Column(String(255))
    city_id = Column(String(50))
    address_line = Column(String(512))
    latitude = Column(Float)
    longitude = Column(Float)
    remark = Column(Text)
    
    # Relationship
    room_type = relationship("RoomType", back_populates="address")


class Occupancy(Base):
    __tablename__ = "occupancy"
    
    id = Column(Integer, primary_key=True, index=True)
    room_type_id = Column(String(50), ForeignKey("room_types.id"), nullable=False, unique=True)  # Изменяем тип на String
    adult_bed = Column(Integer, default=0)
    extra_bed = Column(Integer, default=0)
    child_without_bed = Column(Integer, default=0)
    
    # Relationship
    room_type = relationship("RoomType", back_populates="occupancy")


class Placement(Base):
    __tablename__ = "placements"
    
    id = Column(Integer, primary_key=True, index=True)
    room_type_id = Column(String(50), ForeignKey("room_types.id"), nullable=False)  # Изменяем тип на String
    kind = Column(String(50), nullable=False)
    count = Column(Integer, nullable=False)
    min_age = Column(Integer)
    max_age = Column(Integer)
    
    # Relationship
    room_type = relationship("RoomType", back_populates="placements")

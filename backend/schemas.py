from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class MainRoomType(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: Optional[int] = None
    adult_bed: Optional[int] = None
    image: Optional[str] = None

    class Config:
        from_attributes = True

class CatalogRoomType(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: int = 2700
    amenities: List[str] = []
    image: Optional[str] = None
    size: Optional[float] = None
    category: Optional[str] = None
    adult_bed: Optional[int] = None

    class Config:
        from_attributes = True

class RoomTypeInfo(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    price: int = 2700
    amenities: List[str] = []
    images: List[str] = []
    size: Optional[float] = None
    category: Optional[str] = None
    adult_bed: Optional[int] = None

    class Config:
        from_attributes = True


class FeedbackBase(BaseModel):
    text: str
    rate: int = Field(..., ge=0, le=5, description="Рейтинг от 0 до 5")


class FeedbackCreate(FeedbackBase):
    pass


class Feedback(FeedbackBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class VideoFeedbackBase(BaseModel):
    file: str
    rate: int = Field(..., ge=0, le=5, description="Рейтинг от 0 до 5")


class VideoFeedbackCreate(VideoFeedbackBase):
    pass


class VideoFeedback(VideoFeedbackBase):
    uuid: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

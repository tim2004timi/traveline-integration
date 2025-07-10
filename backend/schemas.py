from pydantic import BaseModel
from typing import Optional, List


class MainRoomType(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[int] = None
    adult_bed: Optional[int] = None
    image: Optional[str] = None

    class Config:
        from_attributes = True

class CatalogRoomType(BaseModel):
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

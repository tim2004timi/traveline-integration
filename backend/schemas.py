from pydantic import BaseModel
from typing import Optional


class MainRoomType(BaseModel):
    name: str
    description: Optional[str] = None
    price: Optional[int] = None
    adult_bed: Optional[int] = None
    image: Optional[str] = None

    class Config:
        from_attributes = True

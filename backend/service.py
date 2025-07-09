from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import RoomType, Occupancy, RoomTypeImage
from schemas import MainRoomType
from database import async_session


async def get_room_types() -> List[MainRoomType]:
    """
    Получает все типы номеров из базы данных с основной информацией
    """
    async with async_session() as session:
        # Выполняем JOIN запрос для получения данных room_types и occupancy
        query = select(RoomType, Occupancy).outerjoin(
            Occupancy, RoomType.id == Occupancy.room_type_id
        )
        
        result = await session.execute(query)
        room_types = []
        
        for row in result:
            room_type, occupancy = row
            
            # Получаем первое изображение для данного типа номера
            image_query = select(RoomTypeImage.url).where(
                RoomTypeImage.room_type_id == room_type.id
            ).order_by(RoomTypeImage.position).limit(1)
            
            image_result = await session.execute(image_query)
            first_image = image_result.scalar()
            
            main_room_type = MainRoomType(
                name=room_type.name,
                description=room_type.description,
                price=2700,
                adult_bed=occupancy.adult_bed if occupancy else None,
                image=first_image
            )
            room_types.append(main_room_type)
        
        return room_types

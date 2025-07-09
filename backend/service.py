from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models import RoomType, Occupancy
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
            
            main_room_type = MainRoomType(
                name=room_type.name,
                description=room_type.description,
                price=2700,
                adult_bed=occupancy.adult_bed if occupancy else None
            )
            room_types.append(main_room_type)
        
        return room_types

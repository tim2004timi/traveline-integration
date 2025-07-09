from fastapi import APIRouter, HTTPException
from typing import List
from schemas import MainRoomType
from service import get_room_types

router = APIRouter()


@router.get("/main/room-types", response_model=List[MainRoomType])
async def get_main_room_types():
    """
    Получить список всех типов номеров с основной информацией.
    
    Возвращает:
    - name: название типа номера
    - description: описание типа номера
    - price: цена (из position)
    - adult_bed: количество взрослых кроватей (из occupancy)
    - image: URL первого изображения номера
    
    Данные синхронизируются с TravelLine API каждые 2 минуты.
    """
    try:
        room_types = await get_room_types()
        return room_types
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")

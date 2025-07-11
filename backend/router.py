from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from schemas import MainRoomType, CatalogRoomType
from service import get_room_types, get_catalog_room_types, get_catalog_room_types_filtered

router = APIRouter()


@router.get("/main/room-types", response_model=List[MainRoomType])
async def get_main_room_types():
    """
    Получить список всех типов номеров с основной информацией.
    
    Возвращает:
    - name: название типа номера
    - description: описание типа номера
    - price: цена (2700)
    - adult_bed: количество взрослых кроватей (из occupancy)
    - image: URL первого изображения номера
    
    Данные синхронизируются с TravelLine API каждые 2 минуты.
    """
    try:
        room_types = await get_room_types()
        return room_types
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")

@router.get("/catalog/room-types", response_model=List[CatalogRoomType])
async def get_catalog_room_types_endpoint(
    price_from: Optional[int] = Query(None, description="Минимальная цена"),
    price_to: Optional[int] = Query(None, description="Максимальная цена"),
    size_from: Optional[float] = Query(None, description="Минимальный размер номера"),
    size_to: Optional[float] = Query(None, description="Максимальный размер номера"),
    category: Optional[str] = Query(None, description="Категория объекта (например, 'Аппартаменты')"),
    adult_bed: Optional[int] = Query(None, description="Количество взрослых мест"),
    sort_by: Optional[str] = Query(None, description="Сортировка (price, size)")
):
    """
    Получить каталог типов номеров с фильтрацией и сортировкой:
    - price_from: минимальная цена
    - price_to: максимальная цена
    - size_from: минимальный размер
    - size_to: максимальный размер
    - category: категория
    - adult_bed: количество взрослых мест
    - sort_by: сортировка (price, size)
    """
    try:
        return await get_catalog_room_types_filtered(
            price_from=price_from,
            price_to=price_to,
            size_from=size_from,
            size_to=size_to,
            category=category,
            adult_bed=adult_bed,
            sort_by=sort_by
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения данных: {str(e)}")

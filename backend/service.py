from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, asc, desc
from models import RoomType, Occupancy, RoomTypeImage, Amenity
from schemas import MainRoomType, CatalogRoomType
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


async def get_catalog_room_types() -> List[CatalogRoomType]:
    """
    Получает все типы номеров для каталога с подробной информацией
    """
    async with async_session() as session:
        query = select(RoomType)
        result = await session.execute(query)
        room_types = result.scalars().all()
        catalog = []

        for room_type in room_types:
            # Первое изображение
            image_query = select(RoomTypeImage.url).where(
                RoomTypeImage.room_type_id == room_type.id
            ).order_by(RoomTypeImage.position).limit(1)
            image_result = await session.execute(image_query)
            first_image = image_result.scalar()

            # Удобства
            amenities_query = select(Amenity.code).where(
                Amenity.room_type_id == room_type.id
            )
            amenities_result = await session.execute(amenities_query)
            amenities = [row[0] for row in amenities_result.all()]

            # Вместимость
            occ_query = select(Occupancy.adult_bed).where(
                Occupancy.room_type_id == room_type.id
            )
            occ_result = await session.execute(occ_query)
            adult_bed = occ_result.scalar()

            catalog.append(CatalogRoomType(
                name=room_type.name,
                description=room_type.description,
                price=2700,
                amenities=amenities,
                image=first_image,
                size=room_type.size_value,
                category=room_type.category_name,
                adult_bed=adult_bed
            ))
        return catalog

async def get_catalog_room_types_filtered(
    price_from: Optional[int] = None,
    price_to: Optional[int] = None,
    size_from: Optional[float] = None,
    size_to: Optional[float] = None,
    category: Optional[str] = None,
    adult_bed: Optional[int] = None,
    sort_by: Optional[str] = None
) -> List[CatalogRoomType]:
    async with async_session() as session:
        query = select(RoomType)
        filters = []
        # Фильтрация по size
        if size_from is not None:
            filters.append(RoomType.size_value >= size_from)
        if size_to is not None:
            filters.append(RoomType.size_value <= size_to)
        # Фильтрация по категории
        if category:
            filters.append(RoomType.category_name == category)
        # Применяем фильтры к RoomType
        if filters:
            query = query.where(and_(*filters))
        # Сортировка
        if sort_by == "price":
            query = query.order_by(RoomType.position)
        elif sort_by == "size":
            query = query.order_by(RoomType.size_value)
        # Получаем RoomType
        result = await session.execute(query)
        room_types = result.scalars().all()
        catalog = []
        for room_type in room_types:
            # Фильтрация по adult_bed
            occ_query = select(Occupancy.adult_bed).where(
                Occupancy.room_type_id == room_type.id
            )
            occ_result = await session.execute(occ_query)
            adult_bed_val = occ_result.scalar()
            if adult_bed is not None and adult_bed_val != adult_bed:
                continue
            # Фильтрация по цене (position)
            price = 2700  # по умолчанию
            if price_from is not None and price < price_from:
                continue
            if price_to is not None and price > price_to:
                continue
            # Первое изображение
            image_query = select(RoomTypeImage.url).where(
                RoomTypeImage.room_type_id == room_type.id
            ).order_by(RoomTypeImage.position).limit(1)
            image_result = await session.execute(image_query)
            first_image = image_result.scalar()
            # Удобства
            amenities_query = select(Amenity.code).where(
                Amenity.room_type_id == room_type.id
            )
            amenities_result = await session.execute(amenities_query)
            amenities = [row[0] for row in amenities_result.all()]
            catalog.append(CatalogRoomType(
                name=room_type.name,
                description=room_type.description,
                price=price,
                amenities=amenities,
                image=first_image,
                size=room_type.size_value,
                category=room_type.category_name,
                adult_bed=adult_bed_val
            ))
        # Сортировка по цене (если нужно)
        if sort_by == "price":
            catalog.sort(key=lambda x: x.price)
        elif sort_by == "size":
            catalog.sort(key=lambda x: (x.size or 0))
        return catalog

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, asc, desc, delete
from models import RoomType, Occupancy, RoomTypeImage, Amenity, Feedback as FeedbackModel, VideoFeedback as VideoFeedbackModel
from schemas import MainRoomType, CatalogRoomType, RoomTypeInfo, FeedbackCreate, Feedback, VideoFeedbackCreate, VideoFeedback
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
                id=room_type.id,
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
                id=room_type.id,
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
                id=room_type.id,
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

async def get_room_type_info(room_id: str) -> Optional[RoomTypeInfo]:
    async with async_session() as session:
        # Получаем RoomType
        room_type = await session.get(RoomType, room_id)
        if not room_type:
            return None
        # Все изображения
        images_query = select(RoomTypeImage.url).where(
            RoomTypeImage.room_type_id == room_id
        ).order_by(RoomTypeImage.position)
        images_result = await session.execute(images_query)
        images = [row[0] for row in images_result.all()]
        # Удобства
        amenities_query = select(Amenity.code).where(
            Amenity.room_type_id == room_id
        )
        amenities_result = await session.execute(amenities_query)
        amenities = [row[0] for row in amenities_result.all()]
        # Вместимость
        occ_query = select(Occupancy.adult_bed).where(
            Occupancy.room_type_id == room_id
        )
        occ_result = await session.execute(occ_query)
        adult_bed = occ_result.scalar()
        return RoomTypeInfo(
            id=room_type.id,
            name=room_type.name,
            description=room_type.description,
            price=2700,
            amenities=amenities,
            images=images,
            size=room_type.size_value,
            category=room_type.category_name,
            adult_bed=adult_bed
        )

async def get_similar_room_types(room_id: str, limit: int = 10) -> List[MainRoomType]:
    async with async_session() as session:
        # Получаем исходный объект
        room_type = await session.get(RoomType, room_id)
        if not room_type:
            return []
        occ_query = select(Occupancy.adult_bed).where(Occupancy.room_type_id == room_id)
        occ_result = await session.execute(occ_query)
        base_adult_bed = occ_result.scalar() or 0
        base_size = room_type.size_value or 0
        base_price = room_type.position or 0
        # Получаем все остальные объекты
        query = select(RoomType, Occupancy).outerjoin(
            Occupancy, RoomType.id == Occupancy.room_type_id
        ).where(RoomType.id != room_id)
        result = await session.execute(query)
        candidates = []
        for rtype, occ in result:
            adult_bed = occ.adult_bed if occ else 0
            if adult_bed < base_adult_bed:
                continue  # только >= по местам
            size = rtype.size_value or 0
            price = rtype.position or 0
            # Считаем разницу для сортировки
            diff_adult_bed = adult_bed - base_adult_bed
            diff_size = abs(size - base_size)
            diff_price = abs((price or 0) - (base_price or 0))
            # Получаем первое изображение
            image_query = select(RoomTypeImage.url).where(
                RoomTypeImage.room_type_id == rtype.id
            ).order_by(RoomTypeImage.position).limit(1)
            image_result = await session.execute(image_query)
            first_image = image_result.scalar()
            candidates.append({
                "obj": MainRoomType(
                    id=rtype.id,
                    name=rtype.name,
                    description=rtype.description,
                    price=price,
                    adult_bed=adult_bed,
                    image=first_image
                ),
                "diff_adult_bed": diff_adult_bed,
                "diff_size": diff_size,
                "diff_price": diff_price
            })
        # Сортировка: сначала по diff_adult_bed, потом по diff_size, потом по diff_price
        candidates.sort(key=lambda x: (x["diff_adult_bed"], x["diff_size"], x["diff_price"]))
        return [c["obj"] for c in candidates[:limit]]


# CRUD операции для текстовых отзывов
async def get_feedbacks() -> List[Feedback]:
    """Получить все текстовые отзывы"""
    async with async_session() as session:
        query = select(FeedbackModel).order_by(FeedbackModel.created_at.desc())
        result = await session.execute(query)
        feedbacks = result.scalars().all()
        return [Feedback.model_validate(feedback) for feedback in feedbacks]


async def create_feedback(feedback_data: FeedbackCreate) -> Feedback:
    """Создать новый текстовый отзыв"""
    try:
        async with async_session() as session:
            feedback = FeedbackModel(
                text=feedback_data.text,
                rate=feedback_data.rate
            )
            session.add(feedback)
            await session.commit()
            await session.refresh(feedback)
            return Feedback.model_validate(feedback)
    except Exception as e:
        print(f"Ошибка при создании отзыва: {e}")
        raise


async def delete_feedback(feedback_id: int) -> bool:
    try:
        async with async_session() as session:
            result = await session.execute(
                delete(FeedbackModel).where(FeedbackModel.id == feedback_id)
            )
            await session.commit()
            affected = getattr(result, "rowcount", None)
            return (affected or 0) > 0
    except Exception as e:
        print(f"Ошибка при удалении отзыва: {e}")
        return False


async def get_feedback_by_id(feedback_id: int) -> Optional[Feedback]:
    """Получить текстовый отзыв по ID"""
    async with async_session() as session:
        query = select(FeedbackModel).where(FeedbackModel.id == feedback_id)
        result = await session.execute(query)
        fb = result.scalar_one_or_none()
        return Feedback.model_validate(fb) if fb else None


# CRUD операции для видео отзывов
async def get_video_feedbacks() -> List[VideoFeedback]:
    """Получить все видео отзывы"""
    async with async_session() as session:
        query = select(VideoFeedbackModel).order_by(VideoFeedbackModel.created_at.desc())
        result = await session.execute(query)
        return result.scalars().all()


async def create_video_feedback(feedback_data: VideoFeedbackCreate) -> VideoFeedback:
    """Создать новый видео отзыв"""
    async with async_session() as session:
        feedback = VideoFeedbackModel(
            file=feedback_data.file,
            rate=feedback_data.rate
        )
        session.add(feedback)
        await session.commit()
        await session.refresh(feedback)
        return feedback


async def delete_video_feedback(feedback_uuid: str) -> bool:
    """Удалить видео отзыв по UUID"""
    async with async_session() as session:
        result = await session.execute(delete(VideoFeedbackModel).where(VideoFeedbackModel.uuid == feedback_uuid))
        await session.commit()
        return result.rowcount > 0


async def get_video_feedback_by_uuid(feedback_uuid: str) -> Optional[VideoFeedback]:
    """Получить видео отзыв по UUID"""
    async with async_session() as session:
        query = select(VideoFeedbackModel).where(VideoFeedbackModel.uuid == feedback_uuid)
        result = await session.execute(query)
        return result.scalar_one_or_none()

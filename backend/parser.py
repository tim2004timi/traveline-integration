import httpx
import asyncio
from config import Settings
from database import async_session, redis
from models import RoomType, RoomTypeImage, Amenity, Address, Occupancy, Placement
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
import logging

settings = Settings()
logger = logging.getLogger(__name__)

async def fetch_jwt():
    cache_key = "traveline_access_token"
    try:
        token = await redis.get(cache_key)
        if token:
            logger.info("fetch_jwt: token получен из кеша")
            return token

        async with httpx.AsyncClient() as client:
            data = {
                "grant_type": "client_credentials",
                "client_id": settings.TRAVELINE_CLIENT_ID,
                "client_secret": settings.TRAVELINE_CLIENT_SECRET,
            }
            resp = await client.post(settings.TRAVELINE_AUTH_URL, data=data)
            resp.raise_for_status()
            token = resp.json()["access_token"]
            await redis.set(cache_key, token, ex=14 * 60)
            logger.info("fetch_jwt: token успешно получен через API и сохранён в кеш")
            return token
    except Exception as e:
        logger.error(f"fetch_jwt: ошибка получения токена: {e}")
        raise

async def fetch_property_data(jwt: str):
    url = f"{settings.TRAVELINE_API_BASE_URL}/v1/properties/{settings.PROPERTY_ID}"
    headers = {"Authorization": f"Bearer {jwt}"}
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            logger.info("fetch_property_data: данные успешно получены из TravelLine API")
            return resp.json()
    except Exception as e:
        logger.error(f"fetch_property_data: ошибка получения данных: {e}")
        raise

async def save_room_types_to_db(data: dict):
    try:
        async with async_session() as session:
            # Очищаем старые данные (если нужно)
            await session.execute(delete(RoomType))
            await session.commit()

            room_types = data.get("roomTypes", [])
            for rt in room_types:
                # Используем ID из API
                room_type_id = rt.get("id")
                if not room_type_id:
                    logger.warning(f"RoomType без ID пропущен: {rt.get('name', 'Unknown')}")
                    continue
                
                room_type = RoomType(
                    id=room_type_id,  # Используем ID из API
                    name=rt.get("name"),
                    description=rt.get("description"),
                    size_value=rt.get("size", {}).get("value"),
                    category_code=rt.get("categoryCode"),
                    category_name=rt.get("categoryName"),
                    position=rt.get("position"),
                )
                session.add(room_type)

                # Images
                for i, img in enumerate(rt.get("images", [])):
                    session.add(RoomTypeImage(
                        room_type_id=room_type_id,  # Используем ID из API
                        url=img.get("url"),
                        position=i
                    ))

                # Amenities
                for amenity in rt.get("amenities", []):
                    session.add(Amenity(
                        room_type_id=room_type_id,  # Используем ID из API
                        code=amenity.get("code")
                    ))

                # Address
                addr = rt.get("address")
                if addr:
                    session.add(Address(
                        room_type_id=room_type_id,  # Используем ID из API
                        postal_code=addr.get("postalCode"),
                        country_code=addr.get("countryCode"),
                        region=addr.get("region"),
                        region_id=addr.get("regionId"),
                        city_name=addr.get("cityName"),
                        city_id=addr.get("cityId"),
                        address_line=addr.get("addressLine"),
                        latitude=addr.get("latitude"),
                        longitude=addr.get("longitude"),
                        remark=addr.get("remark"),
                    ))

                # Occupancy
                occ = rt.get("occupancy")
                if occ:
                    session.add(Occupancy(
                        room_type_id=room_type_id,  # Используем ID из API
                        adult_bed=occ.get("adultBed", 0),
                        extra_bed=occ.get("extraBed", 0),
                        child_without_bed=occ.get("childWithoutBed", 0),
                    ))

                # Placements
                for placement in rt.get("placements", []):
                    session.add(Placement(
                        room_type_id=room_type_id,  # Используем ID из API
                        kind=placement.get("kind"),
                        count=placement.get("count"),
                        min_age=placement.get("minAge"),
                        max_age=placement.get("maxAge"),
                    ))

            await session.commit()
            logger.info(f"save_room_types_to_db: успешно сохранено {len(room_types)} RoomType в БД")
    except Exception as e:
        logger.error(f"save_room_types_to_db: ошибка сохранения данных: {e}")
        raise

async def fetch_and_save_room_types():
    jwt = await fetch_jwt()
    data = await fetch_property_data(jwt)
    await save_room_types_to_db(data) 

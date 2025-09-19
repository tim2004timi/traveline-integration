import asyncio
import logging
from config import Settings
from parser import fetch_and_save_room_types

settings = Settings()
logger = logging.getLogger(__name__)


async def sync_task():
    """Задача для периодической синхронизации данных"""
    while True:
        try:
            logger.info("Запуск синхронизации данных...")
            await fetch_and_save_room_types()
            logger.info("Синхронизация завершена успешно")
        except Exception as e:
            logger.error(f"Ошибка синхронизации: {e}")
        
        # Ждем указанное количество минут
        await asyncio.sleep(settings.SYNC_INTERVAL_MINUTES * 60)


def start_sync_task():
    """Запускает задачу синхронизации в фоне"""
    asyncio.create_task(sync_task()) 
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import asyncio

from parser import fetch_and_save_room_types
from router import router
from scheduler import start_sync_task
from database import engine
from models import Base
from telegram import start_bot_task

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("App startup: creating database tables...")
    try:
        # Создаем таблицы в БД
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
        
        logger.info("Fetching and saving room types from TravelLine API...")
        await fetch_and_save_room_types()
        logger.info("Room types successfully fetched and saved.")
        
        # Запускаем задачу синхронизации в фоне
        start_sync_task()
        logger.info("Синхронизация запущена в фоне")
        
        # Запускаем Telegram бота
        start_bot_task()
        logger.info("Telegram bot запущен")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
    yield
    logger.info("App shutdown.")

app = FastAPI(lifespan=lifespan)

# Пример настройки CORS (можно изменить по необходимости)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер с префиксом api/
app.include_router(router, prefix="/api")

@app.get("/health/")
async def root():
    return {"message": "TravelLine Integration API is running"}
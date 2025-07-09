from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import threading

from parser import fetch_and_save_room_types
from router import router
from scheduler import start_sync_task

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("App startup: fetching and saving room types from TravelLine API...")
    try:
        await fetch_and_save_room_types()
        logger.info("Room types successfully fetched and saved.")
        
        # Запускаем задачу синхронизации в отдельном потоке
        sync_thread = threading.Thread(target=start_sync_task, daemon=True)
        sync_thread.start()
        logger.info("Синхронизация запущена в отдельном потоке")
        
    except Exception as e:
        logger.error(f"Error during initial fetch: {e}")
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
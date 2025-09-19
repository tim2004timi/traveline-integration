from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from redis.asyncio import Redis
from config import Settings

Base = declarative_base()
settings = Settings()

# Async SQLAlchemy engine/session
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# Dependency for FastAPI
async def get_async_session():
    async with async_session() as session:
        yield session
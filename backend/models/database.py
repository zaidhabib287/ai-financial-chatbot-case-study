from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.config.settings import settings

# For SQLite, we need to modify the URL for async
if settings.database_url.startswith("sqlite"):
    # Convert sqlite:/// to sqlite+aiosqlite:///
    SQLALCHEMY_DATABASE_URL = settings.database_url.replace(
        "sqlite:///", "sqlite+aiosqlite:///"
    )
else:
    # For PostgreSQL, convert to async
    SQLALCHEMY_DATABASE_URL = settings.database_url.replace(
        "postgresql://", "postgresql+asyncpg://"
    )

# Create async engine
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=settings.debug, future=True)

# Create session factory
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Create base class for models
Base = declarative_base()


# Dependency to get DB session
async def get_db():
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

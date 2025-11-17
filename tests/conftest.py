import os
import asyncio
import shutil
import pytest
from httpx import AsyncClient

# 1) Point to test env BEFORE importing app/settings
os.environ["ENVIRONMENT"] = "test"
os.environ["PYTHONUNBUFFERED"] = "1"
# Load dotenv if you prefer: from dotenv import load_dotenv; load_dotenv(".env.test")

# Ensure test paths exist/are clean
os.makedirs("./data/uploads_test", exist_ok=True)
if os.path.exists("./data/vectordb_test"):
    shutil.rmtree("./data/vectordb_test", ignore_errors=True)
os.makedirs("./data/vectordb_test", exist_ok=True)

from backend.config.settings import settings  # now instantiated
settings.environment = "test"
settings.database_url = "sqlite:///./test.db"
settings.upload_dir = "./data/uploads_test"
settings.vector_db_path = "./data/vectordb_test"
settings.mock_api_delay = 0
settings.mock_api_failure_rate = 0

from backend.main import app
from backend.models.database import engine, Base

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def _db_setup():
    # Fresh DB schema for the test session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
import asyncio
from typing import AsyncGenerator, Generator, Any

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db_async
from app.main import create_app

# Use an in-memory SQLite database for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Create test engine and session
engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True,
)
TestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest_asyncio.fixture(scope="function")
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test case."""
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create a new session
    async with TestingSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    # Clean up tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
def app(db: AsyncSession) -> Generator[FastAPI, None, None]:
    """Create a FastAPI test application with overridden dependencies."""
    # Create the app with test settings
    app = create_app()
    
    # Override the database dependency
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        try:
            yield db
        finally:
            await db.rollback()
    
    app.dependency_overrides[get_db_async] = override_get_db
    
    yield app
    
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(app: FastAPI) -> Generator[TestClient, None, None]:
    """Create a test client for making HTTP requests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

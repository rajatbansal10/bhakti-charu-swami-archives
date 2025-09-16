from datetime import datetime
from typing import Any, AsyncGenerator

from sqlalchemy import Column, DateTime, Integer, event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, declared_attr, sessionmaker
from sqlalchemy.pool import NullPool

from app.config import settings

# Create async engine
if settings.APP_ENV == "test":
    # Use NullPool for tests to ensure clean state
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=settings.DEBUG,
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
        pool_recycle=300,  # Recycle connections after 5 minutes
    )

# Create async session factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Base model class with common columns and methods."""

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @declared_attr
    def __tablename__(cls) -> str:
        """
        Generate __tablename__ automatically from class name.
        Converts CamelCase to snake_case and appends 's' for pluralization.
        """
        name = ""
        for i, c in enumerate(cls.__name__):
            if i > 0 and c.isupper():
                name += "_"
            name += c.lower()
        return f"{name}s"

    def to_dict(self) -> dict[str, Any]:
        """Convert model instance to dictionary."""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
            if column.name not in ["password_hash", "otp_secret"]
        }


# Set up event listeners for updated_at
@event.listens_for(Base, "before_update", propagate=True)
def before_update(mapper, connection, target):
    """Update the updated_at timestamp before any update."""
    target.updated_at = datetime.utcnow()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function that yields db sessions.
    Handles session cleanup automatically.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all database tables. Only for testing!"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

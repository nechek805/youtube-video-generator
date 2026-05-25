from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import config

class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    config.get_database_url(),
    echo=False,
    pool_pre_ping=True
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    """Yield a session that does NOT expire attributes on commit.

    Using AsyncSessionLocal (expire_on_commit=False) is required for
    async SQLAlchemy: otherwise, every commit invalidates loaded
    relationships and the next attribute access tries to lazy-load
    from outside a greenlet, raising
    "greenlet_spawn has not been called".
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

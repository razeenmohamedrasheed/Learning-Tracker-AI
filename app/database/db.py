from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config.config import settings
from typing import AsyncGenerator


class Base(DeclarativeBase):
    pass


# -------------------------------------------------------
# Async Engine — the actual connection to PostgreSQL
# -------------------------------------------------------
# engine is the low-level connection pool to your database.
# "async" means FastAPI won't freeze while waiting for DB queries —
# it can handle other requests in the meantime.
# -------------------------------------------------------
engine = create_async_engine(
    settings.ASYNC_DATABASE_URL,
    echo=settings.DEBUG,      # prints all SQL queries in terminal (useful for learning!)
    pool_size=5,              # max 5 simultaneous DB connections
    max_overflow=10,          # 10 extra connections allowed in burst
)


# -------------------------------------------------------
# Session Factory — creates DB sessions on demand
# -------------------------------------------------------
# A "session" is like a conversation with the database.
# You open it, do your queries, then close it.
# AsyncSessionLocal is a factory that creates these sessions.
# -------------------------------------------------------
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,   # keep objects accessible after commit
    autocommit=False,
    autoflush=False,
)


# -------------------------------------------------------
# OOP CONCEPT: GENERATOR FUNCTION as Dependency
# -------------------------------------------------------
# get_db() is used by FastAPI's dependency injection system.
# Every API route that needs the DB will receive a fresh session.
# "yield" makes it a generator — it gives the session to the route,
# waits for the route to finish, then closes the session automatically.
#
# This is ENCAPSULATION — the route doesn't need to know HOW
# to open/close a DB session. It just receives one and uses it.
# -------------------------------------------------------
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# -------------------------------------------------------
# create_tables() — used only in development
# In production we use Alembic migrations instead
# -------------------------------------------------------
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
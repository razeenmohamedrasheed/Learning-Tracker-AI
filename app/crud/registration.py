from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.registration import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalars().first()


async def get_user_by_contact(db: AsyncSession, contact: str) -> User | None:
    result = await db.execute(
        select(User).where(User.contact == contact)
    )
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    result = await db.execute(
        select(User).where(User.user_id == user_id)
    )
    return result.scalars().first()


async def get_user_by_user_code(
    db: AsyncSession,
    user_code: str,
) -> User | None:
    result = await db.execute(
        select(User).where(User.user_id == user_code)
    )
    return result.scalars().first()


async def create_user(
    db: AsyncSession,
    user_data: dict,
) -> User:
    new_user = User(**user_data)
    db.add(new_user)

    # flush() sends the INSERT to DB — this fires the trigger
    await db.flush()

    # FIX: refresh() is critical here — it fetches the trigger-generated
    # user_id (learn-0001) back from the DB into the Python object.
    # Without this, user_id stays NULL and SQLAlchemy raises FlushError.
    await db.refresh(new_user)

    return new_user
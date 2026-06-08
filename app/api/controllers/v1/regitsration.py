from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.registration import (
    get_user_by_email,
    get_user_by_contact,
    create_user,
)
from app.schemas.registration import (
    UserRegistration,
    UserResponse,
)
from app.utils.password_utility import hash_password


class AuthService:

    @staticmethod
    async def register_user(
        db: AsyncSession,
        payload: UserRegistration,
    ) -> UserResponse:
        """
        Registration flow:
        1. Check email uniqueness
        2. Check contact uniqueness
        3. Hash password
        4. Create user  ← DB trigger auto-sets user_id = learn-0001
        5. Commit transaction
        6. Return response
        """

        logger.info(
            f"Registration attempt started for email={payload.email}"
        )

        try:
            # --------------------------------------------------
            # Check if email already exists
            # --------------------------------------------------
            existing_email = await get_user_by_email(db, payload.email)

            if existing_email:
                logger.warning(
                    f"Registration failed - email already exists: "
                    f"{payload.email}"
                )
                raise ValueError("User with this email already exists")

            # --------------------------------------------------
            # Check if contact already exists
            # --------------------------------------------------
            existing_contact = await get_user_by_contact(db, payload.contact)

            if existing_contact:
                logger.warning(
                    f"Registration failed - contact already exists: "
                    f"{payload.contact}"
                )
                raise ValueError("User with this contact number already exists")

            # --------------------------------------------------
            # Hash password
            # --------------------------------------------------
            hashed_password = hash_password(payload.password)

            logger.info(
                f"Password hashed successfully for email={payload.email}"
            )

            # --------------------------------------------------
            # Build user payload
            # NOTE: user_id is intentionally excluded here.
            #       The PostgreSQL trigger (trg_generate_user_id)
            #       auto-generates it as learn-0001, learn-0002, etc.
            # --------------------------------------------------
            user_data = {
                "email": payload.email,
                "name": payload.name,
                "contact": payload.contact,
                "password_hash": hashed_password,
                "role_id": payload.role_id,
            }

            # --------------------------------------------------
            # Create user — trigger fires here and sets user_id
            # --------------------------------------------------
            new_user = await create_user(db, user_data)

            logger.info(
                f"User record created with user_id={new_user.user_id}"
            )

            # --------------------------------------------------
            # Commit transaction
            # --------------------------------------------------
            await db.commit()
            await db.refresh(new_user)

            logger.success(
                f"User registered successfully | "
                f"user_id={new_user.user_id} | "
                f"email={new_user.email}"
            )

            return UserResponse.model_validate(new_user)

        except ValueError:
            await db.rollback()
            raise

        except Exception as e:
            logger.exception(
                f"Unexpected error during registration: {e}"
            )
            await db.rollback()
            raise
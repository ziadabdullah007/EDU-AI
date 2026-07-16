"""
EduCore AI Platform — User Repository

Handles all database operations for User and RefreshToken records.
No business logic. Only queries and persistence.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for User database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        """
        Find a user by their email address.

        Args:
            email: The email to look up (case-insensitive search).

        Returns:
            The User instance or None if not found.
        """
        stmt = select(User).where(
            and_(User.email == email.lower(), User.deleted_at.is_(None))
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_by_id(self, user_id: UUID) -> User | None:
        """
        Find an active, non-deleted user by ID.

        Args:
            user_id: The user's UUID.

        Returns:
            The User instance or None.
        """
        stmt = select(User).where(
            and_(
                User.id == user_id,
                User.is_active.is_(True),
                User.deleted_at.is_(None),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_school_and_role(
        self,
        school_id: UUID,
        role: UserRole,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[list[User], int]:
        """
        List users by school and role with pagination.

        Returns:
            Tuple of (users list, total count).
        """
        base_stmt = select(User).where(
            and_(
                User.school_id == school_id,
                User.role == role,
                User.deleted_at.is_(None),
            )
        )
        total = await self.count(base_stmt)
        stmt = base_stmt.offset(offset).limit(limit)
        users = await self.execute_query(stmt)
        return users, total

    async def update_last_login(self, user_id: UUID) -> None:
        """
        Update the last_login_at timestamp for a user.

        Args:
            user_id: The user's UUID.
        """
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(last_login_at=datetime.now(UTC))
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def email_exists(self, email: str) -> bool:
        """
        Check if an email address is already registered.

        Args:
            email: The email to check.

        Returns:
            True if the email is taken, False otherwise.
        """
        stmt = select(User.id).where(User.email == email.lower())
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None


class RefreshTokenRepository(BaseRepository[RefreshToken]):
    """Repository for RefreshToken database operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(RefreshToken, session)

    async def get_valid_token(self, token_str: str) -> RefreshToken | None:
        """
        Find a refresh token that is not revoked and not expired.

        Args:
            token_str: The raw JWT refresh token string.

        Returns:
            The RefreshToken instance or None.
        """
        stmt = select(RefreshToken).where(
            and_(
                RefreshToken.token == token_str,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.expires_at > datetime.now(UTC),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke_token(self, token_str: str) -> None:
        """
        Mark a refresh token as revoked.

        Args:
            token_str: The JWT token string to revoke.
        """
        stmt = (
            update(RefreshToken)
            .where(RefreshToken.token == token_str)
            .values(is_revoked=True)
        )
        await self.session.execute(stmt)
        await self.session.flush()

    async def revoke_all_user_tokens(self, user_id: UUID) -> None:
        """
        Revoke all active refresh tokens for a user (logout all devices).

        Args:
            user_id: The user whose tokens to revoke.
        """
        stmt = (
            update(RefreshToken)
            .where(
                and_(
                    RefreshToken.user_id == user_id,
                    RefreshToken.is_revoked.is_(False),
                )
            )
            .values(is_revoked=True)
        )
        await self.session.execute(stmt)
        await self.session.flush()

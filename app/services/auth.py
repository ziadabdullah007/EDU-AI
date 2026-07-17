"""
EduCore AI Platform — Authentication Service

Contains all authentication and authorization business logic.
This service is the only place where authentication rules are enforced.

Business Rules:
- Email must be unique platform-wide.
- Passwords are always hashed before storage.
- Inactive users cannot authenticate.
- Refresh tokens rotate on every use.
- Logout revokes all tokens for the user.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.config.settings import get_settings
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    verify_password,
)
from app.exceptions.errors import (
    AccountDeactivatedException,
    AuthenticationException,
    ConflictException,
    ForbiddenException,
    NotFoundException,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User, UserRole
from app.repositories.user import RefreshTokenRepository, UserRepository
from app.schemas.auth import (
    AccessTokenResponse,
    ChangePasswordRequest,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
    UserResponse,
)

logger = get_logger(__name__)


class AuthService:
    """
    Service for all authentication and identity operations.

    Coordinates the UserRepository and RefreshTokenRepository to implement
    JWT-based authentication with token rotation.
    """

    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository,
    ) -> None:
        self._user_repo = user_repo
        self._token_repo = token_repo
        self._settings = get_settings()

    async def register(self, payload: RegisterRequest) -> UserResponse:
        """
        Register a new user on the platform.

        Business Rules:
        - Email must be unique across all schools and roles.
        - Password is hashed before storage.
        - SUPER_ADMIN role cannot self-register.

        Args:
            payload: Validated registration request.

        Returns:
            The newly created UserResponse.

        Raises:
            ConflictException: If the email is already registered.
            ForbiddenException: If attempting to self-register as SUPER_ADMIN.
        """
        if payload.role == UserRole.SUPER_ADMIN:
            raise ForbiddenException(
                "SUPER_ADMIN accounts cannot be self-registered."
            )

        if await self._user_repo.email_exists(payload.email):
            raise ConflictException(
                f"Email address '{payload.email}' is already registered."
            )

        user = User(
            email=payload.email.lower(),
            password_hash=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            role=payload.role,
        )
        created_user = await self._user_repo.create(user)

        logger.info("user_registered", user_id=str(created_user.id), role=payload.role)
        return UserResponse.model_validate(created_user)

    async def login(self, payload: LoginRequest) -> TokenResponse:
        """
        Authenticate a user and issue JWT tokens.

        Business Rules:
        - Email lookup is case-insensitive.
        - Inactive users receive a specific error, not a generic auth failure.
        - last_login_at is updated on every successful login.
        - Tokens are issued with role and school_id claims.

        Args:
            payload: Login credentials.

        Returns:
            TokenResponse with access and refresh tokens.

        Raises:
            AuthenticationException: If credentials are invalid.
            AccountDeactivatedException: If the account is deactivated.
        """
        user = await self._user_repo.get_by_email(payload.email)

        if user is None or not verify_password(payload.password, user.password_hash):
            logger.warning("login_failed", email=payload.email)
            raise AuthenticationException("Invalid email address or password.")

        if not user.is_active:
            raise AccountDeactivatedException()

        await self._user_repo.update_last_login(user.id)
        access_token = create_access_token(
            user_id=user.id,
            role=user.role.value,
            school_id=user.school_id,
        )
        raw_refresh = create_refresh_token(user.id)

        token_record = RefreshToken(
            user_id=user.id,
            token=raw_refresh,
            expires_at=datetime.now(UTC)
            + timedelta(days=self._settings.jwt_refresh_token_expire_days),
        )
        await self._token_repo.create(token_record)

        logger.info("user_logged_in", user_id=str(user.id))
        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            user=UserResponse.model_validate(user),
        )

    async def refresh_access_token(
        self, payload: RefreshTokenRequest
    ) -> AccessTokenResponse:
        """
        Rotate a refresh token and issue a new access token.

        Business Rules:
        - The refresh token must be valid and non-revoked.
        - The old token is revoked before issuing the new one (rotation).
        - The associated user must still be active.

        Args:
            payload: The refresh token string.

        Returns:
            A new access token.

        Raises:
            AuthenticationException: If the token is invalid or revoked.
        """
        token_record = await self._token_repo.get_valid_token(payload.refresh_token)
        if token_record is None:
            raise AuthenticationException("Refresh token is invalid or has expired.")

        user = await self._user_repo.get_active_by_id(token_record.user_id)
        if user is None:
            raise AuthenticationException("Token owner account is not active.")

        await self._token_repo.revoke_token(payload.refresh_token)
        new_access = create_access_token(
            user_id=user.id,
            role=user.role.value,
            school_id=user.school_id,
        )

        logger.info("token_refreshed", user_id=str(user.id))
        return AccessTokenResponse(access_token=new_access)

    async def logout(self, current_user: User) -> None:
        """
        Revoke all refresh tokens for the user (logout from all devices).

        Args:
            current_user: The authenticated user requesting logout.
        """
        await self._token_repo.revoke_all_user_tokens(current_user.id)
        logger.info("user_logged_out", user_id=str(current_user.id))

    async def change_password(
        self, current_user: User, payload: ChangePasswordRequest
    ) -> None:
        """
        Change the authenticated user's password.

        Business Rules:
        - Current password must be verified before allowing the change.
        - All existing tokens are revoked after a password change.

        Args:
            current_user: The authenticated user.
            payload: Current and new password.

        Raises:
            AuthenticationException: If the current password is incorrect.
        """
        if not verify_password(payload.current_password, current_user.password_hash):
            raise AuthenticationException("Current password is incorrect.")

        await self._user_repo.update(
            current_user.id, {"password_hash": hash_password(payload.new_password)}
        )
        await self._token_repo.revoke_all_user_tokens(current_user.id)

        logger.info("password_changed", user_id=str(current_user.id))

    async def get_current_user_profile(self, current_user: User) -> UserResponse:
        """
        Return the authenticated user's public profile.

        Args:
            current_user: The authenticated user.

        Returns:
            UserResponse without any sensitive fields.
        """
        return UserResponse.model_validate(current_user)

    async def deactivate_account(
        self, target_user_id: UUID, requesting_user: User
    ) -> None:
        """
        Deactivate a user account.

        Business Rules:
        - Only SUPER_ADMIN or SCHOOL_ADMIN in the same school can deactivate.
        - Deactivation revokes all tokens.
        - SUPER_ADMIN accounts cannot be deactivated by non-SUPER_ADMIN users.

        Args:
            target_user_id: UUID of the account to deactivate.
            requesting_user: The authenticated user performing the action.

        Raises:
            NotFoundException: If the target user does not exist.
            ForbiddenException: If the requesting user lacks permission.
        """
        target = await self._user_repo.get(target_user_id)
        if target is None:
            raise NotFoundException("User not found.")

        if target.role == UserRole.SUPER_ADMIN and requesting_user.role != UserRole.SUPER_ADMIN:
            raise ForbiddenException("Cannot deactivate a SUPER_ADMIN account.")

        if (
            requesting_user.role == UserRole.SCHOOL_ADMIN
            and target.school_id != requesting_user.school_id
        ):
            raise ForbiddenException("Cannot deactivate users from other schools.")

        await self._user_repo.update(target_user_id, {"is_active": False})
        await self._token_repo.revoke_all_user_tokens(target_user_id)

        logger.info(
            "account_deactivated",
            target_user_id=str(target_user_id),
            by_user_id=str(requesting_user.id),
        )

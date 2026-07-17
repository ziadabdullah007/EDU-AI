"""
EduCore AI Platform — Create Super Admin Script

Bootstrap script for creating the first SUPER_ADMIN account.
Run once after deployment to initialize the platform.

Usage:
    python scripts/create_superadmin.py

Environment variables required (same as .env):
    DATABASE_URL, JWT_SECRET_KEY, etc.
"""

import asyncio
import os
import sys

# Allow running from the project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def create_superadmin() -> None:
    """Create the initial SUPER_ADMIN account."""
    from app.core.security import hash_password
    from app.database.session import get_session_factory
    from app.models.user import User, UserRole

    email = input("Super Admin Email: ").strip()
    first_name = input("First Name: ").strip()
    last_name = input("Last Name: ").strip()
    password = input("Password (min 8 chars): ").strip()

    if len(password) < 8:
        print("Error: Password must be at least 8 characters.")
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            email=email.lower(),
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            role=UserRole.SUPER_ADMIN,
            is_active=True,
        )
        session.add(user)
        await session.commit()
        print(f"\n✅ SUPER_ADMIN created successfully: {email}")
        print(f"   ID: {user.id}")


if __name__ == "__main__":
    asyncio.run(create_superadmin())

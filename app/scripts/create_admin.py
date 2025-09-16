#!/usr/bin/env python3
"""
Script to create an initial admin user.
Run with: python -m app.scripts.create_admin
"""
import asyncio
import getpass
import re
from datetime import datetime

from sqlalchemy import select

from app.db import async_session
from app.models import User, UserRole
from app.utils.security import get_password_hash


def is_valid_email(email: str) -> bool:
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_strong_password(password: str) -> bool:
    """Check if password meets security requirements."""
    if len(password) < 8:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[^A-Za-z0-9]', password):
        return False
    return True


async def create_admin_user():
    """Create an admin user with interactive input."""
    print("\n=== Create Admin User ===")
    
    # Get user input with validation
    while True:
        username = input("Username: ").strip()
        if username:
            break
        print("Username cannot be empty")
    
    while True:
        email = input("Email: ").strip()
        if is_valid_email(email):
            break
        print("Please enter a valid email address")
    
    while True:
        password = getpass.getpass("Password: ")
        if is_strong_password(password):
            confirm = getpass.getpass("Confirm password: ")
            if password == confirm:
                break
            print("Passwords do not match")
        else:
            print("""Password must be at least 8 characters long and contain:
            - At least one uppercase letter
            - At least one lowercase letter
            - At least one digit
            - At least one special character""")
    
    first_name = input("First name (optional): ").strip() or None
    last_name = input("Last name (optional): ").strip() or None
    
    # Create user
    async with async_session() as session:
        # Check if admin user already exists
        result = await session.execute(
            select(User).where(User.role == UserRole.ADMIN)
        )
        if result.scalars().first():
            print("\n[WARNING] Admin user already exists. Creating another admin user...")
        
        # Create new admin user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            role=UserRole.ADMIN,
            email_verified=True,
            password_hash=get_password_hash(password),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        print(f"\n✅ Admin user '{username}' created successfully!")
        print(f"User ID: {user.id}")
        print(f"Email: {email}")


if __name__ == "__main__":
    asyncio.run(create_admin_user())

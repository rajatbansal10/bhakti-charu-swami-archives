from typing import Optional, Tuple

from fastapi import Request, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy import select
from sqladmin.authentication import AuthenticationBackend
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db_async
from app.models import User, UserRole

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


class AdminAuthBackend(AuthenticationBackend):
    """Authentication backend for SQLAdmin interface."""
    
    async def login(self, request: Request) -> bool:
        """Handle login request."""
        form = await request.form()
        username = form.get("username")
        password = form.get("password")
        
        if not username or not password:
            return False
        
        # Verify credentials
        user = await self.authenticate_user(username, password)
        if not user:
            return False
        
        # Check if user has admin privileges
        if user.role != UserRole.ADMIN:
            return False
        
        # Store user ID in session
        request.session.update({"token": str(user.id)})
        return True
    
    async def logout(self, request: Request) -> bool:
        """Handle logout request."""
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> Optional[bool]:
        """Authenticate the request."""
        token = request.session.get("token")
        
        if not token:
            return False
        
        # Get user from token
        user = await self.get_current_user(token)
        if not user or user.role != UserRole.ADMIN:
            return False
        
        return True
    
    @staticmethod
    async def authenticate_user(username: str, password: str) -> Optional[User]:
        """Authenticate a user with username and password."""
        async with get_db_async() as db:
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalars().first()
            
            if not user:
                return None
            
            if not user.is_active():
                return None
            
            if not pwd_context.verify(password, user.password_hash):
                return None
            
            return user
    
    @staticmethod
    async def get_current_user(token: str) -> Optional[User]:
        """Get the current user from the token."""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            # In this simple implementation, the token is just the user ID
            user_id = int(token)
        except (ValueError, TypeError):
            raise credentials_exception
        
        async with get_db_async() as db:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalars().first()
            
            if user is None:
                raise credentials_exception
            
            return user


# Create an instance of the authentication backend
authentication_backend = AdminAuthBackend(secret_key=settings.SECRET_KEY)

# OAuth2 scheme for API authentication
async def get_current_user_from_token(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db_async),
) -> User:
    """Get the current user from an OAuth2 token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user_from_token),
) -> User:
    """Get the current active user."""
    if not current_user.is_active():
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


async def get_current_active_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get the current active admin user."""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

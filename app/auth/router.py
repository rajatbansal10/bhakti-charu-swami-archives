from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db_async
from app.models import User, UserRole, UserStatus
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_active_user,
)
from app.utils.email import send_verification_email, send_password_reset_email

router = APIRouter(prefix="/auth", tags=["auth"])

# Response models
class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    first_name: str
    last_name: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    status: str
    email_verified: bool
    created_at: datetime

    class Config:
        from_attributes = True

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db_async)):
    """Register a new user."""
    # Check if username or email already exists
    result = await db.execute(
        select(User).where(
            (User.username == user_data.username) | (User.email == user_data.email)
        )
    )
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username or email already registered",
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        password_hash=hashed_password,
        role=UserRole.VIEWER,  # Default role
        status=UserStatus.PENDING,  # Require email verification
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # Send verification email
    await send_verification_email(user)
    
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_async),
):
    """OAuth2 compatible token login, get an access token for future requests."""
    # Find user by username or email
    result = await db.execute(
        select(User).where(
            (User.username == form_data.username) | (User.email == form_data.username)
        )
    )
    user = result.scalars().first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is not active. Please check your email for verification.",
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    
    # Set secure HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        secure=not settings.DEBUG,
        samesite="lax",
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }

@router.post("/logout")
async def logout(response: Response):
    """Logout by removing the access token cookie."""
    response.delete_cookie("access_token")
    return {"message": "Successfully logged out"}

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user

@router.post("/verify-email/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db_async)):
    """Verify user's email using the verification token."""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )
    
    # Update user status to active
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    
    if user.status == UserStatus.ACTIVE:
        return {"message": "Email already verified"}
    
    user.status = UserStatus.ACTIVE
    user.email_verified = True
    await db.commit()
    
    return {"message": "Email verified successfully"}

@router.post("/forgot-password")
async def forgot_password(
    email: str, request: Request, db: AsyncSession = Depends(get_db_async)
):
    """Request a password reset email."""
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    
    if user:
        # Generate password reset token
        reset_token = create_access_token(
            data={"sub": user.username}, expires_delta=timedelta(hours=1)
        )
        
        # Send password reset email
        await send_password_reset_email(user, reset_token, request)
    
    # Always return success to prevent email enumeration
    return {"message": "If your email is registered, you will receive a password reset link"}

class ResetPassword(BaseModel):
    token: str
    new_password: str

@router.post("/reset-password")
async def reset_password(
    reset_data: ResetPassword, db: AsyncSession = Depends(get_db_async)
):
    """Reset password using the reset token."""
    try:
        payload = jwt.decode(
            reset_data.token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token"
        )
    
    # Update user's password
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    
    user.password_hash = get_password_hash(reset_data.new_password)
    await db.commit()
    
    return {"message": "Password updated successfully"}

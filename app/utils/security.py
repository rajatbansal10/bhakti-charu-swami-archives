from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db_async
from app.models import User, UserStatus

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Generate a bcrypt hash for the given password."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/token",
    auto_error=False,
)

# HTTP Bearer scheme for API token authentication
bearer_scheme = HTTPBearer(auto_error=False)

def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    
    return jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )

async def get_current_user(
    request: Request = None,
    token: str = Depends(oauth2_scheme),
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db_async),
) -> User:
    """Get the current authenticated user from the token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Try to get token from Authorization header or cookie
    token_value = None
    
    # Check Bearer token first
    if credentials and credentials.scheme == "Bearer":
        token_value = credentials.credentials
    # Then check OAuth2 token
    elif token:
        token_value = token
    # Finally check cookies
    elif request:
        token_value = request.cookies.get("access_token")
        if token_value and token_value.startswith("Bearer "):
            token_value = token_value[7:]  # Remove 'Bearer ' prefix
    
    if not token_value:
        raise credentials_exception
    
    try:
        payload = jwt.decode(
            token_value, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Check token type
        token_type = payload.get("type")
        if token_type != "access":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get user from database
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalars().first()
    
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get the current active user."""
    if current_user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Inactive user"
        )
    return current_user

async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get the current admin user."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

def verify_csrf_token(csrf_token: str, request: Request) -> bool:
    """Verify CSRF token from request."""
    if not csrf_token:
        return False
    
    # Get CSRF token from session
    session_token = request.session.get("csrf_token")
    if not session_token:
        return False
    
    # Verify token matches
    return csrf_token == session_token

def generate_csrf_token() -> str:
    """Generate a new CSRF token."""
    return jwt.encode(
        {"timestamp": str(datetime.utcnow().timestamp())},
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )

def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    if x_forwarded_for := request.headers.get("X-Forwarded-For"):
        return x_forwarded_for.split(",")[0]
    return request.client.host if request.client else "unknown"

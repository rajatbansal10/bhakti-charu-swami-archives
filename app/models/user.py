from datetime import datetime, timedelta
from enum import Enum, auto
from typing import TYPE_CHECKING, Optional

from passlib.context import CryptContext
from pydantic import EmailStr
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM as PGEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.asset import Asset

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserRole(str, Enum):
    """User roles with different permission levels."""
    VIEWER = "viewer"
    UPLOADER = "uploader"
    EDITOR = "editor"
    ADMIN = "admin"

    def __str__(self):
        return self.value

    @classmethod
    def from_string(cls, role_str: str) -> 'UserRole':
        """Convert string to UserRole enum."""
        try:
            return cls[role_str.upper()]
        except KeyError:
            raise ValueError(f"Invalid role: {role_str}")


class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"
    
    # Core fields
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    last_name: Mapped[Optional[str]] = mapped_column(String(100))
    mobile: Mapped[Optional[str]] = mapped_column(String(20))
    
    # Authentication
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    otp_secret: Mapped[Optional[str]] = mapped_column(String(255))
    otp_expires_at: Mapped[Optional[datetime]]
    
    # Status and role
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role"),
        default=UserRole.VIEWER,
        nullable=False,
    )
    status: Mapped[UserStatus] = mapped_column(
        SQLEnum(UserStatus, name="user_status"),
        default=UserStatus.ACTIVE,
        nullable=False,
    )
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]]
    
    # Relationships
    assets: Mapped[list["Asset"]] = relationship(
        "Asset", back_populates="uploader", cascade="all, delete-orphan"
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        UniqueConstraint("username", name="uq_user_username"),
    )
    
    def __init__(self, **kwargs):
        if "password" in kwargs:
            self.set_password(kwargs.pop("password"))
        super().__init__(**kwargs)
    
    def set_password(self, password: str) -> None:
        """Hash password and store the hash."""
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return pwd_context.verify(password, self.password_hash)
    
    def generate_otp(self, expires_in: int = 300) -> str:
        """
        Generate a time-based OTP and store its hash.
        
        Args:
            expires_in: OTP validity period in seconds (default: 300)
            
        Returns:
            str: The generated OTP
        """
        import pyotp
        import secrets
        
        # Generate a random secret if none exists
        if not self.otp_secret:
            self.otp_secret = pyotp.random_base32()
        
        # Create TOTP instance
        totp = pyotp.TOTP(self.otp_secret, digits=6, interval=60)
        
        # Set expiration
        self.otp_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Generate and return OTP
        return totp.now()
    
    def verify_otp(self, otp: str) -> bool:
        """
        Verify the provided OTP.
        
        Args:
            otp: The OTP to verify
            
        Returns:
            bool: True if OTP is valid and not expired, False otherwise
        """
        if not self.otp_secret or not self.otp_expires_at:
            return False
            
        # Check if OTP is expired
        if datetime.utcnow() > self.otp_expires_at:
            return False
            
        # Verify OTP
        import pyotp
        totp = pyotp.TOTP(self.otp_secret, digits=6, interval=60)
        return totp.verify(otp)
    
    @property
    def full_name(self) -> str:
        """Return the full name of the user."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username
    
    def has_permission(self, required_role: UserRole) -> bool:
        """Check if user has the required role or higher."""
        role_hierarchy = {
            UserRole.VIEWER: 0,
            UserRole.UPLOADER: 1,
            UserRole.EDITOR: 2,
            UserRole.ADMIN: 3,
        }
        return role_hierarchy[self.role] >= role_hierarchy[required_role]
    
    def is_active(self) -> bool:
        """Check if the user is active."""
        return self.status == UserStatus.ACTIVE
    
    def to_dict(self) -> dict:
        """Convert user to dictionary, excluding sensitive data."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "role": self.role.value,
            "status": self.status.value,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

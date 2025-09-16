import pytest
from datetime import datetime, timedelta

from app.models.user import User, UserRole, UserStatus
from app.auth import get_password_hash


class TestUserModel:
    """Test cases for the User model."""

    @pytest.mark.asyncio
    async def test_create_user(self, db):
        """Test creating a new user."""
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            hashed_password=get_password_hash("testpass123"),
            role=UserRole.VIEWER,
            status=UserStatus.ACTIVE,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.role == UserRole.VIEWER
        assert user.status == UserStatus.ACTIVE
        assert user.is_active is True
        assert user.is_verified is False
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_verify_password(self):
        """Test password verification."""
        password = "securepassword123"
        hashed_password = get_password_hash(password)
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=hashed_password,
        )
        
        # Test correct password
        assert user.verify_password(password) is True
        # Test incorrect password
        assert user.verify_password("wrongpassword") is False

    @pytest.mark.parametrize("role,required_role,expected", [
        (UserRole.ADMIN, UserRole.VIEWER, True),
        (UserRole.EDITOR, UserRole.EDITOR, True),
        (UserRole.EDITOR, UserRole.ADMIN, False),
        (UserRole.VIEWER, UserRole.EDITOR, False),
    ])
    def test_has_permission(self, role, required_role, expected):
        """Test role-based permission checking."""
        user = User(
            username="testuser",
            email="test@example.com",
            role=role,
        )
        assert user.has_permission(required_role) == expected

    @pytest.mark.asyncio
    async def test_generate_otp(self, db):
        """Test OTP generation and verification."""
        user = User(
            username="testuser",
            email="test@example.com",
            hashed_password=get_password_hash("testpass123"),
        )
        
        # Generate OTP
        otp = user.generate_otp()
        assert len(otp) == 6
        assert user.otp_secret is not None
        assert user.otp_expires_at is not None
        assert user.otp_expires_at > datetime.utcnow()
        
        # Verify OTP
        assert user.verify_otp(otp) is True
        # Test with wrong OTP
        assert user.verify_otp("000000") is False
        
        # Test expired OTP
        user.otp_expires_at = datetime.utcnow() - timedelta(minutes=1)
        assert user.verify_otp(otp) is False

    def test_full_name_property(self):
        """Test the full_name property."""
        user = User(
            first_name="John",
            last_name="Doe",
        )
        assert user.full_name == "John Doe"
        
        # Test with missing last name
        user.last_name = None
        assert user.full_name == "John"
        
        # Test with missing first name
        user.first_name = None
        user.last_name = "Doe"
        assert user.full_name == "Doe"
        
        # Test with no names
        user.first_name = None
        user.last_name = None
        assert user.full_name is None

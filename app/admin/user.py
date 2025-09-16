from typing import Any, Optional

from fastapi import Request
from sqladmin import ModelView
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models import User, UserRole, UserStatus


class UserAdmin(ModelView, model=User):
    """Admin interface for managing users."""
    
    # Display columns
    column_list = [
        User.id,
        User.username,
        User.email,
        User.first_name,
        User.last_name,
        User.role,
        User.status,
        User.email_verified,
        User.last_login,
        User.created_at,
    ]
    
    # Columns to include in the edit form
    form_columns = [
        'username',
        'email',
        'first_name',
        'last_name',
        'mobile',
        'role',
        'status',
        'email_verified',
    ]
    
    # Columns that can be used for searching
    column_searchable_list = [
        User.username,
        User.email,
        User.first_name,
        User.last_name,
    ]
    
    # Columns that can be used for filtering
    column_filters = [
        User.role,
        User.status,
        User.email_verified,
        User.created_at,
    ]
    
    # Column formatters
    column_formatters = {
        'last_login': lambda m, a: m.last_login.strftime('%Y-%m-%d %H:%M') if m.last_login else None,
    }
    
    # Export formats
    can_export = True
    export_types = ['csv', 'xlsx']
    
    # Page size for list view
    page_size = 50
    
    # Disable create, edit, delete based on user permissions
    def is_accessible(self, request: Request) -> bool:
        # Only allow access to admin users
        return request.state.user.role == UserRole.ADMIN if hasattr(request.state, 'user') else False
    
    def is_visible(self, request: Request) -> bool:
        # Only show in the menu for admin users
        return self.is_accessible(request)
    
    # Customize the form
    form_widget_args = {
        'password_hash': {
            'readonly': True
        },
        'otp_secret': {
            'readonly': True
        },
        'otp_expires_at': {
            'readonly': True
        },
    }
    
    # Prevent deleting the last admin user
    async def delete_model(self, request: Request, pk: Any) -> bool:
        # Check if this is the last admin
        session = request.state.session
        user = await session.get(User, pk)
        
        if user.role == UserRole.ADMIN:
            # Count other admin users
            stmt = select(User).where(User.role == UserRole.ADMIN, User.id != user.id)
            result = await session.execute(stmt)
            other_admins = result.scalars().all()
            
            if not other_admins:
                raise Exception("Cannot delete the last admin user")
        
        return await super().delete_model(request, pk)
    
    # Customize the list view query
    async def get_list(self, request: Request, *args, **kwargs):
        # Add eager loading for related models
        stmt = select(User).options(
            selectinload(User.assets)
        )
        
        # Apply search and filters
        stmt = await self._apply_search(stmt, request)
        stmt = await self._apply_filters(stmt, request)
        
        # Get pagination parameters
        skip, limit = await self._get_pagination_parameters(request)
        
        # Execute the query
        result = await request.state.session.execute(stmt.offset(skip).limit(limit))
        count_result = await request.state.session.execute(select(func.count()).select_from(stmt.subquery()))
        
        return result.scalars().all(), count_result.scalar_one()
    
    # Customize the detail view
    async def get_detail(self, request: Request, pk: Any) -> Optional[dict]:
        # Get the user with relationships loaded
        stmt = select(User).options(
            selectinload(User.assets)
        ).where(User.id == pk)
        
        result = await request.state.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        # Convert to dict and remove sensitive data
        data = {c.name: getattr(user, c.name) for c in user.__table__.columns}
        data.pop('password_hash', None)
        data.pop('otp_secret', None)
        
        # Add related data
        data['assets'] = [asset.to_dict() for asset in user.assets]
        
        return data

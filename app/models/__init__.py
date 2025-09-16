# Import all models here to make them accessible via app.models
from .user import User, UserRole, UserStatus
from .asset import Asset, AssetType, AssetStatus, AssetCategory
from .audit_log import AuditLog, AuditAction

# This makes it easier to import all models in one go
__all__ = [
    'User', 'UserRole', 'UserStatus',
    'Asset', 'AssetType', 'AssetStatus', 'AssetCategory',
    'AuditLog', 'AuditAction',
]

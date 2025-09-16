from .user import UserAdmin
from .asset import AssetAdmin
from .audit_log import AuditLogAdmin
from .auth import authentication_backend

# List of all admin views
__all__ = [
    'UserAdmin',
    'AssetAdmin',
    'AuditLogAdmin',
    'authentication_backend',
]

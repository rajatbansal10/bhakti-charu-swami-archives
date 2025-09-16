import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqladmin import Admin

from app.admin import UserAdmin, AssetAdmin, AuditLogAdmin
from app.admin.auth import authentication_backend
from app.config import settings
from app.db import engine, Base, create_tables, get_db_async
from app.middleware import AuditLogMiddleware
from app.models import User

# Create database tables on startup if they don't exist
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Handle application startup and shutdown events."""
    # Create database tables if they don't exist
    await create_tables()
    
    # Create admin user if it doesn't exist
    await create_initial_admin()
    
    # Add any other startup logic here
    yield
    
    # Add any cleanup logic here


async def create_initial_admin() -> None:
    """Create an initial admin user if no users exist."""
    from app.models import UserRole, UserStatus
    from app.auth import get_password_hash
    
    async with get_db_async() as db:
        # Check if any users exist
        result = await db.execute("SELECT COUNT(*) FROM users")
        user_count = result.scalar_one()
        
        if user_count == 0 and settings.ADMIN_EMAIL and settings.ADMIN_PASSWORD:
            # Create admin user
            admin_user = User(
                username="admin",
                email=settings.ADMIN_EMAIL,
                first_name="Admin",
                last_name="User",
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                email_verified=True,
                password_hash=get_password_hash(settings.ADMIN_PASSWORD),
            )
            
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)
            
            print(f"Created initial admin user with email: {settings.ADMIN_EMAIL}")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        description="Veda Foundation — Bhakti Charu Swami Archives API",
        version="0.1.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add audit logging middleware
    app.add_middleware(AuditLogMiddleware)
    
    # Mount static files
    os.makedirs("static", exist_ok=True)
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Setup SQLAdmin with authentication
    admin = Admin(
        app=app,
        engine=engine,
        base_url="/admin",
        authentication_backend=authentication_backend,
        title="Veda Foundation Admin",
        logo_url="https://vedabase.io/static/img/vedabase-logo.png",
    )
    
    # Add admin views
    admin.add_view(UserAdmin)
    admin.add_view(AssetAdmin)
    admin.add_view(AuditLogAdmin)
    
    # Import and include routers
    from app.api.v1.router import api_router
    app.include_router(api_router, prefix="/api/v1")
    
    # Import and include auth router
    from app.auth.router import auth_router
    app.include_router(auth_router, prefix="/auth", tags=["auth"])
    
    # Register exception handlers
    register_exception_handlers(app)
    
    return app


def register_exception_handlers(app: FastAPI) -> None:
    """Register exception handlers for the application."""
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle request validation errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": {
                    "errors": exc.errors(),
                    "body": exc.body,
                },
                "message": "Validation error",
            },
        )
    
    @app.exception_handler(404)
    async def not_found_exception_handler(request: Request, exc: Exception):
        """Handle 404 Not Found errors."""
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": "The requested resource was not found"},
        )
    
    @app.exception_handler(500)
    async def server_error_exception_handler(request: Request, exc: Exception):
        """Handle 500 Internal Server errors."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "message": "An internal server error occurred",
                "detail": str(exc) if settings.DEBUG else None,
            },
        )


# Create the FastAPI application
app = create_app()


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "ok", 
        "app": settings.APP_NAME, 
        "environment": settings.APP_ENV,
        "version": "0.1.0",
    }

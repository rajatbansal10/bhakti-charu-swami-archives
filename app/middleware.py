import json
import time
from datetime import datetime
from typing import Callable, Awaitable

from fastapi import Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.config import settings
from app.db import get_db
from app.models import AuditLog, AuditAction


class AuditLogMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Process the request and log the audit entry."""
        # Skip logging for certain paths
        if any(path in request.url.path for path in [
            "/static",
            "/health",
            "/favicon.ico",
            "/api/docs",
            "/api/redoc",
            "/api/openapi.json",
        ]):
            return await call_next(request)
        
        # Get client IP address
        client_host = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "")
        
        # Get user ID if authenticated
        user_id = None
        if hasattr(request.state, "user"):
            user_id = request.state.user.id
        
        # Prepare request details
        request_body = {}
        if request.method in ["POST", "PUT", "PATCH"] and "application/json" in request.headers.get("content-type", ""):
            try:
                request_body = await request.json()
                # Remove sensitive data
                for field in ["password", "new_password", "current_password", "token"]:
                    if field in request_body:
                        request_body[field] = "***REDACTED***"
            except json.JSONDecodeError:
                request_body = {"error": "Failed to parse JSON body"}
        
        # Determine the action type based on the request path and method
        action = self._determine_action(request.method, request.url.path)
        
        # Process the request and time it
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        # Add server timing header
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log the audit entry asynchronously
        await self._log_audit_entry(
            action=action,
            user_id=user_id,
            status_code=response.status_code,
            client_host=client_host,
            user_agent=user_agent,
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            request_body=request_body,
            process_time=process_time,
        )
        
        return response
    
    def _determine_action(self, method: str, path: str) -> AuditAction:
        """Determine the audit action based on the request method and path."""
        path_parts = path.strip("/").split("/")
        
        # Auth actions
        if path == "/auth/login" and method == "POST":
            return AuditAction.USER_LOGIN
        elif path == "/auth/logout" and method == "POST":
            return AuditAction.USER_LOGOUT
        elif path == "/auth/register" and method == "POST":
            return AuditAction.USER_CREATE
        elif path.startswith("/auth/password/change") and method == "POST":
            return AuditAction.USER_PASSWORD_CHANGE
        elif path.startswith("/auth/password/reset") and method == "POST":
            return AuditAction.USER_PASSWORD_RESET
        
        # User management actions
        if path_parts[0] == "users":
            if method == "POST":
                return AuditAction.USER_CREATE
            elif method in ["PUT", "PATCH"]:
                return AuditAction.USER_UPDATE
            elif method == "DELETE":
                return AuditAction.USER_DELETE
        
        # Asset actions
        elif path_parts[0] == "assets":
            if method == "POST":
                return AuditAction.ASSET_UPLOAD
            elif method in ["PUT", "PATCH"]:
                return AuditAction.ASSET_UPDATE
            elif method == "DELETE":
                return AuditAction.ASSET_DELETE
            elif method == "GET" and len(path_parts) > 1 and path_parts[1].isdigit():
                return AuditAction.ASSET_DOWNLOAD
        
        # Default action based on HTTP method
        return {
            "GET": AuditAction.READ,
            "POST": AuditAction.CREATE,
            "PUT": AuditAction.UPDATE,
            "PATCH": AuditAction.UPDATE,
            "DELETE": AuditAction.DELETE,
        }.get(method, AuditAction.READ)
    
    async def _log_audit_entry(
        self,
        action: AuditAction,
        user_id: int = None,
        status_code: int = None,
        client_host: str = None,
        user_agent: str = None,
        method: str = None,
        path: str = None,
        query_params: dict = None,
        request_body: dict = None,
        process_time: float = None,
    ) -> None:
        """Create an audit log entry asynchronously."""
        # Don't log successful health checks
        if path == "/health" and status_code == status.HTTP_200_OK:
            return
        
        # Prepare metadata
        metadata = {
            "method": method,
            "path": path,
            "query_params": query_params or {},
            "process_time_seconds": round(process_time, 4) if process_time else None,
        }
        
        # Add request body if present (except for sensitive endpoints)
        if request_body and not any(p in path for p in [
            "/auth/login",
            "/auth/register",
            "/auth/password",
        ]):
            metadata["request_body"] = request_body
        
        # Create the audit log entry
        audit_log = AuditLog(
            action=action,
            user_id=user_id,
            status_code=status_code,
            ip_address=client_host,
            user_agent=user_agent,
            metadata=metadata,
        )
        
        # Save to database in the background
        async with get_db() as db:
            db.add(audit_log)
            await db.commit()
            await db.refresh(audit_log)

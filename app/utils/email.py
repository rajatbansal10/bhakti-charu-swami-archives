import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional, Dict, Any

from fastapi import Request
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

from app.config import settings
from app.models import User

logger = logging.getLogger(__name__)

# Email templates directory
TEMPLATES_DIR = Path(__file__).parent.parent / "templates" / "emails"

# Initialize Jinja2 environment
env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

class EmailService:
    """Service for sending emails."""
    
    def __init__(self):
        self.smtp_server = settings.SMTP_SERVER
        self.smtp_port = settings.SMTP_PORT
        self.smtp_username = settings.SMTP_USERNAME
        self.smtp_password = settings.SMTP_PASSWORD
        self.sender_email = settings.EMAIL_FROM
        self.site_name = settings.APP_NAME
        self.base_url = settings.FRONTEND_URL or "http://localhost:3000"
    
    def _send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = "",
    ) -> bool:
        """Send an email using SMTP."""
        if not all([self.smtp_server, self.smtp_port, self.sender_email]):
            logger.warning("Email configuration is incomplete. Email not sent.")
            return False
        
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{self.site_name} <{self.sender_email}>"
        msg['To'] = to_email
        
        # Attach parts (text and HTML)
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        try:
            # Connect to SMTP server and send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if settings.SMTP_USE_TLS:
                    server.starttls()
                
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                
                server.send_message(msg)
                logger.info(f"Email sent to {to_email}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    def _render_template(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Render an email template with the given context."""
        if context is None:
            context = {}
        
        # Add common context
        context.setdefault('site_name', self.site_name)
        context.setdefault('base_url', self.base_url)
        
        template = env.get_template(template_name)
        return template.render(**context)
    
    async def send_verification_email(
        self,
        user: User,
        request: Optional[Request] = None,
    ) -> bool:
        """Send an email verification email to the user."""
        from app.utils.security import create_access_token
        
        # Generate verification token (expires in 24 hours)
        token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(hours=24)
        )
        
        # Build verification URL
        verification_url = f"{self.base_url}/verify-email/{token}"
        
        # Render email template
        context = {
            'user': user,
            'verification_url': verification_url,
        }
        
        subject = f"Verify your email for {self.site_name}"
        html_content = self._render_template("verify_email.html", context)
        text_content = self._render_template("verify_email.txt", context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
    
    async def send_password_reset_email(
        self,
        user: User,
        reset_token: str,
        request: Optional[Request] = None,
    ) -> bool:
        """Send a password reset email to the user."""
        # Build reset URL
        reset_url = f"{self.base_url}/reset-password?token={reset_token}"
        
        # Get client IP for security notice
        client_ip = None
        if request:
            client_ip = request.client.host if request.client else "unknown"
        
        # Render email template
        context = {
            'user': user,
            'reset_url': reset_url,
            'client_ip': client_ip,
            'expires_hours': 1,  # Token expires in 1 hour
        }
        
        subject = f"Password reset request for {self.site_name}"
        html_content = self._render_template("password_reset.html", context)
        text_content = self._render_template("password_reset.txt", context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )
    
    async def send_welcome_email(
        self,
        user: User,
        password: Optional[str] = None,
    ) -> bool:
        """Send a welcome email to a new user."""
        context = {
            'user': user,
            'password': password,  # Only included for new accounts with generated passwords
        }
        
        subject = f"Welcome to {self.site_name}!"
        html_content = self._render_template("welcome.html", context)
        text_content = self._render_template("welcome.txt", context)
        
        return self._send_email(
            to_email=user.email,
            subject=subject,
            html_content=html_content,
            text_content=text_content,
        )

# Create a singleton instance
email_service = EmailService()

# Helper functions for direct imports
async def send_verification_email(user: User, request: Optional[Request] = None) -> bool:
    """Send a verification email to the user."""
    return await email_service.send_verification_email(user, request)

async def send_password_reset_email(user: User, token: str, request: Optional[Request] = None) -> bool:
    """Send a password reset email to the user."""
    return await email_service.send_password_reset_email(user, token, request)

async def send_welcome_email(user: User, password: Optional[str] = None) -> bool:
    """Send a welcome email to a new user."""
    return await email_service.send_welcome_email(user, password)

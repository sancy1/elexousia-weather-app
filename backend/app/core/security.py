"""
FILE: backend/app/core/security.py
Security utilities for session tokens and OAuth state
"""

import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings


def generate_session_token() -> str:
    """
    Generate a secure 32-byte URL-safe random session token.
    Returns base64 encoded string.
    """
    random_bytes = secrets.token_bytes(32)
    token = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
    return token


def hash_session_token(token: str) -> str:
    """
    Hash a session token for storage in database.
    Uses SHA-256.
    """
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def verify_session_token(token: str, hashed_token: str) -> bool:
    """
    Verify a session token against its hashed version.
    """
    return hash_session_token(token) == hashed_token


def generate_oauth_state() -> str:
    """
    Generate a CSRF protection token for OAuth flows.
    Returns a 32-byte URL-safe random string.
    """
    random_bytes = secrets.token_bytes(32)
    state = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
    return state


def verify_oauth_state(state: str, stored_state: str) -> bool:
    """
    Verify OAuth state matches stored state.
    """
    if not state or not stored_state:
        return False
    return secrets.compare_digest(state, stored_state)


def get_session_expiry() -> datetime:
    """
    Get session expiry datetime (default: 24 hours from now).
    """
    return datetime.now() + timedelta(days=settings.SESSION_EXPIRY_DAYS)


def is_session_expired(expires_at: datetime) -> bool:
    """
    Check if a session has expired.
    """
    return datetime.now() > expires_at


def generate_user_initials(name: Optional[str], email: str) -> str:
    """
    Generate user initials from name or email.
    Examples:
        - "John Doe" -> "JD"
        - "john@example.com" -> "JO"
    """
    if name:
        parts = name.strip().split()
        if len(parts) >= 2:
            return (parts[0][0] + parts[-1][0]).upper()
        elif parts:
            return (parts[0][0] + (parts[0][1] if len(parts[0]) > 1 else 'X')).upper()
    
    # Fallback to email
    if email:
        email_prefix = email.split('@')[0]
        if len(email_prefix) >= 2:
            return email_prefix[:2].upper()
        return email_prefix.upper() if email_prefix else 'U'
    
    return 'U'


# Make sure all functions are exported
__all__ = [
    'generate_session_token',
    'hash_session_token', 
    'verify_session_token',
    'generate_oauth_state',
    'verify_oauth_state',
    'get_session_expiry',
    'is_session_expired',
    'generate_user_initials'
]
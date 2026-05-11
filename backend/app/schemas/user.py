"""
FILE: backend/app/schemas/user.py
Pydantic schemas for authentication and user management
"""

from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserProfile(BaseModel):
    """User profile response schema."""
    id: int
    name: Optional[str] = None
    email: EmailStr
    avatar_url: Optional[str] = None
    initials: Optional[str] = None
    unit_preference: Literal['C', 'F'] = 'C'
    theme: Literal['light', 'dark', 'system'] = 'system'
    provider: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionResponse(BaseModel):
    """Session creation response schema."""
    session_token: str
    expires_at: datetime
    user: UserProfile


class PreferencesUpdate(BaseModel):
    """Update user preferences request schema."""
    unit_preference: Optional[Literal['C', 'F']] = None
    theme: Optional[Literal['light', 'dark', 'system']] = None


class OAuthCallback(BaseModel):
    """OAuth callback query parameters."""
    code: str
    state: Optional[str] = None
    error: Optional[str] = None


class AuthResponse(BaseModel):
    """Authentication response schema."""
    success: bool
    user: Optional[UserProfile] = None
    message: str


class LogoutResponse(BaseModel):
    """Logout response schema."""
    success: bool
    message: str
"""
FILE: backend/app/api/routes/auth.py
Authentication routes - Social Login only (Google & GitHub)
No email/password authentication
"""

from fastapi import APIRouter, Request, Response, HTTPException, status, Depends
from fastapi.responses import RedirectResponse
from typing import Optional
import logging
import httpx
import os

from app.api.dependencies import get_current_user, get_optional_user
from app.schemas.user import UserProfile, PreferencesUpdate, LogoutResponse
from app.infrastructure.repositories.user_repository import UserRepository
from app.core.security import generate_session_token, generate_oauth_state
from app.core.oauth import oauth

logger = logging.getLogger(__name__)

# Frontend URL for OAuth callbacks (use environment variable for flexibility)
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ============================================================
# GOOGLE OAuth - Social Login
# ============================================================

@router.get("/google")
async def google_login(request: Request):
    """
    Redirect user to Google OAuth consent screen.
    User approves, then redirects back to /google/callback
    """
    try:
        # Generate state for CSRF protection
        state = generate_oauth_state()
        request.session['oauth_state'] = state
        
        # Redirect to Google
        redirect_uri = request.url_for('google_callback')
        return await oauth.google.authorize_redirect(request, redirect_uri, state=state)
    except Exception as e:
        logger.error(f"Google OAuth init failed: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth initialization failed: {str(e)}")


@router.get("/google/callback")
async def google_callback(request: Request):
    """
    Handle Google OAuth callback.
    Exchanges code for user info, creates/updates user, sets session cookie.
    """
    try:
        # Exchange code for access token
        token = await oauth.google.authorize_access_token(request)
        
        # Get user info from userinfo endpoint (more reliable than id_token)
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f"Bearer {token['access_token']}"}
            )
            user_info = resp.json()
        
        # Extract user data
        email = user_info.get('email')
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        
        name = user_info.get('name')
        avatar_url = user_info.get('picture')
        provider_id = user_info.get('id')
        
        # Upsert user in database
        user = await UserRepository.upsert_user(
            provider='google',
            provider_id=str(provider_id),
            email=email,
            name=name,
            avatar_url=avatar_url
        )
        
        # Create session token
        session_token = generate_session_token()
        
        # Get IP and User-Agent
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent')
        
        # Create session in database
        session = await UserRepository.create_session(
            user_id=user.id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Create response with redirect
        response = RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?success=true")
        
        # Set HTTP-only cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=True,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400,  # 24 hours
            path="/"
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Google OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


# ============================================================
# GITHUB OAuth - Social Login
# ============================================================

@router.get("/github")
async def github_login(request: Request):
    """
    Redirect user to GitHub OAuth consent screen.
    """
    try:
        # Generate state for CSRF protection
        state = generate_oauth_state()
        request.session['oauth_state'] = state
        
        # Redirect to GitHub
        redirect_uri = request.url_for('github_callback')
        return await oauth.github.authorize_redirect(request, redirect_uri, state=state)
    except Exception as e:
        logger.error(f"GitHub OAuth init failed: {e}")
        raise HTTPException(status_code=500, detail=f"OAuth initialization failed: {str(e)}")


@router.get("/github/callback")
async def github_callback(request: Request):
    """
    Handle GitHub OAuth callback.
    Exchanges code for user info, creates/updates user, sets session cookie.
    """
    try:
        # Exchange code for access token
        token = await oauth.github.authorize_access_token(request)
        
        # Get user info from GitHub API with increased timeout
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Get user profile
            user_resp = await client.get(
                'https://api.github.com/user',
                headers={'Authorization': f"Bearer {token['access_token']}"}
            )
            user_resp.raise_for_status()
            user_data = user_resp.json()
            
            # Get user email (GitHub may not return email in profile)
            email_resp = await client.get(
                'https://api.github.com/user/emails',
                headers={'Authorization': f"Bearer {token['access_token']}"}
            )
            email_resp.raise_for_status()
            emails = email_resp.json()
        
        # Find primary email
        email = None
        for e in emails:
            if e.get('primary') and e.get('verified'):
                email = e.get('email')
                break
        
        if not email:
            email = user_data.get('email')
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by GitHub")
        
        # Extract user data
        name = user_data.get('name') or user_data.get('login')
        avatar_url = user_data.get('avatar_url')
        provider_id = str(user_data.get('id'))
        
        # Upsert user in database
        user = await UserRepository.upsert_user(
            provider='github',
            provider_id=provider_id,
            email=email,
            name=name,
            avatar_url=avatar_url
        )
        
        # Create session token
        session_token = generate_session_token()
        
        # Get IP and User-Agent
        ip_address = request.client.host if request.client else None
        user_agent = request.headers.get('user-agent')
        
        # Create session in database
        session = await UserRepository.create_session(
            user_id=user.id,
            session_token=session_token,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Create response with redirect
        response = RedirectResponse(url=f"{FRONTEND_URL}/auth/callback?success=true")
        
        # Set HTTP-only cookie
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=86400,  # 24 hours
            path="/"
        )
        
        return response
        
    except httpx.TimeoutException as e:
        logger.error(f"GitHub API timeout: {e}")
        raise HTTPException(status_code=504, detail="GitHub API timeout. Please try again.")
    except httpx.HTTPStatusError as e:
        logger.error(f"GitHub API error: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=502, detail=f"GitHub API error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"GitHub OAuth callback failed: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")


# ============================================================
# USER PROFILE & PREFERENCES
# ============================================================

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    user = Depends(get_current_user)
):
    """
    Get current authenticated user's profile.
    Requires valid session cookie (set after OAuth login).
    """
    return UserProfile(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar_url=user.avatar_url,
        initials=user.initials,
        unit_preference=user.unit_preference,
        theme=user.theme,
        provider=user.provider,
        created_at=user.created_at
    )


@router.patch("/preferences", response_model=UserProfile)
async def update_user_preferences(
    preferences: PreferencesUpdate,
    user = Depends(get_current_user)
):
    """
    Update user preferences (unit_preference and/or theme).
    """
    updated_user = await UserRepository.update_preferences(
        user_id=user.id,
        unit_preference=preferences.unit_preference,
        theme=preferences.theme
    )
    
    return UserProfile(
        id=updated_user.id,
        name=updated_user.name,
        email=updated_user.email,
        avatar_url=updated_user.avatar_url,
        initials=updated_user.initials,
        unit_preference=updated_user.unit_preference,
        theme=updated_user.theme,
        provider=updated_user.provider,
        created_at=updated_user.created_at
    )


@router.delete("/logout", response_model=LogoutResponse)
async def logout(
    request: Request,
    response: Response,
    user = Depends(get_current_user)
):
    """
    Logout user - delete session and clear cookie.
    """
    # Get token from cookie or header
    token = request.cookies.get("session_token")
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
    
    if token:
        await UserRepository.delete_session(token)
    
    # Clear the cookie
    response.delete_cookie(
        key="session_token",
        path="/",
        httponly=True,
        samesite="lax"
    )
    
    return LogoutResponse(
        success=True,
        message="Successfully logged out"
    )


@router.get("/debug/token")
async def get_debug_token(request: Request, user = Depends(get_current_user)):
    """
    DEBUG ENDPOINT: Returns current session token for testing in Postman.
    Remove this endpoint in production.
    """
    token = request.cookies.get("session_token")
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.replace("Bearer ", "")
    
    return {
        "session_token": token,
        "user_id": user.id,
        "email": user.email,
        "note": "Use this token in Postman with Authorization: Bearer <token>"
    }
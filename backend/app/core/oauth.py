"""
FILE: backend/app/core/oauth.py
OAuth configuration for Google and GitHub (social login only)
"""

from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from app.core.config import settings

# Create OAuth instance
oauth = OAuth()

# Configure Google OAuth
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile',
        'redirect_uri': 'http://localhost:8000/api/auth/google/callback'
    }
)

# Configure GitHub OAuth
oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/user',
    client_kwargs={'scope': 'user:email'},
    redirect_uri='http://localhost:8000/api/auth/github/callback'
)
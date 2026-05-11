"""
FILE: backend/app/tests/integration/test_middleware.py
Integration tests for authentication middleware
"""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi import Request
from starlette.responses import Response

from app.middleware.auth import AuthMiddleware
from app.infrastructure.database.models import WeatherUser
from datetime import datetime


class TestAuthMiddleware:
    """Integration tests for AuthMiddleware."""
    
    @pytest.mark.asyncio
    @patch('app.middleware.auth.get_optional_user')
    async def test_public_route_skips_auth(self, mock_get_user):
        """Test that public routes skip authentication."""
        # Create middleware instance
        middleware = AuthMiddleware(app=None)
        
        # Create mock request for public route
        request = Request(scope={
            'type': 'http',
            'method': 'GET',
            'path': '/api/health',
            'headers': [],
            'query_string': b'',
            'path_params': {}
        })
        
        # Create mock call_next
        async def call_next(req):
            return Response(content="OK")
        
        # Execute
        response = await middleware.dispatch(request, call_next)
        
        # Verify
        assert response.status_code == 200
        mock_get_user.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('app.middleware.auth.get_optional_user')
    async def test_protected_route_with_valid_token(self, mock_get_user):
        """Test that protected route adds user to request.state with valid token."""
        # Setup mock
        mock_user = WeatherUser(
            id=1,
            provider='google',
            provider_id='12345',
            email='john@example.com',
            name='John Doe',
            avatar_url='http://avatar.com',
            initials='JD',
            unit_preference='C',
            theme='system',
            is_active=True,
            created_at=datetime.now(),
            last_login_at=datetime.now()
        )
        mock_get_user.return_value = mock_user
        
        # Create middleware instance
        middleware = AuthMiddleware(app=None)
        
        # Create mock request for protected route
        request = Request(scope={
            'type': 'http',
            'method': 'GET',
            'path': '/api/auth/me',
            'headers': [],
            'query_string': b'',
            'path_params': {}
        })
        
        # Create mock call_next that checks request.state.user
        async def call_next(req):
            # Verify user was added to request.state
            assert hasattr(req.state, 'user')
            assert req.state.user is not None
            assert req.state.user.email == 'john@example.com'
            return Response(content="OK")
        
        # Execute
        response = await middleware.dispatch(request, call_next)
        
        # Verify
        assert response.status_code == 200
        mock_get_user.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.middleware.auth.get_optional_user')
    async def test_protected_route_with_no_token(self, mock_get_user):
        """Test that protected route sets user to None when no token provided."""
        # Setup mock
        mock_get_user.return_value = None
        
        # Create middleware instance
        middleware = AuthMiddleware(app=None)
        
        # Create mock request for protected route
        request = Request(scope={
            'type': 'http',
            'method': 'GET',
            'path': '/api/auth/me',
            'headers': [],
            'query_string': b'',
            'path_params': {}
        })
        
        # Create mock call_next
        async def call_next(req):
            # Verify user was set to None
            assert hasattr(req.state, 'user')
            assert req.state.user is None
            return Response(content="OK")
        
        # Execute
        response = await middleware.dispatch(request, call_next)
        
        # Verify
        assert response.status_code == 200
        mock_get_user.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('app.middleware.auth.get_optional_user')
    async def test_weather_route_is_public(self, mock_get_user):
        """Test that weather endpoints are public routes."""
        # Create middleware instance
        middleware = AuthMiddleware(app=None)
        
        # Create mock request for weather route
        request = Request(scope={
            'type': 'http',
            'method': 'GET',
            'path': '/api/weather/current',
            'headers': [],
            'query_string': b'',
            'path_params': {}
        })
        
        # Create mock call_next
        async def call_next(req):
            return Response(content="OK")
        
        # Execute
        response = await middleware.dispatch(request, call_next)
        
        # Verify
        assert response.status_code == 200
        mock_get_user.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('app.middleware.auth.get_optional_user')
    async def test_auth_callback_routes_are_public(self, mock_get_user):
        """Test that OAuth callback routes are public."""
        # Create middleware instance
        middleware = AuthMiddleware(app=None)
        
        # Create mock request for callback route
        request = Request(scope={
            'type': 'http',
            'method': 'GET',
            'path': '/api/auth/google/callback',
            'headers': [],
            'query_string': b'',
            'path_params': {}
        })
        
        # Create mock call_next
        async def call_next(req):
            return Response(content="OK")
        
        # Execute
        response = await middleware.dispatch(request, call_next)
        
        # Verify
        assert response.status_code == 200
        mock_get_user.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('app.middleware.auth.get_optional_user')
    async def test_docs_routes_are_public(self, mock_get_user):
        """Test that documentation routes are public."""
        # Create middleware instance
        middleware = AuthMiddleware(app=None)
        
        # Test docs route
        request = Request(scope={
            'type': 'http',
            'method': 'GET',
            'path': '/docs',
            'headers': [],
            'query_string': b'',
            'path_params': {}
        })
        
        async def call_next(req):
            return Response(content="OK")
        
        response = await middleware.dispatch(request, call_next)
        assert response.status_code == 200
        mock_get_user.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('app.middleware.auth.get_optional_user')
    async def test_search_route_is_public(self, mock_get_user):
        """Test that search endpoints are public routes."""
        # Create middleware instance
        middleware = AuthMiddleware(app=None)
        
        # Create mock request for search route
        request = Request(scope={
            'type': 'http',
            'method': 'GET',
            'path': '/api/search/cities',
            'headers': [],
            'query_string': b'',
            'path_params': {}
        })
        
        # Create mock call_next
        async def call_next(req):
            return Response(content="OK")
        
        # Execute
        response = await middleware.dispatch(request, call_next)
        
        # Verify
        assert response.status_code == 200
        mock_get_user.assert_not_called()
    
    @pytest.mark.asyncio
    @patch('app.middleware.auth.get_optional_user')
    async def test_custom_protected_route_requires_auth(self, mock_get_user):
        """Test that custom protected routes require authentication."""
        # Setup mock
        mock_user = WeatherUser(
            id=1,
            provider='google',
            provider_id='12345',
            email='john@example.com',
            name='John Doe',
            avatar_url='http://avatar.com',
            initials='JD',
            unit_preference='C',
            theme='system',
            is_active=True,
            created_at=datetime.now(),
            last_login_at=datetime.now()
        )
        mock_get_user.return_value = mock_user
        
        # Create middleware instance
        middleware = AuthMiddleware(app=None)
        
        # Create mock request for custom protected route
        request = Request(scope={
            'type': 'http',
            'method': 'GET',
            'path': '/api/saved-locations',
            'headers': [],
            'query_string': b'',
            'path_params': {}
        })
        
        # Create mock call_next
        async def call_next(req):
            assert hasattr(req.state, 'user')
            assert req.state.user is not None
            return Response(content="OK")
        
        # Execute
        response = await middleware.dispatch(request, call_next)
        
        # Verify
        assert response.status_code == 200
        mock_get_user.assert_called_once()


class TestAuthMiddlewareRouteMatching:
    """Test route matching logic for public vs protected routes."""
    
    def test_is_public_route_exact_match(self):
        """Test exact route matching."""
        middleware = AuthMiddleware(app=None)
        
        assert middleware._is_public_route('/api/health') is True
        assert middleware._is_public_route('/') is True
        assert middleware._is_public_route('/docs') is True
        assert middleware._is_public_route('/redoc') is True
    
    def test_is_public_route_prefix_match(self):
        """Test prefix route matching."""
        middleware = AuthMiddleware(app=None)
        
        assert middleware._is_public_route('/api/auth/google/callback?code=123') is True
        assert middleware._is_public_route('/api/auth/github/callback?code=456') is True
        assert middleware._is_public_route('/static/css/main.css') is True
        assert middleware._is_public_route('/favicon.ico') is True
    
    def test_is_public_route_protected(self):
        """Test that protected routes return False."""
        middleware = AuthMiddleware(app=None)
        
        assert middleware._is_public_route('/api/auth/me') is False
        assert middleware._is_public_route('/api/auth/preferences') is False
        assert middleware._is_public_route('/api/auth/logout') is False
        assert middleware._is_public_route('/api/saved-locations') is False
        assert middleware._is_public_route('/api/notifications') is False

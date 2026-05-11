"""
FILE: backend/app/tests/unit/test_user_repository.py
Unit tests for UserRepository using mocked database connections
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.infrastructure.repositories.user_repository import UserRepository
from app.infrastructure.database.models import WeatherUser, WeatherSession
from app.core.exceptions import DatabaseError, AuthError


class TestUserRepositoryUpsert:
    """Test user upsert operations."""
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    @patch('app.infrastructure.repositories.user_repository.generate_user_initials')
    async def test_upsert_creates_new_user(self, mock_initials, mock_get_db):
        """Test upsert creates a new user when provider_id doesn't exist."""
        # Setup mocks
        mock_initials.return_value = "JD"
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'provider': 'google',
            'provider_id': '12345',
            'email': 'john@example.com',
            'name': 'John Doe',
            'avatar_url': 'http://avatar.com',
            'initials': 'JD',
            'unit_preference': 'C',
            'theme': 'system',
            'is_active': True,
            'created_at': datetime.now(),
            'last_login_at': datetime.now()
        }
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.upsert_user(
            provider='google',
            provider_id='12345',
            email='john@example.com',
            name='John Doe',
            avatar_url='http://avatar.com'
        )
        
        # Verify
        assert isinstance(result, WeatherUser)
        assert result.email == 'john@example.com'
        assert result.provider == 'google'
        assert result.name == 'John Doe'
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    @patch('app.infrastructure.repositories.user_repository.generate_user_initials')
    async def test_upsert_updates_existing_user(self, mock_initials, mock_get_db):
        """Test upsert updates existing user when provider_id exists."""
        # Setup mocks
        mock_initials.return_value = "JD"
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'provider': 'google',
            'provider_id': '12345',
            'email': 'john.new@example.com',  # Updated email
            'name': 'John Updated',
            'avatar_url': 'http://new-avatar.com',
            'initials': 'JD',
            'unit_preference': 'F',  # Updated preference
            'theme': 'dark',
            'is_active': True,
            'created_at': datetime.now(),
            'last_login_at': datetime.now()
        }
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.upsert_user(
            provider='google',
            provider_id='12345',
            email='john.new@example.com',
            name='John Updated',
            avatar_url='http://new-avatar.com'
        )
        
        # Verify
        assert isinstance(result, WeatherUser)
        assert result.email == 'john.new@example.com'
        assert result.name == 'John Updated'
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    async def test_upsert_handles_database_error(self, mock_get_db):
        """Test upsert handles database errors gracefully."""
        # Setup mock to raise exception
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.execute.side_effect = Exception("Database connection failed")
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute and verify exception
        with pytest.raises(DatabaseError):
            await UserRepository.upsert_user(
                provider='google',
                provider_id='12345',
                email='john@example.com'
            )


class TestUserRepositoryGetUser:
    """Test user retrieval operations."""
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    async def test_get_user_by_id_found(self, mock_get_db):
        """Test get_user_by_id returns user when found."""
        # Setup mocks
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'provider': 'google',
            'provider_id': '12345',
            'email': 'john@example.com',
            'name': 'John Doe',
            'avatar_url': 'http://avatar.com',
            'initials': 'JD',
            'unit_preference': 'C',
            'theme': 'system',
            'is_active': True,
            'created_at': datetime.now(),
            'last_login_at': datetime.now()
        }
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.get_user_by_id(1)
        
        # Verify
        assert isinstance(result, WeatherUser)
        assert result.id == 1
        assert result.email == 'john@example.com'
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    async def test_get_user_by_id_not_found(self, mock_get_db):
        """Test get_user_by_id returns None when user not found."""
        # Setup mocks
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.get_user_by_id(999)
        
        # Verify
        assert result is None


class TestUserRepositorySession:
    """Test session operations."""
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    @patch('app.infrastructure.repositories.user_repository.hash_session_token')
    @patch('app.infrastructure.repositories.user_repository.get_session_expiry')
    async def test_create_session(self, mock_expiry, mock_hash, mock_get_db):
        """Test creating a new session."""
        # Setup mocks
        mock_hash.return_value = "hashed_token_123"
        mock_expiry.return_value = datetime.now()
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'user_id': 1,
            'session_token': 'hashed_token_123',
            'expires_at': datetime.now(),
            'ip_address': '127.0.0.1',
            'user_agent': 'Mozilla',
            'created_at': datetime.now()
        }
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.create_session(
            user_id=1,
            session_token='raw_token_123',
            ip_address='127.0.0.1',
            user_agent='Mozilla'
        )
        
        # Verify
        assert isinstance(result, WeatherSession)
        assert result.user_id == 1
        mock_hash.assert_called_once_with('raw_token_123')
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    @patch('app.infrastructure.repositories.user_repository.hash_session_token')
    async def test_get_session_valid(self, mock_hash, mock_get_db):
        """Test get_session returns session data for valid token."""
        # Setup mocks
        mock_hash.return_value = "hashed_token_123"
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'user_id': 1,
            'session_token': 'hashed_token_123',
            'expires_at': datetime.now(),
            'ip_address': '127.0.0.1',
            'user_agent': 'Mozilla',
            'created_at': datetime.now(),
            'user_id': 1,
            'email': 'john@example.com',
            'name': 'John Doe',
            'avatar_url': 'http://avatar.com',
            'initials': 'JD',
            'unit_preference': 'C',
            'theme': 'system',
            'provider': 'google'
        }
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.get_session('raw_token_123')
        
        # Verify
        assert result is not None
        assert 'session' in result
        assert 'user' in result
        assert isinstance(result['user'], WeatherUser)
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    @patch('app.infrastructure.repositories.user_repository.hash_session_token')
    async def test_get_session_invalid(self, mock_hash, mock_get_db):
        """Test get_session returns None for invalid token."""
        # Setup mocks
        mock_hash.return_value = "hashed_token_123"
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.get_session('invalid_token')
        
        # Verify
        assert result is None
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    @patch('app.infrastructure.repositories.user_repository.hash_session_token')
    async def test_delete_session(self, mock_hash, mock_get_db):
        """Test deleting a session."""
        # Setup mocks
        mock_hash.return_value = "hashed_token_123"
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.delete_session('raw_token_123')
        
        # Verify
        assert result is True
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    async def test_delete_expired_sessions(self, mock_get_db):
        """Test deleting expired sessions."""
        # Setup mocks
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.rowcount = 5
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.delete_expired_sessions()
        
        # Verify
        assert result == 5
        mock_cursor.execute.assert_called_once()
        mock_conn.commit.assert_called_once()


class TestUserRepositoryPreferences:
    """Test user preference updates."""
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    async def test_update_preferences_unit(self, mock_get_db):
        """Test updating unit preference."""
        # Setup mocks
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'provider': 'google',
            'provider_id': '12345',
            'email': 'john@example.com',
            'name': 'John Doe',
            'avatar_url': 'http://avatar.com',
            'initials': 'JD',
            'unit_preference': 'F',  # Updated
            'theme': 'system',
            'is_active': True,
            'created_at': datetime.now(),
            'last_login_at': datetime.now()
        }
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.update_preferences(
            user_id=1,
            unit_preference='F'
        )
        
        # Verify
        assert isinstance(result, WeatherUser)
        assert result.unit_preference == 'F'
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    async def test_update_preferences_theme(self, mock_get_db):
        """Test updating theme preference."""
        # Setup mocks
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'provider': 'google',
            'provider_id': '12345',
            'email': 'john@example.com',
            'name': 'John Doe',
            'avatar_url': 'http://avatar.com',
            'initials': 'JD',
            'unit_preference': 'C',
            'theme': 'dark',  # Updated
            'is_active': True,
            'created_at': datetime.now(),
            'last_login_at': datetime.now()
        }
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.update_preferences(
            user_id=1,
            theme='dark'
        )
        
        # Verify
        assert isinstance(result, WeatherUser)
        assert result.theme == 'dark'
    
    @patch('app.infrastructure.repositories.user_repository.get_db_connection')
    async def test_update_preferences_both(self, mock_get_db):
        """Test updating both preferences."""
        # Setup mocks
        mock_conn = AsyncMock()
        mock_cursor = AsyncMock()
        mock_cursor.fetchone.return_value = {
            'id': 1,
            'provider': 'google',
            'provider_id': '12345',
            'email': 'john@example.com',
            'name': 'John Doe',
            'avatar_url': 'http://avatar.com',
            'initials': 'JD',
            'unit_preference': 'F',
            'theme': 'dark',
            'is_active': True,
            'created_at': datetime.now(),
            'last_login_at': datetime.now()
        }
        mock_conn.cursor.return_value.__aenter__ = AsyncMock(return_value=mock_cursor)
        mock_conn.cursor.return_value.__aexit__ = AsyncMock()
        mock_get_db.return_value.__aenter__ = AsyncMock(return_value=mock_conn)
        mock_get_db.return_value.__aexit__ = AsyncMock()
        
        # Execute
        result = await UserRepository.update_preferences(
            user_id=1,
            unit_preference='F',
            theme='dark'
        )
        
        # Verify
        assert isinstance(result, WeatherUser)
        assert result.unit_preference == 'F'
        assert result.theme == 'dark'
    
    async def test_update_preferences_no_changes(self):
        """Test update_preferences raises error when no changes provided."""
        with pytest.raises(ValueError):
            await UserRepository.update_preferences(user_id=1)

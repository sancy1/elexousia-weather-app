"""
FILE: backend/app/tests/unit/test_location_repository.py
Unit tests for location repository
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.infrastructure.repositories.location_repository import (
    add_saved_location,
    get_saved_locations,
    update_saved_location,
    set_default_location,
    delete_saved_location,
    get_default_location
)


class TestLocationRepository:
    """Test saved locations repository functions"""
    
    @pytest.mark.asyncio
    async def test_add_saved_location_success(self):
        """Test successfully adding a saved location"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 1, "Lagos", "NG", "Home", 6.5244, 3.3792, "Africa/Lagos", 1, False, None)
        mock_cursor.fetchone.return_value = (1, 1, "Lagos", "NG", "Home", 6.5244, 3.3792, "Africa/Lagos", 1, False, None)
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.location_repository.get_db_connection', return_value=mock_conn):
            result = await add_saved_location(
                user_id=1,
                city_name="Lagos",
                country_code="NG",
                label="Home",
                latitude=6.5244,
                longitude=3.3792,
                timezone="Africa/Lagos"
            )
            
            assert result is not None
            assert result["city_name"] == "Lagos"
            assert result["label"] == "Home"
    
    @pytest.mark.asyncio
    async def test_get_saved_locations(self):
        """Test getting saved locations for a user"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            (1, 1, "Lagos", "NG", "Home", 6.5244, 3.3792, "Africa/Lagos", 1, False, None),
            (2, 1, "London", "GB", "Work", 51.5074, -0.1278, "Europe/London", 2, True, None)
        ]
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.location_repository.get_db_connection', return_value=mock_conn):
            result = await get_saved_locations(user_id=1)
            
            assert len(result) == 2
            assert result[0]["city_name"] == "Lagos"
            assert result[1]["city_name"] == "London"
    
    @pytest.mark.asyncio
    async def test_update_saved_location_label(self):
        """Test updating saved location label"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.location_repository.get_db_connection', return_value=mock_conn):
            result = await update_saved_location(
                location_id=1,
                user_id=1,
                label="Updated Label"
            )
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_set_default_location(self):
        """Test setting a location as default"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.location_repository.get_db_connection', return_value=mock_conn):
            result = await set_default_location(location_id=1, user_id=1)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_saved_location(self):
        """Test deleting a saved location"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.location_repository.get_db_connection', return_value=mock_conn):
            result = await delete_saved_location(location_id=1, user_id=1)
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_get_default_location(self):
        """Test getting default location"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, 1, "Lagos", "NG", "Home", 6.5244, 3.3792, "Africa/Lagos", 1, True, None)
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.infrastructure.repositories.location_repository.get_db_connection', return_value=mock_conn):
            result = await get_default_location(user_id=1)
            
            assert result is not None
            assert result["city_name"] == "Lagos"
            assert result["is_default"] is True

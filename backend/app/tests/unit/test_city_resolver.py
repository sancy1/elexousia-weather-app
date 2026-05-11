"""
FILE: backend/app/tests/unit/test_city_resolver.py
Unit tests for city resolution functionality
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agent.tools.city_resolver import resolve_city, resolve_city_from_db, detect_region_from_query


class TestRegionDetection:
    """Test region detection from query"""
    
    def test_detect_region_nigeria(self):
        """Detect Nigeria from query"""
        result = detect_region_from_query("weather in nigeria")
        assert result == ["NG"]
    
    def test_detect_region_west_africa(self):
        """Detect West Africa from query"""
        result = detect_region_from_query("cities in west africa")
        assert "NG" in result
        assert "GH" in result
    
    def test_detect_region_europe(self):
        """Detect Western Europe from query"""
        result = detect_region_from_query("western europe weather")
        assert "GB" in result
        assert "FR" in result
    
    def test_detect_region_none(self):
        """Return empty list when no region detected"""
        result = detect_region_from_query("random query text")
        assert result == []


class TestCityResolver:
    """Test city resolution"""
    
    @pytest.mark.asyncio
    async def test_resolve_city_from_db_success(self):
        """Test successful city resolution from database"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1, "Lagos", "Nigeria", "NG", 6.5244, 3.3792, "Africa/Lagos")
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.agent.tools.city_resolver.get_db_connection', return_value=mock_conn):
            result = await resolve_city_from_db("Lagos")
            
            assert result is not None
            assert result["city_name"] == "Lagos"
            assert result["country_name"] == "Nigeria"
            assert result["resolution"] == "db"
    
    @pytest.mark.asyncio
    async def test_resolve_city_from_db_not_found(self):
        """Test city not found in database"""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn.cursor.return_value = mock_cursor
        
        with patch('app.agent.tools.city_resolver.get_db_connection', return_value=mock_conn):
            result = await resolve_city_from_db("UnknownCity")
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_resolve_city_fallback_chain(self):
        """Test city resolution fallback chain"""
        # Mock DB to return None
        mock_db_result = None
        
        # Mock vector search to return None
        with patch('app.agent.tools.city_resolver.resolve_city_from_db', return_value=mock_db_result), \
             patch('app.agent.tools.city_resolver.resolve_city_by_vector', return_value=None), \
             patch('app.agent.tools.city_resolver.resolve_city_via_api', return_value={
                 "city_name": "London",
                 "country_name": "United Kingdom",
                 "country_code": "GB",
                 "latitude": 51.5074,
                 "longitude": -0.1278,
                 "timezone": "Europe/London",
                 "resolution": "api_geocode"
             }):
            
            result = await resolve_city("London")
            
            assert result is not None
            assert result["city_name"] == "London"
            assert result["resolution"] == "api_geocode"
    
    @pytest.mark.asyncio
    async def test_resolve_city_clean_query(self):
        """Test query cleaning removes weather-related words"""
        mock_result = {
            "city_name": "Paris",
            "country_name": "France",
            "country_code": "FR",
            "latitude": 48.8566,
            "longitude": 2.3522,
            "timezone": "Europe/Paris",
            "resolution": "db"
        }
        
        with patch('app.agent.tools.city_resolver.resolve_city_from_db', return_value=mock_result):
            result = await resolve_city("What's the weather in Paris today?")
            
            assert result is not None
            assert result["city_name"] == "Paris"

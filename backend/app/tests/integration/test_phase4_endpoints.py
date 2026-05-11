"""
FILE: backend/app/tests/integration/test_phase4_endpoints.py
Integration tests for Phase 4 endpoints (saved locations, conversations, search, notifications)
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from app.main import app

client = TestClient(app)


class TestSavedLocationsEndpoints:
    """Test saved locations API endpoints"""
    
    def test_list_saved_locations(self):
        """Test GET /api/saved-locations"""
        with patch('app.api.routes.saved_locations.get_saved_locations', return_value=[
            {"id": 1, "city_name": "Lagos", "country_code": "NG", "label": "Home", "display_order": 1}
        ]):
            response = client.get("/api/saved-locations")
            assert response.status_code == 200
            assert "locations" in response.json()
    
    def test_create_saved_location(self):
        """Test POST /api/saved-locations"""
        with patch('app.api.routes.saved_locations.resolve_city', return_value={
            "city_name": "Lagos", "country_code": "NG", "latitude": 6.5244, "longitude": 3.3792, "timezone": "Africa/Lagos"
        }):
            with patch('app.api.routes.saved_locations.add_saved_location', return_value={
                "id": 1, "city_name": "Lagos", "country_code": "NG", "label": "Home"
            }):
                response = client.post("/api/saved-locations", json={
                    "city_name": "Lagos",
                    "country_code": "NG",
                    "label": "Home"
                })
                assert response.status_code == 200
                assert response.json()["city_name"] == "Lagos"
    
    def test_update_saved_location(self):
        """Test PATCH /api/saved-locations/{id}"""
        with patch('app.api.routes.saved_locations.update_saved_location', return_value=True):
            response = client.patch("/api/saved-locations/1", json={"label": "Updated"})
            assert response.status_code == 200
    
    def test_set_default_location(self):
        """Test PATCH /api/saved-locations/{id}/default"""
        with patch('app.api.routes.saved_locations.set_default_location', return_value=True):
            response = client.patch("/api/saved-locations/1/default")
            assert response.status_code == 200
    
    def test_delete_saved_location(self):
        """Test DELETE /api/saved-locations/{id}"""
        with patch('app.api.routes.saved_locations.delete_saved_location', return_value=True):
            response = client.delete("/api/saved-locations/1")
            assert response.status_code == 200


class TestConversationsEndpoints:
    """Test conversations API endpoints"""
    
    def test_list_conversations(self):
        """Test GET /api/conversations"""
        with patch('app.api.routes.conversations.get_conversations', return_value={
            "conversations": [
                {"id": 1, "title": "Lagos weather", "message_count": 4}
            ],
            "total": 1, "page": 1, "per_page": 20
        }):
            response = client.get("/api/conversations")
            assert response.status_code == 200
            assert "conversations" in response.json()
    
    def test_create_conversation(self):
        """Test POST /api/conversations"""
        with patch('app.api.routes.conversations.create_conversation', return_value={
            "id": 1, "session_id": "session-123", "title": "Weather Chat"
        }):
            response = client.post("/api/conversations", json={
                "session_id": "session-123",
                "title": "Weather Chat"
            })
            assert response.status_code == 200
            assert response.json()["session_id"] == "session-123"
    
    def test_get_conversation(self):
        """Test GET /api/conversations/{id}"""
        with patch('app.api.routes.conversations.get_conversation', return_value={
            "id": 1, "title": "Lagos weather", "message_count": 4
        }):
            response = client.get("/api/conversations/1")
            assert response.status_code == 200
    
    def test_update_conversation(self):
        """Test PATCH /api/conversations/{id}"""
        with patch('app.api.routes.conversations.update_conversation_title', return_value=True):
            response = client.patch("/api/conversations/1", json={"title": "Updated"})
            assert response.status_code == 200
    
    def test_delete_conversation(self):
        """Test DELETE /api/conversations/{id}"""
        with patch('app.api.routes.conversations.delete_conversation_endpoint', return_value={"message": "deleted"}):
            response = client.delete("/api/conversations/1")
            assert response.status_code == 200
    
    def test_get_conversation_messages(self):
        """Test GET /api/conversations/{id}/messages"""
        with patch('app.api.routes.conversations.get_conversation', return_value={"id": 1}):
            with patch('app.api.routes.conversations.get_messages', return_value={
                "messages": [{"role": "user", "content": "Hello"}],
                "total": 1
            }):
                response = client.get("/api/conversations/1/messages")
                assert response.status_code == 200


class TestSearchEndpoints:
    """Test search API endpoints"""
    
    def test_search_all(self):
        """Test GET /api/search"""
        with patch('app.api.routes.search.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                ("saved_location", 1, "Lagos, Nigeria", "Home", 2.4)
            ]
            mock_conn.return_value.__aenter__.return_value.cursor.return_value = mock_cursor
            
            response = client.get("/api/search?q=Lagos")
            assert response.status_code == 200
            assert "results" in response.json()
    
    def test_search_cities(self):
        """Test GET /api/search/cities"""
        with patch('app.api.routes.search.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                (1, "Lagos", "Nigeria", "NG", 6.5244, 3.3792, "Africa/Lagos")
            ]
            mock_conn.return_value.__aenter__.return_value.cursor.return_value = mock_cursor
            
            response = client.get("/api/search/cities?q=Lag")
            assert response.status_code == 200
            assert "cities" in response.json()


class TestNotificationsEndpoints:
    """Test notifications API endpoints"""
    
    def test_list_notifications(self):
        """Test GET /api/notifications"""
        with patch('app.api.routes.notifications.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchone.return_value = (3,)
            mock_cursor.fetchall.return_value = [
                (1, 1, "rain_alert", "Lagos", "Rain expected", "80% chance", False, None)
            ]
            mock_conn.return_value.__aenter__.return_value.cursor.return_value = mock_cursor
            
            response = client.get("/api/notifications")
            assert response.status_code == 200
            assert "unread_count" in response.json()
    
    def test_mark_as_read(self):
        """Test PATCH /api/notifications/{id}/read"""
        with patch('app.api.routes.notifications.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 1
            mock_conn.return_value.__aenter__.return_value.cursor.return_value = mock_cursor
            
            response = client.patch("/api/notifications/1/read")
            assert response.status_code == 200
    
    def test_mark_all_as_read(self):
        """Test PATCH /api/notifications/read-all"""
        with patch('app.api.routes.notifications.get_db_connection') as mock_conn:
            mock_conn.return_value.__aenter__.return_value.cursor.return_value = MagicMock()
            
            response = client.patch("/api/notifications/read-all")
            assert response.status_code == 200
    
    def test_delete_notification(self):
        """Test DELETE /api/notifications/{id}"""
        with patch('app.api.routes.notifications.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.rowcount = 1
            mock_conn.return_value.__aenter__.return_value.cursor.return_value = mock_cursor
            
            response = client.delete("/api/notifications/1")
            assert response.status_code == 200
    
    def test_check_notifications(self):
        """Test POST /api/notifications/check"""
        with patch('app.api.routes.notifications.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [(1, 1, "Lagos", 6.5244, 3.3792)]
            mock_cursor.rowcount = 1
            mock_conn.return_value.__aenter__.return_value.cursor.return_value = mock_cursor
            
            with patch('app.api.routes.notifications.fetch_forecast', return_value={
                "forecast": {"forecastday": [{"day": {"daily_chance_of_rain": 80, "maxtemp_c": 30, "mintemp_c": 25}}]}
            }):
                response = client.post("/api/notifications/check")
                assert response.status_code == 200

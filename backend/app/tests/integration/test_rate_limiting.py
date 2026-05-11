"""
FILE: backend/app/tests/integration/test_rate_limiting.py
Integration tests for rate limiting middleware
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from time import sleep

client = TestClient(app)


class TestRateLimiting:
    """Test rate limiting middleware"""
    
    def test_chat_rate_limit(self):
        """Test chat endpoint rate limit (30 req/min)"""
        # Make 31 requests to exceed the limit
        responses = []
        for i in range(31):
            response = client.post("/api/chat", json={
                "message": "test",
                "session_id": "test-session"
            }, headers={"Authorization": "Bearer test-token"})
            responses.append(response.status_code)
        
        # First 30 should succeed (or fail for other reasons), last should be 429
        assert responses[-1] == 429
    
    def test_weather_rate_limit(self):
        """Test weather endpoint rate limit (100 req/min)"""
        responses = []
        for i in range(101):
            response = client.get("/api/weather/current?city=Lagos")
            responses.append(response.status_code)
        
        # Should hit rate limit after 100 requests
        assert 429 in responses
    
    def test_rate_limit_headers(self):
        """Test rate limit headers are present"""
        response = client.get("/api/weather/current?city=Lagos")
        assert "X-RateLimit-Limit" in response.headers
        assert "X-RateLimit-Window" in response.headers

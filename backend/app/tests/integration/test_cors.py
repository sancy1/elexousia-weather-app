"""
FILE: backend/app/tests/integration/test_cors.py
Integration tests for CORS configuration
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestCORS:
    """Test CORS middleware configuration"""
    
    def test_cors_headers_present(self):
        """Test CORS headers are present in response"""
        response = client.get("/api/health", headers={
            "Origin": "http://localhost:5173"
        })
        assert "access-control-allow-origin" in response.headers
    
    def test_allowed_origin_success(self):
        """Test request from allowed origin succeeds"""
        response = client.get("/api/health", headers={
            "Origin": "http://localhost:5173"
        })
        assert response.status_code == 200
    
    def test_preflight_request(self):
        """Test OPTIONS preflight request"""
        response = client.options("/api/health", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        })
        assert response.status_code == 200 or response.status_code == 204

"""
FILE: backend/app/tests/integration/test_docker_health.py
Integration tests for Docker health checks
"""

import pytest
import requests
from time import sleep, time

class TestDockerHealth:
    """Test Docker container health checks"""
    
    def test_health_endpoint_response(self):
        """Test that /api/health returns 200"""
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_health_endpoint_within_30_seconds(self):
        """Test that health endpoint responds within 30 seconds"""
        start = time()
        response = requests.get("http://localhost:8000/api/health", timeout=30)
        elapsed = time() - start
        assert response.status_code == 200
        assert elapsed < 30
    
    def test_db_health_endpoint(self):
        """Test database health check"""
        response = requests.get("http://localhost:8000/api/health/db", timeout=10)
        assert response.status_code in [200, 503]  # 503 if DB not available
    
    def test_agent_health_endpoint(self):
        """Test Ollama agent health check"""
        response = requests.get("http://localhost:8000/api/health/agent", timeout=10)
        assert response.status_code in [200, 503]  # 503 if Ollama not available

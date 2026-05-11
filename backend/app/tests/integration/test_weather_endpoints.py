"""
FILE: backend/app/tests/integration/test_weather_endpoints.py
Integration tests for weather endpoints
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


class TestWeatherEndpoints:
    """Test weather API endpoints"""
    
    @pytest.fixture
    def client(self):
        from app.main import app
        return TestClient(app)
    
    def test_get_current_weather_success(self, client):
        """Test GET /api/weather/current with valid city"""
        with patch('app.api.routes.weather.resolve_city') as mock_resolve, \
             patch('app.api.routes.weather.get_cache', return_value=None), \
             patch('app.api.routes.weather.fetch_current') as mock_fetch:
            
            mock_resolve.return_value = {
                "city_id": 1,
                "city_name": "Lagos",
                "latitude": 6.5244,
                "longitude": 3.3792
            }
            
            mock_fetch.return_value = {
                "current": {
                    "temp_c": 28,
                    "temp_f": 82.4,
                    "feelslike_c": 32,
                    "feelslike_f": 89.6,
                    "condition": {"text": "Partly cloudy"},
                    "humidity": 75,
                    "wind_kph": 15,
                    "wind_dir": "SW",
                    "uv": 7,
                    "vis_km": 10,
                    "cloud": 50,
                    "pressure_mb": 1013
                },
                "location": {
                    "name": "Lagos",
                    "country": "Nigeria",
                    "country_code": "NG",
                    "localtime": "2026-05-05 15:00"
                }
            }
            
            response = client.get("/api/weather/current?city=Lagos")
            
            assert response.status_code == 200
            data = response.json()
            assert data["city"] == "Lagos"
            assert data["temperature_c"] == 28
    
    def test_get_current_weather_city_not_found(self, client):
        """Test GET /api/weather/current with unknown city"""
        with patch('app.api.routes.weather.resolve_city', return_value=None):
            response = client.get("/api/weather/current?city=UnknownCity")
            
            assert response.status_code == 404
            data = response.json()
            assert "not found" in data["detail"].lower()
    
    def test_get_forecast_success(self, client):
        """Test GET /api/weather/forecast"""
        with patch('app.api.routes.weather.resolve_city') as mock_resolve, \
             patch('app.api.routes.weather.get_cache', return_value=None), \
             patch('app.api.routes.weather.fetch_forecast') as mock_fetch:
            
            mock_resolve.return_value = {
                "city_id": 1,
                "city_name": "Lagos",
                "latitude": 6.5244,
                "longitude": 3.3792
            }
            
            mock_fetch.return_value = {
                "location": {
                    "name": "Lagos",
                    "country": "Nigeria"
                },
                "forecast": {
                    "forecastday": [
                        {
                            "date": "2026-05-06",
                            "day": {
                                "maxtemp_c": 30,
                                "mintemp_c": 25,
                                "maxtemp_f": 86,
                                "mintemp_f": 77,
                                "condition": {"text": "Sunny"},
                                "daily_chance_of_rain": 10,
                                "totalprecip_mm": 0,
                                "avghumidity": 70,
                                "uv": 8,
                                "astro": {"sunrise": "06:30", "sunset": "18:45"}
                            }
                        }
                    ]
                }
            }
            
            response = client.get("/api/weather/forecast?city=Lagos&days=1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["city"] == "Lagos"
            assert len(data["forecast"]) == 1
    
    def test_get_forecast_exactly_7_days(self, client):
        """Test GET /api/weather/forecast returns exactly 7 days when requested"""
        with patch('app.api.routes.weather.resolve_city') as mock_resolve, \
             patch('app.api.routes.weather.get_cache', return_value=None), \
             patch('app.api.routes.weather.fetch_forecast') as mock_fetch:
            
            mock_resolve.return_value = {
                "city_id": 1,
                "city_name": "Lagos",
                "latitude": 6.5244,
                "longitude": 3.3792
            }
            
            # Generate 7 days of forecast
            forecast_days = []
            for i in range(7):
                forecast_days.append({
                    "date": f"2026-05-0{6+i}",
                    "day": {
                        "maxtemp_c": 30,
                        "mintemp_c": 25,
                        "maxtemp_f": 86,
                        "mintemp_f": 77,
                        "condition": {"text": "Sunny"},
                        "daily_chance_of_rain": 10,
                        "totalprecip_mm": 0,
                        "avghumidity": 70,
                        "uv": 8,
                        "astro": {"sunrise": "06:30", "sunset": "18:45"}
                    }
                })
            
            mock_fetch.return_value = {
                "location": {"name": "Lagos", "country": "Nigeria"},
                "forecast": {"forecastday": forecast_days}
            }
            
            response = client.get("/api/weather/forecast?city=Lagos&days=7")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["forecast"]) == 7
    
    def test_compare_weather_success(self, client):
        """Test GET /api/weather/compare"""
        with patch('app.api.routes.weather.resolve_city') as mock_resolve, \
             patch('app.api.routes.weather.fetch_current') as mock_fetch:
            
            mock_resolve.side_effect = [
                {
                    "city_id": 1,
                    "city_name": "Lagos",
                    "latitude": 6.5244,
                    "longitude": 3.3792
                },
                {
                    "city_id": 2,
                    "city_name": "London",
                    "latitude": 51.5074,
                    "longitude": -0.1278
                }
            ]
            
            mock_fetch.side_effect = [
                {
                    "current": {
                        "temp_c": 28,
                        "temp_f": 82.4,
                        "feelslike_c": 32,
                        "condition": {"text": "Sunny"},
                        "humidity": 75,
                        "wind_kph": 15,
                        "uv": 7
                    },
                    "location": {"name": "Lagos", "country": "Nigeria"}
                },
                {
                    "current": {
                        "temp_c": 15,
                        "temp_f": 59,
                        "feelslike_c": 13,
                        "condition": {"text": "Cloudy"},
                        "humidity": 80,
                        "wind_kph": 20,
                        "uv": 3
                    },
                    "location": {"name": "London", "country": "United Kingdom"}
                }
            ]
            
            response = client.get("/api/weather/compare?city1=Lagos&city2=London")
            
            assert response.status_code == 200
            data = response.json()
            assert "city_1" in data
            assert "city_2" in data
            assert "comparison" in data
            assert data["comparison"]["warmer_city"] == "Lagos"
    
    def test_get_clothing_advice(self, client):
        """Test GET /api/weather/wear"""
        with patch('app.api.routes.weather.resolve_city') as mock_resolve, \
             patch('app.api.routes.weather.fetch_current') as mock_fetch:
            
            mock_resolve.return_value = {
                "city_id": 1,
                "city_name": "Lagos",
                "latitude": 6.5244,
                "longitude": 3.3792
            }
            
            mock_fetch.return_value = {
                "current": {
                    "temp_c": 28,
                    "temp_f": 82.4,
                    "condition": {"text": "Rain"},
                    "daily_chance_of_rain": 70,
                    "uv": 5
                },
                "location": {
                    "name": "Lagos",
                    "country": "Nigeria"
                }
            }
            
            response = client.get("/api/weather/wear?city=Lagos")
            
            assert response.status_code == 200
            data = response.json()
            assert data["city"] == "Lagos"
            assert "items" in data
            assert len(data["items"]) > 0
            assert "emoji" in data
            assert "summary" in data
    
    def test_get_chips(self, client):
        """Test GET /api/chips"""
        with patch('app.api.routes.chips.get_db_connection') as mock_conn:
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                (1, "3-day forecast", "Give me a detailed 3-day weather forecast for", "📅", True),
                (2, "Current weather", "What's the current weather in", "🌤️", True)
            ]
            mock_conn().__aenter__.return_value.cursor.return_value = mock_cursor
            
            response = client.get("/api/chips")
            
            assert response.status_code == 200
            data = response.json()
            assert "chips" in data
            assert len(data["chips"]) > 0
            assert "label" in data["chips"][0]
            assert "prompt_text" in data["chips"][0]

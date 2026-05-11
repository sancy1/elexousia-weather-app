"""
FILE: backend/app/tests/unit/test_weather_tools.py
Unit tests for weather tools
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.agent.tools.weather_tools import build_advice, build_travel_advice


class TestAdviceGeneration:
    """Test weather advice generation functions"""
    
    def test_build_advice_rainy(self):
        """Test advice generation for rainy conditions"""
        cur = {
            "temp_c": 20,
            "humidity": 85,
            "uv": 5,
            "wind_kph": 10,
            "precip_mm": 2.5
        }
        
        advice = build_advice(cur)
        
        assert "umbrella" in advice.lower()
    
    def test_build_advice_hot(self):
        """Test advice generation for hot conditions"""
        cur = {
            "temp_c": 38,
            "humidity": 60,
            "uv": 9,
            "wind_kph": 5,
            "precip_mm": 0
        }
        
        advice = build_advice(cur)
        
        assert "hydrated" in advice.lower()
        assert "light" in advice.lower()
    
    def test_build_advice_cold(self):
        """Test advice generation for cold conditions"""
        cur = {
            "temp_c": 0,
            "humidity": 70,
            "uv": 2,
            "wind_kph": 15,
            "precip_mm": 0
        }
        
        advice = build_advice(cur)
        
        assert "jacket" in advice.lower() or "coat" in advice.lower()
    
    def test_build_advice_pleasant(self):
        """Test advice generation for pleasant conditions"""
        cur = {
            "temp_c": 22,
            "humidity": 50,
            "uv": 4,
            "wind_kph": 10,
            "precip_mm": 0
        }
        
        advice = build_advice(cur)
        
        assert "pleasant" in advice.lower()
    
    def test_build_travel_advice_rainy(self):
        """Test travel advice for rainy forecast"""
        daily = [
            {"rain_chance_pct": 80, "high_c": 25},
            {"rain_chance_pct": 70, "high_c": 24},
            {"rain_chance_pct": 60, "high_c": 26}
        ]
        
        advice = build_travel_advice(daily)
        
        assert "rain" in advice.lower() or "jacket" in advice.lower()
    
    def test_build_travel_advice_hot(self):
        """Test travel advice for hot forecast"""
        daily = [
            {"rain_chance_pct": 10, "high_c": 35},
            {"rain_chance_pct": 5, "high_c": 36},
            {"rain_chance_pct": 0, "high_c": 34}
        ]
        
        advice = build_travel_advice(daily)
        
        assert "hot" in advice.lower() or "spf" in advice.lower()
    
    def test_build_travel_advice_cold(self):
        """Test travel advice for cold forecast"""
        daily = [
            {"rain_chance_pct": 20, "high_c": 5},
            {"rain_chance_pct": 10, "high_c": 4},
            {"rain_chance_pct": 15, "high_c": 6}
        ]
        
        advice = build_travel_advice(daily)
        
        assert "cold" in advice.lower() or "winter" in advice.lower()
    
    def test_build_travel_advice_empty(self):
        """Test travel advice with no data"""
        advice = build_travel_advice([])
        
        assert "no forecast" in advice.lower()


class TestWeatherTools:
    """Test weather tool functions"""
    
    @pytest.mark.asyncio
    async def test_get_current_weather_success(self):
        """Test successful weather fetch"""
        mock_loc = {
            "city_id": 1,
            "city_name": "Lagos",
            "latitude": 6.5244,
            "longitude": 3.3792
        }
        
        mock_weather_data = {
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
                "cloud": 50
            },
            "location": {
                "name": "Lagos",
                "country": "Nigeria",
                "localtime": "2026-05-05 15:00"
            }
        }
        
        with patch('app.agent.tools.weather_tools.resolve_city', return_value=mock_loc), \
             patch('app.agent.tools.weather_tools.get_cache', return_value=None), \
             patch('app.agent.tools.weather_tools.fetch_current', return_value=mock_weather_data), \
             patch('app.agent.tools.weather_tools.save_cache', return_value=True):
            
            from app.agent.tools.weather_tools import get_current_weather
            result = await get_current_weather("Lagos")
            
            assert result is not None
            data = eval(result)
            assert data["status"] == "success"
            assert data["data"]["city"] == "Lagos"
    
    @pytest.mark.asyncio
    async def test_get_current_weather_city_not_found(self):
        """Test weather fetch with city not found"""
        with patch('app.agent.tools.weather_tools.resolve_city', return_value=None):
            from app.agent.tools.weather_tools import get_current_weather
            result = await get_current_weather("UnknownCity")
            
            data = eval(result)
            assert data["status"] == "error"
            assert "not found" in data["message"].lower()
    
    @pytest.mark.asyncio
    async def test_get_weather_forecast_success(self):
        """Test successful forecast fetch"""
        mock_loc = {
            "city_id": 1,
            "city_name": "Lagos",
            "latitude": 6.5244,
            "longitude": 3.3792
        }
        
        mock_forecast_data = {
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
        
        with patch('app.agent.tools.weather_tools.resolve_city', return_value=mock_loc), \
             patch('app.agent.tools.weather_tools.get_cache', return_value=None), \
             patch('app.agent.tools.weather_tools.fetch_forecast', return_value=mock_forecast_data), \
             patch('app.agent.tools.weather_tools.save_cache', return_value=True):
            
            from app.agent.tools.weather_tools import get_weather_forecast
            result = await get_weather_forecast("Lagos", days=1)
            
            assert result is not None
            data = eval(result)
            assert data["status"] == "success"
            assert len(data["data"]["forecast"]) == 1

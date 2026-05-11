"""
FILE: backend/app/tests/unit/test_wear_logic.py
Unit tests for clothing recommendation logic
"""

import pytest
from app.api.routes.weather import generate_clothing_advice


class TestClothingAdvice:
    """Test clothing recommendation logic"""
    
    def test_rainy_conditions_produce_umbrella(self):
        """Test rainy conditions include umbrella in recommendations"""
        advice = generate_clothing_advice(
            temp_c=20,
            condition="Rain",
            rain_chance=70,
            uv_index=5
        )
        
        assert any(item["name"] == "Umbrella" for item in advice["items"])
        assert advice["emoji"] == "🌧️"
        assert "rain" in advice["summary"].lower()
    
    def test_hot_conditions_produce_spf(self):
        """Test hot conditions include sunscreen"""
        advice = generate_clothing_advice(
            temp_c=32,
            condition="Sunny",
            rain_chance=10,
            uv_index=9
        )
        
        assert any("sunscreen" in item["name"].lower() or "SPF" in item["name"] for item in advice["items"])
        assert advice["emoji"] == "☀️"
    
    def test_cold_conditions_produce_jacket(self):
        """Test cold conditions include jacket"""
        advice = generate_clothing_advice(
            temp_c=3,
            condition="Clear",
            rain_chance=5,
            uv_index=2
        )
        
        assert any("jacket" in item["name"].lower() or "coat" in item["name"].lower() for item in advice["items"])
        assert advice["emoji"] == "❄️"
    
    def test_mild_conditions_produce_layers(self):
        """Test mild conditions recommend light layers"""
        advice = generate_clothing_advice(
            temp_c=18,
            condition="Partly cloudy",
            rain_chance=20,
            uv_index=4
        )
        
        assert advice["summary"] == "Comfortable layers"
    
    def test_snow_conditions_produce_snow_gear(self):
        """Test snow conditions include snow gear"""
        advice = generate_clothing_advice(
            temp_c=0,
            condition="Snow",
            rain_chance=50,
            uv_index=2
        )
        
        assert any("snow boots" in item["name"].lower() for item in advice["items"])
        assert advice["emoji"] == "❄️"
    
    def test_high_uv_produces_sun_protection(self):
        """Test high UV index produces sun protection recommendations"""
        advice = generate_clothing_advice(
            temp_c=25,
            condition="Sunny",
            rain_chance=0,
            uv_index=10
        )
        
        assert any("sunscreen" in item["name"].lower() or "hat" in item["name"].lower() for item in advice["items"])
    
    def test_tip_generation_rain(self):
        """Test tip generation for rainy conditions"""
        advice = generate_clothing_advice(
            temp_c=20,
            condition="Rain",
            rain_chance=70,
            uv_index=5
        )
        
        assert "umbrella" in advice["tip"].lower()
    
    def test_tip_generation_hot(self):
        """Test tip generation for hot conditions"""
        advice = generate_clothing_advice(
            temp_c=35,
            condition="Sunny",
            rain_chance=0,
            uv_index=8
        )
        
        assert "hydrated" in advice["tip"].lower()
    
    def test_tip_generation_cold(self):
        """Test tip generation for cold conditions"""
        advice = generate_clothing_advice(
            temp_c=2,
            condition="Clear",
            rain_chance=0,
            uv_index=2
        )
        
        assert "cold" in advice["tip"].lower()
    
    def test_all_fields_present(self):
        """Test all required fields are present in response"""
        advice = generate_clothing_advice(
            temp_c=20,
            condition="Partly cloudy",
            rain_chance=30,
            uv_index=5
        )
        
        assert "emoji" in advice
        assert "summary" in advice
        assert "tagline" in advice
        assert "items" in advice
        assert "tip" in advice
        assert isinstance(advice["items"], list)
        assert len(advice["items"]) > 0

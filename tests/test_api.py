import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.weather_service import WeatherService

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data

def test_weather_service_direct():
    service = WeatherService()
    weather = service.get_district_weather("Ludhiana", "Punjab")
    assert "current_temperature" in weather
    assert "current_humidity" in weather
    assert "weather_condition" in weather
    assert len(weather["daily_forecast"]) > 0

def test_metadata_endpoint():
    response = client.get("/api/metadata")
    assert response.status_code == 200
    data = response.json()
    assert len(data["states"]) > 0
    assert "Punjab" in data["states"]
    assert len(data["crops"]) > 0
    assert "Wheat" in data["crops"]

def test_prediction_endpoint():
    payload = {
        "state": "Punjab",
        "district": "Ludhiana",
        "crop": "Wheat",
        "season": "Rabi",
        "year": 2025
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["predicted_yield_kg_ha"] > 0
    assert data["predicted_yield_quintal_acre"] > 0
    assert data["state"] == "Punjab"
    assert data["district"] == "Ludhiana"
    assert "shap_feature_importance" in data
    assert len(data["shap_feature_importance"]) > 0

def test_historical_trends_endpoint():
    response = client.get("/api/historical-trends?state=Punjab&district=Ludhiana&crop=Wheat")
    assert response.status_code == 200
    data = response.json()
    assert data["crop"] == "Wheat"
    assert len(data["trends"]) > 0

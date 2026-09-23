import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.schemas import (
    PredictionRequest,
    PredictionResponse,
    WeatherResponse,
    HistoricalTrendsResponse,
    MetadataResponse
)
from backend.services.inference_service import inference_service
from backend.services.weather_service import WeatherService

weather_service = WeatherService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load ML artifacts once when server starts
    try:
        inference_service.load_artifacts()
    except Exception as e:
        print(f"Warning on startup artifact loading: {e}")
    yield

app = FastAPI(
    title="AI Crop Yield Prediction API",
    description="High-performance REST API for Indian district-level agricultural yield forecasting with live agro-weather integration and SHAP explainability.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for frontend clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "AI Crop Yield Prediction API",
        "artifacts_loaded": inference_service.is_loaded
    }

@app.get("/api/metadata", response_model=MetadataResponse, tags=["Metadata"])
def get_metadata():
    """Returns lists of available states, cascading districts per state, crops, and seasons."""
    try:
        return inference_service.get_metadata()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predict", response_model=PredictionResponse, tags=["Inference"])
def predict_crop_yield(request: PredictionRequest):
    """
    Predict crop yield for a specified State, District, Crop, Season, and Year.
    Automatically looks up lag yield and computes SHAP feature importance.
    """
    try:
        result = inference_service.predict_yield(
            state=request.state,
            district=request.district,
            crop=request.crop,
            season=request.season,
            year=request.year,
            custom_lag=request.custom_lag_yield
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

@app.get("/api/weather", response_model=WeatherResponse, tags=["Weather"])
def get_district_weather(
    district: str = Query(..., description="Name of the district"),
    state: str = Query(..., description="Name of the state")
):
    """
    Fetches real-time agro-weather, temperature, precipitation, humidity, and 7-day outlook
    for the selected district via Open-Meteo API.
    """
    try:
        return weather_service.get_district_weather(district=district, state=state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Weather retrieval error: {str(e)}")

@app.get("/api/historical-trends", response_model=HistoricalTrendsResponse, tags=["Analytics"])
def get_historical_trends(
    state: str = Query(..., description="State name"),
    district: str = Query(..., description="District name"),
    crop: str = Query(..., description="Crop name")
):
    """
    Retrieves historical yield trends across recorded years (2016-2024) for a specific district and crop.
    """
    try:
        return inference_service.get_historical_trends(state=state, district=district, crop=crop)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Historical data error: {str(e)}")

from typing import Optional, List, Dict
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    state: str = Field(..., examples=["Punjab"])
    district: str = Field(..., examples=["Ludhiana"])
    crop: str = Field(..., examples=["Wheat"])
    season: str = Field(..., examples=["Rabi"])
    year: int = Field(2025, examples=[2025])
    custom_lag_yield: Optional[float] = Field(None, description="Optional override for prior year's yield in kg/ha")

class ShapImpact(BaseModel):
    feature: str
    feature_name_clean: str
    impact: float
    value: Optional[float] = None

class PredictionResponse(BaseModel):
    state: str
    district: str
    crop: str
    season: str
    year: int
    predicted_yield_kg_ha: float
    predicted_yield_quintal_acre: float
    lag_yield_used: float
    is_lag_estimated: bool
    district_avg_yield: Optional[float] = None
    state_avg_yield: Optional[float] = None
    delta_vs_district_pct: Optional[float] = None
    delta_vs_state_pct: Optional[float] = None
    confidence_level: str = "High"
    shap_feature_importance: List[ShapImpact] = []

class WeatherForecastDay(BaseModel):
    date: str
    temp_max: float
    temp_min: float
    precipitation_sum: float
    rain_probability: Optional[float] = None

class WeatherResponse(BaseModel):
    district: str
    state: str
    latitude: float
    longitude: float
    current_temperature: float
    current_humidity: float
    current_precipitation: float
    current_wind_speed: float
    weather_condition: str
    agricultural_advisory: str
    daily_forecast: List[WeatherForecastDay]

class HistoricalTrendPoint(BaseModel):
    year: str
    year_start: int
    yield_kg_ha: float
    season: str

class HistoricalTrendsResponse(BaseModel):
    state: str
    district: str
    crop: str
    trends: List[HistoricalTrendPoint]
    min_yield: Optional[float] = None
    max_yield: Optional[float] = None
    avg_yield: Optional[float] = None

class MetadataResponse(BaseModel):
    states: List[str]
    state_to_districts: Dict[str, List[str]]
    crops: List[str]
    seasons: List[str]

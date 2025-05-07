"""Adapter for the OpenDataHub weather endpoint (SKELETON)."""
from typing import Tuple
from ..models import WeatherIndex

class WeatherAdapter:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    def fetch_weather(self, position: Tuple[float, float]) -> WeatherIndex:
        """Placeholder implementation that returns dummy data."""
        # TODO: perform real HTTP request
        return WeatherIndex(
            rain_intensity=0.0,
            visibility=1.0,
            temperature_c=15.0,
            frost_risk=0.0,
        )

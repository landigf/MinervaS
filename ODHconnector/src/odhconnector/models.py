"""Simple dataclasses used across the connector."""
from dataclasses import dataclass
from typing import Optional, List, Tuple
from datetime import datetime

@dataclass
class Event:
    """Base class for all external events."""
    type: str
    description: str
    timestamp: datetime
    lat: float
    lon: float
    distance_km: Optional[float] = None

@dataclass
class Incident(Event):
    severity: Optional[int] = None  # 0-5 scale

@dataclass
class WorkZone(Event):
    active: bool = True

@dataclass
class WeatherIndex:
    """Normalized weather data (0-1)."""
    rain_intensity: float
    visibility: float
    temperature_c: float
    frost_risk: float

@dataclass
class Alert:
    """Fuzzy‑logic advisory returned to MinervaS."""
    message: str
    suggested_speed_factor: float  # 0-1 multiplier w.r.t. limit
    relevance: float               # confidence 0-1

"""
WeatherAdapter
--------------

Fetches real-time weather measurements from the **mobility** domain and,
if unavailable, falls back to district-level forecasts in the tourism domain.

Normalises only temperature, precipitation, visibility and frost risk into a
``WeatherIndex`` dataclass. Configuration via ``PHENOMENA``.
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, Optional, Tuple, List

import requests

from ..models import WeatherIndex

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

ODH_MOBILITY_BASE = "https://mobility.api.opendatahub.com".rstrip("/")
ODH_TOURISM_BASE  = "https://tourism.api.opendatahub.com".rstrip("/")

REPRESENTATION = "flat,node"
STATION_TYPE   = "MeteoStation"

# phenomenon → (field_name, min_value, max_value)
PHENOMENA: Dict[str, Tuple[str, float, float]] = {
    "air-temperature":   ("temperature_c", -20.0,  40.0),
    "precipitation-rate":("rain_intensity",   0.0,  50.0),
    "visibility":        ("visibility",       0.0,10000.0),
}

DEFAULT_RADIUS_M = 10_000  # 10 km
_TIMEOUT = 8  # seconds

# ---------------------------------------------------------------------------
# Public adapter
# ---------------------------------------------------------------------------

class WeatherAdapter:
    """Fetches and normalises weather for a given (lat, lon)."""

    def __init__(
        self,
        mobility_base: str = ODH_MOBILITY_BASE,
        tourism_base:  str = ODH_TOURISM_BASE,
        radius_m:      int = DEFAULT_RADIUS_M,
    ) -> None:
        self.mobility_base = mobility_base.rstrip("/")
        self.tourism_base  = tourism_base.rstrip("/")
        self.radius_m      = radius_m

    def fetch_weather(self, position: Tuple[float, float]) -> WeatherIndex:
        lat, lon = position
        # Attempt live measurements
        try:
            live = self._fetch_live(lat, lon)
            if live is not None:
                return live
        except Exception as exc:
            log.warning("Error fetching live data: %s", exc)
        # Fallback to district forecast
        return self._fetch_forecast(lat, lon)

    def _fetch_live(self, lat: float, lon: float) -> Optional[WeatherIndex]:
        """Retrieve latest readings from nearest MeteoStation."""
        base = f"{self.mobility_base}/v2/{REPRESENTATION}/{STATION_TYPE}"
        raw: Dict[str, float] = {}

        # For each phenomenon, fetch latest
        for phen, (field, lo, hi) in PHENOMENA.items():
            url = (
                f"{base}/{phen}/latest"
                f"?coords={lon},{lat}&radius={self.radius_m}&limit=1"
            )
            resp = requests.get(url, timeout=_TIMEOUT)
            if resp.status_code != 200:
                log.debug("Live %s HTTP %d", phen, resp.status_code)
                return None
            j = resp.json()
            # extract list of observations
            if isinstance(j, dict) and 'data' in j:
                rows = j.get('data', [])
            elif isinstance(j, list):
                rows = j
            else:
                return None
            if not rows:
                return None
            row = rows[0]
            # value key may be 'mvalue' or 'value'
            val = row.get('mvalue', row.get('value'))
            raw[field] = float(val)

        return self._make_index(raw)

    def _fetch_forecast(self, lat: float, lon: float) -> WeatherIndex:
        """Get district forecast and collapse into single index."""
        # find nearest district
        district = self._closest_district(lat, lon)
        # fetch all district forecasts
        url = f"{self.tourism_base}/v1/Weather/District?language=en"
        resp = requests.get(url, timeout=_TIMEOUT)
        resp.raise_for_status()
        entries = resp.json()
        # select matching or first
        entry = next((e for e in entries if e.get("Id") == district.get("Id")), entries[0])
        today = entry.get("BezirksForecast", [])[0]
        raw = {
            "temperature_c":  (today.get("MinTemp",0) + today.get("MaxTemp",0)) / 2,
            "rain_intensity": today.get("RainTo",0),
            "visibility":     10000.0 if today.get("WeatherDesc",""
                                       ).lower().startswith("sunny") else 4000.0,
        }
        return self._make_index(raw)

    def _closest_district(self, lat: float, lon: float) -> Dict[str, Any]:
        """Retrieve district centroids and pick nearest."""
        url = f"{self.tourism_base}/v1/Location/District"
        try:
            resp = requests.get(url, timeout=_TIMEOUT)
            resp.raise_for_status()
            districts = resp.json()
        except Exception:
            return {"Id":7, "Latitude":46.5, "Longitude":11.9}
        # pick min haversine
        best = min(
            districts,
            key=lambda d: _haversine(lat, lon, d.get("Latitude"), d.get("Longitude")),
        )
        return best

    def _make_index(self, raw: Dict[str, float]) -> WeatherIndex:
        """Normalise raw readings into WeatherIndex dataclass."""
        t = raw.get("temperature_c", 0.0)
        return WeatherIndex(
            temperature_c   = t,
            rain_intensity  = self._norm(raw.get("rain_intensity",0.0), "precipitation-rate"),
            visibility      = self._norm(raw.get("visibility",0.0), "visibility"),
            frost_risk      = 1.0 if t < 0 else 0.0,
        )

    def _norm(self, value: float, phenomenon: str) -> float:
        _, lo, hi = PHENOMENA[phenomenon]
        return max(0.0, min(1.0, (value - lo) / (hi - lo)))

# ---------------------------------------------------------------------------
# Geometry helper
# ---------------------------------------------------------------------------

def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))

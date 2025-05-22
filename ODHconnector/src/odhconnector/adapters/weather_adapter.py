# src/odhconnector/adapters/weather_adapter.py
from __future__ import annotations
from typing import Tuple
from datetime import datetime, timezone
import logging
import requests

from ..models import WeatherIndex

log = logging.getLogger(__name__)


class WeatherAdapter:
    """
    Recupera il *meteo real-time* dal dominio «mobility» di Open Data Hub.

    Strategy
    --------
    1. usiamo l'endpoint *flat,measurement* filtrando il tipo di stazione
       **WeatherStation** e chiedendo solo l'ultima misura per ciascun fenomeno;
    2. estraiamo i fenomeni chiave che servono a MinervaS
       (temperatura, pioggia, visibilità);
    3. normalizziamo su range 0-1 (funzioni private).

    NOTE: l'API non richiede chiavi; rate-limit ≃ 30 req/min.
    """

    _STATION_TYPE = "WeatherStation"
    _PHENOMENA = {
        "air_temperature": ("temperature_c", -20.0, 40.0),      # min, max
        "precipitation_rate": ("rain_intensity", 0.0, 50.0),
        "visibility": ("visibility", 0.0, 10000.0),             # m
    }

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def fetch_weather(self, position: Tuple[float, float]) -> WeatherIndex:
        """Recupera separatamente temperatura, pioggia e visibilità, normalizzando 0–1."""
        lat, lon = position
        data_raw: dict[str, float] = {}

        for phen, (key, lo, hi) in self._PHENOMENA.items():
            url = (
                f"{self.base_url}/v2/flat,measurement/WeatherStation/{phen}/latest"
                f"?coords={lon},{lat}&radius=10000&limit=1"
            )
            resp = requests.get(url, timeout=10)
            try:
                resp.raise_for_status()
            except Exception:
                log.warning("Weather phen=%s failed: %s", phen, resp.status_code)
                # fallback a default
                data_raw[key] = lo if key != "rain_intensity" else 0.0
                continue

            rows = resp.json()
            if not rows:
                data_raw[key] = lo if key != "rain_intensity" else 0.0
            else:
                # prendo il primo valore
                data_raw[key] = float(rows[0]["value"])

        # ora ho data_raw = {"temperature_c": val, "rain_intensity": val2, "visibility": val3}
        t = data_raw["temperature_c"]
        rain = data_raw["rain_intensity"]
        vis  = data_raw["visibility"]

        return WeatherIndex(
            rain_intensity=self._norm(rain, "precipitation_rate"),
            visibility=self._norm(vis, "visibility"),
            temperature_c=t,
            frost_risk=1.0 if t < 0 else 0.0,
        )



    # ------------------------------------------------------------------ #
    # Helpers                                                             #
    # ------------------------------------------------------------------ #

    def _norm(self, value: float, phenomenon: str) -> float:
        key, lo, hi = self._PHENOMENA[phenomenon]
        return max(0.0, min(1.0, (value - lo) / (hi - lo)))

"""ODHConnector: public entry‑point used by MinervaS.

Unifica in un *unico* file il connettore verso gli endpoint traffico **e**
meteo di OpenDataHub, senza sottoclassare alcuna implementazione esterna.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable, List, Optional, Tuple

from ..models import Alert, Event, Incident, WeatherIndex, WorkZone
from ..utils import haversine
from ..adapters.weather_adapter import WeatherAdapter
from ..adapters.traffic_adapter import TrafficAdapter

# motore fuzzy
from ..risk.fuzzy_engine import build_fuzzy_controller
from skfuzzy import control as ctrl

logger = logging.getLogger(__name__)


class ODHConnector:
    """Connector towards OpenDataHub weather & traffic APIs.

    Args:
        odh_base_url: Base URL of the OpenDataHub API (mobility domain).
        odh_api_key:  Optional API key.
        position_provider: Callable that returns *(lat, lon)* in WGS‑84.
        route_segment: Identifier of the route segment (e.g. ``'A22_Trentino'``).
        auto_refresh: When ``True`` the cache is refreshed transparently.
        last_n_hours: Default time window (hours) for ``get_events`` filtering.
    """

    _TTL = timedelta(seconds=30)

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    def __init__(
        self,
        odh_base_url: str,
        odh_api_key: str,
        position_provider: Callable[[], Tuple[float, float]],
        route_segment: str,
        auto_refresh: bool = True,
        last_n_hours: int = 24,
        weather_radius_m: int = 10_000,
    ) -> None:
        self.odh_base_url = odh_base_url.rstrip("/")
        self.odh_api_key = odh_api_key
        self.position_provider = position_provider
        self.route_segment = route_segment
        self.auto_refresh = auto_refresh
        self.last_n_hours = last_n_hours

        self._last_refresh: datetime | None = None
        self._cache: dict[str, object] = {}

        # internal adapters ------------------------------------------------
        self._traffic_adapter = TrafficAdapter(self.odh_base_url)
        self._weather_adapter = WeatherAdapter(
            radius_m=weather_radius_m,
            mobility_base=self.odh_base_url,
        )

        # fuzzy engine -----------------------------------------------------
        self._fuzzy_sim: ctrl.ControlSystemSimulation = build_fuzzy_controller()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _maybe_refresh(self) -> None:
        if not self.auto_refresh:
            return
        if self._last_refresh is None or datetime.now(timezone.utc) - self._last_refresh > self._TTL:
            self.refresh_data()

    # ------------------------------------------------------------------
    # Data download & caching
    # ------------------------------------------------------------------

    def refresh_data(self) -> None:  # noqa: C901 – keeps traffic+meteo together
        """Download latest traffic + weather data and cache them."""
        pos = self.position_provider()

        # ── traffic ------------------------------------------------------
        events = self._traffic_adapter.fetch_events(self.route_segment)
        for ev in events:
            ev.distance_km = haversine(pos, (ev.lat, ev.lon))
        self._cache["events"] = events

        # ── weather (soft‑fail) -----------------------------------------
        try:
            self._cache["weather"] = self._weather_adapter.fetch_weather(pos)
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Weather fetch failed → %s", exc)
            self._cache["weather"] = None

        # timestamp -------------------------------------------------------
        self._last_refresh = datetime.now(timezone.utc)
        logger.debug(
            "Data refreshed @ %s – events=%d, weather=%s",
            self._last_refresh.isoformat(timespec="seconds"),
            len(events),
            self._cache["weather"],
        )

    # ------------------------------------------------------------------
    # Generic event retrieval
    # ------------------------------------------------------------------

    def _filter_events(
        self,
        *,
        last_n_hours: Optional[int],
        within_km: Optional[float],
    ) -> list[Event]:
        self._maybe_refresh()
        events: list[Event] = self._cache.get("events", [])  # type: ignore[assignment]

        # 1) time‑based filter ------------------------------------------
        hrs = last_n_hours if last_n_hours is not None else self.last_n_hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hrs)
        events = [e for e in events if e.timestamp >= cutoff]

        # 2) distance‑based filter --------------------------------------
        if within_km is not None:
            pos = self.position_provider()
            events = [e for e in events if e.distance_km is not None and e.distance_km <= within_km]
        return events

    # ------------------------------------------------------------------
    # Public getters -----------------------------------------------------
    # ------------------------------------------------------------------

    def get_events(
        self,
        *,
        last_n_hours: Optional[int] = None,
        within_km: Optional[float] = None,
    ) -> list[Event]:
        """Return events filtered by time (hours) and distance (km)."""
        return self._filter_events(last_n_hours=last_n_hours, within_km=within_km)

    # convenience wrappers ----------------------------------------------
    def get_incidents(self, **kw) -> list[Incident]:
        return [e for e in self.get_events(**kw) if isinstance(e, Incident)]

    def get_workzones(self, **kw) -> list[WorkZone]:
        return [e for e in self.get_events(**kw) if isinstance(e, WorkZone)]

    def get_queues(self, **kw) -> list[Event]:
        return [e for e in self.get_events(**kw) if "coda" in e.type or "stau" in e.type]

    def get_closures(self, **kw) -> list[Event]:
        return [e for e in self.get_events(**kw) if "chiusura" in e.type or "sperre" in e.type]

    def get_manifestations(self, **kw) -> list[Event]:
        return [e for e in self.get_events(**kw) if "manifestazione" in e.type or "veranstaltung" in e.type]

    def get_snow_warnings(self, **kw) -> list[Event]:
        return [e for e in self.get_events(**kw) if "nevischio" in e.type or "schneeregen" in e.type]

    def get_fog_warnings(self, **kw) -> list[Event]:
        return [e for e in self.get_events(**kw) if "nebbia" in e.type or "nebel" in e.type]

    def get_chain_requirements(self, **kw) -> list[Event]:
        return [e for e in self.get_events(**kw) if "catene" in e.type or "kettenpflicht" in e.type]

    def get_wildlife_hazards(self, **kw) -> list[Event]:
        return [e for e in self.get_events(**kw) if "animali" in e.type or "tiere" in e.type]

    def get_free_flow(self, **kw) -> list[Event]:
        return [e for e in self.get_events(**kw) if "percorribile" in e.type or "frei befahrbar" in e.type]

    # ------------------------------------------------------------------
    # Summaries & weather access
    # ------------------------------------------------------------------

    def get_events_summary(
        self,
        *,
        last_n_hours: Optional[int] = None,
        within_km: Optional[float] = None,
    ) -> dict[str, int]:
        """Return ``{category: n_events}`` after the requested filters."""
        evts = self.get_events(last_n_hours=last_n_hours, within_km=within_km)
        counts: dict[str, int] = {}
        for e in evts:
            counts[e.type] = counts.get(e.type, 0) + 1
        return counts

    # weather -----------------------------------------------------------
    def get_weather_index(self, verbose: bool = False) -> WeatherIndex | None:
        self._maybe_refresh()
        wx: WeatherIndex | None = self._cache.get("weather")  # type: ignore[assignment]
        if verbose:
            logger.debug("Weather index: %s", wx)
        return wx

    def get_weather(
        self,
        positions: Iterable[Tuple[float, float]],
    ) -> List[Tuple[Tuple[float, float], WeatherIndex]]:
        """Return ``[(pos, WeatherIndex), …]`` (skips failures)."""
        out: List[Tuple[Tuple[float, float], WeatherIndex]] = []
        for pos in positions:
            try:
                out.append((pos, self._weather_adapter.fetch_weather(pos)))
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("Weather fetch failed @ %s → %s", pos, exc)
        return out

    # ------------------------------------------------------------------
    # Alerts
    # ------------------------------------------------------------------

    def generate_alerts(
        self,
        *,
        within_km: float = 5.0,
        last_n_hours: Optional[int] = None,
        verbose: bool = False,
    ) -> list[Alert]:
        # group events ---------------------------------------------------
        groups = {
            "incident": self.get_incidents(within_km=within_km, last_n_hours=last_n_hours),
            "queue": self.get_queues(within_km=within_km, last_n_hours=last_n_hours),
            "workzone": self.get_workzones(within_km=within_km, last_n_hours=last_n_hours),
            "closure": self.get_closures(within_km=within_km, last_n_hours=last_n_hours),
            "manifest": self.get_manifestations(within_km=within_km, last_n_hours=last_n_hours),
            "snow": self.get_snow_warnings(within_km=within_km, last_n_hours=last_n_hours),
            "fog": self.get_fog_warnings(within_km=within_km, last_n_hours=last_n_hours),
            "chain": self.get_chain_requirements(within_km=within_km, last_n_hours=last_n_hours),
            "wildlife": self.get_wildlife_hazards(within_km=within_km, last_n_hours=last_n_hours),
        }

        alerts: list[Alert] = []

        # critical traffic events ---------------------------------------
        for inc in groups["incident"]:
            if getattr(inc, "severity", 0) >= 3:
                alerts.append(Alert("Incidente grave: rallentare 50%", 0.5, 0.9))
        if groups["queue"]:
            alerts.append(Alert("Code sulla tratta: considerare deviazione (–20%)", 0.8, 0.7))
        if groups["workzone"]:
            alerts.append(Alert("Cantieri in zona: guidare con cautela (–10%)", 0.9, 0.6))
        for c in groups["closure"]:
            alerts.append(Alert(f"Chiusura: {c.description}", 0.0, 1.0))
        if groups["manifest"]:
            alerts.append(Alert("Manifestazioni: possibili deviazioni (–30%)", 0.7, 0.5))
        # weather‑related -----------------------------------------------
        if groups["snow"]:
            alerts.append(Alert("Nevischio: ridurre di 30%", 0.7, 0.6))
        if groups["fog"]:
            alerts.append(Alert("Nebbia fitta: ridurre di 40%", 0.6, 0.6))
        if groups["chain"]:
            alerts.append(Alert("Obbligo catene: attrezzarsi", 0.5, 0.8))
        if groups["wildlife"]:
            alerts.append(Alert("Animali in carreggiata: prudenza", 0.8, 0.7))

        wx = self.get_weather_index()
        if wx:
            if wx.rain_intensity > 0.5:
                alerts.append(Alert("Pioggia intensa: ridurre di 30%", 0.7, 0.7))
            if wx.visibility < 0.4:
                alerts.append(Alert("Scarsa visibilità: ridurre di 40%", 0.6, 0.8))

        if verbose:
            for a in alerts:
                logger.debug("Alert → %s", a)
        return alerts

    # ------------------------------------------------------------------
    # Composite KPIs
    # ------------------------------------------------------------------

    def compute_attention_score(
        self,
        *,
        within_km: float = 5.0,
        last_n_hours: Optional[int] = None,
        weights: Optional[dict[str, float]] = None,
    ) -> float:
        alerts = self.generate_alerts(within_km=within_km, last_n_hours=last_n_hours)
        if not alerts:
            return 0.0
        default_weights = {
            "incident": 3.0,
            "closure": 2.5,
            "queue": 2.0,
            "workzone": 1.5,
            "manifest": 1.0,
            "snow": 1.2,
            "fog": 1.2,
            "chain": 1.3,
            "wildlife": 1.4,
            "meteo": 1.1,
        }
        w = weights or default_weights
        num = den = 0.0
        for a in alerts:
            kind = next((k for k in w if k in a.message.lower()), "incident")
            weight = w.get(kind, 1.0)
            num += weight * a.relevance
            den += weight
        return min(max(num / den if den else 0.0, 0.0), 1.0)

    # ------------------------------------------------------------------
    # Fuzzy speed factor
    # ------------------------------------------------------------------

    def get_speed_factor(
        self,
        *,
        fatigue: float = 0.0,
        deadline_pressure: float = 0.0,
        within_km: float = 5.0,
        last_n_hours: Optional[int] = None,
        verbose: bool = False,
    ) -> float:
        traffic_risk = self.compute_attention_score(within_km=within_km, last_n_hours=last_n_hours)
        wx = self.get_weather_index() or WeatherIndex(temperature_c=15.0, rain_intensity=0.0, visibility=1.0, frost_risk=0.0)  # type: ignore[arg-type]
        weather_risk = max(wx.rain_intensity, 1 - wx.visibility)
        temp_c = wx.temperature_c

        sim = self._fuzzy_sim
        sim.input["traffic"] = traffic_risk
        sim.input["weather"] = weather_risk
        sim.input["fatigue"] = fatigue
        sim.input["deadline"] = deadline_pressure
        sim.input["temp"] = temp_c
        sim.compute()
        sf = float(sim.output["speed"])
        if verbose:
            logger.debug(
                "Fuzzy: traffic=%.2f weather=%.2f fatigue=%.2f deadline=%.2f temp=%.1f → speed=%.2f",
                traffic_risk, weather_risk, fatigue, deadline_pressure, temp_c, sf,
            )
        return max(0.0, min(1.0, sf))

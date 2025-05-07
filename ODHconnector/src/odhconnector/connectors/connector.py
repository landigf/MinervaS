"""ODHConnector: public entry‑point used by MinervaS."""
import logging
from datetime import datetime
from typing import Callable, List, Optional, Tuple

from ..models import Event, Incident, WorkZone, WeatherIndex, Alert
from ..utils import haversine
from ..adapters.weather_adapter import WeatherAdapter
from ..adapters.traffic_adapter import TrafficAdapter

logger = logging.getLogger(__name__)

class ODHConnector:
    """Connector towards OpenDataHub weather & traffic APIs.

    Args:
        odh_base_url: Base URL of the OpenDataHub API.
        odh_api_key: API key string.
        position_provider: Callable returning current (lat, lon).
        route_segment: Identifier of the route segment (e.g., ``'A22_Trentino'``).
        auto_refresh: When ``True``, data are refreshed on every public method call.
    """

    def __init__(
        self,
        odh_base_url: str,
        odh_api_key: str,
        position_provider: Callable[[], Tuple[float, float]],
        route_segment: str,
        auto_refresh: bool = True,
    ):
        self.odh_base_url = odh_base_url.rstrip('/')
        self.odh_api_key = odh_api_key
        self.position_provider = position_provider
        self.route_segment = route_segment
        self.auto_refresh = auto_refresh

        self._weather_adapter = WeatherAdapter(self.odh_base_url, self.odh_api_key)
        self._traffic_adapter = TrafficAdapter(self.odh_base_url, self.odh_api_key)

        self._cache: dict[str, object] = {}

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _maybe_refresh(self) -> None:
        if self.auto_refresh:
            self.refresh_data()

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def refresh_data(self) -> None:
        """Force fetch of all data from OpenDataHub APIs."""
        logger.debug("Refreshing all data from ODH")
        self._cache['weather'] = self._weather_adapter.fetch_weather(self.position_provider())
        self._cache['events'] = self._traffic_adapter.fetch_events(self.route_segment)

    def get_events(
        self,
        all: bool = True,
        last_n_hours: int = 2,
        position_override: Optional[Tuple[float, float]] = None,
        verbose: bool = False,
    ) -> List[Event]:
        self._maybe_refresh()
        events: List[Event] = self._cache.get('events', [])
        # NOTE: Skeleton implementation – add filtering later
        if verbose:
            logger.debug("Returning %d events", len(events))
        return events

    def get_incidents(
        self,
        within_km: Optional[float] = None,
        position_override: Optional[Tuple[float, float]] = None,
        last_n_hours: int = 1,
        verbose: bool = False,
    ) -> List[Incident]:
        all_events = self.get_events(all=False)
        incidents = [e for e in all_events if isinstance(e, Incident)]
        # basic distance filter
        if within_km is not None:
            pos = position_override or self.position_provider()
            incidents = [
                i for i in incidents if i.distance_km is not None and i.distance_km <= within_km
            ]
        if verbose:
            logger.debug("Returning %d incidents", len(incidents))
        return incidents

    def get_weather_index(
        self,
        position_override: Optional[Tuple[float, float]] = None,
        verbose: bool = False,
    ) -> WeatherIndex:
        self._maybe_refresh()
        weather: WeatherIndex = self._cache.get('weather')
        if verbose:
            logger.debug("Weather data: %s", weather)
        return weather

    def generate_alerts(
        self,
        focus_route: bool = False,
        thresholds: Optional[dict] = None,
        verbose: bool = False,
    ) -> List[Alert]:
        """Very naive example: returns an empty list.

        Real logic will apply fuzzy rules on weather & traffic.
        """
        self._maybe_refresh()
        if verbose:
            logger.debug("generate_alerts called – not yet implemented")
        return []

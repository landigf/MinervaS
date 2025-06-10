"""ODHConnector: public entry-point used by MinervaS.

Unifica in un *unico* file il connettore verso gli endpoint traffico **e**
meteo di OpenDataHub, senza sottoclassare alcuna implementazione esterna.
"""
from __future__ import annotations

import os
import time
import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import Callable, Iterable, List, Optional, Tuple

import folium
import requests
from rich.console import Console
from rich.table import Table

from ..models import Alert, Event, Incident, WeatherIndex, WorkZone
from ..utils import haversine
from ..adapters.weather_adapter import WeatherAdapter
from ..adapters.traffic_adapter import TrafficAdapter

# motore fuzzy
from ..risk.fuzzy_engine import build_fuzzy_controller
from skfuzzy import control as ctrl

logger = logging.getLogger(__name__)
console = Console()


class ODHConnector:
    """Connector towards OpenDataHub weather & traffic APIs.

    Args:
        odh_base_url: Base URL of the OpenDataHub API (mobility domain).
        odh_api_key:  Optional API key.
        position_provider: Callable that returns *(lat, lon)* in WGS-84.
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

    def refresh_data(self) -> None:
        """Download latest traffic + weather data and cache them."""
        pos = self.position_provider()

        # ── traffic ------------------------------------------------------
        events = self._traffic_adapter.fetch_events(self.route_segment)
        for ev in events:
            ev.distance_km = haversine(pos, (ev.lat, ev.lon))
        self._cache["events"] = events

        # ── weather (soft-fail) -----------------------------------------
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

        # 1) time-based filter ------------------------------------------
        hrs = last_n_hours if last_n_hours is not None else self.last_n_hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hrs)
        events = [e for e in events if e.timestamp >= cutoff]

        # 2) distance-based filter --------------------------------------
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
        # weather-related -----------------------------------------------
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
        """Compute a speed factor in [0,1] by combining normalized risks and fatigue/deadline."""
        # 1) compute risks
        traffic_risk = self.compute_attention_score(within_km=within_km, last_n_hours=last_n_hours)
        wx = self.get_weather_index() or WeatherIndex(temperature_c=15.0, rain_intensity=0.0, visibility=1.0, frost_risk=0.0)
        weather_risk = max(wx.rain_intensity, 1 - wx.visibility)
        
        # 2) linear combination weights (sum=1)
        w_traffic = 0.5
        w_weather = 0.3
        w_fatigue = 0.1
        w_deadline = 0.1
        
        # Calculate base speed factor considering risks and fatigue
        base_sf = 1.0 - (w_traffic * traffic_risk + w_weather * weather_risk + w_fatigue * fatigue)
        
        # Apply deadline pressure: higher pressure increases speed factor
        sf = base_sf + (w_deadline * deadline_pressure)
        
        sf = max(0.0, min(1.0, sf))
        if verbose:
            logger.debug(
                "Speed factor → traffic: %.2f, weather: %.2f, fatigue: %.2f, deadline: %.2f => sf: %.2f",
                traffic_risk, weather_risk, fatigue, deadline_pressure, sf
            )
        return sf

    # ------------------------------------------------------------------
    # Dashboard & visualization
    # ------------------------------------------------------------------

    def run_dashboard(
        self,
        *,
        start: Tuple[float,float],
        end:   Tuple[float,float],
        buffer_km:    float = 5.0,
        spacing_km:   float = 10.0,
        hours:        int   = 6,
        output_html:  str   = "dashboard_map.html",
        fatigue:      float = 0.0,
        deadline:     float = 0.0,
    ) -> None:
        """Prints a rich dashboard and saves an interactive HTML map.
        
        Args:
            start: Starting coordinates (lat, lon) in WGS-84.
            end: Ending coordinates (lat, lon) in WGS-84.
            buffer_km: Search radius around route for events/weather.
            spacing_km: Distance between weather sampling points.
            hours: Time window for event filtering.
            output_html: Path for the generated HTML map file.
            fatigue: Driver fatigue level (0.0-1.0) for speed calculations.
            deadline: Deadline pressure level (0.0-1.0) for speed calculations.
        """
        # 1) fetch route geometry & sample points for analysis ----------
        route = self._fetch_route(start, end)
        samples = self._sample_route(route, spacing_km)

        # 2) gather all relevant data -----------------------------------
        events  = self.get_events(within_km=buffer_km, last_n_hours=hours)
        wx_pts  = self.get_weather(samples)
        alerts  = self.generate_alerts(within_km=buffer_km, last_n_hours=hours)
        attn    = self.compute_attention_score(within_km=buffer_km, last_n_hours=hours)

        # 3) compute speed factor for each sample point ----------------
        speed_pts: List[Tuple[Tuple[float,float],float]] = []
        for pos, wx in wx_pts:
            # temporarily cache weather for this position
            self._cache['weather'] = wx
            sf = self.get_speed_factor(fatigue=fatigue, deadline_pressure=deadline,
                                        within_km=buffer_km, last_n_hours=hours)
            speed_pts.append((pos, sf))

        # 4) print rich console summary --------------------------------
        console.rule("🚦  Traffic & Weather Dashboard  🚦")
        
        # events summary table
        tbl = Table(title=f"Events (last {hours}h)")
        tbl.add_column("Type"); tbl.add_column("Count", justify="right")
        for full_key, count in self.get_events_summary(last_n_hours=hours, within_km=buffer_km).items():
            # Prendi solo la parte italiana prima del '|'
            name_it = full_key.split('|')[0].strip()
            tbl.add_row(name_it, str(count))
        console.print(tbl)

        # alerts section
        if alerts:
            console.print("[bold red]Alerts:[/bold red]")
            for a in alerts:
                console.print(f"• {a.message}  (relevance={a.relevance:.2f})")
        console.print(f"\nAttention score: [bold]{attn:.2f}[/bold]\n")

        # speed advice table
        stbl = Table(title="Speed advice per sample")
        stbl.add_column("Lat,Lon"); stbl.add_column("Speed factor", justify="right")
        for (lat,lon),sf in speed_pts:
            stbl.add_row(f"{lat:.4f},{lon:.4f}", f"{sf:.2f}")
        console.print(stbl)

        # 5) generate interactive map and save to file -----------------
        m = self._build_map(route, events, wx_pts, speed_pts, buffer_km)
        os.makedirs(os.path.dirname(output_html) or ".", exist_ok=True)
        m.save(output_html)
        console.print(f"\nInteractive map saved to [green]{output_html}[/green]")

    # ------------------------------------------------------------------
    # Live monitoring
    # ------------------------------------------------------------------

    def watch_live(
        self,
        *,
        within_km: float,
        callback: Callable[[Event],None],
        poll_seconds: int = 60,
    ) -> threading.Thread:
        """Background thread calling callback(e) on new important events.
        
        Args:
            within_km: Search radius for events monitoring.
            callback: Function to call when new important events are detected.
            poll_seconds: Polling interval for checking new events.
            
        Returns:
            The background thread (already started).
        """
        start_time = datetime.now(timezone.utc)
        
        def loop():
            nonlocal start_time
            while True:
                time.sleep(poll_seconds)
                self.refresh_data()  # Force refresh to get latest data
                
                evts = self.get_events(within_km=within_km)
                for e in evts:
                    # Check if event timestamp is after our monitoring start time
                    if e.timestamp > start_time and self._is_important(e):
                        callback(e)
                
        t = threading.Thread(target=loop, daemon=True)
        t.start()
        return t

    # ------------------------------------------------------------------
    # Internal route & mapping helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _fetch_route(start: Tuple[float,float], end: Tuple[float,float]) -> List[Tuple[float,float]]:
        """Fetch route geometry from OSRM routing service."""
        url = (
            f"http://router.project-osrm.org/route/v1/driving/{start[1]},{start[0]};{end[1]},{end[0]}"
            "?overview=full&geometries=geojson"
        )
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        coords = resp.json()['routes'][0]['geometry']['coordinates']
        # OSRM returns [lon, lat] but we use [lat, lon]
        return [(lat, lon) for lon, lat in coords]

    @staticmethod
    def _sample_route(route: List[Tuple[float,float]], spacing_km: float) -> List[Tuple[float,float]]:
        """Sample points along route at regular distance intervals."""
        out = [route[0]]  # always include start point
        acc = 0.0
        
        for a, b in zip(route, route[1:]):
            acc += haversine(a, b)
            if acc >= spacing_km:
                out.append(b)
                acc = 0.0  # reset accumulator
                
        # ensure end point is included
        if out[-1] != route[-1]:
            out.append(route[-1])
        return out

    def _build_map(
        self,
        route: List[Tuple[float, float]],
        events: List[Event],
        wx_pts: List[Tuple[Tuple[float, float], WeatherIndex]],
        speed_pts: List[Tuple[Tuple[float, float], float]],
        buffer_km: float
    ) -> folium.Map:
        """Constructs an interactive Folium map showing route, traffic, weather, and speed advice."""
        # Center on middle of route
        m = folium.Map(location=route[len(route)//2], zoom_start=10)
        # Plot route
        folium.PolyLine(
            route,
            color="blue",
            weight=6,
            opacity=0.7,
            tooltip="Route"
        ).add_to(m)

        # Traffic events
        color_map = {
            "incident": "red",
            "coda": "orange",
            "stau": "orange",
            "cantiere": "blue",
            "closure": "black",
            "chiusura": "black",
            "manifest": "green",
        }
        for ev in events:
            ev_type = ev.type.lower()
            # choose first matching key
            color = next((col for key, col in color_map.items() if key in ev_type), "purple")
            popup = folium.Popup(
                f"<b>{ev.type}</b><br>{ev.description}<br>"
                f"{ev.timestamp.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC<br>"
                f"Dist: {ev.distance_km:.1f} km",
                max_width=300,
            )
            folium.CircleMarker(
                location=(ev.lat, ev.lon),
                radius=6,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=popup
            ).add_to(m)

        # Weather points
        for (lat, lon), idx in wx_pts:
            # marker color by temperature
            if idx.temperature_c < 0:
                col = "navy"
            elif idx.temperature_c < 10:
                col = "blue"
            elif idx.temperature_c < 20:
                col = "green"
            elif idx.temperature_c < 30:
                col = "orange"
            else:
                col = "red"
            popup = folium.Popup(
                f"<b>{idx.temperature_c:.1f} °C</b><br>"
                f"Rain idx: {idx.rain_intensity:.2f}<br>"
                f"Vis idx: {idx.visibility:.2f}<br>"
                f"Frost risk: {'yes' if idx.frost_risk else 'no'}<br>"
                f"Speed advice: ×{next((sf for (p, sf) in speed_pts if p == (lat, lon)), 0):.2f}",
                max_width=260,
            )
            folium.CircleMarker(
                location=(lat, lon),
                radius=6,
                color=col,
                fill=True,
                fill_opacity=0.8,
                popup=popup
            ).add_to(m)

                # Legend HTML overlay
        legend = """
        <div style="position: fixed; bottom: 50px; left: 50px; width: 240px; \
                    background: white; border:2px solid grey; z-index:9999; font-size:14px; padding:10px;">
          &nbsp;<b>Traffic legend</b><br>
          &nbsp;<i class='fa fa-circle' style='color:red'></i>&nbsp;Incident<br>
          &nbsp;<i class='fa fa-circle' style='color:orange'></i>&nbsp;Queue<br>
          &nbsp;<i class='fa fa-circle' style='color:blue'></i>&nbsp;WorkZone<br>
          &nbsp;<i class='fa fa-circle' style='color:black'></i>&nbsp;Closure<br>
          &nbsp;<i class='fa fa-circle' style='color:green'></i>&nbsp;Manifest<br>
          &nbsp;<i class='fa fa-circle' style='color:purple'></i>&nbsp;Other<br><br>
          &nbsp;<b>Weather legend (°C)</b><br>
          &nbsp;<i class='fa fa-circle' style='color:navy'></i>&nbsp;< 0<br>
          &nbsp;<i class='fa fa-circle' style='color:blue'></i>&nbsp;0-9<br>
          &nbsp;<i class='fa fa-circle' style='color:green'></i>&nbsp;10-19<br>
          &nbsp;<i class='fa fa-circle' style='color:orange'></i>&nbsp;20-29<br>
          &nbsp;<i class='fa fa-circle' style='color:red'></i>&nbsp;>=30<br><br>
          &nbsp;<b>Speed advice</b><br>
          &nbsp;× factor on marker popup
        </div>
        """
        m.get_root().html.add_child(folium.Element(legend))

        # Speed advice icons - use built-in icons instead of custom logo
        for (lat, lon), sf in speed_pts:
            # Color code based on speed factor
            if sf >= 0.8:
                icon_color = 'green'
            elif sf >= 0.6:
                icon_color = 'orange'
            else:
                icon_color = 'red'
            
            folium.Marker(
                location=(lat, lon),
                icon=folium.Icon(color=icon_color, icon='tachometer-alt', prefix='fa'),
                tooltip=f"Speed factor: {sf:.2f} (buffer: {buffer_km}km)",
                popup=f"Recommended speed factor: {sf:.2f}<br>Search radius: {buffer_km}km"
            ).add_to(m)

        return m


    @staticmethod
    def _is_important(ev: Event) -> bool:
        """Determine if an event is important enough to trigger alerts."""
        return (getattr(ev, 'severity', 0) >= 3 or 
                any(k in ev.type.lower() for k in ('chiusura','incident','manifest')))
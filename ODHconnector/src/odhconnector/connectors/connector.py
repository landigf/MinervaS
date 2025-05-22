"""ODHConnector: public entry-point used by MinervaS."""
import logging
from datetime import datetime
from typing import Callable, List, Optional, Tuple
from datetime import datetime, timezone, timedelta

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

    _TTL = timedelta(seconds=30)

    def __init__(
        self,
        odh_base_url: str,
        odh_api_key: str,
        position_provider: Callable[[], Tuple[float, float]],
        route_segment: str,
        auto_refresh: bool = True,
        last_n_hours: int = 24,            # ← default 24 h
    ):
        self.odh_base_url = odh_base_url.rstrip('/')
        self.odh_api_key = odh_api_key
        self.position_provider = position_provider
        self.route_segment = route_segment
        self.auto_refresh = auto_refresh
        self._last_refresh: datetime | None = None
        self.last_n_hours = last_n_hours

        self._weather_adapter = WeatherAdapter(self.odh_base_url)
        self._traffic_adapter = TrafficAdapter(self.odh_base_url)

        self._cache: dict[str, object] = {}

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _maybe_refresh(self) -> None:
        if self.auto_refresh and (
            self._last_refresh is None
            or datetime.now(timezone.utc) - self._last_refresh > self._TTL
        ):
            self.refresh_data()

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def refresh_data(self) -> None:
        """Scarica traffico + meteo; il meteo può fallire senza bloccare."""
        pos = self.position_provider()

        # ── traffico ────────────────────────────────────────────────────
        events = self._traffic_adapter.fetch_events(self.route_segment)
        for ev in events:
            ev.distance_km = haversine(pos, (ev.lat, ev.lon))
        self._cache["events"] = events

        # ── meteo (soft-fail) ───────────────────────────────────────────
        try:
            self._cache["weather"] = self._weather_adapter.fetch_weather(pos)
        except Exception as exc:
            logger.warning("Weather fetch failed, using None: %s", exc)
            self._cache["weather"] = None

        self._last_refresh = datetime.now(timezone.utc)
        logger.debug("Data refreshed: %s", self._last_refresh)
        logger.debug("Events: %d, Weather: %s", len(self._cache["events"]), self._cache["weather"])


    """Ritorna gli eventi filtrati per tempo e distanza.
    Se all=True, ritorna anche gli eventi storici (fino a 24h fa)."""
    def get_events(
        self,
        all: bool = True,
        last_n_hours: Optional[int] = None,
        within_km: Optional[float] = None,
        verbose: bool = False,
    ) -> list[Event]:
        self._maybe_refresh()
        evts: list[Event] = self._cache.get("events", [])

        # 1) tempo
        hrs = last_n_hours if last_n_hours is not None else self.last_n_hours
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hrs)
        evts = [e for e in evts if e.timestamp >= cutoff]
        # 2) distanza
        if within_km is not None:
            pos = self.position_provider()
            evts = [e for e in evts if e.distance_km is not None and e.distance_km <= within_km]
        if verbose:
            logger.debug("Filtered to %d events (last %dh)", len(evts), hrs)
        return evts

    #------------------------------------------------------------------ #

    def get_incidents(self, within_km=None, last_n_hours=None, verbose=False) -> list[Incident]:
        """Eventi di tipo incidente."""
        return [
            e for e in self.get_events(all=False,
                                       within_km=within_km,
                                       last_n_hours=last_n_hours,
                                       verbose=verbose)
            if isinstance(e, Incident)
        ]

    def get_queues(self, **kwargs) -> list[Event]:
        """Eventi di tipo coda/stau."""
        return [e for e in self.get_events(**kwargs)
                if "code" in e.type or "stau" in e.type]

    def get_workzones(self, **kwargs) -> list[Event]:
        """Eventi di tipo cantiere/baustelle."""
        return [e for e in self.get_events(**kwargs)
                if "cantiere" in e.type or "baustelle" in e.type]

    def get_closures(self, **kwargs) -> list[Event]:
        """Eventi di tipo chiusura temporanea/permanente."""
        return [e for e in self.get_events(**kwargs)
                if "chiusura" in e.type or "sperre" in e.type]

    def get_manifestations(self, **kwargs) -> list[Event]:
        """Eventi di manifestazione/veranstaltung."""
        return [e for e in self.get_events(**kwargs)
                if "manifestazione" in e.type or "veranstaltung" in e.type]

    def get_temporary_closures(self, **kw) -> list[Event]:
        """Eventi di tipo chiusura temporanea/temporäre sperre."""
        return [e for e in self.get_events(**kw)
                if "chiusura temporanea" in e.type or "zeitweilige sperre" in e.type]

    def get_winter_closures(self, **kw) -> list[Event]:
        """Eventi di tipo chiusura invernale/wintersperre."""
        return [e for e in self.get_events(**kw)
                if "chiusura invernale" in e.type or "wintersperre" in e.type]

    def get_snow_warnings(self, **kw) -> list[Event]:
        """Eventi di tipo neve/neve."""
        return [e for e in self.get_events(**kw)
                if "nevischio" in e.type or "schneeregen" in e.type]

    def get_fog_warnings(self, **kw) -> list[Event]:
        """Eventi di tipo banchi di nebbia/nebelbänke."""
        return [e for e in self.get_events(**kw)
                if "banchi di nebbia" in e.type or "nebelbänke" in e.type]

    def get_chain_requirements(self, **kw) -> list[Event]:
        """Eventi di tipo obbligo di catene/kettenpflicht."""
        return [e for e in self.get_events(**kw)
                if "obbligo di catene" in e.type or "kettenpflicht" in e.type]

    def get_wildlife_hazards(self, **kw) -> list[Event]:
        """Eventi di tipo animali vaganti/tiere auf fahrbahn."""
        return [e for e in self.get_events(**kw)
                if "animali vaganti" in e.type or "tiere auf fahrbahn" in e.type]

    def get_free_flow(self, **kw) -> list[Event]:
        """Eventi di tipo percorribile senza limitazione."""
        return [e for e in self.get_events(**kw)
                if "percorribile senza limitazione" in e.type or "frei befahrbar" in e.type]

    # ------------------------------------------------------------------ #
    def get_events_summary(
        self,
        within_km: float | None = None,
        last_n_hours: int | None = None,
    ) -> dict[str, int]:
        """Ritorna {categoria: n_eventi} filtrato per raggio/tempo."""
        evts = self.get_events(all=True, last_n_hours=last_n_hours)
        if within_km is not None:
            pos = self.position_provider()
            evts = [e for e in evts if e.distance_km is not None and e.distance_km <= within_km]
        counts: dict[str, int] = {}
        for e in evts:
            counts[e.type] = counts.get(e.type, 0) + 1
        return counts


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

    #------------------------------------------------------------------ #

    def generate_alerts(
        self,
        within_km: float = 5,
        last_n_hours: int | None = None,
        verbose: bool = False,
    ) -> list[Alert]:
        """
        Genera avvisi basati su eventi di traffico e meteo.
        
        Gli avvisi sono generati in base alla gravità degli eventi, alla
        loro distanza dalla posizione attuale e alle condizioni meteo.
        Filtra eventi per distanza e tempo, quindi applica regole fuzzy:
        
        - Incidenti gravi (severity ≥3) → rallentamento al 50%
        - Code → suggerisce deviazione (velocità 80%)
        - Cantieri → guida con cautela (velocità 90%)
        - Chiusure → stop obbligatorio (velocità 0%)
        - Manifestazioni → possibili deviazioni (velocità 70%)
        - Nevischio → riduzione 70%, rischio di slittamento
        - Nebbia → riduzione 60%, visibilità
        - Obbligo catene → alert catene (velocità 50%)
        - Animali vaganti → guida con prudenza (velocità 80%)
        - Flusso libero → conferma adeguato mantenimento (no alert)
        - Meteo (best‐effort): pioggia intensa o visibilità scarsa
        
        Restituisce lista di Alert con:
        - message: descrizione
        - suggested_speed_factor: frazione del limite
        - relevance: peso [0–1]
        """
        alerts: list[Alert] = []
        # helper per raccogliere eventi grouped
        groups = {
            "incident": self.get_incidents(within_km, last_n_hours, verbose),
            "queue":    self.get_queues(within_km=within_km, last_n_hours=last_n_hours),
            "workzone": self.get_workzones(within_km=within_km, last_n_hours=last_n_hours),
            "closure":  self.get_closures(within_km=within_km, last_n_hours=last_n_hours),
            "manifest": self.get_manifestations(within_km=within_km, last_n_hours=last_n_hours),
            "snow":     self.get_snow_warnings(within_km=within_km, last_n_hours=last_n_hours),
            "fog":      self.get_fog_warnings(within_km=within_km, last_n_hours=last_n_hours),
            "chain":    self.get_chain_requirements(within_km=within_km, last_n_hours=last_n_hours),
            "wildlife": self.get_wildlife_hazards(within_km=within_km, last_n_hours=last_n_hours),
            # free_flow non genera alert
        }
        # Incidenti gravi
        for inc in groups["incident"]:
            if inc.severity >= 3:
                alerts.append(Alert(
                    message=f"Incidente grave a {inc.distance_km:.1f} km: rallentamento 50 %",
                    suggested_speed_factor=0.5,
                    relevance=0.9
                ))
        # Code
        cnt = len(groups["queue"])
        if cnt:
            alerts.append(Alert(
                message=f"{cnt} code entro {within_km} km: valuta deviazione",
                suggested_speed_factor=0.8,
                relevance=0.7
            ))
        # Cantieri
        cnt = len(groups["workzone"])
        if cnt:
            alerts.append(Alert(
                message=f"{cnt} cantieri entro {within_km} km: guida con cautela",
                suggested_speed_factor=0.9,
                relevance=0.6
            ))
        # Chiusure (stop)
        for e in groups["closure"]:
            alerts.append(Alert(
                message=f"Chiusura: {e.description}",
                suggested_speed_factor=0.0,
                relevance=1.0
            ))
        # Manifestazioni
        cnt = len(groups["manifest"])
        if cnt:
            alerts.append(Alert(
                message=f"{cnt} manifestazioni in zona: possibili deviazioni",
                suggested_speed_factor=0.7,
                relevance=0.5
            ))
        # Neve
        if groups["snow"]:
            alerts.append(Alert(
                message="Nevischio rilevato: riduci 30 %",
                suggested_speed_factor=0.7,
                relevance=0.6
            ))
        # Nebbia
        if groups["fog"]:
            alerts.append(Alert(
                message="Nebbia: riduci 40 %",
                suggested_speed_factor=0.6,
                relevance=0.6
            ))
        # Catene
        if groups["chain"]:
            alerts.append(Alert(
                message="Obbligo catene: verifica equipaggiamento",
                suggested_speed_factor=0.5,
                relevance=0.8
            ))
        # Animali
        if groups["wildlife"]:
            alerts.append(Alert(
                message="Animali vaganti: guida con prudenza",
                suggested_speed_factor=0.8,
                relevance=0.7
            ))
        # Meteo (best‐effort)
        wx = self._cache.get("weather")
        if wx:
            if wx.rain_intensity > 0.5:
                alerts.append(Alert(
                    message="Pioggia intensa: riduci 30 %",
                    suggested_speed_factor=0.7,
                    relevance=0.7
                ))
            if wx.visibility < 0.4:
                alerts.append(Alert(
                    message="Scarsa visibilità: riduci 40 %",
                    suggested_speed_factor=0.6,
                    relevance=0.8
                ))
        if verbose:
            for a in alerts:
                logger.debug("Alert generated: %s", a)
        return alerts



    # ------------------------------------------------------------------ #

    def compute_attention_score(
        self,
        within_km: float = 5,
        last_n_hours: int | None = None,
        weights: dict[str, float] | None = None,
        verbose: bool = False,
    ) -> float:
        """
        Calcola un punteggio [0–1] che rappresenta l’attenzione richiesta,
        pesando ogni alert per la sua rilevanza e gravità.

        Args:
            within_km: raggio in km per filtrare eventi.
            last_n_hours: orizzonte temporale (ore).
            weights: mappa opzionale {tipo_alert: peso} per personalizzare.
            verbose: se True, logga dettagli.

        Returns:
            score (float): somma(peso_tipo × relevance_alert) / somma(peso_tipo).
        """
        alerts = self.generate_alerts(within_km, last_n_hours, verbose)
        if not alerts:
            return 0.0

        # default weights (punti per categoria di alert)
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

        num, den = 0.0, 0.0
        for a in alerts:
            # deduco un tipo base dall’alert.message o relevance
            kind = None
            for k in w:
                if k in a.message.lower():
                    kind = k
                    break
            kind = kind or "incident"
            weight = w.get(kind, 1.0)
            num += weight * a.relevance
            den += weight

            if verbose:
                logger.debug("Alert %r weight=%.1f relevance=%.2f", a.message, weight, a.relevance)

        score = num / den if den > 0 else 0.0
        return min(max(score, 0.0), 1.0)

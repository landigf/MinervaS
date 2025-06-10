#!/usr/bin/env python
"""
live_monitoring.py
-------------------
Demo che bypassa il sistema di refresh e di watch_live di ODHConnector,
forzando la cache interna e invocando la callback immediatamente.

1. Crea ODHConnector con auto_refresh disabilitato.
2. Sovrascrive refresh_data e get_events per usare solo la cache.
3. Inietta un evento simulato in conn._cache["events"].
4. Override di watch_live per leggere direttamente la cache e chiamare callback.
5. Chiama watch_live (callback subito invocata), poi termina.
"""
import time
from datetime import datetime, timezone

from odhconnector.connectors.connector import ODHConnector
from odhconnector.models import Event

def notify(event: Event) -> None:
    print("🔔 NOTIFY:", event.type, "|", event.description,
          "@", event.timestamp.astimezone(timezone.utc).isoformat())

def main():
    # 1) Setup connettore senza auto-refresh
    start = (46.07, 11.12)
    conn = ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",
        position_provider=lambda: start,
        route_segment="*",
        auto_refresh=False,
        last_n_hours=1,
    )

    # 2) Bypass del refresh e del filtraggio eventi reali
    conn.refresh_data = lambda: None
    # Override get_events per tornare solo ciò che c'è in cache
    conn.get_events = lambda *, within_km=None, last_n_hours=None: conn._cache.get("events", [])

    # 3) Inietta un evento simulato nella cache
    sim_event = Event(
        type="incident",
        description="Evento simulato forzato",
        timestamp=datetime.now(timezone.utc),
        lat=start[0],
        lon=start[1],
    )
    conn._cache["events"] = [sim_event]
    print("✉️ Evento simulato iniettato nella cache.")

    # 4) Override watch_live per leggere immediatamente la cache
    def fake_watch(*, within_km, callback, poll_seconds):
        # Ignora poll_seconds, chiama subito la callback su tutti gli eventi
        for ev in conn._cache["events"]:
            if conn._is_important(ev):
                callback(ev)
        return None

    conn.watch_live = fake_watch

    # 5) Invoca il “watch_live” finto: callback è chiamata all'istante
    print("▶️ Invocazione fake_watch…")
    conn.watch_live(within_km=10.0, callback=notify, poll_seconds=2)

    print("✅ Demo live monitoring completata.")

if __name__ == "__main__":
    main()

#!/usr/bin/env python
"""
live_monitoring.py
-------------------
Esempio di uso della funzionalità di live monitoring di ODHConnector.
Il programma avvia un thread che ascolta nuovi eventi "importanti" (severity>=3,
chiusure, incidenti, manifestazioni) entro un raggio specificato, chiamando
una callback ogni volta che ne rileva uno nuovo.

In questo demo:
 1. Si avvia watch_live() con polling ogni 2 secondi.
 2. Disabilitiamo l'auto refresh per preservare eventi iniettati.
 3. Dopo 1 secondo, si inietta un evento simulato nel cache del connector.
 4. La callback stampa la notifica dell'evento.
 5. Il programma termina dopo pochi secondi.

Usage:
    python demos/live_monitoring.py
"""
import time
from datetime import datetime, timezone

from odhconnector.connectors.connector import ODHConnector
from odhconnector.models import Event

# Callback invoked on new important event
def notify(event: Event) -> None:
    print("🔔 New important event detected:")
    print(f"   Type       : {event.type}")
    print(f"   Description: {event.description}")
    print(f"   Timestamp  : {event.timestamp.astimezone(timezone.utc)} UTC")
    print(f"   Location   : ({event.lat:.4f}, {event.lon:.4f})")
    print()


def main():
    # 1) Setup connector with auto_refresh disabled
    start = (46.07, 11.12)
    conn = ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",
        position_provider=lambda: start,
        route_segment="*",
        auto_refresh=False,  # disabilita il refresh automatico
        last_n_hours=1,
    )
    # Override refresh_data to prevent cache overwrite
    conn.refresh_data = lambda: None
    # Initialize empty events cache
    conn._cache["events"] = []

    # 2) Avvia il live watcher (poll ogni 2 secondi)
    print("📡 Starting live monitoring (within 10 km, poll every 2s)...")
    watcher = conn.watch_live(within_km=10.0, callback=notify, poll_seconds=2)

    # 3) Attendi 1 secondo e inietta l'evento simulato
    time.sleep(1)
    sim_event = Event(
        type="incident",
        description="Simulated test event for live monitoring",
        timestamp=datetime.now(timezone.utc),
        lat=start[0],
        lon=start[1],
    )
    conn._cache["events"].append(sim_event)
    print("✉️ Simulated event injected into cache.")

    # 4) Attendi qualche secondo per ricevere la notifica
    time.sleep(5)
    print("✅ Live monitoring demo completed.")


if __name__ == "__main__":
    main()

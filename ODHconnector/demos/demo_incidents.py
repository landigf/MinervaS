#!/usr/bin/env python
"""
debug_incidents.py
------------------
Demo avanzato: analizza ogni Incidento, stampa i dettagli e rivela
eventuali duplicati, ordinando per distanza.
"""

from __future__ import annotations
import argparse
import logging
import sys

from odhconnector.connectors.connector import ODHConnector

# ——————————————————————————————————————————————————————————————————————————————
# abilitiamo DEBUG su tutto il package per vedere esattamente le chiamate HTTP
# logging.basicConfig(
#     level=logging.DEBUG,
#     format="%(levelname)s %(name)s: %(message)s",
#     stream=sys.stdout,
# )
# ——————————————————————————————————————————————————————————————————————————————

def build_connector(lat: float, lon: float) -> ODHConnector:
    c = ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",                # Public API
        position_provider=lambda: (lat, lon),
        route_segment="*",             # prendi tutte le origini
        auto_refresh=True,
    )
    return c

def main() -> None:
    p = argparse.ArgumentParser(
        description="Debug degli Incidenti ODH entro un raggio.")
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--km",  type=float, default=15)
    args = p.parse_args()

    conn = build_connector(args.lat, args.lon)

    # 1) Prendi gli incidenti
    incidents = conn.get_incidents(within_km=args.km, verbose=True)

    if not incidents:
        print(f"\nNessun incidente entro {args.km} km da ({args.lat},{args.lon})")
        return

    # 2) Ordina per distanza
    incidents.sort(key=lambda i: i.distance_km or float("inf"))

    # 3) Raccogli un set per dedupe basato su (time, lat, lon)
    seen = set()

    print(f"\n== INCIDENTI DETTAGLIATI entro {args.km} km ==")
    for inc in incidents:
        key = (inc.timestamp.isoformat(), inc.lat, inc.lon)
        dup = " (DUPLICATO)" if key in seen else ""
        seen.add(key)

        sev = getattr(inc, "severity", "n/a")
        print(
            f"- Time: {inc.timestamp.isoformat()} | "
            f"Type: {inc.type} | "
            f"Desc: {inc.description!r} | "
            f"Dist: {inc.distance_km:.2f} km | "
            f"Sev: {sev}{dup}"
        )

    # 4) Report di riepilogo finale
    print(f"\nTotale incidenti trovati (prima del dedupe): {len(incidents)}")
    print(f"Totale unici dopo dedupe: {len(seen)}")

if __name__ == "__main__":
    main()

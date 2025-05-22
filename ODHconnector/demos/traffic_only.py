#!/usr/bin/env python
"""
traffic_only.py - traffic-only + time filter + route-aware alerts

python demos/traffic_only.py --lat 46.07 --lon 11.12 --km 15 --hours 12
"""

import argparse
from odhconnector.connectors.connector import ODHConnector

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--lat", type=float, required=True)
    p.add_argument("--lon", type=float, required=True)
    p.add_argument("--km", type=float, default=10)
    p.add_argument("--hours", type=int, default=6)
    args = p.parse_args()

    conn = ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",
        position_provider=lambda: (args.lat, args.lon),
        route_segment="*",          # o "A22_Trentino" per filtrare per origin
        auto_refresh=True,
        last_n_hours=args.hours,
    )

    print("Incidenti:", len(conn.get_incidents(within_km=args.km)))
    print("Code   :", len(conn.get_queues(within_km=args.km)))
    print("Cantieri:", len(conn.get_workzones(within_km=args.km)))
    print("Chiusure:", len(conn.get_closures(within_km=args.km)))
    print("Manifestazioni:", len(conn.get_manifestations(within_km=args.km)))

    print("\nALERTS:")
    for a in conn.generate_alerts(within_km=args.km):
        print("-", a.message)

if __name__ == "__main__":
    main()

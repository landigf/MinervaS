#!/usr/bin/env python
"""
traffic.py - prova tutti i metodi traffic-only.
"""

from odhconnector.connectors.connector import ODHConnector

def main():
    conn = ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",
        position_provider=lambda: (46.07, 11.12),
        route_segment="*", 
        auto_refresh=True, 
        last_n_hours=1000
    )

    km = 20

    print("Incidenti:", len(conn.get_incidents(within_km=km)))
    print("Code:", len(conn.get_queues(within_km=km)))
    print("Cantieri:", len(conn.get_workzones(within_km=km)))
    print("Chiusure:", len(conn.get_closures(within_km=km)))
    print("Manifestazioni:", len(conn.get_manifestations(within_km=km)))

    print("\nALERTS:")
    for a in conn.generate_alerts(within_km=km):
        print("-", a.message)

if __name__ == "__main__":
    main()

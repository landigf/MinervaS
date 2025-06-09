#!/usr/bin/env python
"""
demo_traffic_map.py
-------------------
Genera una mappa interattiva del percorso reale tra inizio e fine e degli eventi traffico lungo la route.

Usage:
    python demos/demo_traffic_map.py \
      --start 46.07,11.12 --end 46.4983,11.3548 \
      --buffer 10 --hours 1000 \
      --output demos/web-demo/traffic_map.html
"""
import argparse
import logging
import os
import sys
from datetime import timezone, timedelta
import requests
import folium
from math import radians, cos, sin, asin, sqrt
from odhconnector.connectors.connector import ODHConnector

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)


def haversine(p1, p2):
    """Calcola distanza km tra due punti (lat, lon)."""
    lat1, lon1 = p1
    lat2, lon2 = p2
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1)*cos(lat2)*sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    return 6371 * c


def fetch_route(start, end):
    """Chiama OSRM per ottenere il percorso driving overview full."""
    lat1, lon1 = start
    lat2, lon2 = end
    url = (
        f"http://router.project-osrm.org/route/v1/driving/"
        f"{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    coords = data["routes"][0]["geometry"]["coordinates"]
    # convert [lon,lat] to (lat,lon)
    return [(lat, lon) for lon, lat in coords]


def filter_along_route(events, route, buffer_km):
    """Filtra gli eventi entro buffer_km da uno qualsiasi dei punti del percorso."""
    result = []
    for ev in events:
        for pt in route:
            if haversine(pt, (ev.lat, ev.lon)) <= buffer_km:
                result.append(ev)
                break
    return result


def build_map(route, events, buffer_km):
    """Costruisce la mappa con route e marker per ogni evento."""
    mid = route[len(route) // 2]
    m = folium.Map(location=mid, zoom_start=10)
    # Path
    folium.PolyLine(route, color="blue", weight=4, opacity=0.6, tooltip="Route").add_to(m)
    # Color map per tipo
    color_map = {
        "incident": "red",
        "coda": "orange",
        "cantiere": "blue",
        "chiusura": "black",
        "manifestazione": "green",
        "unknown": "purple",
    }
    for ev in events:
        base = "unknown"
        for key in color_map:
            if key in ev.type:
                base = key
                break
        color = color_map.get(base, "purple")
        popup = folium.Popup(
            f"<b>{ev.type}</b><br>{ev.description}<br>"
            f"{ev.timestamp.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M')} UTC<br>"
            f"{ev.distance_km:.1f} km",
            max_width=300,
        )
        folium.CircleMarker(
            location=(ev.lat, ev.lon),
            radius=6,
            color=color,
            fill=True,
            fill_opacity=0.7,
            popup=popup,
        ).add_to(m)
    # Legend HTML overlay
    legend = """
    <div style="position: fixed; bottom: 50px; left: 50px; width: 150px; 
                background-color: white; border:2px solid grey; z-index:9999; font-size:14px;">
      &nbsp;<b>Legend</b><br>
      &nbsp;<i class='fa fa-circle' style='color:red'></i>&nbsp;Incident<br>
      &nbsp;<i class='fa fa-circle' style='color:orange'></i>&nbsp;Queue<br>
      &nbsp;<i class='fa fa-circle' style='color:blue'></i>&nbsp;Workzone<br>
      &nbsp;<i class='fa fa-circle' style='color:black'></i>&nbsp;Closure<br>
      &nbsp;<i class='fa fa-circle' style='color:green'></i>&nbsp;Manifestation<br>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend))
    return m


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start", type=str, required=True, help="Lat,Lon iniziali, es 46.07,11.12"
    )
    parser.add_argument(
        "--end", type=str, required=True, help="Lat,Lon finali, es 46.4983,11.3548"
    )
    parser.add_argument(
        "--buffer",
        type=float,
        default=0.1,
        help="Raggio di buffer km attorno al percorso",
    )
    parser.add_argument(
        "--hours", type=int, default=6, help="Considera eventi ultime N ore"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="demos/web-demo/traffic_map.html",
        help="Percorso output HTML",
    )
    args = parser.parse_args()

    start = tuple(map(float, args.start.split(",")))
    end = tuple(map(float, args.end.split(",")))
    route = fetch_route(start, end)

    conn = ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",
        position_provider=lambda: start,
        route_segment="*",
        auto_refresh=True,
        last_n_hours=args.hours,
    )

    events = conn.get_events(within_km=args.buffer, last_n_hours=args.hours)
    events_on_route = filter_along_route(events, route, args.buffer)
    for ev in events_on_route:
        ev.distance_km = haversine(start, (ev.lat, ev.lon))

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    m = build_map(route, events_on_route, args.buffer)
    m.save(args.output)
    print(f"Map saved to {args.output}")


if __name__ == "__main__":
    main()

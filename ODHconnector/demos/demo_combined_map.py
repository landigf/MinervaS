#!/usr/bin/env python
"""
demo_combined_map.py
---------------------
Genera una mappa interattiva del percorso fra inizio e fine mostrando:

 1. Eventi traffico (incidenti, code, cantieri, chiusure, manifestazioni, etc.)
 2. Condizioni meteo (temperatura, pioggia, visibilità, rischio gelo)

Uso:
    python demos/demo_combined_map.py \
      --start 46.07,11.12 --end 46.4983,11.3548 \
      --buffer 20 --spacing 10 \
      --hours 5000 --output demos/web-demo/combined_map.html

Argomenti:
  --start     Lat,Lon iniziali (es. 46.07,11.12)
  --end       Lat,Lon finali   (es. 46.4983,11.3548)
  --buffer    Raggio km per filtri eventi e marker meteo (default 5)
  --spacing   Distanza km fra campioni meteo (default 10)
  --hours     Orizzonte temporale per eventi traffico (default 6)
  --output    File HTML d'uscita (default demos/web-demo/combined_map.html)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from math import radians, cos, sin, asin, sqrt
from datetime import timezone
from typing import List, Tuple

import folium
from odhconnector.connectors.connector import ODHConnector

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("demo_combined_map")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def haversine(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Great-circle distance in km."""
    lat1, lon1 = p1
    lat2, lon2 = p2
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    return 6371 * 2 * asin(sqrt(a))


def fetch_route(start: Tuple[float, float], end: Tuple[float, float]) -> List[Tuple[float, float]]:
    """Ottiene percorso driving da OSRM."""
    import requests
    lat1, lon1 = start
    lat2, lon2 = end
    url = (
        f"http://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
        "?overview=full&geometries=geojson"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    coords = resp.json()["routes"][0]["geometry"]["coordinates"]
    return [(lat, lon) for lon, lat in coords]


def sample_route(route: List[Tuple[float, float]], spacing_km: float) -> List[Tuple[float, float]]:
    """Campiona route ogni spacing_km km."""
    if not route:
        return []
    samples = [route[0]]
    acc = 0.0
    for prev, curr in zip(route, route[1:]):
        d = haversine(prev, curr)
        acc += d
        if acc >= spacing_km:
            samples.append(curr)
            acc = 0.0
    if samples[-1] != route[-1]:
        samples.append(route[-1])
    return samples

# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

def temp_color(temp: float) -> str:
    if temp < 0:
        return "navy"
    if temp < 10:
        return "blue"
    if temp < 20:
        return "green"
    if temp < 30:
        return "orange"
    return "red"

traffic_color_map = {
    "Incident": "red",
    "Queue":    "orange",
    "WorkZone": "blue",
    "Closure":  "black",
    "Manifest": "green",
    "Default":  "purple",
}

# ---------------------------------------------------------------------------
# Map builder
# ---------------------------------------------------------------------------

def build_map(
    route: List[Tuple[float, float]],
    events,
    weather_pts,
    buffer_km: float
) -> folium.Map:
    # Center map
    m = folium.Map(location=route[len(route)//2], zoom_start=10)
    # Highlight route in bold blue
    folium.PolyLine(
        route,
        color="blue",
        weight=6,
        opacity=0.7,
        tooltip="Route"
    ).add_to(m)

    # Traffic events
    for ev in events:
        # choose color
        for key, col in traffic_color_map.items():
            if key.lower() in ev.type.lower():
                color = col
                break
        else:
            color = traffic_color_map["Default"]
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
    for (lat, lon), idx in weather_pts:
        col = temp_color(idx.temperature_c)
        popup = folium.Popup(
            f"<b>{idx.temperature_c:.1f} °C</b><br>"
            f"Rain idx: {idx.rain_intensity:.2f}<br>"
            f"Vis idx: {idx.visibility:.2f}<br>"
            f"Frost: {'yes' if idx.frost_risk else 'no'}",
            max_width=200
        )
        folium.CircleMarker(
            location=(lat, lon),
            radius=6,
            color=col,
            fill=True,
            fill_opacity=0.8,
            popup=popup
        ).add_to(m)

        # Legends
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; width: 220px; \
                background: white; border:2px solid grey; z-index:9999; font-size:14px;">
      &nbsp;<b>Traffic legend</b><br>
      &nbsp;<i class='fa fa-circle' style='color:red'></i>&nbsp;Incident<br>
      &nbsp;<i class='fa fa-circle' style='color:orange'></i>&nbsp;Queue<br>
      &nbsp;<i class='fa fa-circle' style='color:blue'></i>&nbsp;WorkZone<br>
      &nbsp;<i class='fa fa-circle' style='color:black'></i>&nbsp;Closure<br>
      &nbsp;<i class='fa fa-circle' style='color:green'></i>&nbsp;Manifest<br>
      &nbsp;<i class='fa fa-circle' style='color:purple'></i>&nbsp;Other<br><br>
      &nbsp;<b>Weather (°C)</b><br>
      &nbsp;<i class='fa fa-circle' style='color:navy'></i>&nbsp;< 0<br>
      &nbsp;<i class='fa fa-circle' style='color:blue'></i>&nbsp;0-9<br>
      &nbsp;<i class='fa fa-circle' style='color:green'></i>&nbsp;10-19<br>
      &nbsp;<i class='fa fa-circle' style='color:orange'></i>&nbsp;20-29<br>
      &nbsp;<i class='fa fa-circle' style='color:red'></i>&nbsp;>=30
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    return m

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True, help="Lat,Lon iniziali")
    parser.add_argument("--end", required=True, help="Lat,Lon finali")
    parser.add_argument("--buffer", type=float, default=5.0, help="Raggio km buffer")
    parser.add_argument("--spacing", type=float, default=10.0, help="Spacing campioni meteo")
    parser.add_argument("--hours", type=int, default=6, help="Eventi ultime N ore")
    parser.add_argument("--output", default="demos/web-demo/combined_map.html", help="Output HTML")
    args = parser.parse_args()

    start = tuple(map(float, args.start.split(",")))
    end = tuple(map(float, args.end.split(",")))

    log.info("Fetching route…")
    route = fetch_route(start, end)

    log.info("Loading traffic & weather…")
    conn = ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",
        position_provider=lambda: start,
        route_segment="*",
        auto_refresh=True,
        last_n_hours=args.hours
    )
    # traffic events filtered by buffer and time
    events = conn.get_events(within_km=args.buffer, last_n_hours=args.hours)
    # weather samples along route
    samples = sample_route(route, args.spacing)
    weather_pts = conn.get_weather(samples)

    log.info("Plotting %d events and %d weather points", len(events), len(weather_pts))

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    m = build_map(route, events, weather_pts, args.buffer)
    m.save(args.output)
    print(f"Map saved to {args.output}")


if __name__ == "__main__":
    main()

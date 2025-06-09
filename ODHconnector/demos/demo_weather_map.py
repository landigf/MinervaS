#!/usr/bin/env python
"""
demo_weather_map.py
-------------------
Genera una mappa interattiva del percorso stradale reale (OSRM) fra inizio e
fine e visualizza le *condizioni meteo* (live o forecast) lungo la route.

Usage
-----
    python demos/demo_weather_map.py \
      --start 46.07,11.12 --end 46.4983,11.3548 \
      --buffer 5 --spacing 10 \
      --output demos/web-demo/weather_map.html

Arguments
~~~~~~~~~
--start   Lat,Lon iniziali   (es. 46.07,11.12)
--end     Lat,Lon finali     (es. 46.4983,11.3548)
--buffer  Raggio km dei marker meteo attorno al percorso (default 5)
--spacing Distanza km fra due campioni meteo lungo il percorso (default 10)
--output  Percorso file HTML d'uscita (default demos/web-demo/weather_map.html)
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from math import radians, cos, sin, asin, sqrt
from typing import List, Tuple

import folium
import requests

from odhconnector.connectors.connector import ODHConnector

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s %(name)s: %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("demo_weather_map")

# ---------------------------------------------------------------------------
# Helpers comuni
# ---------------------------------------------------------------------------

def haversine(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
    """Distanza great-circle (km) fra due punti (lat, lon)."""
    lat1, lon1 = p1
    lat2, lon2 = p2
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    return 6371 * 2 * asin(sqrt(a))


def fetch_route(start: Tuple[float, float], end: Tuple[float, float]) -> List[Tuple[float, float]]:
    """Chiama OSRM (public) per ottenere il percorso driving completo."""
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
    """Ritorna sottocampioni equidistanti (~spacing_km) lungo la route."""
    if not route:
        return []
    samples = [route[0]]
    accum = 0.0
    for i in range(1, len(route)):
        d = haversine(route[i - 1], route[i])
        accum += d
        if accum >= spacing_km:
            samples.append(route[i])
            accum = 0.0
    if samples[-1] != route[-1]:
        samples.append(route[-1])
    return samples

# ---------------------------------------------------------------------------
# Styling temperature markers
# ---------------------------------------------------------------------------

def temp_color(temp: float) -> str:
    """Mappa temperatura (°C) → colore marker."""
    if temp < 0:
        return "navy"
    if temp < 10:
        return "blue"
    if temp < 20:
        return "green"
    if temp < 30:
        return "orange"
    return "red"

# ---------------------------------------------------------------------------
# Costruzione mappa
# ---------------------------------------------------------------------------

def build_map(
    route: List[Tuple[float, float]],
    weather_pts: List[Tuple[Tuple[float, float], object]],
    buffer_km: float,
) -> folium.Map:
    mid = route[len(route) // 2]
    m = folium.Map(location=mid, zoom_start=9)
    folium.PolyLine(route, color="black", weight=4, opacity=0.6, tooltip="Route").add_to(m)

    for (lat, lon), idx in weather_pts:
        color = temp_color(idx.temperature_c)
        popup = folium.Popup(
            f"<b>{idx.temperature_c:.1f} °C</b><br>"
            f"Rain idx: {idx.rain_intensity:.2f}<br>"
            f"Visibility idx: {idx.visibility:.2f}<br>"
            f"Frost risk: {'yes' if idx.frost_risk else 'no'}",
            max_width=250,
        )
        folium.CircleMarker(
            location=(lat, lon),
            radius=6,
            color=color,
            fill=True,
            fill_opacity=0.8,
            popup=popup,
        ).add_to(m)

    # Legend
    legend = (
        "<div style='position: fixed; bottom:50px; left:50px; width:180px;"
        " background:white; border:2px solid grey; z-index:9999; font-size:14px;'>"
        "&nbsp;<b>Temperature</b><br>"
        "&nbsp;<i class='fa fa-circle' style='color:navy'></i>&nbsp;< 0 °C<br>"
        "&nbsp;<i class='fa fa-circle' style='color:blue'></i>&nbsp;0-9 °C<br>"
        "&nbsp;<i class='fa fa-circle' style='color:green'></i>&nbsp;10-19 °C<br>"
        "&nbsp;<i class='fa fa-circle' style='color:orange'></i>&nbsp;20-29 °C<br>"
        "&nbsp;<i class='fa fa-circle' style='color:red'></i>&nbsp;≥ 30 °C<br>"
        "</div>"
    )
    m.get_root().html.add_child(folium.Element(legend))
    return m

# ---------------------------------------------------------------------------
# Entry-point CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start", required=True,
        help="Lat,Lon iniziali, es 46.07,11.12"
    )
    parser.add_argument(
        "--end", required=True,
        help="Lat,Lon finali, es 46.4983,11.3548"
    )
    parser.add_argument(
        "--buffer", type=float, default=5.0,
        help="Raggio km dei marker meteo attorno al percorso"
    )
    parser.add_argument(
        "--spacing", type=float, default=10.0,
        help="Distanza km fra campioni meteo lungo la route"
    )
    parser.add_argument(
        "--output", default="demos/web-demo/weather_map.html",
        help="Percorso file HTML d'uscita"
    )
    args = parser.parse_args()

    start = tuple(map(float, args.start.split(",")))
    end = tuple(map(float, args.end.split(",")))

    log.info("Fetching route from OSRM …")
    route = fetch_route(start, end)

    samples = sample_route(route, args.spacing)
    log.info("Sampling %d points every %.1f km", len(samples), args.spacing)

    conn = ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",
        position_provider=lambda: start,
        route_segment="*",
        auto_refresh=True,
    )
    weather_pts = conn.get_weather(samples)
    log.info("Fetched weather for %d/%d points", len(weather_pts), len(samples))

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    m = build_map(route, weather_pts, args.buffer)
    m.save(args.output)
    print(f"Map saved to {args.output}")


if __name__ == "__main__":
    main()

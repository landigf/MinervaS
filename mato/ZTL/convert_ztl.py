#!/usr/bin/env python3
"""
convert_ztl.py - Toolkit per il dataset "Perimetro e orari ZTL" di Torino
----------------------------------------------------------------------------
Funzionalità principali:
  1. Scarica l'XML dal servizio open-data 5T (comando `download`)
  2. Converte il file in GeoJSON (comando `geojson`)
  3. Crea una mappa HTML autonoma con Folium/Leaflet (comando `map`)

Usage:
  python convert_ztl.py download
  python convert_ztl.py geojson
  python convert_ztl.py map

Requisiti minimi:
  * Python ≥ 3.9 (testato fino a 3.13)
  * requests ≥ 2.31
  * folium 0.15 (branca 0.7)

Installazione rapida:
  python -m venv .venv && source .venv/bin/activate
  pip install "requests>=2.31" "folium>=0.15"

Lo script genera:
  data/raw/ztl.xml                       # snapshot originale
  data/processed/ztl_centrale.geojson    # poligono + gates
  web-demo/ztl_map.html                  # mappa offline

License: MIT per questo codice; dati sotto IODL v2.0.
"""
from __future__ import annotations

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import List, Tuple

import requests

# ---------------------------------------------------------------------------
SRC_URL = "https://opendata.5t.torino.it/get_access_control"
RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")
WEB_DIR = Path("web-demo")
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR.mkdir(parents=True, exist_ok=True)

XML_PATH = RAW_DIR / "ztl.xml"
GEOJSON_PATH = PROC_DIR / "ztl_centrale.geojson"
HTML_PATH = WEB_DIR / "ztl_map.html"

NS = {"a": "https://simone.5t.torino.it/ns/access_control.xsd"}

# ---------------------------------------------------------------------------

def download_xml(url: str = SRC_URL, dst: Path = XML_PATH) -> Path:
    """Scarica l'XML dal portale dati."""
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    dst.write_bytes(r.content)
    print(f"Scaricato {len(r.content)/1024:.1f} kB → {dst}")
    return dst


def _polyline_coords(poly_node) -> List[Tuple[float, float]]:
    pts = [
        (float(p.attrib["lng"]), float(p.attrib["lat"])) for p in poly_node.iterfind("a:point", NS)
    ]
    if pts[0] != pts[-1]:
        pts.append(pts[0])
    return pts


def convert_to_geojson(xml_path: Path = XML_PATH, geojson_path: Path = GEOJSON_PATH) -> Path:
    """Converte l'XML in GeoJSON (Polygon + Points)."""
    tree = ET.parse(xml_path)
    ztl = tree.find("a:ztl", NS)
    if ztl is None:
        raise RuntimeError("Elemento <ztl> assente nell'XML.")

    # poligono
    coords = _polyline_coords(ztl.find("a:polyline", NS))
    poly_feat = {
        "type": "Feature",
        "geometry": {"type": "Polygon", "coordinates": [coords]},
        "properties": {"id": int(ztl.attrib["id"]), "name": ztl.attrib["name"]},
    }

    # gates → Point features
    gate_feats = []
    for g in ztl.find("a:gates", NS).iterfind("a:gate", NS):
        gate_feats.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(g.attrib["lng"]), float(g.attrib["lat"])]
                },
                "properties": {
                    "id": int(g.attrib["id"]),
                    "name": g.attrib["name"],
                    "heading": int(g.attrib.get("heading", 0)),
                },
            }
        )

    fc = {"type": "FeatureCollection", "features": [poly_feat, *gate_feats]}
    geojson_path.write_text(json.dumps(fc, indent=2))
    print(f"Scritto GeoJSON → {geojson_path}")
    return geojson_path

# ---------------------------------------------------------------------------

def build_folium_map(geojson_path: Path = GEOJSON_PATH, html_path: Path = HTML_PATH) -> Path:
    """Genera una mappa HTML auto-contenuta via Folium."""
    import folium

    gj = json.loads(geojson_path.read_text())
    poly = next(f for f in gj["features"] if f["geometry"]["type"] == "Polygon")
    pts = poly["geometry"]["coordinates"][0]
    cen_lat = sum(lat for _, lat in pts) / len(pts)
    cen_lon = sum(lon for lon, _ in pts) / len(pts)

    m = folium.Map(location=[cen_lat, cen_lon], zoom_start=15, control_scale=True)

    # Poligono ZTL
    folium.GeoJson(
        data=poly,
        name="ZTL Centrale",
        style_function=lambda *_: {"color": "red", "weight": 2, "fillOpacity": 0.0},
        tooltip="ZTL Centrale",
    ).add_to(m)

    # Varchi → Marker singoli (evita serializzazione di funzioni Python)
    gate_fg = folium.FeatureGroup(name="Varchi", show=True)
    for feat in (f for f in gj["features"] if f["geometry"]["type"] == "Point"):
        lon, lat = feat["geometry"]["coordinates"]
        props = feat["properties"]
        popup_html = (
            f"<b>{props['name']}</b><br>ID: {props['id']}<br>Heading: {props['heading']}°"
        )
        folium.Marker(
            location=[lat, lon],
            icon=folium.Icon(icon="camera", prefix="fa", color="blue"),
            popup=popup_html,
        ).add_to(gate_fg)
    gate_fg.add_to(m)

    folium.LayerControl(collapsed=False).add_to(m)
    m.save(html_path)
    print(f"Mappa HTML pronta → {html_path}")
    return html_path

# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None):
    parser = argparse.ArgumentParser(description="Utility per il dataset ZTL Torino")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("download", help="Scarica l'XML originale")
    sub.add_parser("geojson", help="Converte l'XML in GeoJSON")
    sub.add_parser("map", help="Genera la mappa HTML interattiva")
    args = parser.parse_args(argv)

    if args.cmd == "download":
        download_xml()
    elif args.cmd == "geojson":
        if not XML_PATH.exists():
            download_xml()
        convert_to_geojson()
    elif args.cmd == "map":
        if not GEOJSON_PATH.exists():
            if not XML_PATH.exists():
                download_xml()
            convert_to_geojson()
        build_folium_map()
    else:
        parser.error("Comando non valido")


if __name__ == "__main__":
    main()

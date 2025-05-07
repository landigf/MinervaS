#!/usr/bin/env python3
"""
convert_fdt.py - Toolkit per il dataset "Flussi di Traffico" (FDT) di Torino
----------------------------------------------------------------------------
Funzionalità:
  1. Scarica l'XML tempo-reale da 5T (`download`)
  2. Converte in CSV e GeoJSON (`csv`)
  3. Crea mappa HTML con Folium (`map`)

Dipendenze: requests ≥2.31, pandas ≥2.2, folium ≥0.15
"""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd
import requests

# ---------------------------------------------------------------------------
SRC_URL = "https://opendata.5t.torino.it/get_fdt"
RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")
WEB_DIR = Path("web-demo")
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR.mkdir(parents=True, exist_ok=True)

XML_PATH = RAW_DIR / "fdt.xml"
CSV_PATH = PROC_DIR / "fdt.csv"
GEOJSON_PATH = PROC_DIR / "fdt.geojson"
HTML_PATH = WEB_DIR / "fdt_map.html"

NS = {"t": "https://simone.5t.torino.it/ns/traffic_data.xsd"}

# ---------------------------------------------------------------------------


def download_xml(url: str = SRC_URL, dst: Path = XML_PATH) -> Path:
    """Scarica l'XML in tempo reale."""
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    dst.write_bytes(r.content)
    print(f"Scaricato {len(r.content)/1024:.1f} kB → {dst}")
    return dst


def xml_to_dataframe(xml_path: Path = XML_PATH) -> pd.DataFrame:
    """Parsa l'XML in un DataFrame pandas."""
    tree = ET.parse(xml_path)
    rows = []
    for node in tree.findall("t:FDT_data", NS):
        sp = node.find("t:speedflow", NS)
        rows.append(
            {
                "lcd1": int(node.attrib["lcd1"]),
                "road_id": int(node.attrib["Road_LCD"]),
                "road_name": node.attrib["Road_name"],
                "offset": int(node.attrib["offset"]),
                "direction": node.attrib["direction"],
                "lat": float(node.attrib["lat"]),
                "lng": float(node.attrib["lng"]),
                "accuracy": int(node.attrib["accuracy"]),
                "period_min": int(node.attrib["period"]),
                "flow": int(sp.attrib["flow"]),
                "speed_kmh": float(sp.attrib["speed"]),
            }
        )
    return pd.DataFrame(rows)


def save_csv_and_geojson(
    df: pd.DataFrame, csv_path: Path = CSV_PATH, geojson_path: Path = GEOJSON_PATH
):
    """Salva CSV e GeoJSON derivati dal DataFrame."""
    df.to_csv(csv_path, index=False)
    print(f"Scritto CSV → {csv_path}")

    feats = []
    for rec in df.to_dict(orient="records"):
        feats.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [rec["lng"], rec["lat"]]},
                "properties": {k: rec[k] for k in rec if k not in ("lat", "lng")},
            }
        )
    geojson_path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}, indent=2))
    print(f"Scritto GeoJSON → {geojson_path}")


def build_map(geojson_path: Path = GEOJSON_PATH, html_path: Path = HTML_PATH):
    """Genera una mappa Folium con i flussi di traffico colorati per velocità."""
    import folium

    gj = json.loads(geojson_path.read_text())
    lats = [f["geometry"]["coordinates"][1] for f in gj["features"]]
    lngs = [f["geometry"]["coordinates"][0] for f in gj["features"]]
    m = folium.Map(location=[pd.Series(lats).median(), pd.Series(lngs).median()], zoom_start=11)

    def color_by_speed(speed):
        if speed == 0:
            return "gray"
        if speed < 20:
            return "red"
        if speed < 40:
            return "orange"
        if speed < 60:
            return "yellow"
        return "green"

    for feat in gj["features"]:
        lon, lat = feat["geometry"]["coordinates"]
        props = feat["properties"]
        folium.CircleMarker(
            location=[lat, lon],
            radius=5,
            color=color_by_speed(props["speed_kmh"]),
            fill=True,
            fill_opacity=0.8,
            popup=(
                f"<b>{props['road_name']}</b><br>"
                f"Flow: {props['flow']} veh/5min<br>"
                f"Speed: {props['speed_kmh']} km/h"
            ),
        ).add_to(m)

    m.save(html_path)
    print(f"Mappa HTML pronta → {html_path}")


# ---------------------------------------------------------------------------


def main(argv=None):
    parser = argparse.ArgumentParser(description="Toolkit FDT Torino")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("download")
    sub.add_parser("csv")
    sub.add_parser("map")
    args = parser.parse_args(argv)

    if args.cmd == "download":
        download_xml()
    elif args.cmd == "csv":
        if not XML_PATH.exists():
            download_xml()
        df = xml_to_dataframe()
        save_csv_and_geojson(df)
    elif args.cmd == "map":
        if not GEOJSON_PATH.exists():
            if not CSV_PATH.exists():
                if not XML_PATH.exists():
                    download_xml()
                df = xml_to_dataframe()
                save_csv_and_geojson(df)
            else:
                df = pd.read_csv(CSV_PATH)
                save_csv_and_geojson(df)
        build_map()


if __name__ == "__main__":
    main()

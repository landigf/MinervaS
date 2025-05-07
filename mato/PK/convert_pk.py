#!/usr/bin/env python3
"""
convert_pk.py - Toolkit per il dataset "Parcheggi in Struttura" (PK) di Torino
----------------------------------------------------------------------------
Funzionalità:
  1. Scarica l'XML in tempo reale da 5T (`download`)
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
SRC_URL = "https://opendata.5t.torino.it/get_pk"
RAW_DIR = Path("data/raw")
PROC_DIR = Path("data/processed")
WEB_DIR = Path("web-demo")
RAW_DIR.mkdir(parents=True, exist_ok=True)
PROC_DIR.mkdir(parents=True, exist_ok=True)
WEB_DIR.mkdir(parents=True, exist_ok=True)

XML_PATH = RAW_DIR / "pk.xml"
CSV_PATH = PROC_DIR / "pk.csv"
GEOJSON_PATH = PROC_DIR / "pk.geojson"
HTML_PATH = WEB_DIR / "pk_map.html"

NS = {"t": "https://simone.5t.torino.it/ns/traffic_data.xsd"}

# ---------------------------------------------------------------------------

def download_xml(url: str = SRC_URL, dst: Path = XML_PATH) -> Path:
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    dst.write_bytes(r.content)
    print(f"Scaricato {len(r.content)/1024:.1f} kB → {dst}")
    return dst


def xml_to_dataframe(xml_path: Path = XML_PATH) -> pd.DataFrame:
    tree = ET.parse(xml_path)
    rows = []
    for node in tree.findall("t:PK_data", NS):
        rows.append(
            {
                "id": int(node.attrib["ID"]),
                "name": node.attrib["Name"].title(),
                "lat": float(node.attrib["lat"]),
                "lng": float(node.attrib["lng"]),
                "total": int(node.attrib["Total"]),
                "free": int(node.attrib.get("Free", 0)),
                "status": int(node.attrib["status"]),
                "tendence": int(node.attrib["tendence"]),
            }
        )
    df = pd.DataFrame(rows)
    df["occupancy_pct"] = 100 * (df["total"] - df["free"]) / df["total"]
    return df


def save_csv_and_geojson(df: pd.DataFrame, csv_path: Path = CSV_PATH, geojson_path: Path = GEOJSON_PATH):
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
    import folium

    gj = json.loads(geojson_path.read_text())
    lats = [f["geometry"]["coordinates"][1] for f in gj["features"]]
    lngs = [f["geometry"]["coordinates"][0] for f in gj["features"]]
    m = folium.Map(location=[pd.Series(lats).median(), pd.Series(lngs).median()], zoom_start=12)

    def color_by_occ(pct, status):
        if status == 0:
            return "gray"  # parcheggio offline/chiuso
        if pct < 50:
            return "green"
        if pct < 80:
            return "orange"
        return "red"

    for feat in gj["features"]:
        lon, lat = feat["geometry"]["coordinates"]
        props = feat["properties"]
        pct = props["occupancy_pct"]
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            color=color_by_occ(pct, props["status"]),
            fill=True,
            fill_opacity=0.9,
            popup=(f"<b>{props['name']}</b><br>Posti liberi: {props['free']} / {props['total']}<br>"
                   f"Occupazione: {pct:.0f}%"),
        ).add_to(m)

    m.save(html_path)
    print(f"Mappa HTML pronta → {html_path}")

# ---------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Toolkit PK Torino")
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

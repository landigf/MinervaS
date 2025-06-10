#!/usr/bin/env python
"""High-level CLI demo that showcases **ODHConnector** capabilities.

Example
~~~~~~~
$ python demos/dashboard.py \
    --start 46.07,11.12 --end 46.4983,11.3548 \
    --buffer 30 --spacing 8 --hours 1200 --deadline 1 \
    --output demos/dashboards/combined_map.html

The script prints a rich console dashboard and saves an HTML map.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from odhconnector.connectors.connector import ODHConnector


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--start", required=True, help="lat,lon")
    p.add_argument("--end", required=True, help="lat,lon")
    p.add_argument("--buffer", type=float, default=5.0)
    p.add_argument("--spacing", type=float, default=10.0)
    p.add_argument("--hours", type=int, default=6)
    p.add_argument("--output", default="dashboards/combined_map.html")
    p.add_argument("--fatigue", type=float, default=0.0)
    p.add_argument("--deadline", type=float, default=0.0)
    args = p.parse_args()

    start = tuple(map(float, args.start.split(",")))
    end   = tuple(map(float, args.end.split(",")))

    conn = ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",
        position_provider=lambda: start,
        route_segment="*",
        auto_refresh=True,
        last_n_hours=args.hours,
    )

    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    conn.run_dashboard(
        start=start,
        end=end,
        buffer_km=args.buffer,
        spacing_km=args.spacing,
        hours=args.hours,
        output_html=args.output,
        fatigue=args.fatigue,
        deadline=args.deadline,
    )


if __name__ == "__main__":
    main()

# MinervaS-ODH Connector

> **Lightweight bridge between the MinervaS fleet-guidance core and the OpenDataHub (ODH) Weather & Traffic APIs for the *A22 Trentino* corridor.**
>
> **Status**: *Skeleton/PoC — ready for extension.*

---

## Table of Contents

1. [Features](#features)
2. [Project Structure](#project-structure)
3. [Prerequisites](#prerequisites)
4. [Quick Start](#quick-start)
5. [Usage Example](#usage-example)
6. [Environment Variables](#environment-variables)
7. [Generating the Documentation](#generating-the-documentation)
8. [Running Tests](#running-tests)
9. [Authors](#authors)
10. [Last Update](#last-update)

---

## Features

* **ODHConnector** — single entry‑point class with a minimal public API (`get_incidents()`, `get_weather_index()`, `generate_alerts()`, …).
* **Modular Adapters** — separate weather & traffic adapters you can swap or extend.
* **In-memory caching** with opt-in auto-refresh.
* **Fuzzy-logic stubs** ready for your advisory rules.
* **Typed dataclasses** for all domain objects (Incident, WeatherIndex, …).
* **Sphinx docs** (HTML/PDF) generated from inline docstrings.
* **Pytest smoke tests** — CI-friendly from day 1.

## Project Structure

```text
ODHconnector/
│   pyproject.toml   # build metadata & deps (PEP 621)
│   README.md        # ← this file
│   .env.example     # sample env vars
│
├── src/
│   └── odhconnector/  # package root
│       ├── models.py
│       ├── utils.py
│       ├── connectors/
│       │   └── connector.py
│       └── adapters/
│           ├── weather_adapter.py
│           └── traffic_adapter.py
│
├── tests/           # pytest test suite
└── docs/            # Sphinx documentation source
```

## Prerequisites

* **Python ≥ 3.10**
* Optional: system packages for building wheels (e.g. `build-essential`, `python3-dev`).

## Quick Start

```bash
# 1 - create & activate a virtual environment
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate

# 2 - install the package in editable mode + docs & test extras
pip install -e '.[docs,test]'

# 3 - run the smoke tests (should pass)
pytest

# 4 - build HTML documentation
cd docs && make html          # output in docs/_build/html/
```

## Usage Example

```python
from odhconnector.connectors.connector import ODHConnector

connector = ODHConnector(
    odh_base_url="https://mobility.api.opendatahub.com",
    odh_api_key="<YOUR_API_KEY>",
    position_provider=lambda: (46.07, 11.12),
    route_segment="A22_Trentino",
    auto_refresh=True,
)

# Get incidents within 5 km
danger = connector.get_incidents(within_km=5)
for inc in danger:
    print(inc.description, inc.distance_km)
```

## Environment Variables

Create a `.env` file (or export them in your shell):

```bash
ODH_BASE_URL="https://mobility.api.opendatahub.com"  # override if needed
```

## Generating the Documentation

```bash
pip install -e '.[docs]'
cd docs
make html      # or: sphinx-build -b html . _build/html
open _build/html/index.html
```

## Running Tests

```bash
pip install -e '.[test]'
pytest -q      # -q for quiet output
```

## Authors

* **Landi Gennaro Francesco** - [gennaro.landi@minervas.it](mailto:gennaro.landi@minervas.it)
* **Palmisano Elettra** - [elettra.palmisano@minervas.it](mailto:elettra.palmisano@minervas.it)

## Last Update

|today|

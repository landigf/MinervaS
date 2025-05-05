# 🌤️ Meteomatics API Integration

Meteomatics provides a REST-style API to retrieve historic, current, and forecast data globally. This includes model data and observational data in time series and areal formats. Areal formats are also offered through a WMS/WFS-compatible interface. Geographic and time series data can be combined in certain file formats, such as NetCDF.

## Overview

This directory demonstrates how to use the **Meteomatics REST API** to retrieve real-time, forecast, and historical weather data — suitable for integration in intelligent transport systems, data pipelines, and weather-aware applications.

> ✅ This example uses a **free developer account** with access to:
> - 500 requests per day
> - 15 basic weather parameters
> - No premium data (ex. road_surface_temperature, visibility, cloud_cover, ecc.)

---

## 🔗 API Endpoint Structure

All API requests follow the format:
- https://api.meteomatics.com/{datetime}/{parameters}/{location}/{format}


- `datetime`: ISO format, e.g. `2025-04-18T12:00:00Z`
- `parameters`: comma-separated codes (e.g. `t_2m:C,wind_speed_10m:ms`)
- `location`: lat,long or path
- `format`: `json`, `csv`, `png`, `netcdf`, etc.

---

## 📦 Features Implemented

- [x] Authentication via Basic Auth
- [x] Single point forecast query
- [x] Multi-parameter request
- [x] Historical and forecast queries
- [x] Integration-ready output in JSON/CSV
- [ ] Geospatial map previews via WMS (coming soon)

---

## 🌍 Available Parameters (Free Basic API Tier)

Below are the 15 weather parameters included in the **free basic package**, calibrated with real station observations. You can query up to **10 at a time**, for **one location per request**, and up to **500 queries per day**.

| API Parameter                | Description                                                  | Unit                      |
|-----------------------------|--------------------------------------------------------------|---------------------------|
| `t_2m:C`                    | Instantaneous temperature at 2 meters above ground           | °C / K / °F               |
| `t_max_2m_24h:C`            | Maximum temperature at 2 meters over the last 24 hours       | °C / K / °F               |
| `t_min_2m_24h:C`            | Minimum temperature at 2 meters over the last 24 hours       | °C / K / °F               |
| `wind_speed_10m:ms`         | Instantaneous wind speed at 10 meters above ground           | m/s                       |
| `wind_dir_10m:d`            | Wind direction at 10 meters above ground                     | degrees (°)               |
| `wind_gusts_10m_1h:ms`      | Wind gusts at 10 meters in the past hour                     | m/s / km/h / kn / bft     |
| `wind_gusts_10m_24h:ms`     | Wind gusts at 10 meters in the past 24 hours                 | m/s / km/h / kn / bft     |
| `precip_1h:mm`              | Precipitation in the past hour                               | mm                        |
| `precip_24h:mm`             | Precipitation in the past 24 hours                           | mm                        |
| `msl_pressure:hPa`          | Mean sea level pressure                                      | hPa / Pa                  |
| `weather_symbol_1h:idx`     | Weather summary symbol for the past hour                     | index (0–99)              |
| `weather_symbol_24h:idx`    | Weather summary symbol for the past 24 hours                 | index (0–99)              |
| `uv:idx`                    | Ultraviolet radiation index                                  | index (0–11+)             |
| `sunrise:sql`               | Sunrise time                                                 | SQL-like time (HH:MM)     |
| `sunset:sql`                | Sunset time                                                  | SQL-like time (HH:MM)     |

> 📌 Note: These parameters are ideal for building a weather-aware routing system or risk analysis in fleet management platforms.



# Docs & References
- [Getting Started with Meteomatics Weather API](https://www.meteomatics.com/en/api/getting-started/)



### Contributors
- Elettra Palmisano
- Gennaro Francesco Landi
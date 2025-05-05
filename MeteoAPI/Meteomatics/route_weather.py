import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime, timedelta, timezone
from math import radians, cos, sin, asin, sqrt
import folium
import branca.colormap as cm
import os

# === Config ===
USERNAME = "minervas_landi_gennarofrancesco"
PASSWORD = "uMHJ6C89mf"
BASE_URL = "https://api.meteomatics.com"

# === Percorso: Salerno → Milano con tappe camionistiche ===
departure_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
route_points = [
    {"name": "Salerno (Partenza)", "lat": 40.6829, "lon": 14.7681, "time": departure_time},
    {"name": "Sosta a Cassino", "lat": 41.4831, "lon": 13.8298, "time": departure_time + timedelta(hours=2)},
    {"name": "Sosta a Roma Sud", "lat": 41.7992, "lon": 12.6074, "time": departure_time + timedelta(hours=4)},
    {"name": "Sosta a Firenze Nord", "lat": 43.8324, "lon": 11.1958, "time": departure_time + timedelta(hours=7)},
    {"name": "Milano (Arrivo)", "lat": 45.4642, "lon": 9.1900, "time": departure_time + timedelta(hours=10)},
]

# === Parametri free-tier ===
param_group_1 = ",".join([
    "t_2m:C", "t_max_2m_24h:C", "t_min_2m_24h:C",
    "wind_speed_10m:ms", "wind_dir_10m:d",
    "wind_gusts_10m_1h:ms", "wind_gusts_10m_24h:ms",
    "precip_1h:mm", "precip_24h:mm", "msl_pressure:hPa"
])
param_group_2 = ",".join([
    "weather_symbol_1h:idx", "weather_symbol_24h:idx",
    "uv:idx", "sunrise:sql", "sunset:sql"
])

# === Soglie critiche ===
CRITICAL = {
    "wind_gusts_10m_1h:ms": 15,
    "precip_1h:mm": 5,
    "uv:idx": 8,
    "t_2m:C_low": 0,
    "t_2m:C_high": 35,
    "msl_pressure:hPa": 990,
    "weather_symbol_1h:idx": [6, 7, 8, 9, 19, 20, 24]
}

def get_weather(lat, lon, time_iso, parameters):
    url = f"{BASE_URL}/{time_iso}/{parameters}/{lat},{lon}/json"
    response = requests.get(url, auth=HTTPBasicAuth(USERNAME, PASSWORD))
    if response.ok:
        return response.json()
    else:
        print(f"❌ Errore per {lat},{lon} @ {time_iso}: {response.status_code}")
        return None

def analyze_weather(data):
    alerts = []
    values = {d["parameter"]: d["coordinates"][0]["dates"][0]["value"] for d in data["data"]}
    if values.get("wind_gusts_10m_1h:ms", 0) >= CRITICAL["wind_gusts_10m_1h:ms"]:
        alerts.append("💨 Raffiche forti")
    if values.get("precip_1h:mm", 0) >= CRITICAL["precip_1h:mm"]:
        alerts.append("🌧️ Pioggia intensa")
    if values.get("uv:idx", 0) >= CRITICAL["uv:idx"]:
        alerts.append("☀️ UV molto alto")
    temp = values.get("t_2m:C", 20)
    if temp <= CRITICAL["t_2m:C_low"]:
        alerts.append("❄️ Rischio ghiaccio")
    elif temp >= CRITICAL["t_2m:C_high"]:
        alerts.append("🔥 Caldo estremo")
    if values.get("msl_pressure:hPa", 1000) <= CRITICAL["msl_pressure:hPa"]:
        alerts.append("⚠️ Possibile perturbazione")
    if int(values.get("weather_symbol_1h:idx", 0)) in CRITICAL["weather_symbol_1h:idx"]:
        alerts.append("🌩️ Condizioni meteo avverse")
    return alerts, values

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))

def interpolate_coords(lat1, lon1, lat2, lon2, n):
    return [(lat1 + i*(lat2 - lat1)/(n+1), lon1 + i*(lon2 - lon1)/(n+1)) for i in range(1, n+1)]

print("🚚 CHECKING WEATHER AT WAYPOINTS...")
for point in route_points:
    time_iso = point["time"].strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"📍 {point['name']} @ {time_iso}")
    d1 = get_weather(point["lat"], point["lon"], time_iso, param_group_1)
    d2 = get_weather(point["lat"], point["lon"], time_iso, param_group_2)
    if d1 and d2:
        full_data = {"data": d1["data"] + d2["data"]}
        alerts, values = analyze_weather(full_data)
        for param, value in values.items():
            print(f"  - {param}: {value}")
        if alerts:
            print("  ⚠️  Criticità:")
            for a in alerts:
                print("   →", a)
        else:
            print("  ✅ Nessuna criticità")
    print("---")

# === Raccolta dati per mappa ===
temperature_points = []
print("\n📊 REPORT METEO PER TRATTA\n")
for i in range(len(route_points)-1):
    start = route_points[i]
    end = route_points[i+1]
    trat_name = f"{start['name']} → {end['name']}"
    dist = haversine(start['lat'], start['lon'], end['lat'], end['lon'])
    delta_time = (end['time'] - start['time']).total_seconds()
    n_points = max(1, int(dist // 20))
    step_time = delta_time / (n_points + 1)
    coords = interpolate_coords(start['lat'], start['lon'], end['lat'], end['lon'], n_points)

    temp_vals, wind_vals = [], []
    all_alerts = set()

    for idx, (lat, lon) in enumerate(coords):
        t = start['time'] + timedelta(seconds=step_time * (idx + 1))
        time_iso = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        d1 = get_weather(lat, lon, time_iso, param_group_1)
        d2 = get_weather(lat, lon, time_iso, param_group_2)
        if d1 and d2:
            merged = {"data": d1["data"] + d2["data"]}
            alerts, values = analyze_weather(merged)
            temp_vals.append(values.get("t_2m:C", 0))
            wind_vals.append(values.get("wind_speed_10m:ms", 0))
            all_alerts.update(alerts)
            # Collect temperature points for map
            values = {d["parameter"]: d["coordinates"][0]["dates"][0]["value"] for d in d1["data"]}
            temp = values.get("t_2m:C")
            if temp is not None:
                temperature_points.append((lat, lon, temp))

    avg_temp = round(sum(temp_vals)/len(temp_vals), 1) if temp_vals else "N/A"
    avg_wind = round(sum(wind_vals)/len(wind_vals), 1) if wind_vals else "N/A"

    print(f"🛣️ Tratta: {trat_name}")
    print(f"   ▸ Distanza: {round(dist)} km")
    print(f"   ▸ Temperatura media: {avg_temp} °C")
    print(f"   ▸ Vento medio: {avg_wind} m/s")
    if all_alerts:
        print(f"   ▸ Criticità: {', '.join(sorted(all_alerts))}")
    else:
        print("   ▸ Nessuna criticità ✅")
    print("---")

print("✅ REPORT COMPLETATO.")

# === GENERAZIONE MAPPA ===
if temperature_points:
    avg_lat = sum([pt[0] for pt in temperature_points]) / len(temperature_points)
    avg_lon = sum([pt[1] for pt in temperature_points]) / len(temperature_points)

    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=6, tiles="cartodbpositron")
    temps = [pt[2] for pt in temperature_points]

    colormap = cm.linear.RdYlBu_11.scale(min(temps), max(temps)).to_step(10)
    colormap.caption = 'Temperatura (°C)'
    m.add_child(colormap)

    for lat, lon, temp in temperature_points:
        color = colormap(temp)
        folium.CircleMarker(
            location=[lat, lon],
            radius=6,
            fill=True,
            fill_color=color,
            color=color,
            fill_opacity=0.9,
            popup=f"{temp} °C"
        ).add_to(m)

    # Salva nella stessa cartella dello script
    current_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(current_dir, "mappa_temperatura_reale.html")
    m.save(map_path)
    print(f"✅ Mappa generata: {map_path}")
else:
    print("⚠️ Nessun dato temperatura disponibile per generare la mappa.")
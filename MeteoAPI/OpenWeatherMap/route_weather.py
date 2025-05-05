import requests
from datetime import datetime, timedelta, timezone
from math import radians, cos, sin, asin, sqrt
import folium
import branca.colormap as cm
import os

# === Config ===
OWM_API_KEY = "3e667bfde6de5b586705f59ea4fc6b79"
OWM_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather"

# === Percorso: Salerno → Milano ===
departure_time = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
route_points = [
    {"name": "Salerno", "lat": 40.6829, "lon": 14.7681, "time": departure_time},
    {"name": "Cassino", "lat": 41.4831, "lon": 13.8298, "time": departure_time + timedelta(hours=2)},
    {"name": "Roma Sud", "lat": 41.7992, "lon": 12.6074, "time": departure_time + timedelta(hours=4)},
    {"name": "Firenze Nord", "lat": 43.8324, "lon": 11.1958, "time": departure_time + timedelta(hours=7)},
    {"name": "Milano", "lat": 45.4642, "lon": 9.1900, "time": departure_time + timedelta(hours=10)},
]

def get_weather(lat, lon):
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OWM_API_KEY,
        "units": "metric"
    }
    response = requests.get(OWM_ENDPOINT, params=params)
    if response.ok:
        return response.json()
    else:
        print(f"❌ Errore @ {lat},{lon}: {response.status_code}")
        return None

def analyze_weather(data):
    alerts = []
    values = {
        "temperature": data["main"].get("temp", 20),
        "windSpeed": data["wind"].get("speed", 0),
        "pressure": data["main"].get("pressure", 1013),
        "weather": data["weather"][0]["description"]
    }
    if data["wind"].get("gust", 0) >= 15:
        alerts.append("💨 Raffiche forti")
    if data.get("rain", {}).get("1h", 0) >= 5:
        alerts.append("🌧️ Pioggia intensa")
    if values["temperature"] <= 0:
        alerts.append("❄️ Rischio ghiaccio")
    elif values["temperature"] >= 35:
        alerts.append("🔥 Caldo estremo")
    if values["pressure"] <= 990:
        alerts.append("⚠️ Pressione bassa")
    return alerts, values

def haversine(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = radians(lat2 - lat1), radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    return R * 2 * asin(sqrt(a))

def interpolate_coords(lat1, lon1, lat2, lon2, n):
    return [(lat1 + i*(lat2 - lat1)/(n+1), lon1 + i*(lon2 - lon1)/(n+1)) for i in range(1, n+1)]

print("🚚 CHECKING WEATHER ALONG ROUTE...")
temperature_points = []

for i in range(len(route_points)-1):
    start = route_points[i]
    end = route_points[i+1]
    dist = haversine(start['lat'], start['lon'], end['lat'], end['lon'])
    n_points = max(1, int(dist // 20))
    coords = interpolate_coords(start['lat'], start['lon'], end['lat'], end['lon'], n_points)

    temp_vals, wind_vals = [], []
    all_alerts = set()

    for lat, lon in coords:
        weather = get_weather(lat, lon)
        if weather:
            alerts, values = analyze_weather(weather)
            temp_vals.append(values["temperature"])
            wind_vals.append(values["windSpeed"])
            all_alerts.update(alerts)
            temperature_points.append((lat, lon, values["temperature"]))

    avg_temp = round(sum(temp_vals)/len(temp_vals), 1) if temp_vals else "N/A"
    avg_wind = round(sum(wind_vals)/len(wind_vals), 1) if wind_vals else "N/A"

    print(f"🛣️ Tratta: {start['name']} → {end['name']}")
    print(f"   ▸ Temperatura media: {avg_temp} °C")
    print(f"   ▸ Vento medio: {avg_wind} m/s")
    print(f"   ▸ Criticità: {', '.join(sorted(all_alerts)) if all_alerts else 'Nessuna'}")
    print("---")

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

    current_dir = os.path.dirname(os.path.abspath(__file__))
    map_path = os.path.join(current_dir, "mappa_temperatura_owm.html")
    m.save(map_path)
    print(f"✅ Mappa generata: {map_path}")
else:
    print("⚠️ Nessun dato temperatura disponibile per generare la mappa.")

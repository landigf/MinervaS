import os
import requests
from datetime import datetime, timezone, timedelta
import polyline
import folium

# === CONFIG ===
API_KEY = "Beas2JbBFJi4JBXns0wsQHivUnDlYfYh"
BASE_ROUTE_URL = "https://api.tomtom.com/routing/1/calculateRoute"
BASE_FLOW_URL  = "https://api.tomtom.com/traffic/4/flowSegmentData"

# === PERCORSO ===
route_points = [
    (40.6829, 14.7681),  # Salerno
    (41.4831, 13.8298),  # Cassino
    (41.7992, 12.6074),  # Roma Sud
    (43.8324, 11.1958),  # Firenze Nord
    (45.4642, 9.1900),   # Milano
]
locations = ":".join(f"{lat},{lon}" for lat,lon in route_points)

# Forecast fra 1h (UTC)
depart_at = (datetime.now(timezone.utc) + timedelta(hours=1)) \
    .strftime("%Y-%m-%dT%H:%M:%SZ")

# === 1) CALCOLA PERCORSO CON TRAFFICO PREVISTO ===
r = requests.get(
    f"{BASE_ROUTE_URL}/{locations}/json",
    params={
        "key": API_KEY,
        "traffic": "true",
        "departAt": depart_at,
        "computeTravelTimeFor": "all",
        "routeRepresentation": "polyline"
    }
)
r.raise_for_status()
route = r.json()["routes"][0]
summary = route["summary"]

print("📅 Partenza forecast:", depart_at)
print("⏱️ Travel time (traffic):        ", summary["travelTimeInSeconds"], "s")
print("🚀 Travel time (free-flow):      ", summary["noTrafficTravelTimeInSeconds"], "s")
print("🐌 Ritardo vs free-flow:         ", summary["trafficDelayInSeconds"], "s")

# Decodifica la polilinea completa
poly = route["guidance"]["polyline"]
coords = polyline.decode(poly)  # lista di (lat,lon)

# === 2) SAMPLE TRAFFIC FLOW PER OGNI PUNTO ===
flow_data = []
for lat, lon in coords[:: max(1, len(coords)//20)]:  # prendi ~20 punti
    t_iso = depart_at  # per forecast usa lo stesso depart_at
    url = f"{BASE_FLOW_URL}/absolute/{t_iso}/{lat},{lon}/json"
    q = {"key": API_KEY, "unit": "KMPH", "fields": "currentSpeed,freeFlowSpeed"}
    resp = requests.get(url, params=q)
    if resp.ok:
        d = resp.json()["flowSegmentData"]
        flow_data.append((lat, lon, d["currentSpeed"], d["freeFlowSpeed"]))
    else:
        flow_data.append((lat, lon, None, None))

# Stampa rapido
for lat, lon, cs, ff in flow_data:
    print(f"📍 {lat:.4f},{lon:.4f} → speed: {cs} km/h (free: {ff})")

# === 3) MAPPA FOLIUM ===
m = folium.Map(location=coords[len(coords)//2], zoom_start=6, tiles="cartodbpositron")
# Linea del percorso
folium.PolyLine(coords, weight=4, opacity=0.7).add_to(m)
# Marker con colore in base alla congestione
for lat, lon, cs, ff in flow_data:
    if cs is None: continue
    # congestion ratio: 1 = free-flow; >1 = rallentamento
    ratio = ff / cs if cs>0 else 1
    color = "green" if ratio<=1 else "orange" if ratio<1.5 else "red"
    folium.CircleMarker(
        location=(lat, lon),
        radius=5,
        color=color,
        fill=True,
        fill_opacity=0.7,
        popup=f"{cs} km/h (free {ff})"
    ).add_to(m)

m.save("route_with_flow_forecast.html")
print("✅ Mappa salvata in ./route_with_flow_forecast.html")

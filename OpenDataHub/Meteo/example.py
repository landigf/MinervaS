import requests
import pandas as pd

# Parametri API
base_url = "https://mobility.api.opendatahub.com/v2"
representation = "flat,node"
station_type = "MeteoStation"
data_type = "air-temperature-min"
start_date = "2024-01-01"
end_date = "2024-01-05"

# Componi URL
url = f"{base_url}/{representation}/{station_type}/{data_type}/{start_date}/{end_date}"

# Esegui richiesta
response = requests.get(url, headers={"accept": "application/json"})

# Parsing JSON
if response.status_code == 200:
    data = response.json()
    print("✅ Dati ricevuti correttamente!")
else:
    print(f"❌ Errore: {response.status_code}")
    exit()

# Estrai solo la lista di osservazioni meteo
records = data["data"]

# Normalizza in un DataFrame
df = pd.json_normalize(records)

# Estrai e rinomina solo le colonne che ti servono
df_clean = df[[
    "_timestamp", "mvalue", "sname",
    "scoordinate.x", "scoordinate.y"
]].rename(columns={
    "_timestamp": "timestamp",
    "mvalue": "min_temperature",
    "sname": "station_name",
    "scoordinate.x": "longitude",
    "scoordinate.y": "latitude"
})

# Mostra i primi 5 risultati
print(df_clean.head())

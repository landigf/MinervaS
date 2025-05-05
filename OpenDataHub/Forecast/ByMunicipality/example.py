import requests
from datetime import datetime

# Endpoint API
url = "https://tourism.api.opendatahub.com/v1/Weather/Forecast"

# Parametri
params = {
    "language": "en",
    "limit": 3
}

# Richiesta GET
response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()
    for forecast in data:
        name = forecast.get("MunicipalityName", {}).get("en", "Unknown")
        print("=" * 70)
        print(f"🌍 Comune: {name}")
        print(f"🆔 ID previsione: {forecast.get('Id')}")
        print(f"📅 Ultimo aggiornamento: {forecast.get('_Meta', {}).get('LastUpdate')}")
        print()

        # Previsioni giornaliere
        print("📅 Previsioni giornaliere:")
        for day in forecast.get("ForeCastDaily", []):
            print(f" - Giorno: {day.get('Date')[:10]}")
            print(f"   🌡️ Min: {day.get('MinTemp')}°C | Max: {day.get('MaxTemp')}°C")
            print(f"   ☀️ Sole: {day.get('SunshineDuration')} h")
            print(f"   🌧️ Pioggia: {day.get('Precipitation')} mm (Prob: {day.get('PrecipitationProbability')}%)")
            print(f"   🌤️ Meteo: {day.get('WeatherDesc')}")
            print(f"   🖼️ Icona: {day.get('WeatherImgUrl')}")
            print()

        # Previsioni orarie (ogni 3 ore)
        print("⏱️ Previsioni ogni 3 ore:")
        for slot in forecast.get("Forecast3HoursInterval", []):
            timestamp = datetime.fromisoformat(slot["Date"]).strftime("%Y-%m-%d %H:%M")
            print(f" - {timestamp}:")
            print(f"     🌡️ Temp: {slot.get('Temperature')}°C")
            print(f"     🌧️ Pioggia: {slot.get('Precipitation')} mm (Prob: {slot.get('PrecipitationProbability')}%)")
            print(f"     🌤️ Meteo: {slot.get('WeatherDesc')}")
            print(f"     💨 Vento: {slot.get('WindSpeed')} km/h da {slot.get('WindDirection')}°")
            print(f"     🖼️ Icona: {slot.get('WeatherImgUrl')}")
            print()

        print("=" * 70 + "\n")
else:
    print(f"Errore {response.status_code}: {response.text}")

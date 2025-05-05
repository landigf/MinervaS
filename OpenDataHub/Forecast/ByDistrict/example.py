import requests

# Endpoint API
url = "https://tourism.api.opendatahub.com/v1/Weather/District"

params = {
    "language": "en",
}

response = requests.get(url, params=params)

if response.status_code == 200:
    data = response.json()

    for district in data:
        print("=" * 50)
        print(f"DISTRETTO: {district.get('DistrictName')}")
        print(f"Data aggiornamento: {district.get('date')}")
        print("ID Distretto:", district.get('Id'))
        print("Lingua:", district.get('Language'))

        print("\n📅 PREVISIONI:")
        for forecast in district.get('BezirksForecast', []):
            print("-" * 30)
            print(f"  Giorno: {forecast.get('date')}")
            print(f"  Descrizione meteo: {forecast.get('WeatherDesc')}")
            print(f"  Temperatura massima: {forecast.get('MaxTemp')} °C")
            print(f"  Temperatura minima: {forecast.get('MinTemp')} °C")
            print(f"  Pioggia prevista: da {forecast.get('RainFrom')} a {forecast.get('RainTo')} mm")
            print(f"  Icona meteo: {forecast.get('WeatherImgUrl')}")
            print(f"  Parti del giorno (1-4): {[forecast.get('Part1'), forecast.get('Part2'), forecast.get('Part3'), forecast.get('Part4')]}")
            print(f"  Fulmini previsti: {forecast.get('Thunderstorm')}")
            print(f"  Affidabilità: {forecast.get('Reliability')}")
        print("\n🔗 Link API distretto:", district.get('Self'))
        print("📝 Licenza:", district.get('LicenseInfo', {}).get('License'))
        print("=" * 50 + "\n")

else:
    print(f"Errore {response.status_code}: {response.text}")

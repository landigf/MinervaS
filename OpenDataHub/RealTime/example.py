import requests
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# 🔹 Intervallo temporale fisso (esempio: ultimi 7 giorni)
end = datetime.now(timezone.utc).replace(microsecond=0)
start = end - timedelta(days=20)

start_iso = start.isoformat().replace("+00:00", "Z")
end_iso = end.isoformat().replace("+00:00", "Z")

# 🔹 1. Richiesta dataset disponibili
base_url = "https://mobility.api.opendatahub.com/v2/flat,event"
response = requests.get(base_url)

# Dizionario {categoria: [lista eventi]}
categorie_eventi = defaultdict(list)

if response.status_code == 200:
    print(response.json())
    print("\n\n\n")
    datasets = response.json()

    print(f"Trovati {len(datasets)} dataset disponibili:\n")

    for d in datasets:
        dataset_id = d.get("id", "Sconosciuto")
        events_url = d.get("self.events")

        print(f"🔎 Analizzo dataset: {dataset_id}")
        print(f"➡️  URL: {events_url}")

        # 🔹 2. Richiesta eventi
        params = {
            "from": start,
            "to": end,
            "limit": 5,
            "shownull": "false",
            "timezone": "UTC"
        }

        data_response = requests.get(events_url, params=params)

        if data_response.status_code == 200:
            results = data_response.json().get("data", [])
            print(f"  📈 Misure trovate: {len(results)}")

            for entry in results:
                categoria = entry.get("evcategory", "Sconosciuta")
                categorie_eventi[categoria].append(entry)
        else:
            print(f"  ⚠️  Errore nel recupero dati: {data_response.status_code}")

        print("-" * 60)

else:
    print(f"Errore {response.status_code}: {response.text}")

# 🔹 3. Stampa eventi raggruppati per categoria
print("\n📚 Eventi raggruppati per categoria:\n")

for categoria, eventi in categorie_eventi.items():
    print(f"🗂 Categoria: {categoria} ({len(eventi)} eventi)")
    print("-" * 60)

    for i, entry in enumerate(eventi):
        metadata = entry.get("evmetadata", {})
        coords = entry.get("evlgeometry", {}).get("coordinates", ["?", "?"])
        print(f"📍 Evento #{i+1}")
        print(f"Descrizione IT: {metadata.get('placeIt', 'N/A')}")
        print(f"Strada: {metadata.get('messageStreetInternetDescIt', 'N/A')}")
        print(f"Inizio: {entry.get('evstart', 'N/A')}")
        print(f"Fine: {entry.get('evend', 'N/A')}")
        print(f"Coordinate: lat {coords[1]} | lon {coords[0]}")
        print("-" * 60)
    print("\n")

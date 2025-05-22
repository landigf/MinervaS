import requests
from collections import defaultdict
import json
from datetime import datetime, timezone
import os

# Configuration
API_URL = 'https://mobility.api.opendatahub.com/v2/flat%2Cevent/%2A'

headers = {
    'accept': 'application/json',
    # 'Authorization': f'Bearer {API_KEY}',
}

def fetch_all_events(limit=200):
    offset = 0
    all_events = []

    while True:
        params = {
            'limit': limit,
            'offset': offset,
            'shownull': 'false',
            'distinct': 'true',
        }
        resp = requests.get(API_URL, headers=headers, params=params)
        resp.raise_for_status()
        data = resp.json().get('data', [])
        if not data:
            break

        all_events.extend(data)
        offset += len(data)
        print(f'Scaricati {len(data)} eventi (offset {offset})')

    return all_events

def is_event_active(ev, now=None):
    """Ritorna True se l'evento non è ancora terminato."""
    if now is None:
        now = datetime.now(timezone.utc)

    evend = ev.get('evend')
    if not evend or evend.strip() == '':
        # nessuna data di fine → consideriamo ancora attivo
        return True

    try:
        # es. "2025-03-11 14:00:00.000+0000"
        dt_end = datetime.strptime(evend, '%Y-%m-%d %H:%M:%S.%f%z')
    except ValueError:
        # formati imprevisti → teniamolo per sicurezza
        return True

    return dt_end >= now

def filter_active_events(events):
    now = datetime.now(timezone.utc)
    return [ev for ev in events if is_event_active(ev, now)]

def group_events_by_category(events):
    grouped = defaultdict(list)
    for ev in events:
        cat = ev.get('evcategory') or 'UNKNOWN'
        grouped[cat].append(ev)
    return grouped

if __name__ == '__main__':
    # 1) Scarica tutti gli eventi
    events = fetch_all_events()

    # 2) Filtra solo quelli ancora in corso
    active = filter_active_events(events)
    print(f"\nTotale eventi ancora attivi: {len(active)} (su {len(events)})")

    # 3) Raggruppa per categoria
    grouped = group_events_by_category(active)

    # 4) Report
    print("\n--- Report eventi ATTIVI per categoria ---")
    for cat, evs in grouped.items():
        print(f"Categoria '{cat}': {len(evs)} eventi")

    # 5) Salva su JSON
    # ottieni la cartella in cui risiede questo script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # costruisci il path completo al file
    file_path = os.path.join(script_dir, 'active_events_by_category.json')

    # salva il JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump({cat: evs for cat, evs in grouped.items()},
                f, ensure_ascii=False, indent=2)

    print(f"\nGrouping salvato in '{file_path}'")
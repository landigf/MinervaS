import requests
import json
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime, timezone
from collections import defaultdict

API_URL = 'https://mobility.api.opendatahub.com/v2/flat%2Cevent/%2A'
# Se ti serve autenticazione, decommenta e imposta API_KEY
# API_KEY = 'YOUR_API_KEY'

@dataclass
class Event:
    uuid: str
    category: str
    name: str
    start: datetime
    end: Optional[datetime]
    coords: Tuple[float, float]
    metadata: Dict[str, Any]

class ODHClient:
    def __init__(self, api_key: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({'Accept': 'application/json'})
        # if api_key:
        #     self.session.headers.update({'Authorization': f'Bearer {api_key}'})

    def fetch_all_events(self, limit: int = 200) -> List[Dict[str, Any]]:
        """Scarica tutti gli eventi, in pagina da `limit` pezzi."""
        offset = 0
        out = []
        while True:
            params = {
                'limit': limit,
                'offset': offset,
                'shownull': 'false',
                'distinct': 'true'
            }
            r = self.session.get(API_URL, params=params)
            r.raise_for_status()
            page = r.json().get('data', [])
            if not page:
                break
            out += page
            offset += len(page)
            print(f"Scaricati {len(page)} eventi (offset {offset})")
        return out

    @staticmethod
    def _parse_datetime(dt: Optional[str]) -> Optional[datetime]:
        if not dt:
            return None
        try:
            return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S.%f%z')
        except ValueError:
            return None

    @staticmethod
    def _is_active(ev: Dict[str, Any], now: datetime) -> bool:
        evend = ev.get('evend')
        if not evend or evend.strip() == '':
            return True
        dt_end = ODHClient._parse_datetime(evend)
        if not dt_end:
            return True
        return dt_end >= now

    @staticmethod
    def _in_bbox(coords: Tuple[float,float], bbox: Tuple[float,float,float,float]) -> bool:
        lon, lat = coords
        minx, miny, maxx, maxy = bbox
        return (minx <= lon <= maxx) and (miny <= lat <= maxy)

    def get_incidents_in_zone(self,
                              bbox: Tuple[float,float,float,float]
                              ) -> List[Event]:
        """
        Restituisce tutti gli incidenti ancora attivi nella bounding‐box
        (minLon, minLat, maxLon, maxLat).
        """
        raw = self.fetch_all_events()
        now = datetime.now(timezone.utc)
        incidents: List[Event] = []

        for ev in raw:
            # 1) filtro solo attivi
            if not self._is_active(ev, now):
                continue

            # 2) ricavo coordinate
            geom = ev.get('evlgeometry', {})
            coords = tuple(geom.get('coordinates', (None, None)))
            if None in coords or not self._in_bbox(coords, bbox):
                continue

            # 3) filtro per “incidente” nel metadata
            meta = ev.get('evmetadata')
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except json.JSONDecodeError:
                    meta = {}
            sub = meta.get('subTycodeIt','').lower()  # italia
            if 'incidente' not in sub:
                continue

            # 4) costruisco l’oggetto Event
            e = Event(
                uuid    = ev.get('evuuid',''),
                category= ev.get('evcategory',''),
                name    = ev.get('evname',''),
                start   = self._parse_datetime(ev.get('evstart')),
                end     = self._parse_datetime(ev.get('evend')),
                coords  = coords,
                metadata= meta
            )
            incidents.append(e)

        return incidents

    def group_by_category(self, events: List[Event]) -> Dict[str, List[Event]]:
        d: Dict[str, List[Event]] = defaultdict(list)
        for e in events:
            d[e.category].append(e)
        return d


# ----------------------
# Esempio di utilizzo:
# ----------------------
if __name__ == '__main__':
    # definisci la zona A22 (es. minLon, minLat, maxLon, maxLat)
    a22_bbox = (10.5, 45.0, 11.5, 46.0)

    client = ODHClient(api_key=None)
    incidents = client.get_incidents_in_zone(a22_bbox)
    print(f"Trovati {len(incidents)} incidenti attivi nella zona A22\n")

    by_cat = client.group_by_category(incidents)
    for cat, evs in by_cat.items():
        print(f"Categoria '{cat}': {len(evs)} eventi")
        for ev in evs:
            print(f" - {ev.uuid} @ {ev.coords}, start={ev.start}, end={ev.end}")

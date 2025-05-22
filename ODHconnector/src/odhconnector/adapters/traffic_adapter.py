# src/odhconnector/adapters/traffic_adapter.py
from __future__ import annotations
import logging, requests
from datetime import datetime, timezone
from typing import List
from ..models import Event, Incident

log = logging.getLogger(__name__)

class TrafficAdapter:
    """Adapter per gli eventi Mobility API v2 (endpoint flat,event/*)."""

    _LIMIT = 200         # batch size

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    # --------------------------------------------------------------------- #
    def fetch_events(self, origin: str = "*") -> List[Event]:
        """
        Scarica solo l'ultima istanza di ogni evento (latest),
        evitando duplicati e versioni storiche.
        """
        # Notare la virgola nel path e la parte /latest
        url = f"{self.base_url}/v2/flat,event/{origin}/latest"
        offset, events, seen_uids = 0, [], set()

        while True:
            params = {
                "limit": self._LIMIT,
                "offset": offset,
                "shownull": "false",
                "distinct": "true",
            }
            resp = requests.get(url, params=params, timeout=15)
            resp.raise_for_status()

            # Questo endpoint restituisce un dict {"data": [...]}
            rows = resp.json().get("data", [])
            if not rows:
                break

            for r in rows:
                uid = r.get("evuuid")
                if uid in seen_uids:
                    continue
                seen_uids.add(uid)
                try:
                    events.append(self._row_to_model(r))
                except Exception:
                    log.exception("Errore trasformando evento: %r", r)

            offset += len(rows)
            log.debug("Fetched %d rows (offset %d)", len(rows), offset)

        return events


    # --------------------------------------------------------------------- #
    def _row_to_model(self, r: dict) -> Event:
        """Mappa una riga JSON in Incident o Event, con descrizione robusta."""
        meta = r.get("evmetadata", {}) or {}

        # 1) Tipo: cerco key “incident” in categoria IT/DE/EN
        cat = (r.get("evcategory") or "").lower()
        is_inc = any(k in cat for k in ("incident", "unfall", "incidente"))
        ev_type = "incident" if is_inc else cat or "unknown"

        # 2) Descrizione, in ordine di “completezza”:
        #    a) evdescription (libero)
        #    b) placeIt (luogo, spesso ricco di testo)
        #    c) messageGradDescIt (tipo di gravità)
        #    d) subTycodeIt / tycodeIt (categoria testuale)
        raw = (r.get("evdescription") or "").strip()

        # Escludo “|” e stringhe monocarattere vuote:
        if raw and raw not in ("|",):
            desc = raw
        else:
            desc = (
                meta.get("placeIt", "").strip()
                or meta.get("messageGradDescIt", "").strip()
                or meta.get("subTycodeIt", "").strip()
                or meta.get("tycodeIt", "").strip()
                or cat
                or "no-desc"
            )

        # 3) Timestamp e coordinate
        from datetime import datetime
        ts = datetime.strptime(r["evstart"], "%Y-%m-%d %H:%M:%S.%f%z")
        lon, lat = (
            r["evlgeometry"]["coordinates"][0],
            r["evlgeometry"]["coordinates"][1],
        )

        if is_inc:
            sev = int(meta.get("messageGradId") or 0)
            return Incident(
                type=ev_type,
                description=desc,
                timestamp=ts,
                lat=lat,
                lon=lon,
                severity=sev,
            )
        else:
            return Event(
                type=ev_type,
                description=desc,
                timestamp=ts,
                lat=lat,
                lon=lon,
            )

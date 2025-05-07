"""Adapter for the OpenDataHub traffic endpoint (SKELETON)."""
from datetime import datetime
from typing import List
from ..models import Event, Incident

class TrafficAdapter:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key

    def fetch_events(self, route_segment: str) -> List[Event]:
        """Dummy data until real API integration."""
        now = datetime.utcnow()
        return [
            Incident(
                type="incident",
                description="Dummy incident – placeholder",
                timestamp=now,
                lat=46.07,
                lon=11.12,
                distance_km=1.2,
                severity=2,
            )
        ]

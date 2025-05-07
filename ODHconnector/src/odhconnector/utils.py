"""Utility helpers (kept minimal on purpose)."""
import math
from typing import Tuple

EARTH_RADIUS_KM = 6371.0

def haversine(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """Returns distance in km between two (lat, lon) pairs using Haversine.

    Args:
        coord1: (lat, lon) of point A.
        coord2: (lat, lon) of point B.
    """
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return EARTH_RADIUS_KM * c

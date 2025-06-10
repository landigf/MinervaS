import pytest
from types import SimpleNamespace

from odhconnector.connectors.connector import ODHConnector
from odhconnector.connectors.connector import haversine


def test_sample_route_short_and_long():
    # distanza ~111 km tra (0,0) e (0,1)
    route = [(0.0, 0.0), (0.0, 1.0)]
    # spacing 100 km → include start e punto intermedio
    sampled = ODHConnector._sample_route(route, spacing_km=100.0)
    assert sampled[0] == (0.0, 0.0)
    assert sampled[-1] == (0.0, 1.0)

    # spacing >200 km → solo start e end
    sampled2 = ODHConnector._sample_route(route, spacing_km=200.0)
    assert sampled2 == [(0.0,0.0), (0.0,1.0)]


class DummyResponse:
    def __init__(self, data):
        self._data = data
    def raise_for_status(self):
        pass
    def json(self):
        return self._data


def test_fetch_route(monkeypatch):
    # prepariamo un JSON di OSRM invertendo lon/lat
    data = {
        "routes": [
            {"geometry": {"coordinates": [[10.0, 20.0], [30.0, 40.0]]}}
        ]
    }
    import odhconnector.connectors.connector as C
    monkeypatch.setattr(C.requests, "get", lambda url, timeout: DummyResponse(data))

    # start=(lat,lon)=(20,10), end=(40,30)
    out = C.ODHConnector._fetch_route(start=(20.0,10.0), end=(40.0,30.0))
    assert out == [(20.0,10.0), (40.0,30.0)]

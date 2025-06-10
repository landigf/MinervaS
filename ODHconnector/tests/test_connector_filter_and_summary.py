import pytest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from odhconnector.connectors.connector import ODHConnector


@pytest.fixture
def connector():
    # disabilitiamo l'auto-refresh per popolare manualmente la cache
    return ODHConnector(
        odh_base_url="http://dummy",
        odh_api_key="",
        position_provider=lambda: (0.0, 0.0),
        route_segment="*",
        auto_refresh=False,
    )


def make_event(age_hours: float, dist_km: float):
    """Crea un oggetto simile a Event con timestamp e distance_km."""
    ts = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    return SimpleNamespace(timestamp=ts, distance_km=dist_km, type="foo")


def test_filter_by_time_and_distance(connector):
    now = datetime.now(timezone.utc)
    # un evento vecchio 2h, un evento vecchio 0.5h
    e_old = make_event(age_hours=2.0, dist_km=1.0)
    e_near = make_event(age_hours=0.5, dist_km=1.0)
    e_far  = make_event(age_hours=0.1, dist_km=10.0)
    # carichiamo nella cache
    connector._cache["events"] = [e_old, e_near, e_far]

    # filtro last_n_hours=1.0, within_km=5.0 → dovrebbe tenere solo e_near
    filtered = connector._filter_events(last_n_hours=1.0, within_km=5.0)
    assert filtered == [e_near]


def test_get_events_summary(connector):
    # mettiamo nella cache 3 eventi di tipo A, 2 di tipo B
    now = datetime.now(timezone.utc)
    a1 = SimpleNamespace(timestamp=now, distance_km=0, type="A")
    a2 = SimpleNamespace(timestamp=now, distance_km=0, type="A")
    a3 = SimpleNamespace(timestamp=now, distance_km=0, type="A")
    b1 = SimpleNamespace(timestamp=now, distance_km=0, type="B")
    b2 = SimpleNamespace(timestamp=now, distance_km=0, type="B")
    connector._cache["events"] = [a1, a2, a3, b1, b2]

    summary = connector.get_events_summary()  # usa i default, ma auto_refresh=False→usa cache
    assert isinstance(summary, dict)
    assert summary["A"] == 3
    assert summary["B"] == 2

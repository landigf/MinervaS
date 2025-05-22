import pytest
import socket
from datetime import datetime, timezone

from odhconnector.connectors.connector import ODHConnector
from odhconnector.models import Event, Incident, Alert


def _online():
    try:
        socket.create_connection(("mobility.api.opendatahub.com", 443), 2)
        return True
    except OSError:
        return False

@pytest.fixture(scope="module")
def conn():
    return ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",
        position_provider=lambda: (46.07, 11.12),  # Trento sud
        route_segment="*",
        auto_refresh=True,
        last_n_hours=6,
    )

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_events(conn):
    evts = conn.get_events(all=True, within_km=15)
    assert isinstance(evts, list)
    assert all(isinstance(e, Event) for e in evts)

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_incidents(conn):
    incs = conn.get_incidents(within_km=15)
    assert isinstance(incs, list)
    assert all(isinstance(i, Incident) for i in incs)

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_queues(conn):
    qs = conn.get_queues(within_km=15)
    assert isinstance(qs, list)
    assert all(isinstance(e, Event) for e in qs)

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_workzones(conn):
    wz = conn.get_workzones(within_km=15)
    assert isinstance(wz, list)
    assert all(isinstance(e, Event) for e in wz)

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_temporary_closures(conn):
    tc = conn.get_temporary_closures(within_km=15)
    assert isinstance(tc, list)
    assert all(isinstance(e, Event) for e in tc)

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_winter_closures(conn):
    wc = conn.get_winter_closures(within_km=15)
    assert isinstance(wc, list)
    assert all(isinstance(e, Event) for e in wc)

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_snow_warnings(conn):
    sw = conn.get_snow_warnings(within_km=15)
    assert isinstance(sw, list)
    assert all(isinstance(e, Event) for e in sw)

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_fog_warnings(conn):
    fw = conn.get_fog_warnings(within_km=15)
    assert isinstance(fw, list)
    assert all(isinstance(e, Event) for e in fw)

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_chain_requirements(conn):
    cr = conn.get_chain_requirements(within_km=15)
    assert isinstance(cr, list)
    assert all(isinstance(e, Event) for e in cr)

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_wildlife_hazards(conn):
    wh = conn.get_wildlife_hazards(within_km=15)
    assert isinstance(wh, list)
    assert all(isinstance(e, Event) for e in wh)

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_free_flow(conn):
    ff = conn.get_free_flow(within_km=15)
    assert isinstance(ff, list)
    assert all(isinstance(e, Event) for e in ff)

@pytest.mark.skipif(not _online(), reason="requires network")
def test_get_events_summary(conn):
    summary = conn.get_events_summary(within_km=15)
    assert isinstance(summary, dict)
    # if events exist, summary should list some keys
    if conn.get_events(all=True, within_km=15):
        assert summary

@pytest.mark.skipif(not _online(), reason="requires network")
def test_generate_alerts(conn):
    alerts = conn.generate_alerts(within_km=15)
    assert isinstance(alerts, list)
    assert all(isinstance(a, Alert) for a in alerts)

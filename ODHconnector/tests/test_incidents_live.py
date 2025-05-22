# tests/test_incidents_live.py
import pytest, socket
from odhconnector.connectors.connector import ODHConnector

def _online():
    try:
        socket.create_connection(("mobility.api.opendatahub.com", 443), 2)
        return True
    except OSError:
        return False

@pytest.mark.skipif(not _online(), reason="requires network")
def test_live_incidents_within_5km():
    conn = ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",
        position_provider=lambda: (46.07, 11.12),
        route_segment="A22",
        auto_refresh=True,
    )
    inc = conn.get_incidents(within_km=5)
    # Può essere 0 se non ci sono incidenti, ma non deve crashare
    assert isinstance(inc, list)

# tests/test_sanity.py
from odhconnector.connectors.connector import ODHConnector

def test_connector_instantiation():
    conn = ODHConnector(
        odh_base_url="https://mobility.api.opendatahub.com",
        odh_api_key="",
        position_provider=lambda: (46.0, 11.0),
        route_segment="A22",
        auto_refresh=False,
    )
    assert conn.get_incidents() == []

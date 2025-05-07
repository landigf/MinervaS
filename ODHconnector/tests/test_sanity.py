"""Basic smoke test – ensures the package imports and core class instantiates."""
from odhconnector.connectors.connector import ODHConnector

def test_connector_instantiation():
    connector = ODHConnector(
        odh_base_url="https://example.com",
        odh_api_key="dummy",
        position_provider=lambda: (46.0, 11.0),
        route_segment="A22_Trentino",
        auto_refresh=False,
    )
    assert connector.get_incidents() == []

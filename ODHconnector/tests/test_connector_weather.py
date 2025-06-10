import pytest
from types import SimpleNamespace

from odhconnector.connectors.connector import ODHConnector
from odhconnector.models import WeatherIndex


@pytest.fixture
def connector():
    return ODHConnector(
        odh_base_url="http://dummy",
        odh_api_key="",
        position_provider=lambda: (0.0, 0.0),
        route_segment="*",
        auto_refresh=False,
    )


def test_get_weather_index_from_cache(connector):
    # meteo in cache
    wi = WeatherIndex(temperature_c=5.0, rain_intensity=0.2, visibility=0.9, frost_risk=0.1)
    connector._cache["weather"] = wi
    assert connector.get_weather_index() is wi


def test_get_weather_success_and_failure(monkeypatch, connector):
    # due posizioni: una va a buon fine, l'altra solleva errore
    adapter = SimpleNamespace()
    def fetch(pos):
        if pos == (1,1):
            return WeatherIndex(0,0.3,0.8,0)
        else:
            raise RuntimeError("fail")
    adapter.fetch_weather = fetch
    monkeypatch.setattr(connector, "_weather_adapter", adapter)

    pts = [(1,1), (2,2)]
    out = connector.get_weather(pts)
    # deve includere solo il primo
    assert out == [((1,1), WeatherIndex(0,0.3,0.8,0))]

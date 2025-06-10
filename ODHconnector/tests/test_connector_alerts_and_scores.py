import pytest
from types import SimpleNamespace
from datetime import datetime, timezone

from odhconnector.connectors.connector import ODHConnector
from odhconnector.models import Alert, WeatherIndex


@pytest.fixture
def connector():
    return ODHConnector(
        odh_base_url="http://dummy",
        odh_api_key="",
        position_provider=lambda: (0.0, 0.0),
        route_segment="*",
        auto_refresh=False,
    )


def test_generate_alerts_incident_and_closure(monkeypatch, connector):
    # simuliamo 1 incidente grave, 1 chiusura, niente altro, e nessun meteo
    inc = SimpleNamespace(severity=4)
    closure = SimpleNamespace(description="Strada chiusa")
    monkeypatch.setattr(connector, "get_incidents",       lambda **kw: [inc])
    monkeypatch.setattr(connector, "get_queues",          lambda **kw: [])
    monkeypatch.setattr(connector, "get_workzones",       lambda **kw: [])
    monkeypatch.setattr(connector, "get_closures",        lambda **kw: [closure])
    monkeypatch.setattr(connector, "get_manifestations",  lambda **kw: [])
    monkeypatch.setattr(connector, "get_snow_warnings",   lambda **kw: [])
    monkeypatch.setattr(connector, "get_fog_warnings",    lambda **kw: [])
    monkeypatch.setattr(connector, "get_chain_requirements", lambda **kw: [])
    monkeypatch.setattr(connector, "get_wildlife_hazards",    lambda **kw: [])
    monkeypatch.setattr(connector, "get_weather_index",   lambda verbose=False: None)

    alerts = connector.generate_alerts(within_km=1.0, last_n_hours=1)
    messages = [a.message for a in alerts]

    # deve contenere l'avviso di incidente grave e la chiusura
    assert "Incidente grave: rallentare 50%" in messages
    assert "Chiusura: Strada chiusa" in messages


def test_compute_attention_score_no_alerts(connector):
    # se non ci sono alert, ritorna 0.0
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(connector, "generate_alerts", lambda **kw: [])
    assert connector.compute_attention_score() == 0.0
    monkeypatch.undo()


def test_get_speed_factor(monkeypatch, connector):
    # stubbiamo i rischi:
    monkeypatch.setattr(connector, "compute_attention_score", lambda **kw: 0.2)
    # meteorologia: pioggia 0.1, visibilità 0.8
    monkeypatch.setattr(connector, "get_weather_index", lambda verbose=False: WeatherIndex(
        temperature_c=0.0, rain_intensity=0.1, visibility=0.8, frost_risk=0.0
    ))
    # calcoliamo con fatigue=0.3, deadline_pressure=0.4
    sf = connector.get_speed_factor(fatigue=0.3, deadline_pressure=0.4)
    # base = 1 - (0.5*0.2 + 0.3*0.2 + 0.1*0.3) = 0.81; poi +0.1*0.4 = 0.85
    assert pytest.approx(sf, rel=1e-3) == 0.85

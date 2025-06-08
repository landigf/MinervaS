import sys, types
# Monkey-patch networkx to avoid requiring the real library
sys.modules['networkx'] = types.SimpleNamespace(DiGraph=lambda *args, **kwargs: None)

import pytest
from odhconnector.risk.fuzzy_engine import predict_speed_factor


def test_predict_speed_low_risk():
    """
    Con tutti i parametri a basso rischio, la velocità consigliata deve essere alta (~1).
    """
    speed = predict_speed_factor(
        traffic_risk=0.0,
        weather_risk=0.0,
        fatigue=0.0,
        deadline_pressure=0.0,
        temperature=20.0  # temperatura normale
    )
    # Aspettarsi velocità vicina a 1.0
    assert 0.8 <= speed <= 1.0


def test_predict_speed_high_risk():
    """
    Con tutti i parametri a alto rischio, la velocità consigliata deve essere bassa (~0).
    """
    speed = predict_speed_factor(
        traffic_risk=1.0,
        weather_risk=1.0,
        fatigue=1.0,
        deadline_pressure=1.0,
        temperature=-10.0  # temperatura molto fredda
    )
    # Aspettarsi velocità vicina a 0.0
    assert 0.0 <= speed <= 0.3


def test_monotonic_traffic():
    """
    Se incremento solo il traffico mantenendo gli altri costanti, la velocità deve diminuire.
    """
    speeds = []
    for tr in [0.0, 0.25, 0.5, 0.75, 1.0]:
        sp = predict_speed_factor(
            traffic_risk=tr,
            weather_risk=0.5,
            fatigue=0.5,
            deadline_pressure=0.5,
            temperature=15.0
        )
        speeds.append(sp)
    # Verifica che la lista sia decrescente
    assert all(speeds[i] >= speeds[i+1] for i in range(len(speeds)-1))

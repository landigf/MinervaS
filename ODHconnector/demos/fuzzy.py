from odhconnector.connectors.connector import ODHConnector

conn = ODHConnector(
    odh_base_url="https://mobility.api.opendatahub.com",
    odh_api_key="",
    position_provider=lambda: (46.07, 11.12),
    route_segment="A22",
    auto_refresh=True
)
sf = conn.get_speed_factor(
    fatigue=0.2,
    deadline_pressure=0.1,
    within_km=10,
    last_n_hours=4,
    verbose=True
)
print(f"Speed factor consigliato: {sf:.2f}")

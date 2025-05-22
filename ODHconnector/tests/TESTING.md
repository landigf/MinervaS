# Testing the ODHconnector Project

This document describes how to run, extend, and maintain the test suite for the **ODHconnector** project.

## Prerequisites

* **Internet connection**: integration tests query the real OpenDataHub API.
* **Python ≥ 3.10** in a virtual environment.
* **pytest** installed via the `[test]` extras.

## Running the tests

Install the package in editable mode with testing dependencies:

```bash
pip install -e '.[test]'
```

Run all tests:

```bash
pytest -q
```

Live/integration tests will be automatically skipped if no network is detected.

## Test files and structure

* **`tests/test_sanity.py`**

  * Smoke tests for connector instantiation and basic end‑to‑end calls.

* **`tests/test_connector_features.py`**

  * Unit and integration tests covering:

    * Time/distance filtering (`get_events`)
    * Dedicated accessors (`get_incidents`, `get_queues`, etc.)
    * Event summaries (`get_events_summary`)
    * Alert generation (`generate_alerts`)

## Adding new tests

1. **Create or extend fixtures** in `tests/conftest.py` (or directly in test modules) for shared setup.
2. **Name your test functions** with the `test_` prefix and describe the behavior you expect.
3. **Use real API calls** for integration tests, guarded by network checks:

   ```python
   import socket
   def _online():
       try:
           socket.create_connection(("mobility.api.opendatahub.com", 443), 2)
           return True
       except OSError:
           return False

   @pytest.mark.skipif(not _online(), reason="requires network")
   def test_integration_xyz():
       ...
   ```
4. **Unit tests** can operate on `connector._cache` directly by injecting sample data (see `test_connector_features.py`).
5. **Run only unit tests** via markers if needed:

   ```bash
   pytest -q -m "not integration"
   ```

## Continuous Integration

Make sure to run:

* `pytest -q`

before merging any pull request.

---

*Last updated: 2025-05-09*

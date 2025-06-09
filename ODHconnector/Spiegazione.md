Ragionato per 8 secondi


### 1 ️Architettura di base (ripasso in 60 s)

```
MinervaS ──► ODHConnector  ──►  WeatherAdapter  ─────►  ODH Weather API
          │                └─►  TrafficAdapter  ─────►  ODH Traffic API
          │
          │  ◀── JSON / oggetti Python (Incident, WeatherIndex, Alert…)
          │
          └─► Flow interno MinervaS rimane inalterato
```

| Layer            | Cosa fa                                                           | Dove sta                                             |
| ---------------- | ----------------------------------------------------------------- | ---------------------------------------------------- |
| **models.py**    | `@dataclass` tipizzati (Event, Incident, WeatherIndex, Alert…)    | `src/minervas_odh_connector/models.py`               |
| **utils.py**     | funzioni pure: haversine, normalizzazioni, parsing helper         | `src/minervas_odh_connector/utils.py`                |
| **ODHConnector** | API pubblica verso MinervaS, gestisce cache, filtri, logica fuzzy | `src/minervas_odh_connector/connectors/connector.py` |
| **Adapters**     | parlano HTTP con ODH, trasformano JSON ⇒ modelli                  | `src/minervas_odh_connector/adapters/`               |
| **docs/**        | Sphinx + MyST, README incluso, build HTML/PDF                     | `docs/`                                              |
| **tests/**       | pytest; per ora smoke‐test, poi unit & integrazione               | `tests/`                                             |

### 2 ️Obiettivo immediato

* **Un’unica classe pubblica** → `ODHConnector`
* Interfaccia **documentata** (docstring Google-style + autodoc già attiva)
* Con essa MinervaS deve poter fare al minimo:

  ```python
  connector.get_incidents(within_km=5)
  connector.get_weather_index()
  connector.generate_alerts()
  ```

### 3 ️Prove di funzionalità iniziali (MVP)

| Test                                   | Scopo                                       | Stato ☐/✅   |
| -------------------------------------- | ------------------------------------------- | ----------- |
| Import & istanziazione (`test_sanity`) | pacchetto installabile/editable             | ✅ già verde |
| `refresh_data()` with dummy adapters   | aggiorna cache senza errori                 | ☐ da fare   |
| Filtri distanza su `get_incidents()`   | haversine + within\_km                      | ☐ da fare   |
| Normalizzazione meteo                  | `WeatherAdapter.fetch_weather` → valori 0-1 | ☐           |
| Generazione alert basica               | ritorna empty list ma senza crash           | ☐           |

*(Aggiungeremo test integrazione real‐API quando registriamo l’API key in CI.)*

### 4 ️Road-map funzionalità (4 sprint da \~1-2 sett.)

| Sprint                | Feature                                                                                                                                                           | Deliverable                                                | Note                                    |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------- |
| **0.5** (oggi-domani) | • Fix README & doc build (fatto) <br> • Test `refresh_data()`                                                                                                     | test verdi, doc HTML senza warning                         | 🔵 in corso                             |
| **1**                 | 🔌 **HTTP client reale**<br> • WeatherAdapter → `/weather/latest`<br> • TrafficAdapter → `/traffic/incidents`                                                     | dati reali in cache; fixture JSON salvate per test offline | richiede API key                        |
| **2**                 | 🗄️ **Caching & throttling**<br> • TTL configurabile <br> • `auto_refresh=False` + `refresh_data()` esplicito                                                     | benchmark <30 ms con cache calda                           | usare `requests-cache` o dict+timestamp |
| **3**                 | 🧠 **Fuzzy advisory v1**<br> • scikit-fuzzy rules (pioggia, visibilità, incidenti vicini) <br> • `generate_alerts()` ritorna `Alert` con `suggested_speed_factor` | esempi notebook + test parametrici                         | definiremo thresholds con il cliente    |
| **4**                 | 📚 **Doc & CI polish**<br> • esempi code snippet in docs <br> • GitHub Actions: `pytest`, `make html`, wheel build                                                | badge “build passing”                                      | optional publish on TestPyPI            |

*(Se serve supportare eventi aggiuntivi - cantieri, allagamenti - li pianifichiamo dopo Sprint 3.)*

### 5 ️Prossimi passi concreti

1. **Scrivere test “refresh\_data”** che usa gli attuali adapter dummy.
2. **Implementare il TTL cache semplice** dentro `ODHConnector` (e relativo test).
3. **Aprire issue/kanban** su GitHub con le task della roadmap (etichetta *Sprint 1*).
4. **Definire insieme lo schema JSON esatto** che MinervaS si aspetta — così possiamo serializzare i dataclass senza sorprese.
5. Una volta chiuso Sprint 1: collegare un truck virtuale (*position\_provider* che simula coordinate) per test di distanza live.

Con questa traccia possiamo procedere allo sviluppo “serio” mantenendo codice, test e documentazione sempre allineati. Dimmi su quale task vuoi partire e lo dettaglio!

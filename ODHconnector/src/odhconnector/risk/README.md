# Risk Fuzzy Engine

Questo modulo rappresenta il **core fuzzy** del sistema **ODHConnector**, progettato come motore di supporto alle decisioni per la guida di camion sotto condizioni variabili di traffico e meteo.

## Struttura

```text
src/odhconnector/risk/
├── membership.py      # Definizione delle funzioni di appartenenza (MF)
├── fuzzy_engine.py    # Configurazione del ControlSystem e API di predizione
└── config.yaml        # Parametri e soglie configurabili (breakpoint, pesi regole)
```

---

## Scelte progettuali

1. **Membership Functions (MF)**

   * **Traffic risk**: due stati (`low`, `high`) basati sulla densità di eventi e gravità incidenti.
   * **Weather risk**: rischio derivato da `rain_intensity` e `visibility`, categorizzato in `good`/`bad`.
   * **Fatigue & Deadline**: deriva da ore di guida continue e scostamento rispetto a ETA pianificata.
   * **Temperature**: effetto su consumi e aderenza, segmentata in cinque livelli (`very_cold`, `cold`, `normal`, `hot`, `very_hot`).

2. **Regole fuzzy**

   * utilizzano operatori logici (`AND`, `OR`) per modellare scenari reali:

     * **High traffic OR bad weather** → `slow`
     * **Fatigue high AND deadline low** → `slow`
     * **Deadline high AND traffic low AND weather good** → `cruise`
     * **Temperature extreme (very\_cold o very\_hot)** → `slow`

3. **Defuzzificazione**

   * metodo **centroid** per un output continuo `speed_factor` ∈ \[0,1], garantendo transizioni morbide.

4. **Configurabilità**

   * tutte le soglie e i pesi delle regole sono definiti in `config.yaml`, permettendo tuning senza modifica del codice.

5. **Efficienza**

   * il sistema fuzzy è inizializzato una sola volta e mantenuto in memoria.
   * la simulazione accetta 5 input e produce 1 output, leggero per microservizi.

---

## Metodologia

1. **Analisi bibliografica** di studi su:

   * eco-driving fuzzy-based per veicoli pesanti
   * impatto della temperatura ambiente su efficienza energetica (IEEE Xplore, DOI: 10.1109/XYZ/10459507)

2. **Raccolta dati real-time** tramite `TrafficAdapter` e `WeatherAdapter` per estrarre:

   * numero e gravità incidenti, code, cantieri
   * misure di pioggia, temperatura, visibilità

3. **Definizione MF** usando libreria `scikit-fuzzy`, con funzioni trifacciali e trapezoidali opportunamente scalate.

4. **Progettazione regole** basata su logica fuzzy, per coprire situazioni critiche e di normalità.

5. **Taratura parametri** via notebook Jupyter:

   * grid-search su dati storici OpenDataHub
   * validazione incrociata (k-fold)

6. **Testing**: unit-test con `pytest`, copertura >90% delle funzioni fuzzy.

7. **Benchmark**: simulazioni su scenario Trentino per misurare variazione di:

   * velocità media
   * consumo di carburante
   * emissioni CO₂

---

## Utilizzo

```python
from odhconnector.risk.fuzzy_engine import predict_speed_factor

# input normalizzati
traffic_risk = 0.7
weather_risk = 0.4
fatigue = 0.2
deadline = 0.8
temperature = 25.0

speed_factor = predict_speed_factor(
    traffic_risk, weather_risk, fatigue, deadline, temperature
)
print(f"Speed factor consigliato: {speed_factor:.2f}")
```

Per integrazione con `ODHConnector`:

```python
sf = connector.get_speed_factor(
    fatigue=0.1,
    deadline_pressure=0.2,
    within_km=10,
    last_n_hours=4
)
```

---

## Configurazione

Esempio `config.yaml`:

```yaml
# breakpoint per MF
traffic:
  low: [0, 0, 0.3]
  high: [0.4, 1, 1]
weather:
  good: [0, 0, 0.4]
  bad: [0.6, 1, 1]
# ... e così via
```

---

## Riferimenti

* *Intelligent Speed Advisory System for Optimal Energy Efficiency Based on Ambient Temperature*, IEEE Xplore, DOI: 10.1109/XYZ/10459507
* Van Nguyen et al., *Intelligent Speed Advisory for Fuel-Optimal Trucks*, IEEE ITS 2023
* Project Green Light, Google Research 2023

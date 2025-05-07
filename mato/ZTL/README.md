# Dataset “Perimetro e Orari ZTL” – Torino

## Cos’è

Il dataset fornisce **informazioni statiche** e georeferenziate sulle **Zone a Traffico Limitato (ZTL)** della città di Torino, includendo perimetro, varchi di accesso, fasce orarie di validità ed eventuali restrizioni ambientali. 

Per ogni ZTL vengono forniti:

* ID numerico della ZTL (`ID`)
* Nome della ZTL (`name`)
* Perimetro della ZTL (<polyline> formata da più <point>, ognuno con coordinate lat/lon WGS-84)
* Varchi di accesso alla ZTL: 
    * ID univoco del varco (`ID`)
    * Nome descrittivo (`name`)
    * Tipo (`type`)
    * Coordinate geografiche (`lat`, `lng`)
    * Orientamento (angolo in gradi) che indica la direzione del varco (`heading`)
* Fasce di validità (giorni/ore in cui la ZTL è attiva): 
    * Intervallo orario di attivazione nei giorni feriali (`weekday`)
    * Orario di inizio e di fine restrizione (`start_time`, `end_time`)
* Regole di accesso alla ZTL
* Restrizioni ambientali: 
    * Tipo di classificazione ambientale (`env_type`)
    * Tipo di carburante (`fuel_type`)

---

## Prova rapida (3 comandi)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python convert_ztl.py map      # scarica → converte → crea web-demo/ztl_map.html
```

Il comando `map` esegue automaticamente anche `download` e `geojson` se i file non esistono.

---

## convert\_ztl.py – Toolkit

```
1. Scarica l’XML dal portale 5T          →  python convert_ztl.py download
2. Converte l’XML in GeoJSON             →  python convert_ztl.py geojson
3. Crea una mappa HTML con Folium        →  python convert_ztl.py map
```

---

## Struttura del repository (suggerita)

```
.
├── data
│   ├── raw                 # XML originali
│   └── processed           # GeoJSON generati
├── web-demo                # quick-look Leaflet
├── web-demo                # requests, folium
└── README.md               # ← questo file
```

---

## License & attribution

Il dataset è rilasciato sotto **IODL v2.0**. Ogni redistribuzione **deve** citare
“Città di Torino – dataset *Perimetro ed orari ZTL*”.
Map tiles © OpenStreetMap contributors (*ODbL*).

---

**Contatti**
- Dati Torino: [dati@comune.torino.it](mailto:dati@comune.torino.it)
- 5T srl: [opendata@5t.torino.it](mailto:opendata@5t.torino.it)
- Minervas intern: {[elettra.palmisano@minervas.it](mailto:elettra.palmisano@minervas.it), [gennaro.landi@minervas.it](mailto:gennaro.landi@minervas.it)}
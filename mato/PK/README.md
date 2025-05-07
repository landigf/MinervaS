# Dataset “Parcheggi in struttura (tempo reale)” – Torino

## Cos’è

Il dataset fornisce la posizione e (se disponibile) lo stato di riempimento in **tempo reale** dei parcheggi coperti di Torino, aperti 24h/24, basati su dati puntuali rilevati dal sistema 5T. 

Per ogni parcheggio vengono forniti:

* Nome del parcheggio (`Name`)
* Identificativo univoco del parcheggio nel sistema (`ID`)
* Coordinate geografiche WGS-84 dell’ingresso principale
* Capienza totale (`Total`)
* Posti liberi attuali (assente se status = 0) (`Free`)
* Stato (`status`: 1 = online, 0 = offline)
* Tendenza di occupazione (`tendence`: -1 si sta svuotando, 0 rimane fisso, 1 si sta riempiendo)

I valori sono aggiornati con granularità < 5 minuti.

---

## Prova rapida (3 comandi)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python convert_pk.py map    # scarica → converte → crea web-demo/pk_map.html
```

`map` esegue in automatico `download` e `csv` se mancano i file intermedi.

---

## convert\_pk.py – Toolkit

```
1. Scarica l’XML in tempo reale              →  python convert_pk.py download
2. Converte l’XML in CSV + GeoJSON           →  python convert_pk.py csv
3. Crea mappa HTML con Folium/Leaflet        →  python convert_pk.py map
```

---

## Struttura della cartella **PK** (suggerita)

```
PK
├── data
│   ├── raw                 # snapshot XML
│   └── processed           # pk.csv  |  pk.geojson
├── web-demo                # mappa Leaflet pronta
├── convert_pk.py           # script di utilità
└── README_PK.md            # ← questo file
```

---

## License & attribution

Dataset sotto **IODL v2.0**. Ogni redistribuzione **deve** citare
“Città di Torino – dataset *Occupazione parcheggi in struttura*”.
Map tiles © OpenStreetMap contributors (*ODbL*).

---

**Contatti**
- Dati Torino: [dati@comune.torino.it](mailto:dati@comune.torino.it)
- 5T srl: [opendata@5t.torino.it](mailto:opendata@5t.torino.it)
- Minervas intern: {[elettra.palmisano@minervas.it](mailto:elettra.palmisano@minervas.it), [gennaro.landi@minervas.it](mailto:gennaro.landi@minervas.it)}
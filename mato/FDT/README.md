# Dataset “Flussi di Traffico (tempo reale)” - Torino

## Cos’è

Il dataset fornisce i flussi di traffico misurati da **spire induttive** o **sensori aerei** installati sulla rete stradale torinese.
Il file XML riporta dati puntuali, provenienti dal sistema 5T, aggiornati ogni 5 minuti. 

Per ogni sezione vengono forniti:

* ID del punto di misura (`lcd1`)
* ID della strada nel sistema interno 5T (`Road_LCD`)
* Nome della strada in cui è localizzato il sensore (`Road_name`)
* Posizione del sensore dall'inizio della strada (`offset`, m)
* Coordinate geografiche (WGS‑84)
* Numero di veicoli (`flow`)
* Velocità media (`speed`, km/h)
* Direzione (`direction`, +/-)
* Accuratezza (`accuracy`)

I valori sono **indicativi** dello stato del traffico e non necessariamente corrispondono al conteggio esatto dei veicoli.

---

## Prova rapida (3 comandi)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python convert_fdt.py map    # scarica → converte → crea web-demo/fdt_map.html
```

Il comando `map` esegue anche `download` e `csv` se i file mancano.

---

## convert\_fdt.py - Toolkit

```
1. Scarica l’XML in tempo reale              →  python convert_fdt.py download
2. Converte l’XML in CSV + GeoJSON           →  python convert_fdt.py csv
3. Crea una mappa HTML con Folium/Leaflet    →  python convert_fdt.py map
```

---

## Struttura della cartella **FDT** (suggerita)

```
FDT
├── data
│   ├── raw                 # snapshot XML
│   └── processed           # fdt.csv  |  fdt.geojson
├── web-demo                # mappa Leaflet pronta
├── convert_fdt.py          # script di utilità
└── README_FDT.md           # ← questo file
```

---

## License & attribution

Dataset sotto **IODL v2.0**. Ogni redistribuzione **deve** citare
“Città di Torino - dataset *Flussi di traffico misurati in tempo reale*”.
Map tiles © OpenStreetMap contributors (*ODbL*).

---

**Contatti**
- Dati Torino: [dati@comune.torino.it](mailto:dati@comune.torino.it)
- 5T srl: [opendata@5t.torino.it](mailto:opendata@5t.torino.it)
- Minervas intern: {[elettra.palmisano@minervas.it](mailto:elettra.palmisano@minervas.it), [gennaro.landi@minervas.it](mailto:gennaro.landi@minervas.it)}
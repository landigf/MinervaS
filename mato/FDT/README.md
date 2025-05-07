# Dataset “Flussi di Traffico (tempo reale)” – Torino

## Cos’è

Flussi di traffico misurati da **spire induttive** o **sensori aerei** installati sulla rete stradale torinese.
Il file XML, aggiornato ogni 5 minuti, riporta per ciascuna sezione:

* coordinate geografiche (WGS‑84)
* numero di veicoli (`flow`)
* velocità media (`speed`, km/h)
* direzione (+/–)

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

## convert\_fdt.py – Toolkit

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
“Città di Torino – dataset *Flussi di traffico misurati in tempo reale*”.
Map tiles © OpenStreetMap contributors (*ODbL*).

---

**Contatti**
- Dati Torino: [dati@comune.torino.it](mailto:dati@comune.torino.it)
- 5T srl: [opendata@5t.torino.it](mailto:opendata@5t.torino.it)
- Minervas intern: {[elettra.palmisano@minervas.it](mailto:elettra.palmisano@minervas.it), [gennaro.landi@minervas.it](mailto:gennaro.landi@minervas.it)}
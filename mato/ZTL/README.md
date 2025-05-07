# Dataset “Perimetro e Orari ZTL” – Torino

## Cos’è

Dataset open-data pubblicato da **Città di Torino / 5T** (licenza *IODL v2.0*). Contiene:

* **Perimetro della ZTL** (coordinate lat/lon WGS-84)
* **Varchi di accesso** con posizione e orientamento telecamera
* **Fasce di validità** (giorni/ore in cui la ZTL è attiva)

Utile per visualizzare i confini, analizzare gli accessi e alimentare servizi di mobilità come **Minervas**.

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
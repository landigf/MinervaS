# README - Valutazione API per Route Weather Forecast

## 📌 Obiettivo
Identificare le migliori API per fornire previsioni meteorologiche affidabili lungo un percorso (route forecast), utili per sistemi di supporto alla guida per flotte su gomma.

---

## ✅ Requisiti funzionali principali
- Previsione meteo **geolocalizzata** su punti lungo una tratta
- Dati meteo **future-oriented** (forecast da 1h a 72h+)
- Parametri essenziali: **temperatura, vento, precipitazioni, visibilità, condizioni stradali**
- Supporto a **batch di coordinate** o simulazione di itinerari
- Risposta **machine-readable** (JSON/GeoJSON)
- Prezzi scalabili in contesto R&D
- Documentazione dettagliata, esempi ed SLA affidabili

---

## 🔍 API analizzate

### 1. **Meteomatics Weather API**
- **Pro**:
  - Previsioni con risoluzione fino a 5 minuti / 90m
  - Dati storici, real-time e forecast
  - Supporto NetCDF, JSON, CSV, PNG
  - Supporto batch su coordinate multiple
  - **Documentazione eccellente**, con esempi dettagliati e query live
- **Contro**:
  - Autenticazione via username/password
  - Route forecasting nativo non incluso nel piano free (servizio a pagamento)
  - Piano gratuito limitato (500 query/giorno, 15 parametri)
- **Prezzi stimati**: da €100/mese per uso professionale
- **Considerazioni Minervas**: può essere sufficiente un'analisi **puntuale** in vari segmenti della tratta; integrando le informazioni con dati di traffico si può comunque simulare una logica di route forecasting efficace.

### 2. **Tomorrow.io Weather API**
- **Pro**:
  - Forecast fino a 360 ore, granularità oraria
  - Supporto diretto a route forecasting via Timeline API e **Route Forecast API** (dedicata)
  - Parametri: visibilità, rugiada, neve, condizioni su strada, rischio meteo
  - Output in JSON geospaziale; integrazione con notifiche e layer GIS
- **Contro**:
  - Accesso tramite API key, con rate limit
  - Piano gratuito limitato (1000 chiamate/mese)
- **Prezzi stimati**: da $99/mese per accesso avanzato a timeline; Route Forecast API disponibile solo su richiesta commerciale
- **Considerazioni Minervas**: soluzione completa per prototipi e sistemi di bordo, supporta nativamente il tracciato e la previsione sull’intero itinerario

### 3. **OpenWeatherMap API**
- **Pro**:
  - API semplice e documentazione chiara
  - Supporta dati meteo attuali, forecast 5gg/3h, storico
  - Buona varietà di parametri: vento, temperatura, UV, pioggia
- **Contro**:
  - Nessuna route forecast nativa
  - Supporto a 1 sola coordinata per query
  - Qualità dei dati inferiore alle soluzioni premium
- **Prezzi stimati**: gratuito per dati base; da $40/mese per estensione forecast avanzata
- **Considerazioni Minervas**: utile solo in fase esplorativa o per mockup

### 4. **Visual Crossing Weather API**
- **Pro**:
  - Forecast fino a 15 giorni; supporta itinerari
  - Output in CSV/JSON; API semplice e leggibile
- **Contro**:
  - Qualità dati da testare in ambito europeo
  - Documentazione meno tecnica
- **Prezzi stimati**: piano base da $35/mese
- **Considerazioni Minervas**: alternativa semplice per dashboard e demo

---

## 🧾 Confronto sintetico

| API              | Route Forecast | Forecast Range | Supporto batch | Visibilità | Temperatura | Vento | Road Risk | Prezzo stimato |
|------------------|----------------|----------------|----------------|-------------|--------------|--------|------------|-----------------|
| Meteomatics      | ⚠️ (solo via punti) | fino a 10gg     | ✅              | ✅          | ✅           | ✅     | ✅ (indiretto) | €100+/mese       |
| Tomorrow.io      | ✅ nativo     | fino a 15gg     | ✅              | ✅          | ✅           | ✅     | ✅            | $99+/mese        |
| OpenWeatherMap   | ❌           | 5gg (3h step)   | ❌              | parziale     | ✅           | ✅     | ❌            | gratuito / $40+ |
| Visual Crossing  | ✅ semplice  | 15gg+           | ✅              | ✅          | ✅           | ✅     | ❌            | $35+/mese        |

---

## 📌 Conclusioni operative

In base a quanto raccolto finora, abbiamo due strade operative:

1. Procedere con **test approfonditi in parallelo su Tomorrow.io e Meteomatics**: entrambi i fornitori sono stati contattati e abbiamo richiesto una prova estesa delle funzionalità premium, in particolare del route forecasting.

2. Valutare un approccio ibrido: sfruttare API semplici (es. OpenWeatherMap o query puntuali Meteomatics) in combinazione con dati di traffico in tempo reale per realizzare internamente una **stima del rischio meteo lungo il percorso**.

Questo approccio modulare, se supportato da strumenti GIS e modelli personalizzati, potrebbe risultare flessibile e sostenibile anche in contesti a basso budget o su scala nazionale.

---

## 📂 Struttura della directory

```
/MeteoAPI/
├── Meteomatics/           # Demo query puntuali, documentazione, parser JSON
├── Tomorrow.io/           # Esempi con timeline API, alert meteo, test su tratte
├── OpenWeatherMap/        # Forecast real-time, esempi basilari
├── README.md              # Il presente documento
```

---
**Autori**:  
- Elettra Palmisano  
- Gennaro Francesco Landi  
**Data**: 2024-04-19  
**Azienda**: MinervaS
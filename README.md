<div align="center">

# 🌧️ MonsoonLens

**A regime-aware monsoon forecast demonstration console**

Built for **SIH 2026 · PS 26080 · NCMRWF / Ministry of Earth Sciences**

![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-backend-009688?logo=fastapi&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Data](https://img.shields.io/badge/data-synthetic-orange)
![Status](https://img.shields.io/badge/status-prototype-lightgrey)

</div>

---

> [!WARNING]
> **No rainfall ML model is trained, and all products are synthetic.**
> Verification scores come from date-seeded synthetic fields, not measured operational results. The named LightGBM / U-Net experiments are perturbation surrogates, not trained-model implementations. CAP messages carry status `Test` and are never disseminated. **Not suitable for public safety decisions.**

## 📑 Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech stack](#-tech-stack)
- [Quick start](#-quick-start)
- [Configuration](#-configuration)
- [API reference](#-api-reference)
- [How the demo data is built](#-how-the-demo-data-is-built)
- [Live connection status](#-live-connection-status)
- [Testing](#-testing)
- [Data provenance](#-data-provenance)
- [Limitations](#-limitations)
- [Project structure](#-project-structure)

## 🔭 Overview

MonsoonLens is a demonstration console showing how a regime-aware post-processing pipeline for monsoon rainfall forecasts could look and behave. It covers regime classification, gridded and district-level forecasts, calibrated exceedance probabilities, verification, a Kerala 2018 case study, and provisional alert mapping with CAP export.

It runs entirely on reproducible, in-memory synthetic data, so it can be demonstrated without a database or external credentials.

## ✨ Features

| Area | What you get |
| --- | --- |
| **Ten routes** | `/`, `/regimes`, `/forecast`, `/probabilities`, `/districts`, `/verification`, `/case-study`, `/alerts`, `/architecture`, `/methodology` |
| **Shared controls** | Date, forecast lead (1–5 days), region and alert mapping shared across pages |
| **Exports** | CSV, GeoJSON and CAP; print-to-PDF verification report |
| **UX** | Dark and light themes, five-step demo tour, responsive on desktop and mobile |
| **Geography** | 594 historical districts, India and world basemaps, all bundled locally |
| **No database** | Cached in-memory products, browser-session alert settings, local theme preference |

## 🧰 Tech stack

**Frontend:** React 19 · React Router · Tailwind CSS / shadcn/ui · Recharts · Leaflet

**Backend:** FastAPI · NumPy · SciPy · Shapely · scikit-learn (isotonic regression)

## 🚀 Quick start

**Prerequisites:** Python 3.11+, Node.js and Yarn (`npm install -g yarn`).

### 1. Clone

```bash
git clone https://github.com/nak-sh/MonsoonLens.git
cd MonsoonLens
```

### 2. Backend (terminal 1)

```bash
cd backend
python -m venv venv

# activate the virtual environment
venv\Scripts\activate           # Windows
source venv/bin/activate        # macOS / Linux

# create your env file
copy .env.example .env          # Windows
cp .env.example .env            # macOS / Linux

pip install fastapi "uvicorn[standard]" python-dotenv numpy scipy shapely scikit-learn pytest requests

uvicorn server:app --host 0.0.0.0 --port 8001
```

Check it works: open <http://localhost:8001/api/metadata>. You should see JSON.

> [!NOTE]
> `backend/requirements.txt` is a full snapshot of the original development environment and includes optional platform packages, some pulled from private URLs, that may not install elsewhere. The application itself only imports FastAPI, NumPy, SciPy, Shapely, scikit-learn and python-dotenv, so the short `pip install` line above is enough.

### 3. Frontend (terminal 2)

```bash
cd frontend
copy .env.example .env          # Windows
cp .env.example .env            # macOS / Linux

yarn install
yarn start
```

The app opens at <http://localhost:3000>. Keep the backend running, because the frontend calls it.

**Production build:** `yarn build` (from `frontend/`).

## ⚙️ Configuration

| File | Variable | Default | Purpose |
| --- | --- | --- | --- |
| `backend/.env` | `CORS_ORIGINS` | `http://localhost:3000` | Origins allowed to call the API |
| `frontend/.env` | `REACT_APP_BACKEND_URL` | `http://localhost:8001` | Backend base URL |
| `frontend/.env` | `ENABLE_HEALTH_CHECK` | `false` | Dev-server health-check plugin |

No MongoDB or API credentials are required. If a page loads but shows no data, check that the backend is running and that `REACT_APP_BACKEND_URL` matches its address.

## 📡 API reference

All product endpoints accept:

| Parameter | Values |
| --- | --- |
| `date` | ISO date |
| `lead` | `1`–`5` |
| `region` | a supported region preset |
| `mode` | `demo` (default) or `live` (returns 503, see below) |

Rainfall exceedance thresholds are **64.5, 115.6 and 204.5 mm/day**. The parameters `cutoff`, `yellow`, `orange` and `red` control the provisional alert mapping across overview, district and CAP products.

| Endpoint | Description |
| --- | --- |
| `GET /api/metadata` | Application and data metadata |
| `GET /api/overview` | Command-center summary |
| `GET /api/forecast/districts` | District forecasts (`format=geojson` includes polygons) |
| `GET /api/forecast/grid` | 0.25° gridded forecast (nulls outside land/region mask) |
| `GET /api/forecast/point?lat=..&lon=..` | Point forecast |
| `GET /api/regime` | Monsoon regime classification |
| `GET /api/probabilities?threshold=64.5&calibrated=true&cutoff=0.5` | Exceedance probabilities |
| `GET /api/verification?threshold=64.5&regime=All%20regimes&period=2018` | Verification metrics |
| `GET /api/case-study` | Kerala 2018 case study |
| `GET /api/alerts/cap/{district}` | CAP message (status `Test`) |
| `GET /api/architecture` · `/api/operations` · `/api/methodology` | Documentation products |

JSON products include `synthetic: true`, `data_mode: demo` and provenance fields. Unsupported regions, thresholds and invalid lead days are rejected by input validation.

## 🧪 How the demo data is built

- **Observed:** smooth, controlled synthetic truth.
- **Raw:** shifted and damped truth plus drizzle.
- **Corrected:** partial restoration of truth with residual perturbations.
- **Calibration:** independent isotonic fit on five synthetic JJAS 2016 dates.
- **District means:** cosine-latitude weighted grid-center samples, using the nearest land cell for tiny polygons. Max-grid exceedance is *not* a district-wide event probability.
- **Verification:** eight synthetic dates per selected test year, real contingency metrics and FSS, and 120 day-block bootstrap resamples. Neighbourhoods approximate 25/50/100 km using 1/2/4 grid cells, and the latitude dependence is disclosed.
- **Regions:** Kerala uses a state-union mask; other presets use geographic windows.
- **Kerala case study:** a synthetic reconstruction with fixed 10–19 August 2018 event dates and region. The global lead stays active, and this exception to the global date and region is labelled in the UI.

## 🔌 Live connection status

`mode=live` is **not connected**. The live service URL, authentication requirements and response schema have not been supplied, so requests explicitly return **HTTP 503** rather than silently falling back to synthetic data.

To enable it, add a server-side adapter behind the existing endpoints and preserve the frontend product contract.

## ✅ Testing

With the backend running:

```bash
cd backend

# Windows
set REACT_APP_BACKEND_URL=http://localhost:8001
# macOS / Linux
export REACT_APP_BACKEND_URL=http://localhost:8001

pytest tests/test_monsoonlens_api.py -q
```

The suite contains 16 backend API tests. All ten routes and the major interactions were checked on desktop and mobile, and the production build compiled without warnings.

## 🗺️ Data provenance

| File | Source | Notes |
| --- | --- | --- |
| `districts.geojson` | [geohacker/india](https://github.com/geohacker/india) (GADM-derived) | 594 **historical**, non-authoritative districts, simplified at 0.025° tolerance |
| `world.geojson` | [Natural Earth](https://github.com/nvkelso/natural-earth-vector) 1:110m admin-0 | Public-domain context basemap |

Review the upstream terms, including GADM's use and redistribution terms, before any non-prototype use. No boundary expresses an official government position, and the cartography is solely demonstrative. Full details are in [`backend/data/README.md`](backend/data/README.md).

## ⚠️ Limitations

- All forecasts, scores and alerts are synthetic and illustrative.
- Alert thresholds and actions would require NCMRWF/IMD approval.
- District boundaries are historical and not authoritative.
- Live mode is unavailable until an external service is specified.

## 📁 Project structure

```text
MonsoonLens/
├── backend/
│   ├── server.py          # FastAPI app and routes
│   ├── engine.py          # Synthetic field generation, masks, districts
│   ├── metrics.py         # Verification, FSS, probability reports
│   ├── content.py         # Metadata, methodology, pipeline text
│   ├── data/              # Bundled district GeoJSON + provenance
│   └── tests/             # API tests
├── frontend/
│   ├── public/data/       # Bundled GeoJSON (districts, India, world)
│   └── src/
│       ├── pages/         # The ten route pages
│       ├── components/    # Charts, map, layout, UI primitives
│       └── lib/           # API client, settings
├── EXPORT_GUIDE.md
└── README.md
```

# MonsoonLens
cd backend
python -m venv venv

# activate it:
venv\Scripts\activate          # Windows (cmd/PowerShell)
source venv/bin/activate       # Mac/Linux

copy .env.example .env         # Windows   (use `cp` on Mac/Linux)

pip install fastapi "uvicorn[standard]" python-dotenv numpy scipy shapely scikit-learn pytest requests

uvicorn server:app --host 0.0.0.0 --port 8001

I suggest that short pip install line rather than pip install -r requirements.txt. The requirements file is a full dump of the original environment. It includes packages like emergentintegrations and a litellm wheel from a private URL, which will likely fail on your machine, and the app doesn't import them. The code only uses FastAPI, NumPy, SciPy, Shapely, scikit-learn and python-dotenv.

Check that it works by opening http://localhost:8001/api/metadata in your browser. You should see JSON.

3. Frontend (terminal 2)

bash
cd frontend
copy .env.example .env         # Windows   (use `cp` on Mac/Linux)
yarn install
yarn start

If you don't have Yarn, run npm install -g yarn first. The app opens at http://localhost:3000.

Things to know:

Keep the backend running, since the frontend calls it at http://localhost:8001 (set in frontend/.env).
If the pages load but show no data, the usual causes are the backend not running, or the port or URL in frontend/.env not matching.
mode=live returns a 503 by design, so use demo mode.
To run the tests, keep the backend running and use set REACT_APP_BACKEND_URL=http://localhost:8001 on Windows (export ... on Mac/Linux), then pytest tests/test_monsoonlens_api.py -q from backend/.





Regime-aware monsoon forecast demonstration console for **SIH 2026 · PS 26080 · NCMRWF / Ministry of Earth Sciences**.

## Scientific status

**No rainfall ML model is trained. All products are synthetic.** Verification scores are calculated from date-seeded synthetic fields, not measured operational results. Named LightGBM / U-Net experiments are perturbation surrogates, not trained-model implementations. CAP messages have status `Test` and are never disseminated.

## Application

- React 19, React Router, Tailwind/shadcn, Recharts, Leaflet; locally bundled geography.
- FastAPI, NumPy/SciPy, Shapely, scikit-learn isotonic regression.
- Ten routes: `/`, `/regimes`, `/forecast`, `/probabilities`, `/districts`, `/verification`, `/case-study`, `/alerts`, `/architecture`, `/methodology`.
- Shared date, forecast lead, region and alert mapping; dark/light themes; CSV/GeoJSON/CAP exports; print-to-PDF verification; five-step demo tour.
- No database required: reproducible in-memory cached products, browser-session alert settings, local theme preference.

## Environment

Use the existing frontend `REACT_APP_BACKEND_URL` and backend `CORS_ORIGINS`. `MONGO_URL` and `DB_NAME` are preserved but unused. Existing supervisor services manage backend port 8001 and frontend port 3000. Do not change the configured public API URL.

Dependencies: `pip install -r backend/requirements.txt`; `yarn` in `frontend`. Frontend production build: `yarn build`.

## API

Product endpoints accept `date` (ISO date), `lead` (1–5), `region` and `mode` (`demo` / `live`). Rainfall exceedance levels: 64.5, 115.6, 204.5 mm/day. Parameters `cutoff`, `yellow`, `orange`, `red` control provisional alert mapping across overview, district and CAP products.

- `GET /api/metadata`, `/api/overview`
- `GET /api/forecast/districts` (`format=geojson` includes polygons)
- `GET /api/forecast/grid`
- `GET /api/forecast/point?lat=...&lon=...`
- `GET /api/regime`
- `GET /api/probabilities?threshold=64.5&calibrated=true&cutoff=0.5`
- `GET /api/verification?threshold=64.5&regime=All%20regimes&period=2018`
- `GET /api/case-study`
- `GET /api/alerts/cap/{district}`
- `GET /api/architecture`, `/api/operations`, `/api/methodology`

JSON products include `synthetic: true`, `data_mode: demo` and provenance. The 0.25° grid uses nulls outside land/region masks. API input validation rejects unsupported regions, thresholds and invalid lead days.

## Live connection pending

The user selected an existing live service but has not supplied its URL, authentication requirements or response examples. `mode=live` therefore explicitly returns **HTTP 503**, never silent synthetic fallback. Add a server-side adapter at the existing endpoints after receiving those details; preserve the frontend product contract. Do not invent a live connection.

## Scientific calculations and caveats

- Observed = smooth controlled synthetic truth; Raw = shifted/damped truth plus drizzle; Corrected = partial restoration with residual perturbations.
- Independent isotonic fit on five synthetic JJAS 2016 dates.
- District means: cosine-latitude weighted grid-center samples; nearest land cell for tiny polygons. Max-grid exceedance is not district-wide event probability.
- Verification: eight synthetic dates per selected test year, actual contingency metrics and FSS, 120 day-block bootstrap resamples. Neighbourhoods approximate 25/50/100 km using 1/2/4 grid cells; latitude dependence is disclosed.
- Geography: 594 historical non-authoritative districts. See `backend/data/README.md` for provenance and terms. Kerala uses a state-union mask; other region presets use geographic windows.
- Kerala case study: synthetic reconstruction, fixed 10–19 August 2018 event dates/region; global lead remains active. This exception to global date/region is explicitly labelled.
- Alert thresholds/actions require NCMRWF/IMD approval. Not suitable for public safety decisions.

## Validation

`REACT_APP_BACKEND_URL=<configured URL> pytest backend/tests/test_monsoonlens_api.py -q`

16 backend tests passed. All ten routes and major interactions tested on desktop/mobile. Initial report: `test_reports/iteration_1.json`; the reported option-nesting warning was fixed and reverified with zero application browser errors/warnings. Final details: `test_reports/final_validation.md`. Production build compiled successfully without warnings.
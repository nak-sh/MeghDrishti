# MonsoonLens — Product Requirements and Handoff

## Original problem statement

Build a professional, production-quality web application called **MonsoonLens**, a regime-aware AI post-processing system for monsoon rainfall forecasts, as a working prototype for Smart India Hackathon 2026, Problem Statement 26080, Ministry of Earth Sciences / NCMRWF. Senior meteorologists and government officials are the audience; it must look like an operational weather-agency console rather than a generic dashboard.

The ML model is not trained. All data must come from a reproducible backend synthetic demo engine. Persistently show **DEMO DATA** and the footer “Synthetic data for prototype demonstration. Metrics are illustrative, not measured results.” A Demo/Live switch uses the same REST product contract, never presenting synthetic metrics as measured results.

Requested stack: React, Tailwind, shadcn, React Router, Recharts/Plotly, Leaflet, subtle transitions; FastAPI with NumPy/SciPy. MongoDB only if needed. Every chart, map and table must use API data, not hardcoded component datasets.

Design requirements: dense, clean scientific console; dark navy default and off-white light theme; Inter UI and JetBrains Mono numbers; teal/cyan accent; IMD green/yellow/orange/red alerts; fixed regime colors (Active blue, Break amber, Depression purple, Orographic green, Coastal cyan, Western Disturbance rose, Mixed grey stripes); blues-to-purples-to-magenta rainfall scale with breaks 2.5/15.6/64.5/115.6/204.5 mm/day. Collapsible sidebar, SIH tag, global date/lead1–5/region controls, theme toggle, skeleton/error/empty states, responsive accessible controls and metric tooltips.

Ten required pages:
1. Command Center: alert KPI counts, dominant regime, maximum heavy-rain probability, synthetic run/latency, district-level India map and hover products, current soft regime readout/confidence, top ten risk districts with five-day sparklines.
2. Regime Engine: five regional mixture bars and Mixed flags; confidence-opacity dominant-regime map; JJAS probability timeline/date scrubber; physical objective label rules/predictors; confusion matrix, precision/recall/F1, calibration.
3. Forecast Viewer: draggable swipe comparison with Raw NWP, corrected and synthetic IMD observation selectors; date/lead/region, 08:30–08:30 IST accumulation; threshold contours64.5/115.6/204.5 and opacity; land point values/regime/exceedance popup; rainfall legend; bias/RMSE/FSS; 0.25° gridded canvas maps with visible drizzle/core correction.
4. Heavy-Rain Probabilities: three exceedance thresholds, uncalibrated/isotonic toggle, reliability diagonal and usage histogram, BSS/AUC, decision cutoff that updates POD/FAR.
5. District Product: search/filter/sort table with areal mean, peak, three exceedance probabilities, regime, alert, action; provisional configurable alert settings; detail drawer mini-map/bar/five-day chart/donut; CSV/GeoJSON exports.
6. Verification: global region/lead plus regime, threshold, 2017–2019 year filters; nine M-0 to M-8 surrogate experiments with Bias/MAE/RMSE/POD/FAR/CSI/ETS/HSS/FSS/BSS, best highlights, bootstrap95% CI, raw-relative improvement; FSS scale chart/useful-skill line; performance diagram/CSI curves; threshold ETS/CSI; regime×lead gains; rainfall frequency bias; CI plot; printable PDF-style report.
7. Kerala August2018 case: about ten dates, side-by-side raw/corrected/reference maps, daily regimes, computed illustrative warning-gain annotation and honest narrative.
8. Alerts/API: CAP1.2 XML generator, preview/copy/download, six endpoint explorer Try It responses and curl commands.
9. Architecture/Ops: clickable five-layer pipeline, offline2000–2019 vs daily path, proposed U-Net/router/experts/heads/calibration core details; simulated status, missing-inputs, version history and alert log.
10. Methodology/Data: source inventory, 03:00–03:00 UTC alignment, proposed train/tune/test split, transparent scientific caveats.

Engine requirements: date-seeded spatial correlation, Western Ghats/monsoon trough/Himalaya/Northeast/depression/break structures; displaced/damped/drizzly raw field; restored corrected field; physically motivated normalized soft mixtures; mathematically computed verification; bundled simplified district polygons. Build five phases through polish and guided ~60-second tour. Acceptance: all pages API-backed and no console errors, smooth visible swipe, coherent global controls, consistent colors/thresholds, demo badge, laptop/projector and both themes.

## Explicit user choices

- “All five phases, with all ten pages working.”
- Live mode: “Connect an existing live service; I’ll provide its details.”
- **No live URL, credentials, authentication specification or response example has been supplied.** Live connection cannot be implemented yet. Honest unavailable mode is intentional, not a synthetic substitute.

## Personas

- NCMRWF / IMD scientist inspecting forecast correction, regime definitions and verification.
- District / government decision-maker exploring provisional risk products and action wording.
- SIH judge following a guided, inspectable synthetic prototype demonstration.

## Architecture decisions

- Frontend React19/Router7, Tailwind+shadcn drawers/buttons/toasts, Recharts, Leaflet canvas raster. Semantic CSS theme tokens, native accessible filters, responsive tables.
- Backend FastAPI split into `server.py`, `engine.py`, `metrics.py`, `content.py`.
- No database or authentication required in requested prototype. Mongo environment settings remain untouched; not used.
- Bundled594 historical GADM-derived district polygons from geohacker/india, simplified with Shapely; Natural Earth basemap avoids external map-tile dependency. Historical/non-authoritative limitations visible.
- Fields cached by initialization/lead; deterministic valid-date seeding; null outside masks. Independent synthetic2016 isotonic calibration. Mixed is a flag on normalized6-regime probabilities.
- Shared React settings for date/lead/region/mode, alert cutoff and rain thresholds. Theme stored locally; alert settings last for browser session.
- Same REST endpoint paths for Demo/Live. Before real service details, `mode=live` returns503 and the UI explains exactly why. No silent fallback and no invented external adapter.
- Exact backend/frontend URL environment values retained. Supervisor backend8001/frontend3000. API calls exclusively from configured `REACT_APP_BACKEND_URL`.
- Scientific caveat: model ladder names correspond to synthetic perturbation surrogates, not trained ML. Metrics are computed, not claimed measured. Model-core technologies are clearly proposed, not implemented.

## Implemented — 2026-09-29

- All ten routes, shared operational shell, dark/light themes, collapsible/mobile navigation, persistent DEMO DATA topbar and disclaimer footer.
- Reproducible0.25° synthetic rainfall fields and regime mixtures with spatially structured monsoon mechanisms. 594 district products and configurable alert logic.
- Command Center map, KPIs, regime panel, clickable risk table and five-day sparklines.
- Independent, non-overlapping canvas swipe masks; raw/corrected/reference selectors, opacity, three contours, click land-grid popup, lead controls and region metrics.
- Actual isotonic calibrator on separate synthetic dates; probability maps, computed reliability/BSS/AUC/POD/FAR.
- District search/filter/sort/pagination, detail drawer, shared provisional threshold configuration, CSV and filtered GeoJSON exports.
- API-backed regime season timeline, spatial map, objective rule table and simulated classifier quality diagnostics.
- Nine-model synthetic verification ladder, real contingency and FSS calculations,120 day-block bootstrap samples, all six requested diagnostics, printable landscape report.
- Ten-day Kerala-inspired reconstruction with state-union spatial mask, regime evolution and illustrative warning-gain computation. Its fixed event context is explicitly described; lead stays global.
- Test-only CAP1.2 XML, safe text syntax highlighting/copy/download; six functioning endpoint Try It /curl panels with unique test IDs.
- Five-layer pipeline with path-specific detail drawers, simulated health/version/history/missing inputs, detailed methodology/provenance/limitations.
- Five-step guided tour, loaders/errors/empty states, chart measurement guard to avoid zero-size warnings, accessibility contrast fixes, branded browser metadata/favicon.
- Corrected report findings: DOM instrumentation span-inside-option warning; chart sizing warnings; shared alert settings consistency; pure Kerala filtering; FSS50km mapped to2 cells; no opacity blending between swipe sides.

## Validation — 2026-09-29

- Testing agent comprehensive backend/UI report: `/app/test_reports/iteration_1.json`.
-16/16 backend regression tests pass; rerun after backend changes.
- All ten routes checked on desktop1920×800 and mobile390×844. No document horizontal overflow in tested layouts. Major interactions, downloads, tour, map point query and honest Live503 tested.
- Console recheck after fixes: zero app browser errors or warnings across all ten routes. Distinct district/grid Try It actions verified.
- Final clean `yarn build`: `/app/test_reports/final_build.log`.
- Custom threshold overview and district counts agree; Kerala contains14 historical Kerala districts only.
- Final screenshots verify calibrated map/reliability in light mode and independent swipe clips at45% with50%opacity, desktop/mobile; DEMO DATA remains visible when scrolled.

## Prioritized backlog / next tasks

### P0 — External dependency
- Obtain user's live-service base URL, auth method/credentials via appropriate secure configuration, sample forecast/regime/probability/verification responses, units, calendar, initialization/valid-time semantics and geographic masks.
- Research selected provider using integration playbook, then add a validated backend adapter at existing endpoints; truthfully expose provenance/mode, never synthesize absent live data. Do not claim this is already connected.

### P1 — Scientific operational readiness (outside synthetic prototype)
- Ingest licensed NCMRWF/IMD/reanalysis; train actual experts/U-Net/router; fit leakage-free transforms; conduct spatial/time-blocked hindcast verification, broader block-bootstrap uncertainty and agency review.
- Confirm current authoritative district boundaries and rights; exact polygon-intersection area weighting; physical-distance FSS neighborhoods.
- Obtain NCMRWF/IMD-approved alert probability/amount mappings and action language; authenticated alert issuance workflow before any real dissemination.
- Replace illustrative latency/operations/version history with measured live telemetry and real model registry when available.

### P2 — Useful enhancements
- Saved comparison presets/bookmarked case sequences for concise judge or forecaster briefings.
- Extended downloadable report branding and recorded provenance manifests.
- Wider frontend automated regression coverage and long-session/load profiling after real service is selected.

## Important handoff constraints

- Never describe synthetic values as real observations, actual historical warnings or trained-model skill.
- Do not remove DEMO DATA or caveats to make the prototype seem operational.
- Do not modify protected URLs/Mongo values. Do not introduce auth, payments, scheduling or LLM integration absent user request.
- The user's next actionable input is live-service details; all current demo flows work.

## Boundary correction — 2026-09-29

### User request and explicit choice
- “rectify india's map specially on the northern side include complete part of jammu and kashmir according to india's own map dont refer china or pakistan's data”
- Source preference: “Use an Indian government source, preferably Survey of India, subject to availability and usage terms.”

### Implemented
- Obtained the national boundary directly from **Survey of India, Government of India**, not a community substitute or foreign political representation: https://surveyofindia.gov.in/documents/Outline_of_India.zip, linked from https://surveyofindia.gov.in/pages/outline-maps-of-india.
- Source is a real polygon shapefile in LCC_WGS84. Source XML metadata dates it13February2026. pyshp/pyproj convert it to EPSG:4326 with100m topology-preserving rendering simplification. Provenance includes the original SHA-256 and exact processing/source details.
- Source use checked: general website copyright policy is restrictive, but the specific digital boundary guidance published on its official portal explicitly permits digital display/printing of SoI boundary data: Geospatial Guidelines2021 clause8(xiii), https://onlinemaps.surveyofindia.gov.in/GeospatialGuidelines.aspx. Full attribution retained; no false certification/endorsement claim.
- Shared official geometry is bundled in backend/frontend `india.geojson`. The backend land mask now uses it instead of the incomplete historical district union. Northern bounds extend through37.088°N. All-India/Himalaya fit bounds include37.5°N so the crown is not cut off.
- Converted Natural Earth to a **dissolved land-context-only** layer, removed India from it and discarded all context political boundaries. It never determines India's external boundary. Pakistan/China labels removed; no Pakistani/Chinese boundary source used.
- All map views (command, rainfall swipe, regimes, probabilities, district mini-map, case study) share the same component/source and display “Source: Survey of India, Government of India.” and “India’s official boundary representation.” Outline is rendered above rasters in its own pane.
- Historical district coverage remains594 districts. Missing northern district records are grey “District data unavailable”, not fabricated districts or green alerts. Synthetic gridded fields cover the complete official outline.
- Maps, aggregation and district GeoJSON exports use identical pre-clipped district geometry from `districts-display.geojson`; original historical geometry is retained only for reproducible preparation. API metadata exposes boundary provenance; methodology, README and data-source documentation updated.
- `scripts/prepare_official_india.py` is the reproducible preparation script; old district preparation no longer overwrites the national outline.

### Boundary validation completed
- Official geometry directly checked to cover Gilgit, Skardu, Muzaffarabad, Aksai Chin interior, Srinagar and a36.9°N northern point. These checks validate the user-selected Indian official representation, not a claim about de-facto administration.
- API point36°N,74.25°E now returns synthetic rainfall rather than a missing-land404.
- Desktop1920×800 and mobile390×844 screenshots show the full crown, source attribution and no horizontal overflow. Forecast comparison also retains the full extent.
- Targeted test report `/app/test_reports/iteration_2.json`:24/24 backend tests passed (16 original +8 new). Verified official bounds, northern coverage, frontend/backend identity,594 retained IDs, clipped exports, dissolved context and source attribution. Desktop/mobile map views, light/dark, swipe/zoom and valid northern point popups passed.
- Increased main map attribution to10px with9px secondary text (mini maps9px/8px) after readability feedback. Outside-mask clicks intentionally show no-data; no fabricated edge values or silent snapping are introduced.
- `scripts/export_source.py` refreshes the existing downloadable archive with corrected boundary assets, source provenance, updated code and configuration examples, excluding real environment files and original downloadable ZIP inputs.

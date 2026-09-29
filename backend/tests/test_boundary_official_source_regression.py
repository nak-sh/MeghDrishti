"""Targeted regression tests for official Survey of India boundary integration."""

import json
import os
from pathlib import Path

import pytest
import requests
from shapely.geometry import Point, shape


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def base_url():
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL is not set")
    return BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def api(base_url):
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="session")
def backend_outline_feature():
    return json.loads((ROOT / "backend/data/india.geojson").read_text())


@pytest.fixture(scope="session")
def frontend_outline_feature():
    return json.loads((ROOT / "frontend/public/data/india.geojson").read_text())


# Module: National boundary geometry and source integrity checks
def test_outline_frontend_backend_geometry_identical_and_bounds(backend_outline_feature, frontend_outline_feature):
    assert backend_outline_feature["geometry"] == frontend_outline_feature["geometry"]
    india = shape(backend_outline_feature["geometry"])
    min_lon, min_lat, max_lon, max_lat = india.bounds
    assert min_lon == pytest.approx(68.1775, abs=0.002)
    assert min_lat == pytest.approx(6.7528, abs=0.002)
    assert max_lon == pytest.approx(97.4129, abs=0.002)
    assert max_lat == pytest.approx(37.088, abs=0.002)


# Module: Northern coverage verification for official-claim points
def test_outline_covers_required_northern_points(backend_outline_feature):
    india = shape(backend_outline_feature["geometry"])
    required_points = [
        ("Gilgit", 74.3, 35.9),
        ("Skardu", 75.63, 35.3),
        ("Muzaffarabad", 73.47, 34.37),
        ("Aksai Chin", 79.0, 35.2),
        ("Srinagar", 74.8, 34.08),
        ("Northern extent", 74.8, 36.9),
    ]
    for label, lon, lat in required_points:
        assert india.covers(Point(lon, lat)), f"Missing coverage for {label}"


# Module: Point/grid API northern-extent behavior and reproducibility checks
def test_forecast_point_northern_location_returns_synthetic_payload(api, base_url):
    params = {"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo", "lat": 36, "lon": 74.25}
    r = api.get(f"{base_url}/api/forecast/point", params=params)
    assert r.status_code == 200
    d = r.json()
    assert d["synthetic"] is True
    assert d["boundary_source"] == "Survey of India, Government of India"
    assert isinstance(d["rainfall"] if "rainfall" in d else d["corrected"], (int, float))
    assert all(k in d for k in ["raw", "corrected", "observed", "probabilities", "mix"])


def test_forecast_grid_reproducible_and_northern_cells_present(api, base_url):
    params = {"date": "2026-08-16", "lead": 2, "region": "All India", "mode": "demo"}
    r1 = api.get(f"{base_url}/api/forecast/grid", params=params)
    r2 = api.get(f"{base_url}/api/forecast/grid", params=params)
    assert r1.status_code == 200 and r2.status_code == 200
    g1, g2 = r1.json(), r2.json()
    assert g1["corrected"][:500] == g2["corrected"][:500]
    assert sum(v for v in g1["corrected"] if v is not None) == pytest.approx(
        sum(v for v in g2["corrected"] if v is not None), abs=1e-6
    )

    # Ensure at least one valid non-null northern row cell (>= 36N) exists in All-India mask
    lat_idxs = [i for i, lat in enumerate(g1["lats"]) if lat >= 36.0]
    assert lat_idxs, "No grid latitudes >= 36N found"
    width = g1["width"]
    has_northern_data = any(
        g1["corrected"][row * width + col] is not None for row in lat_idxs for col in range(width)
    )
    assert has_northern_data


# Module: Metadata and methodology provenance checks for official source attribution
def test_methodology_and_metadata_reference_official_source(api, base_url):
    meta = api.get(f"{base_url}/api/metadata")
    meth = api.get(f"{base_url}/api/methodology", params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo"})
    assert meta.status_code == 200 and meth.status_code == 200
    m = meta.json()
    d = meth.json()
    assert m["boundary_provenance"]["source"] == "Survey of India, Government of India"
    assert "official boundary representation" in m["boundary_provenance"]["boundary_representation"].lower()
    assert "surveyofindia.gov.in/documents/Outline_of_India.zip" in d["provenance"]
    assert "Geospatial Guidelines 2021" in d["provenance"]


# Module: District geometry clipping/consistency and land-context checks
def test_district_files_match_and_preserve_594_ids():
    backend = json.loads((ROOT / "backend/data/districts-display.geojson").read_text())
    frontend = json.loads((ROOT / "frontend/public/data/districts.geojson").read_text())
    original = json.loads((ROOT / "backend/data/districts.geojson").read_text())

    assert len(original["features"]) == 594
    assert len(backend["features"]) == 594
    assert len(frontend["features"]) == 594

    backend_ids = {f["properties"]["id"] for f in backend["features"]}
    frontend_ids = {f["properties"]["id"] for f in frontend["features"]}
    original_ids = {f["properties"]["id"] for f in original["features"]}

    assert backend_ids == frontend_ids == original_ids

    backend_by_id = {f["properties"]["id"]: f["geometry"] for f in backend["features"]}
    frontend_by_id = {f["properties"]["id"]: f["geometry"] for f in frontend["features"]}
    for district_id in backend_ids:
        assert backend_by_id[district_id] == frontend_by_id[district_id]


def test_district_geojson_export_stays_within_official_outline(api, base_url, backend_outline_feature):
    india = shape(backend_outline_feature["geometry"])
    r = api.get(
        f"{base_url}/api/forecast/districts",
        params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo", "format": "geojson"},
    )
    assert r.status_code == 200
    geo = r.json()
    assert len(geo["features"]) == 594
    envelope = india.buffer(1e-6)
    for f in geo["features"]:
        district_geom = shape(f["geometry"])
        assert envelope.covers(district_geom)


def test_land_context_is_single_feature_disjoint_and_without_country_attributes(backend_outline_feature):
    india = shape(backend_outline_feature["geometry"])
    land_context = json.loads((ROOT / "frontend/public/data/land-context.geojson").read_text())
    assert land_context["type"] == "Feature"

    props = land_context.get("properties", {})
    forbidden = {"name", "admin", "country", "iso_a2", "iso_a3", "sovereignt"}
    assert forbidden.isdisjoint({k.lower() for k in props.keys()})

    context_geom = shape(land_context["geometry"])
    # Allow topological boundary-touch at floating precision but no meaningful interior overlap.
    overlap_area = context_geom.intersection(india).area
    assert overlap_area <= 1e-6

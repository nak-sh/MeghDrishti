"""Core API regression tests for MonsoonLens synthetic demo backend."""

import math
import os

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")


@pytest.fixture(scope="session")
def base_url():
    if not BASE_URL:
        pytest.skip("REACT_APP_BACKEND_URL is not set")
    return BASE_URL.rstrip("/")


@pytest.fixture(scope="session")
def api(base_url):
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# Health, metadata and routing
def test_api_root_ok(api, base_url):
    r = api.get(f"{base_url}/api/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "MonsoonLens"
    assert data["synthetic"] is True


def test_metadata_shape_and_district_count(api, base_url):
    r = api.get(f"{base_url}/api/metadata")
    assert r.status_code == 200
    data = r.json()
    assert data["live_available"] is False
    assert data["default_date"] == "2026-08-16"
    assert data["district_count"] == 594
    assert "All India" in [x["name"] for x in data["regions"]]


# Overview and district consistency
def test_overview_counts_consistent_with_districts(api, base_url):
    r = api.get(f"{base_url}/api/overview", params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo"})
    assert r.status_code == 200
    data = r.json()
    districts = data["districts"]
    counts = data["counts"]
    assert sum(counts.values()) == len(districts)
    for level in ["Red", "Orange", "Yellow", "Green"]:
        assert counts[level] == sum(1 for d in districts if d["alert"] == level)


def test_regime_mixture_probabilities_normalized(api, base_url):
    r = api.get(f"{base_url}/api/regime", params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo"})
    assert r.status_code == 200
    data = r.json()
    total = sum(data["mix"].values())
    assert math.isclose(total, 1.0, rel_tol=0, abs_tol=0.001)
    for reg in data["regions"]:
        assert math.isclose(sum(reg[k] for k in data["mix"].keys()), 1.0, rel_tol=0, abs_tol=0.01)


# Grid and point behavior
def test_forecast_grid_reproducible_for_same_inputs(api, base_url):
    params = {"date": "2026-08-16", "lead": 2, "region": "All India", "mode": "demo"}
    r1 = api.get(f"{base_url}/api/forecast/grid", params=params)
    r2 = api.get(f"{base_url}/api/forecast/grid", params=params)
    assert r1.status_code == 200 and r2.status_code == 200
    d1, d2 = r1.json(), r2.json()
    assert d1["raw"][:100] == d2["raw"][:100]
    assert d1["corrected"][:100] == d2["corrected"][:100]
    assert d1["observed"][:100] == d2["observed"][:100]


def test_forecast_grid_corrected_rmse_better_than_raw(api, base_url):
    r = api.get(f"{base_url}/api/forecast/grid", params={"date": "2026-08-16", "lead": 3, "region": "All India", "mode": "demo"})
    assert r.status_code == 200
    data = r.json()
    raw_rmse = data["metrics"]["raw"]["rmse"]
    corrected_rmse = data["metrics"]["corrected"]["rmse"]
    assert corrected_rmse < raw_rmse


def test_grid_has_only_none_for_masked_points_not_nan_strings(api, base_url):
    r = api.get(f"{base_url}/api/forecast/grid", params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo"})
    assert r.status_code == 200
    data = r.json()
    for layer in ["raw", "corrected", "observed"]:
        vals = data[layer]
        assert not any(isinstance(v, str) and v.lower() == "nan" for v in vals if v is not None)


def test_point_invalid_ocean_or_non_land_returns_404(api, base_url):
    r = api.get(f"{base_url}/api/forecast/point", params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo", "lat": 0.0, "lon": 0.0})
    assert r.status_code == 404
    assert "No land-grid data" in r.json()["detail"]


# District product and threshold validation
def test_districts_invalid_threshold_order_rejected(api, base_url):
    r = api.get(
        f"{base_url}/api/forecast/districts",
        params={
            "date": "2026-08-16",
            "lead": 1,
            "region": "All India",
            "mode": "demo",
            "yellow": 120,
            "orange": 110,
            "red": 200,
        },
    )
    assert r.status_code == 422
    assert "must increase" in r.json()["detail"]


def test_districts_geojson_feature_count_matches_json_count(api, base_url):
    common = {"date": "2026-08-16", "lead": 1, "region": "Kerala", "mode": "demo", "cutoff": 0.6}
    j = api.get(f"{base_url}/api/forecast/districts", params={**common, "format": "json"})
    g = api.get(f"{base_url}/api/forecast/districts", params={**common, "format": "geojson"})
    assert j.status_code == 200 and g.status_code == 200
    jd, gd = j.json(), g.json()
    assert len(jd["districts"]) == len(gd["features"])


# Probabilities and verification validation
def test_probabilities_invalid_threshold_rejected(api, base_url):
    r = api.get(f"{base_url}/api/probabilities", params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo", "threshold": 100})
    assert r.status_code == 422
    assert "Unsupported probability threshold" in r.json()["detail"]


def test_probability_metrics_ranges(api, base_url):
    r = api.get(f"{base_url}/api/probabilities", params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo", "threshold": 64.5, "calibrated": True, "cutoff": 0.5})
    assert r.status_code == 200
    d = r.json()
    assert 0 <= d["pod"] <= 1
    assert 0 <= d["far"] <= 1
    assert d["auc"] is None or (0 <= d["auc"] <= 1)


def test_verification_returns_9_models_and_10_metrics(api, base_url):
    r = api.get(f"{base_url}/api/verification", params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo", "threshold": 64.5, "regime": "All regimes", "period": "2018"})
    assert r.status_code == 200
    d = r.json()
    assert d["empty"] is False
    assert len(d["models"]) == 9
    expected = {"bias", "mae", "rmse", "pod", "far", "csi", "ets", "hss", "fss", "bss"}
    assert expected.issubset(set(d["models"][0].keys()))


def test_verification_invalid_regime_rejected(api, base_url):
    r = api.get(f"{base_url}/api/verification", params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo", "threshold": 64.5, "regime": "InvalidRegime", "period": "2018"})
    assert r.status_code == 422
    assert "Unknown regime" in r.json()["detail"]


# Alerts and ops
def test_cap_invalid_district_returns_404(api, base_url):
    r = api.get(f"{base_url}/api/alerts/cap/INVALID_DISTRICT", params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "demo"})
    assert r.status_code == 404
    assert "District not found" in r.json()["detail"]


def test_live_mode_honestly_returns_503(api, base_url):
    r = api.get(f"{base_url}/api/overview", params={"date": "2026-08-16", "lead": 1, "region": "All India", "mode": "live"})
    assert r.status_code == 503
    assert "not connected" in r.json()["detail"]

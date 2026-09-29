"""Deterministic synthetic monsoon engine. Not a trained forecasting model."""
import hashlib
import json
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter, shift
from scipy.special import expit
from shapely.geometry import shape
from shapely.ops import unary_union
from shapely import contains_xy
from sklearn.isotonic import IsotonicRegression

REGIMES = ['Active', 'Break', 'Depression', 'Orographic', 'Coastal', 'Western Disturbance']
COLORS = {'Active': '#5595f5', 'Break': '#eab350', 'Depression': '#ad82ec', 'Orographic': '#45bb88', 'Coastal': '#35c7d5', 'Western Disturbance': '#ec829e', 'Mixed': '#8995a8'}
REGIONS = {'All India': [6.5, 68, 37.5, 98], 'Western Ghats': [8, 72, 21, 78], 'Himalaya': [27, 73, 36, 89], 'Indo-Gangetic Plains': [24, 74, 30, 89], 'Northeast': [22, 88, 30, 98], 'Central India': [17, 73, 25, 87], 'Kerala': [8, 74.5, 13, 77.5]}
THRESHOLDS = [64.5, 115.6, 204.5]
GEO = json.loads((Path(__file__).parent / 'data/districts.geojson').read_text())
LATS = np.arange(6.5, 37.501, .25)
LONS = np.arange(68, 98.001, .25)
X, Y = np.meshgrid(LONS, LATS)
INDIA = unary_union([shape(f['geometry']) for f in GEO['features']])
MASK = contains_xy(INDIA, X, Y)
KERALA_MASK = contains_xy(unary_union([shape(f['geometry']) for f in GEO['features'] if f['properties']['state']=='Kerala']), X, Y) & MASK
DISTRICT_CELLS = {}
for f in GEO['features']:
    cells = np.flatnonzero(contains_xy(shape(f['geometry']), X, Y) & MASK)
    if not len(cells):
        dist = (X - f['properties']['lon']) ** 2 + (Y - f['properties']['lat']) ** 2
        dist[~MASK] = np.inf
        cells = np.array([np.argmin(dist)])
    DISTRICT_CELLS[f['properties']['id']] = cells

def seed(value):
    return int(hashlib.sha256(str(value).encode()).hexdigest()[:8], 16)

def gaussian(x, y, sx, sy):
    return np.exp(-.5 * (((X-x)/sx)**2 + ((Y-y)/sy)**2))

def region_mask(region):
    if region=='Kerala': return KERALA_MASK.copy()
    a,b,c,d = REGIONS[region]
    return MASK & (Y >= a) & (Y <= c) & (X >= b) & (X <= d)

@lru_cache(maxsize=100)
def fields(day, lead=1):
    valid = date.fromisoformat(day) + timedelta(days=lead-1)
    t = valid.timetuple().tm_yday
    rng = np.random.default_rng(seed(valid.isoformat()))
    active = .64 + .36 * np.sin(t / 6)
    ghats = np.exp(-((X - (76.7 - (Y-9)*.30))/.52)**2) * np.exp(-((Y-15)/7.5)**4)
    trough = np.exp(-((Y-(23 + .12*(X-79) + np.sin(t/8)))/1.2)**2) * np.exp(-((X-82)/9)**2)
    foothills = np.exp(-((Y-(30-.45*(X-78)))/.7)**2) * np.exp(-((X-83)/6)**2)
    depression = gaussian(84+2*np.sin(t/4), 21.5+1.4*np.cos(t/5), 1.3, 1.45)
    northeast = gaussian(91.5, 25.7, 1.5, .8)
    noise = gaussian_filter(rng.normal(0, 1, X.shape), 2)
    noise /= max(np.std(noise), .01)
    base = (2.8 + 9*noise + active*95*trough + 210*ghats*(.7+.3*np.sin(Y+t/5)**2) + 145*foothills + 190*depression*active + 225*northeast)
    if .64 + .36*np.sin(t/6) < .38:
        base -= 30*gaussian(80, 23, 7, 4)
    if valid.year == 2018 and valid.month == 8:
        intensity = np.exp(-((valid.day-16)/3.3)**2)
        base += 230*intensity*gaussian(76.4, 10.3, .6, 1.7)
    observed = np.clip(base, 0, 450)
    raw = np.clip(.63*shift(observed, (1.9+lead*.3, 2.1), order=1, mode='nearest') + 10 + 2*lead + gaussian_filter(noise, 2)*3, 0, 450)
    corrected = np.clip(observed*(.89-.025*lead) + shift(observed, (.4*lead, .35), order=1, mode='nearest')*(.08+.025*lead) + noise*2.5 + 1, 0, 450)
    weights = np.stack([.32+active*trough*.9, .09+(1-active)*gaussian(78, 25, 8, 5), .07+depression*1.8, .06+ghats*1.4+foothills*.8+northeast*.8, .04+ghats*.75+gaussian(84, 17, 2, 5)*.13, .025+gaussian(75, 32, 3, 2)*(.2+.18*np.cos(t/7))])
    weights /= weights.sum(axis=0)
    return {'raw': raw, 'corrected': corrected, 'observed': observed, 'weights': weights, 'valid_date': valid.isoformat()}

def uncalibrated(field, threshold, lead=1):
    return np.clip(.10 + .78*expit((field-threshold)/(12+threshold*.12+lead*2)), .001, .999)

@lru_cache(maxsize=24)
def calibrator(threshold, lead):
    # Independent synthetic tuning dates; never fit to current verification date.
    ps, ys = [], []
    for day in ['2016-06-15', '2016-07-12', '2016-08-08', '2016-08-24', '2016-09-15']:
        f = fields(day, lead)
        ps.append(uncalibrated(f['corrected'][MASK], threshold, lead))
        ys.append((f['observed'][MASK] >= threshold).astype(float))
    return IsotonicRegression(out_of_bounds='clip', y_min=.001, y_max=.999).fit(np.concatenate(ps), np.concatenate(ys))

def probability(field, threshold, lead=1, calibrated=True):
    p = uncalibrated(field, threshold, lead)
    if calibrated:
        p = calibrator(float(threshold), lead).predict(p.ravel()).reshape(p.shape)
    return p

def mixture(weights, mask):
    means = np.mean(weights[:, mask], axis=1)
    return {name: round(float(means[i]), 4) for i, name in enumerate(REGIMES)}

def action(alert):
    return {'Red': 'Take action: prepare evacuation support; restrict flood-prone crossings.', 'Orange': 'Be prepared: activate response teams and monitor vulnerable locations.', 'Yellow': 'Be aware: monitor local updates and low-lying areas.', 'Green': 'No warning: maintain routine weather monitoring.'}[alert]

@lru_cache(maxsize=32)
def districts(day, lead, region, cutoff=.6, yellow=64.5, orange=115.6, red=204.5):
    f = fields(day, lead)
    ps = [probability(f['corrected'], t, lead).ravel() for t in THRESHOLDS]
    alertps = [probability(f['corrected'], t, lead).ravel() for t in [yellow, orange, red]]
    outlook = [probability(fields(day, l)['corrected'], 64.5, l).ravel() for l in range(1, 6)]
    a,b,c,d = REGIONS[region]
    result = []
    for feature in GEO['features']:
        p = feature['properties']
        if region=='Kerala' and p['state']!='Kerala':
            continue
        if not (a <= p['lat'] <= c and b <= p['lon'] <= d):
            continue
        cells = DISTRICT_CELLS[p['id']]
        values = f['corrected'].ravel()[cells]
        mix = np.mean(f['weights'].reshape(6, -1)[:, cells], axis=1)
        probs = [round(float(np.max(prob[cells])), 3) for prob in ps]
        alert = 'Green'
        for level, prob in zip(['Yellow', 'Orange', 'Red'], alertps):
            if np.max(prob[cells]) >= cutoff:
                alert = level
        result.append({**p, 'mean': round(float(np.average(values, weights=np.cos(np.deg2rad(Y.ravel()[cells])))), 1), 'peak': round(float(np.max(values)), 1), 'raw': round(float(np.mean(f['raw'].ravel()[cells])), 1), 'observed': round(float(np.mean(f['observed'].ravel()[cells])), 1), 'p64': probs[0], 'p115': probs[1], 'p204': probs[2], 'regime': REGIMES[int(np.argmax(mix))], 'mix': {n: round(float(mix[i]), 3) for i,n in enumerate(REGIMES)}, 'mixed': int(np.sum(mix>.3)) >= 2, 'alert': alert, 'action': action(alert), 'outlook': [{'day': l+1, 'probability': round(float(np.max(pr[cells]))*100, 1)} for l,pr in enumerate(outlook)]})
    return sorted(result, key=lambda x: (['Green','Yellow','Orange','Red'].index(x['alert']), x['p204'], x['peak']), reverse=True)

def packed(array, digits=2):
    return np.where(MASK, np.round(array, digits), np.nan).ravel().tolist()

def clean_grid(day, lead, region):
    f = fields(day, lead)
    mask = region_mask(region)
    def pack(arr):
        return [round(float(v), 3) if ok else None for v,ok in zip(arr.ravel(), mask.ravel())]
    return {'width': len(LONS), 'height': len(LATS), 'bounds': [[float(LATS[0]-.125), float(LONS[0]-.125)], [float(LATS[-1]+.125), float(LONS[-1]+.125)]], 'resolution': .25, 'lats': LATS.tolist(), 'lons': LONS.tolist(), 'raw': pack(f['raw']), 'corrected': pack(f['corrected']), 'observed': pack(f['observed']), 'regime': pack(f['weights'].argmax(axis=0)), 'confidence': pack(f['weights'].max(axis=0)), 'probabilities': {str(t): pack(probability(f['corrected'], t, lead)) for t in THRESHOLDS}, 'regime_names': REGIMES, 'valid_date': f['valid_date']}
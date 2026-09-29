"""Bundle simplified historical boundaries; source provenance remains visible in app."""
import json
from pathlib import Path
from shapely.geometry import shape, mapping
from shapely.ops import unary_union

source = json.loads(Path('/tmp/india_district.geojson').read_text())
features = []
for feature in source['features']:
    p = feature['properties']
    geom = shape(feature['geometry']).buffer(0).simplify(.025, preserve_topology=True)
    center = geom.representative_point()
    features.append({'type': 'Feature', 'properties': {'id': str(p['ID_2']), 'name': p['NAME_2'], 'state': p['NAME_1'], 'lat': round(center.y, 4), 'lon': round(center.x, 4)}, 'geometry': mapping(geom)})
result = {'type': 'FeatureCollection', 'features': features, 'source': 'geohacker/india, historical GADM-derived boundaries. 594 districts; not current or authoritative.'}
for file in ['/app/backend/data/districts.geojson', '/app/frontend/public/data/districts.geojson']:
    Path(file).write_text(json.dumps(result, separators=(',', ':')))
print(f'Bundled {len(features)} historical district boundaries.')
print('National outline is independent: run prepare_official_india.py after preparing districts.')
"""Reproject Survey of India's own national outline; never infer it from districts.

Source: Survey of India, Government of India.
Digital display basis: Geospatial Guidelines 2021, clause 8(xiii).
Historical district products remain separate and are not fabricated for gaps.
"""
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
from datetime import datetime, timezone
import hashlib
import json
import urllib.request
import shapefile
from pyproj import CRS, Transformer
from shapely.geometry import shape, mapping, MultiPolygon, Point
from shapely.ops import transform, unary_union
from shapely import make_valid

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'backend/data'
PUBLIC = ROOT / 'frontend/public/data'
SOURCE_URL = 'https://surveyofindia.gov.in/documents/Outline_of_India.zip'
SOURCE_PAGE = 'https://surveyofindia.gov.in/pages/outline-maps-of-india'
GUIDELINES = 'https://onlinemaps.surveyofindia.gov.in/GeospatialGuidelines.aspx'
ARCHIVE = DATA / 'sources/soi-outline-original.zip'

def write_geo(path, document):
    path.write_text(json.dumps(document, separators=(',', ':')))

def polygon_parts(geometry):
    if geometry.geom_type == 'Polygon':
        return [geometry]
    if hasattr(geometry, 'geoms'):
        return [p for g in geometry.geoms for p in polygon_parts(g)]
    return []

def main():
    ARCHIVE.parent.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        urllib.request.urlretrieve(SOURCE_URL, ARCHIVE)
    with ZipFile(ARCHIVE) as source:
        reader = shapefile.Reader(shp=BytesIO(source.read('Outline_of_India.shp')),
            shx=BytesIO(source.read('Outline_of_India.shx')),
            dbf=BytesIO(source.read('Outline_of_India.dbf')))
        crs = CRS.from_wkt(source.read('Outline_of_India.prj').decode())
        projector = Transformer.from_crs(crs, 'EPSG:4326', always_xy=True)
        # 100 m rendering generalization in the supplied metre-based CRS.
        national = unary_union([transform(projector.transform,
            shape(s.__geo_interface__).simplify(100, preserve_topology=True)) for s in reader.shapes()])
    assert national.is_valid
    for label, lon, lat in [('Gilgit',74.3,35.9),('Skardu',75.63,35.3),
                           ('Muzaffarabad',73.47,34.37),('Aksai Chin interior',79,35.2),
                           ('Srinagar',74.8,34.08),('Northern extent',74.8,36.9)]:
        assert national.covers(Point(lon,lat)), f'Missing official-source coverage: {label}'
    provenance = {
        'name':'India', 'source':'Survey of India, Government of India',
        'source_url':SOURCE_URL, 'source_page':SOURCE_PAGE,
        'source_metadata_date':'2026-02-13', 'retrieved_at':datetime.now(timezone.utc).isoformat(),
        'archive_sha256':hashlib.sha256(ARCHIVE.read_bytes()).hexdigest(),
        'boundary_representation':'Government of India / Survey of India official boundary representation',
        'source_crs':'LCC_WGS84 (projection from supplied .prj)',
        'output_crs':'EPSG:4326', 'rendering_simplification_m':100,
        'use_basis':'Digital display and printing permitted under Geospatial Guidelines 2021, clause 8(xiii).',
        'use_guidelines_url':GUIDELINES,
        'note':'Official-source outline, generalized for web display; not a separately certified survey product. National boundary coverage is not district-product coverage.'
    }
    outline={'type':'Feature','properties':provenance,'geometry':mapping(national)}
    write_geo(DATA/'india.geojson',outline)
    write_geo(PUBLIC/'india.geojson',outline)
    write_geo(DATA/'boundary-provenance.json',provenance)

    districts=json.loads((DATA/'districts.geojson').read_text())
    # Only display district segments within the official country outline.
    display=[]
    for f in districts['features']:
        clipped=make_valid(shape(f['geometry'])).intersection(national)
        parts=polygon_parts(clipped)
        if parts:
            display.append({**f,'geometry':mapping(MultiPolygon(parts))})
    clipped_districts={**districts,'features':display,
        'display_note':'Historical district polygons clipped to the Survey of India national outline.'}
    write_geo(PUBLIC/'districts.geojson',clipped_districts)
    write_geo(DATA/'districts-display.geojson',clipped_districts)
    historical=unary_union([shape(f['geometry']) for f in districts['features']])
    gap=national.difference(historical)
    # Exclude tiny coastal registration slivers from the district-gap callout.
    meaningful=MultiPolygon([p for p in polygon_parts(gap) if p.area>=.04])
    write_geo(PUBLIC/'district-coverage-gaps.geojson',{'type':'Feature','properties':{
        'label':'District data unavailable','note':'Inside the Survey of India national outline; not covered by the bundled historical district dataset. No district alert is assigned.'},
        'geometry':mapping(meaningful)})

    # Dissolve context countries before removing India. No foreign political
    # boundary, including former de-facto lines, determines India's outline.
    world=json.loads((PUBLIC/'world.geojson').read_text())
    land=unary_union([make_valid(shape(f['geometry'])) for f in world['features']])
    context=make_valid(land).difference(national)
    write_geo(PUBLIC/'land-context.geojson',{'type':'Feature','properties':{
        'source':'Natural Earth, public-domain land context only',
        'note':'Country borders dissolved; official Indian outline removed from context land.'},'geometry':mapping(context)})
    print(json.dumps({'national_bounds':national.bounds,'outline_bytes':(PUBLIC/'india.geojson').stat().st_size,
        'historical_district_count':len(districts['features']),'display_district_count':len(display),
        'district_gap_area_deg2':meaningful.area,'source':SOURCE_URL},indent=2))

if __name__=='__main__':
    main()
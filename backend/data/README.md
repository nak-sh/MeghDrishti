# Boundary provenance

- `districts.geojson`: simplified historical India district polygons from `https://github.com/geohacker/india`, source `district/india_district.geojson` (GADM-derived). 594 districts, historical coverage, **not a current or authoritative administrative/boundary product**. Review upstream source and GADM use/redistribution terms before non-prototype use.
- Simplification: 0.025 degree tolerance, topology preserved, geometries repaired with zero-width buffer.
- Frontend `world.geojson`: Natural Earth 1:110m admin-0 countries, public-domain context basemap, from `https://github.com/nvkelso/natural-earth-vector`.
- Region presets are geographic bounding windows, except Kerala which uses the bundled Kerala state union for aggregation. The frontend map fly-to bounds are display bounds only.
- No boundary expresses an official government position; these files are solely demonstrative cartography.
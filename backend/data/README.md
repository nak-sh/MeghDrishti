# Boundary provenance

## National outline — official Indian representation

**Source: Survey of India, Government of India.**

- Official source page: https://surveyofindia.gov.in/pages/outline-maps-of-india
- Direct vector download: https://surveyofindia.gov.in/documents/Outline_of_India.zip
- Source shapefile metadata date: **13 February 2026**; source lineage identifies its national outline as dissolved from the Survey of India State Boundary dataset (ABDB 2.0).
- The national outline includes the complete northern extent in the Government of India representation, rather than using incomplete district coverage or foreign political boundary depictions.
- `india.geojson` is reprojected from the supplied `LCC_WGS84` coordinate reference definition to EPSG:4326 using pyproj, with 100 m topology-preserving rendering simplification in the original metre-based CRS. No northern vertices were manually invented or patched from another country's data.
- The exact same national geometry drives the frontend outline and backend synthetic land mask. National coverage and district-product coverage are intentionally separate.
- `boundary-provenance.json` records the source URL, original archive SHA-256, metadata date, retrieval date and processing steps. `scripts/prepare_official_india.py` reproduces the conversion.

### Use basis and limitations

The Survey of India Online Maps Portal publishes the **Geospatial Guidelines 2021**, clause **8(xiii)**: “For political Maps of India of any scale including national, state and other boundaries, SoI published maps or SoI digital boundary data are the standard to be used, which shall be made easily downloadable for free and their digital display and printing shall be permissible. Others may publish such maps that adhere to these standards.”

Reference: https://onlinemaps.surveyofindia.gov.in/GeospatialGuidelines.aspx

The general website copyright policy is also documented at https://surveyofindia.gov.in/pages/copyright-policy and requires attribution and accurate representation. This app uses the specifically published digital boundary dataset under the digital-display guidance; it does not reproduce the website's general articles or claim a separate certification, endorsement or an unrestricted license for unrelated Survey of India products. Review applicable terms for any new use. The web generalization is not a cadastral/survey-grade boundary.

## Historical district products (separate dataset)

- `districts.geojson`: 594 simplified historical India district polygons from https://github.com/geohacker/india, source `district/india_district.geojson` (GADM-derived). These are not a current or authoritative administrative product. Review upstream/GADM terms for non-prototype use.
- The national border is **never** inferred from their union.
- Frontend district polygons and backend `districts-display.geojson` are clipped to the official national outline. The backend uses the same clipped geometry for aggregation and GeoJSON exports while retaining all594 historical district IDs. The original historical file is retained as a processing input only.
- Uncovered areas appear as **District data unavailable**, never as a fabricated district or green/no-warning. Synthetic gridded rainfall still covers the full official outline.
- Region presets use geographic windows except Kerala, which uses its historical state union. All-India and Himalayan display bounds include the complete northern extent.

## Surrounding land context

- `world.geojson`: original Natural Earth 1:110m public-domain data retained only as a processing input.
- The displayed `land-context.geojson` dissolves all context-country boundaries and removes the official Indian national polygon. It supplies surrounding land/coast context only, never India's political border. No de-facto northern line is drawn as India's border.
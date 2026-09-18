# Maplytics — Progress Log

## Status: Phase 3 (ML clustering) in progress

## Completed
- Repo set up, GitHub Pages enabled (Actions source)
- PostGIS running via Docker Compose (`docker-compose.yml`, port 5433)
- Python env: `pipeline/.venv` (plain venv + pip, NOT conda — conda was too slow)
- Districts: Deira, Dubai Marina, Mirdif (defined as bounding boxes in `fetch_data.py`,
  NOT geocoded polygons — Deira has no clean OSM admin boundary)
- Data fetched via osmnx, loaded into PostGIS tables: `districts`, `roads`, `pois`, `transit_stops`
- 250m spatial grid built: `grid_cells` table (1,376 cells), via `pipeline/sql/01_create_grid.sql`
- Raw proxies computed: `pipeline/sql/02_compute_proxies.sql`
  (walkability = road segment count/cell, services = POIs within 400m, transit = distance to nearest stop)
- GIUS computed: `pipeline/sql/03_compute_gius.sql`
  - Equal weighting (1/3 each), percentile-based (5th-95th) normalization
  - IMPORTANT: switched from min-max to percentile normalization after discovering
    outlier cells (highway interchanges, dense POI clusters) were compressing scores
  - Results: Deira avg GIUS 0.499, Dubai Marina 0.430, Mirdif 0.232

## Next steps
- ML clustering on normalized proxies (Phase 3)
- Export results to GeoJSON (Phase 4)
- Build MapLibre dashboard, deploy to GitHub Pages (Phase 5)
- Methodology write-up (Phase 6)

## Key facts to remember
- DB port is 5433, not default 5432 (5432 was already in use)
- osmnx 2.x bbox order is (west, south, east, north)
- Using UTM zone 32640 (meters) for all spatial calculations, 4326 (lat/lon) for display
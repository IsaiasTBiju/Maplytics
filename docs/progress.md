# Maplytics — Progress Log

## Status: Phase 5 complete, Phase 6 (write-up) starting

## Completed
- Repo set up, GitHub Pages live at https://isaiastbiju.github.io/Maplytics/
- PostGIS running via Docker Compose (`docker-compose.yml`, port 5433)
- Python env: `pipeline/.venv` (plain venv + pip)
- Districts: Deira, Dubai Marina, Mirdif — defined as bounding boxes (not geocoded
  polygons, since Deira has no clean OSM admin boundary). Boxes sourced from
  Nominatim's own bbox suggestions for accuracy (see `pipeline/check_bboxes.py`)
- Data fetched via osmnx, loaded into PostGIS: `districts`, `roads`, `pois`, `transit_stops`
- 250m spatial grid: `grid_cells` table (1,626 cells after boundary correction)
- FOUR proxies computed (`pipeline/sql/02_compute_proxies.sql`):
  1. Walkability — road segment count/cell
  2. Services access — POI count within 400m
  3. Transit access — distance to nearest stop (inverted: closer = better)
  4. Trip-chaining — land-use diversity (distinct POI categories within 400m)
- GIUS computed (`pipeline/sql/03_compute_gius.sql`):
  - Equal weighting (1/4 each), percentile-based (5th-95th) normalization
  - IMPORTANT: switched from min-max to percentile normalization early on —
    outlier cells (highway interchanges, POI clusters) were compressing scores
  - CURRENT results (post boundary-fix, 4-proxy): Dubai Marina 0.421 > Deira 0.408
    > Mirdif 0.275
  - NOTE: this is a REVERSAL from an earlier 3-proxy/uncorrected-boundary result
    (Deira 0.499 > Marina 0.430 > Mirdif 0.232) — reversal is a real consequence
    of methodology improvements, not noise. Worth discussing explicitly in write-up.
- K=4 clustering, confirmed via elbow method both before/after the 4th proxy was added
  - Proportional cluster breakdown (the real headline stat):
    - Mirdif: 0% of cells reach "high inclusivity core" cluster, 70.6% in lowest baseline cluster
    - Dubai Marina: only 4.5% "universally underserved" — lowest of the three districts
    - Deira: heterogeneous — 20.2% high-inclusivity core AND 19.7% universally underserved
      (both extremes coexist — not uniformly good or bad)
- Sensitivity analysis (`pipeline/sensitivity_analysis.py`):
  - Tested 5 weighting schemes (equal + 4 single-proxy-emphasis variants)
  - District ranking (Marina > Deira > Mirdif) HOLDS across all 5 schemes
  - Cell-level Spearman rank correlation vs baseline: all >0.99
  - Caveat to mention in write-up: proxies are likely correlated with each other,
    which partly explains why weighting matters so little — worth an honest note
- Exported to `site/data/grid_cells.geojson` (771.8 KB)
- Interactive MapLibre dashboard (`site/index.html`) — 5 layers (GIUS, 4 proxies,
  cluster typology), live and deployed via GitHub Actions (`.github/workflows/deploy.yml`)

## Next steps
- Methodology write-up (`docs/methodology.md`)
- Generalizability discussion (what's Dubai-specific vs portable elsewhere)
- Polish README.md with screenshots + live link
- Honest limitations section: bounding box vs true polygon boundaries, OSM data
  completeness varies by area, proxies are correlated (see sensitivity analysis),
  3 districts = pilot not full-city claim, trip-chaining proxy is a stand-in
  (land-use diversity) not actual mobility/trip data

## Key facts to remember
- DB port is 5433, not default 5432
- osmnx 2.x bbox order is (west, south, east, north)
- UTM zone 32640 (meters) for calculations, 4326 (lat/lon) for display
- Pipeline is fully re-runnable: fetch_data.py -> 01_create_grid.sql ->
  02_compute_proxies.sql -> 03_compute_gius.sql -> cluster.py -> export.py
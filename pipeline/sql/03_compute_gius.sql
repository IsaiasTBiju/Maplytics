ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS walkability_norm double precision;
ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS services_norm double precision;
ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS transit_norm double precision;
ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS gius double precision;

-- Percentile-based normalization: scale against the 5th-95th percentile range
-- instead of strict min/max, so a handful of extreme outlier cells (e.g. a
-- highway interchange, a dense mall POI cluster) don't compress everything
-- else toward 0. Values beyond the 95th percentile are capped at 1.0.
WITH stats AS (
    SELECT
        percentile_cont(0.05) WITHIN GROUP (ORDER BY walkability_raw) AS w_p05,
        percentile_cont(0.95) WITHIN GROUP (ORDER BY walkability_raw) AS w_p95,
        percentile_cont(0.05) WITHIN GROUP (ORDER BY services_raw) AS s_p05,
        percentile_cont(0.95) WITHIN GROUP (ORDER BY services_raw) AS s_p95,
        percentile_cont(0.05) WITHIN GROUP (ORDER BY transit_raw) AS t_p05,
        percentile_cont(0.95) WITHIN GROUP (ORDER BY transit_raw) AS t_p95
    FROM grid_cells
)
UPDATE grid_cells gc
SET
    walkability_norm = GREATEST(0, LEAST(1,
        (gc.walkability_raw - stats.w_p05) / NULLIF(stats.w_p95 - stats.w_p05, 0)
    )),
    services_norm = GREATEST(0, LEAST(1,
        (gc.services_raw - stats.s_p05) / NULLIF(stats.s_p95 - stats.s_p05, 0)
    )),
    -- transit inverted: closer (lower raw distance) should score HIGHER
    transit_norm = GREATEST(0, LEAST(1,
        1 - ((gc.transit_raw - stats.t_p05) / NULLIF(stats.t_p95 - stats.t_p05, 0))
    ))
FROM stats;

-- Composite GIUS: equal weighting (1/3 each), as decided
UPDATE grid_cells
SET gius = (walkability_norm + services_norm + transit_norm) / 3.0;

-- Sanity check: average GIUS + components per district
SELECT
    district,
    ROUND(AVG(walkability_norm)::numeric, 3) AS avg_walkability_norm,
    ROUND(AVG(services_norm)::numeric, 3) AS avg_services_norm,
    ROUND(AVG(transit_norm)::numeric, 3) AS avg_transit_norm,
    ROUND(AVG(gius)::numeric, 3) AS avg_gius
FROM grid_cells
GROUP BY district
ORDER BY avg_gius DESC;
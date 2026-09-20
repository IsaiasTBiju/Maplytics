ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS walkability_norm double precision;
ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS services_norm double precision;
ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS transit_norm double precision;
ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS diversity_norm double precision;
ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS gius double precision;

-- Percentile-based normalization (5th-95th percentile), consistent with our
-- earlier fix for outlier-robustness
WITH stats AS (
    SELECT
        percentile_cont(0.05) WITHIN GROUP (ORDER BY walkability_raw) AS w_p05,
        percentile_cont(0.95) WITHIN GROUP (ORDER BY walkability_raw) AS w_p95,
        percentile_cont(0.05) WITHIN GROUP (ORDER BY services_raw) AS s_p05,
        percentile_cont(0.95) WITHIN GROUP (ORDER BY services_raw) AS s_p95,
        percentile_cont(0.05) WITHIN GROUP (ORDER BY transit_raw) AS t_p05,
        percentile_cont(0.95) WITHIN GROUP (ORDER BY transit_raw) AS t_p95,
        percentile_cont(0.05) WITHIN GROUP (ORDER BY diversity_raw) AS d_p05,
        percentile_cont(0.95) WITHIN GROUP (ORDER BY diversity_raw) AS d_p95
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
    transit_norm = GREATEST(0, LEAST(1,
        1 - ((gc.transit_raw - stats.t_p05) / NULLIF(stats.t_p95 - stats.t_p05, 0))
    )),
    diversity_norm = GREATEST(0, LEAST(1,
        (gc.diversity_raw - stats.d_p05) / NULLIF(stats.d_p95 - stats.d_p05, 0)
    ))
FROM stats;

-- Composite GIUS: equal weighting across all 4 proxies (1/4 each)
UPDATE grid_cells
SET gius = (walkability_norm + services_norm + transit_norm + diversity_norm) / 4.0;

-- Sanity check
SELECT
    district,
    ROUND(AVG(walkability_norm)::numeric, 3) AS avg_walkability_norm,
    ROUND(AVG(services_norm)::numeric, 3) AS avg_services_norm,
    ROUND(AVG(transit_norm)::numeric, 3) AS avg_transit_norm,
    ROUND(AVG(diversity_norm)::numeric, 3) AS avg_diversity_norm,
    ROUND(AVG(gius)::numeric, 3) AS avg_gius
FROM grid_cells
GROUP BY district
ORDER BY avg_gius DESC;
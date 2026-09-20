-- Add proxy columns to grid_cells
ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS walkability_raw double precision;
ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS services_raw double precision;
ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS transit_raw double precision;

-- Ensure our source tables have projected (meters) geometry too
ALTER TABLE roads ADD COLUMN IF NOT EXISTS geom_utm geometry(Geometry, 32640);
UPDATE roads SET geom_utm = ST_Transform(geometry, 32640) WHERE geom_utm IS NULL;

ALTER TABLE pois ADD COLUMN IF NOT EXISTS geom_utm geometry(Geometry, 32640);
UPDATE pois SET geom_utm = ST_Transform(geometry, 32640) WHERE geom_utm IS NULL;

ALTER TABLE transit_stops ADD COLUMN IF NOT EXISTS geom_utm geometry(Geometry, 32640);
UPDATE transit_stops SET geom_utm = ST_Transform(geometry, 32640) WHERE geom_utm IS NULL;

CREATE INDEX IF NOT EXISTS idx_roads_geom_utm ON roads USING GIST (geom_utm);
CREATE INDEX IF NOT EXISTS idx_pois_geom_utm ON pois USING GIST (geom_utm);
CREATE INDEX IF NOT EXISTS idx_transit_geom_utm ON transit_stops USING GIST (geom_utm);

-- 1. Walkability: count of road segments intersecting each cell
-- (a reasonable proxy for street network density / route choice)
UPDATE grid_cells gc
SET walkability_raw = sub.seg_count
FROM (
    SELECT gc2.cell_id, COUNT(r.*) AS seg_count
    FROM grid_cells gc2
    LEFT JOIN roads r ON ST_Intersects(r.geom_utm, gc2.geom_utm)
    GROUP BY gc2.cell_id
) sub
WHERE gc.cell_id = sub.cell_id;

-- 2. Access to services: count of POIs within 400m of each cell's centroid
UPDATE grid_cells gc
SET services_raw = sub.poi_count
FROM (
    SELECT gc2.cell_id, COUNT(p.*) AS poi_count
    FROM grid_cells gc2
    LEFT JOIN pois p ON ST_DWithin(ST_Centroid(gc2.geom_utm), p.geom_utm, 400)
    GROUP BY gc2.cell_id
) sub
WHERE gc.cell_id = sub.cell_id;

-- 3. Transit access: distance (meters) from cell centroid to nearest transit stop
-- Note: we invert this later (closer = better) when normalizing
UPDATE grid_cells gc
SET transit_raw = sub.min_dist
FROM (
    SELECT gc2.cell_id, MIN(ST_Distance(ST_Centroid(gc2.geom_utm), t.geom_utm)) AS min_dist
    FROM grid_cells gc2
    LEFT JOIN transit_stops t ON t.district = gc2.district
    GROUP BY gc2.cell_id
) sub
WHERE gc.cell_id = sub.cell_id;

-- Sanity check: see the range of raw values per district
SELECT
    district,
    ROUND(AVG(walkability_raw)::numeric, 1) AS avg_walkability,
    ROUND(AVG(services_raw)::numeric, 1) AS avg_services,
    ROUND(AVG(transit_raw)::numeric, 1) AS avg_transit_dist_m
FROM grid_cells
GROUP BY district;

-- 4. Trip-chaining proxy: land-use diversity (distinct POI categories within 400m)
ALTER TABLE grid_cells ADD COLUMN IF NOT EXISTS diversity_raw double precision;

ALTER TABLE pois ADD COLUMN IF NOT EXISTS category text;
UPDATE pois SET category = COALESCE(amenity, shop, leisure);

UPDATE grid_cells gc
SET diversity_raw = sub.category_count
FROM (
    SELECT gc2.cell_id, COUNT(DISTINCT p.category) AS category_count
    FROM grid_cells gc2
    LEFT JOIN pois p ON ST_DWithin(ST_Centroid(gc2.geom_utm), p.geom_utm, 400)
    GROUP BY gc2.cell_id
) sub
WHERE gc.cell_id = sub.cell_id;
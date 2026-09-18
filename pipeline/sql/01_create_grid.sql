-- Add a projected (meters-based) geometry column to districts, for accurate spatial math
ALTER TABLE districts ADD COLUMN IF NOT EXISTS geom_utm geometry(Geometry, 32640);
UPDATE districts SET geom_utm = ST_Transform(geometry, 32640);

-- Rebuild grid_cells fresh each time this script runs
DROP TABLE IF EXISTS grid_cells;

CREATE TABLE grid_cells (
    cell_id serial PRIMARY KEY,
    district text,
    geom_utm geometry(Polygon, 32640),
    geom geometry(Polygon, 4326)
);

-- Generate a 250m x 250m grid over each district's bounding box
INSERT INTO grid_cells (district, geom_utm)
SELECT
    d.district,
    g.geom
FROM districts d,
LATERAL ST_SquareGrid(250, d.geom_utm) AS g(geom, i, j)
WHERE ST_Intersects(g.geom, d.geom_utm);

-- Add back a lat/lon version for mapping later
UPDATE grid_cells SET geom = ST_Transform(geom_utm, 4326);

-- Indexes for fast spatial queries later
CREATE INDEX idx_grid_cells_geom_utm ON grid_cells USING GIST (geom_utm);
CREATE INDEX idx_grid_cells_geom ON grid_cells USING GIST (geom);

-- Quick sanity check
SELECT district, COUNT(*) AS num_cells FROM grid_cells GROUP BY district;
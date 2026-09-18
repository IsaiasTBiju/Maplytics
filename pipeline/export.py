import geopandas as gpd
from db import get_engine

engine = get_engine()

# Load the final clustered results
gdf = gpd.read_postgis(
    "SELECT cell_id, district, gius, walkability_norm, services_norm, transit_norm, cluster, geom FROM grid_cells_clustered",
    engine,
    geom_col="geom"
)

# Round scores for cleaner file size / display
for col in ["gius", "walkability_norm", "services_norm", "transit_norm"]:
    gdf[col] = gdf[col].round(3)

# Export to GeoJSON, ready for the frontend
output_path = "../site/data/grid_cells.geojson"
import os
os.makedirs(os.path.dirname(output_path), exist_ok=True)
gdf.to_file(output_path, driver="GeoJSON")

print(f"Exported {len(gdf)} cells to {output_path}")

# Quick file size check
size_kb = os.path.getsize(output_path) / 1024
print(f"File size: {size_kb:.1f} KB")
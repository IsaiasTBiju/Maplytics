import osmnx as ox
import geopandas as gpd

print("osmnx version:", ox.__version__)
print("geopandas version:", gpd.__version__)

# Tiny real test: fetch the boundary polygon for Dubai Marina
gdf = ox.geocode_to_gdf("Dubai Marina, Dubai, UAE")
print(gdf[["display_name", "geometry"]])
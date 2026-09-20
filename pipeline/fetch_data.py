import os
import osmnx as ox
import geopandas as gpd
from shapely.geometry import box
from db import get_engine

# --- Config ---
# Bounding boxes as (west, south, east, north) -- i.e. (min_lon, min_lat, max_lon, max_lat)
# These are hand-set based on known district geography, since not all Dubai
# districts have clean administrative polygons in OSM.

DISTRICTS = {
    "deira": (55.265334, 25.2327936, 55.345334, 25.3127936),
    "dubai_marina": (55.1235844, 25.0642641, 55.1551429, 25.0950402),
    "mirdif": (55.4028121, 25.2056186, 55.4424026, 25.2352206),
}

POI_TAGS = {
    "amenity": [
        "school", "kindergarten", "childcare",
        "clinic", "hospital", "pharmacy",
        "bank",
    ],
    "shop": ["supermarket", "convenience"],
    "leisure": ["park"],
}

TRANSPORT_TAGS = {
    "public_transport": ["stop_position", "platform", "station"],
    "highway": ["bus_stop"],
    "railway": ["station", "stop"],
}

RAW_DIR = "data/raw"


def fetch_district(name, bbox):
    west, south, east, north = bbox
    print(f"\n--- Fetching {name} ---")

    # 1. Boundary (just the bbox itself, as a polygon, for reference/visualization)
    boundary = gpd.GeoDataFrame(
        {"district": [name]},
        geometry=[box(west, south, east, north)],
        crs="EPSG:4326",
    )
    boundary.to_file(f"{RAW_DIR}/{name}_boundary.geojson", driver="GeoJSON")
    print(f"  boundary: bbox saved")

    # osmnx 2.x expects bbox as (west, south, east, north) -- same order we stored it in
    ox_bbox = (west, south, east, north)

    # 2. Road network -> nodes + edges as GeoDataFrames
    graph = ox.graph_from_bbox(bbox=ox_bbox, network_type="walk")
    nodes, edges = ox.graph_to_gdfs(graph)
    edges = edges.reset_index()
    edges["district"] = name
    edges.to_file(f"{RAW_DIR}/{name}_roads.geojson", driver="GeoJSON")
    print(f"  roads: {len(edges)} segments")

    # 3. POIs (services)
    pois = ox.features_from_bbox(bbox=ox_bbox, tags=POI_TAGS)
    pois = pois[pois.geometry.notnull()].copy()
    pois = pois.reset_index()
    pois["district"] = name
    pois.to_file(f"{RAW_DIR}/{name}_pois.geojson", driver="GeoJSON")
    print(f"  POIs: {len(pois)} features")

    # 4. Transit stops
    transit = ox.features_from_bbox(bbox=ox_bbox, tags=TRANSPORT_TAGS)
    transit = transit[transit.geometry.notnull()].copy()
    transit = transit.reset_index()
    transit["district"] = name
    transit.to_file(f"{RAW_DIR}/{name}_transit.geojson", driver="GeoJSON")
    print(f"  transit stops: {len(transit)} features")

    return boundary, edges, pois, transit


def main():
    os.makedirs(RAW_DIR, exist_ok=True)

    engine = get_engine()

    all_boundaries, all_roads, all_pois, all_transit = [], [], [], []

    for name, bbox in DISTRICTS.items():
        boundary, edges, pois, transit = fetch_district(name, bbox)
        all_boundaries.append(boundary)
        all_roads.append(edges)
        all_pois.append(pois)
        all_transit.append(transit)

    # Combine all districts into single layers and push to PostGIS
    print("\n--- Loading into PostGIS ---")

    combined_boundaries = gpd.pd.concat(all_boundaries, ignore_index=True)
    combined_boundaries.to_postgis("districts", engine, if_exists="replace", index=False)
    print("  districts table loaded")

    combined_roads = gpd.pd.concat(all_roads, ignore_index=True)
    combined_roads = combined_roads[["district", "geometry"]].copy()
    combined_roads.to_postgis("roads", engine, if_exists="replace", index=False)
    print("  roads table loaded")

    combined_pois = gpd.pd.concat(all_pois, ignore_index=True)
    # Keep geometry + a few key columns, drop the rest to avoid column-mismatch issues across districts
    keep_cols = [c for c in ["district", "geometry", "amenity", "shop", "leisure", "name"] if c in combined_pois.columns]
    combined_pois = combined_pois[keep_cols].copy()
    combined_pois.to_postgis("pois", engine, if_exists="replace", index=False)
    print("  pois table loaded")

    combined_transit = gpd.pd.concat(all_transit, ignore_index=True)
    keep_cols = [c for c in ["district", "geometry", "public_transport", "highway", "railway", "name"] if c in combined_transit.columns]
    combined_transit = combined_transit[keep_cols].copy()
    combined_transit.to_postgis("transit_stops", engine, if_exists="replace", index=False)
    print("  transit_stops table loaded")

    print("\nDone.")


if __name__ == "__main__":
    main()
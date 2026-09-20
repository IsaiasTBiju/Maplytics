import pandas as pd
import geopandas as gpd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from db import get_engine

engine = get_engine()

# Load grid cells with normalized proxies
gdf = gpd.read_postgis(
    "SELECT cell_id, district, gius, walkability_norm, services_norm, transit_norm, diversity_norm, geom FROM grid_cells",
    engine,
    geom_col="geom"
)

# Features for clustering: the 3 normalized proxies (not the composite GIUS itself)
features = gdf[["walkability_norm", "services_norm", "transit_norm", "diversity_norm"]].copy()

# Standardize (mean 0, std 1) -- good practice for k-means even though our
# features are already 0-1, since it ensures equal influence during clustering
scaler = StandardScaler()
X = scaler.fit_transform(features)

# --- Elbow method: try k = 2 through 8, plot inertia (within-cluster variance) ---
inertias = []
k_range = range(2, 9)
for k in k_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X)
    inertias.append(km.inertia_)

plt.figure(figsize=(8, 5))
plt.plot(list(k_range), inertias, marker="o")
plt.xlabel("Number of clusters (k)")
plt.ylabel("Inertia (within-cluster variance)")
plt.title("Elbow method for choosing k")
plt.savefig("data/elbow_plot.png", dpi=150, bbox_inches="tight")
print("Elbow plot saved to pipeline/data/elbow_plot.png")
print("\nInertia by k:")
for k, inertia in zip(k_range, inertias):
    print(f"  k={k}: {inertia:.1f}")

# --- Final clustering with k=4 ---
K = 4
km = KMeans(n_clusters=K, random_state=42, n_init=10)
gdf["cluster"] = km.fit_predict(X)

# Interpret clusters: average proxy values per cluster
cluster_summary = gdf.groupby("cluster")[["walkability_norm", "services_norm", "transit_norm", "diversity_norm", "gius"]].mean()
cluster_summary["num_cells"] = gdf.groupby("cluster").size()
cluster_summary = cluster_summary.sort_values("gius", ascending=False)

print("\n--- Cluster summary (sorted by avg GIUS) ---")
print(cluster_summary.round(3))

# Cross-tab: which districts fall into which clusters
print("\n--- District x Cluster breakdown ---")
print(pd.crosstab(gdf["district"], gdf["cluster"]))

# Save clustered data back to PostGIS for later export/mapping
gdf_to_save = gdf[["cell_id", "district", "gius", "walkability_norm", "services_norm", "transit_norm", "diversity_norm", "cluster", "geom"]]
gdf_to_save.to_postgis("grid_cells_clustered", engine, if_exists="replace", index=False)
print("\nSaved clustered results to grid_cells_clustered table")
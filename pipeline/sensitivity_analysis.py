import pandas as pd
from scipy.stats import spearmanr
from db import get_engine

engine = get_engine()

gdf = pd.read_sql(
    "SELECT cell_id, district, walkability_norm, services_norm, transit_norm, diversity_norm FROM grid_cells_clustered",
    engine
)

# --- Define weighting schemes to test ---
# Each must sum to 1.0. Order: walkability, services, transit, diversity
SCHEMES = {
    "equal (baseline)":          [0.25, 0.25, 0.25, 0.25],
    "transit-emphasis":          [0.20, 0.20, 0.40, 0.20],
    "services-emphasis":         [0.20, 0.40, 0.20, 0.20],
    "walkability-emphasis":      [0.40, 0.20, 0.20, 0.20],
    "diversity-emphasis":        [0.20, 0.20, 0.20, 0.40],
}

proxy_cols = ["walkability_norm", "services_norm", "transit_norm", "diversity_norm"]

results = {}
for scheme_name, weights in SCHEMES.items():
    gdf[f"gius_{scheme_name}"] = sum(gdf[col] * w for col, w in zip(proxy_cols, weights))
    results[scheme_name] = gdf.groupby("district")[f"gius_{scheme_name}"].mean()

# --- Table 1: district averages under each scheme ---
summary = pd.DataFrame(results).round(3)
print("=== District avg GIUS under different weighting schemes ===")
print(summary)
print()

# --- Table 2: does the RANKING of districts change? ---
print("=== District ranking (best to worst) under each scheme ===")
for scheme_name in SCHEMES:
    ranked = summary[scheme_name].sort_values(ascending=False)
    print(f"{scheme_name}: {' > '.join(ranked.index)}")
print()

# --- Table 3: cell-level rank stability (Spearman correlation vs baseline) ---
print("=== Cell-level rank correlation vs equal-weight baseline (Spearman) ===")
baseline_col = "gius_equal (baseline)"
for scheme_name in SCHEMES:
    if scheme_name == "equal (baseline)":
        continue
    col = f"gius_{scheme_name}"
    corr, _ = spearmanr(gdf[baseline_col], gdf[col])
    print(f"{scheme_name}: rho = {corr:.3f}")

# Save full table for the write-up
summary.to_csv("data/sensitivity_analysis.csv")
print("\nSaved to pipeline/data/sensitivity_analysis.csv")
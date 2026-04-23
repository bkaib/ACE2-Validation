---
name: spatial-statistics
description: "PCA, covariance matrices, composite analysis, and significance testing for spatial impact data. Use when asked to 'run PCA', 'compute covariance', 'find co-varying regions', 'test significance', 'composite analysis', or 'correlate with drivers'. Keywords: PCA, covariance, composite, significance, Monte Carlo, bootstrap, correlation, NAO, ENSO, QBO, detrend, anomalies."
---

# spatial-statistics

Perform spatial statistical analysis on impact data: PCA decomposition, covariance matrices between regions, composite analysis for extreme impacts, driver attribution via correlation, and significance testing.

## When to Use This Skill

- "Run PCA on the CLIMADA impact data."
- "Compute the impact covariance matrix between NH regions."
- "Find atmospheric drivers of the dominant damage modes."
- "Perform composite analysis on the top 10% high-impact seasons."
- "Test significance of PC-score correlations with NAO."

## Workflow

### Step 1 — Preprocess impact data

Before applying PCA, prepare the impact field $I(t, \lambda, \phi)$:

1. **Linearly detrend** at each grid cell to remove long-term trends:

```python
from scipy.signal import detrend
import numpy as np

# impact_data: shape (n_seasons, n_gridcells)
impact_detrended = detrend(impact_data, axis=0, type="linear")
```

2. **Compute seasonal anomalies**: $I' = I - \bar{I}$

```python
climatology = impact_detrended.mean(axis=0)
anomalies = impact_detrended - climatology
```

3. **Optionally log-transform** to reduce skewness: $\tilde{I} = \log(I + 1)$

```python
# Check skewness first
from scipy.stats import skew
s = skew(anomalies, axis=0)
if np.abs(s).mean() > 1.0:
    anomalies = np.log1p(np.maximum(anomalies, 0))
```

### Step 2 — Compute impact-covariance matrix between predefined regions

Define regions and compute pairwise covariance:

| Region | Lat range | Lon range |
|--------|-----------|-----------|
| NE-USA | 35–50°N | 60–80°W |
| W-Europe | 40–60°N | 10°W–20°E |
| E-Asia | 25–45°N | 100–140°E |
| N-Pacific | 30–50°N | 150°E–150°W |

```python
import xarray as xr

# Compute regional mean impact time series
regions = {"NE-USA": {"lat": slice(35, 50), "lon": slice(-80, -60)}, ...}
regional_ts = {name: ds.sel(**bounds).mean(dim=["lat", "lon"]) for name, bounds in regions.items()}

import pandas as pd
df = pd.DataFrame(regional_ts)
cov_matrix = df.cov()
corr_matrix = df.corr()
```

### Step 3 — Apply PCA to impact field

Extract temporal scores $a(t)$ and spatial loadings $e(\lambda, \phi)$:

```python
from sklearn.decomposition import PCA

pca = PCA(n_components=10)
scores = pca.fit_transform(anomalies)  # a(t): shape (n_seasons, n_components)
loadings = pca.components_             # e(λ,φ): shape (n_components, n_gridcells)
explained_variance = pca.explained_variance_ratio_
```

Select the number of retained components using the North criterion or scree plot.

### Step 4 — Extreme-impact composite analysis

Focus on fat-tail events:

1. Select the **top 10%** high-impact seasons (based on total seasonal impact).
2. Recompute PCA on the **trimmed covariance matrix** using only these extreme seasons.
3. Compare extreme-composite loadings with full-sample loadings.

```python
threshold = np.percentile(anomalies.sum(axis=1), 90)
extreme_mask = anomalies.sum(axis=1) >= threshold
anomalies_extreme = anomalies[extreme_mask]

pca_extreme = PCA(n_components=5)
scores_extreme = pca_extreme.fit_transform(anomalies_extreme)
```

### Step 5 — Driver attribution

Correlate PC scores $a(t)$ with predictor fields $X(t, \lambda, \phi)$:

```python
from scipy.stats import pearsonr

# For climate indices (NAO, ENSO, QBO)
for idx_name, idx_ts in climate_indices.items():
    for pc in range(n_components):
        r, p = pearsonr(scores[:, pc], idx_ts)
        print(f"PC{pc+1} vs {idx_name}: r={r:.3f}, p={p:.4f}")
```

For spatial predictor fields, compute correlation maps:

```python
corr_map = xr.corr(pc_score_da, predictor_field, dim="time")
```

### Step 6 — Significance testing

Apply Monte Carlo permutation or bootstrap testing:

```python
n_permutations = 1000
rng = np.random.default_rng(seed=42)  # Fixed seed for reproducibility

null_distribution = np.zeros(n_permutations)
for i in range(n_permutations):
    shuffled = rng.permutation(scores[:, 0])
    null_distribution[i], _ = pearsonr(shuffled, idx_ts)

p_value = (np.abs(null_distribution) >= np.abs(r_observed)).mean()
```

Report significance at the 5% level with Bonferroni or FDR correction for multiple comparisons.

## Output Artifacts

- PCA scores and loadings (saved as NetCDF or Zarr in `results/`).
- Covariance and correlation matrices (saved as CSV in `results/tables/`).
- Significance test results with p-values.

## References

- Methods draft: `milestones/methods_draft.md` (steps 2–6)
- Path helper: `config/paths.py`
- scikit-learn PCA: https://scikit-learn.org/stable/modules/decomposition.html#pca

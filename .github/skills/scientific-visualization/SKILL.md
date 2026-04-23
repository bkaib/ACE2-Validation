---
name: scientific-visualization
description: "Create publication-quality figures with provenance metadata using matplotlib and cartopy. Use when asked to 'plot PCA loadings', 'create a correlation map', 'generate paper figures', 'visualize covariance matrix', or 'make a time series plot'. Keywords: matplotlib, cartopy, figures, publication, PCA map, correlation, heatmap, time series, provenance, DPI."
---

# scientific-visualization

Create publication-quality scientific figures with provenance metadata. Covers spatial maps, time series, heatmaps, and composite plots for the SYNCDSTRMDMG analysis pipeline.

## When to Use This Skill

- "Plot the PCA spatial loadings on a map."
- "Create a covariance heatmap between NH regions."
- "Generate time series plots of PC scores."
- "Make publication figures for the paper."
- "Visualize the correlation map between PC1 and NAO."

## Workflow

### Step 1 — Set up figure with journal-ready defaults

```python
import matplotlib.pyplot as plt
import matplotlib as mpl

# Journal-ready defaults
plt.rcParams.update({
    "font.size": 10,
    "font.family": "sans-serif",
    "axes.labelsize": 11,
    "axes.titlesize": 12,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "legend.fontsize": 9,
    "figure.dpi": 300,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})
```

### Step 2 — Plot spatial maps (PCA loadings, correlation maps)

```python
import cartopy.crs as ccrs
import cartopy.feature as cfeature

fig, ax = plt.subplots(
    subplot_kw={"projection": ccrs.PlateCarree()},
    figsize=(10, 5),
)
ax.set_extent([-180, 180, 0, 90], crs=ccrs.PlateCarree())
ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")

# Plot PCA loadings
im = ax.pcolormesh(
    lon, lat, loadings_2d,
    cmap="RdBu_r", vmin=-vmax, vmax=vmax,
    transform=ccrs.PlateCarree(),
)
plt.colorbar(im, ax=ax, label="Loading", shrink=0.7)
ax.set_title("PC1 Spatial Loadings — Explained Variance: XX%")
```

### Step 3 — Plot time series (PC scores, seasonal indices)

```python
fig, ax = plt.subplots(figsize=(10, 3))
ax.bar(years, scores[:, 0], color="steelblue", width=0.8, alpha=0.8)
ax.axhline(0, color="k", linewidth=0.5)
ax.set_xlabel("Season (ONDJFM)")
ax.set_ylabel("PC1 Score")
ax.set_title("PC1 Time Series")
```

### Step 4 — Add provenance annotation

```python
import subprocess
from datetime import datetime
from config.paths import FIGURES

commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
provenance = f"Data: climada_impacts.zarr | Commit: {commit} | {datetime.now():%Y-%m-%d}"

fig.text(0.01, 0.01, provenance, fontsize=6, color="gray", transform=fig.transFigure)

# Also save as PNG metadata
fig.savefig(
    FIGURES / "pca_loadings_pc1.pdf",
    metadata={"Creator": "SYNCDSTRMDMG", "Source": provenance},
)
```

### Step 5 — Save to results/figures/ via config.paths

```python
from config.paths import FIGURES

# PDF for paper submission
fig.savefig(FIGURES / "figure_name.pdf")

# PNG for presentations and quick viewing
fig.savefig(FIGURES / "figure_name.png", dpi=300)

plt.close(fig)
```

## Figure Format Guidelines

| Purpose | Format | DPI | Notes |
|---------|--------|-----|-------|
| Journal paper | PDF | vector | Preferred for publication |
| Presentations | PNG | 300 | Use for slides and quick sharing |
| Supplementary | PNG | 150 | Lower DPI acceptable |
| Web/README | PNG | 72–150 | Optimized for file size |

## Accessible Color Palettes

- Use `cmc.batlow` (perceptually uniform) as default sequential colormap.
- Use `RdBu_r` for diverging data (anomalies, correlations).
- Avoid red-green combinations for colorblind accessibility.
- Add contour lines to maps for additional visual encoding.

## Output Artifacts

- PDF and/or PNG figures in `results/figures/` (via `config.paths.FIGURES`).
- Provenance metadata embedded in figure files.

## References

- Path helper: `config/paths.py` → `FIGURES`
- cmcrameri colormaps: https://www.fabiocrameri.ch/colourmaps/
- Cartopy docs: https://scitools.org.uk/cartopy/

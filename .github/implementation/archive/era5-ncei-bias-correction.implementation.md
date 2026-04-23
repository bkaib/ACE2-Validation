# Implementation: era5-ncei-bias-correction

**Source plan**: `.github/plans/era5-ncei-bias-correction.plan.md`
**Generated**: 2026-04-10
**Branch**: `feature/era5-ncei-bias-correction`

**Steps generated**: 7
**Total tasks**: 24 checkboxes
**New dependencies**: none (scipy, cartopy, matplotlib already in environment)
**Files created**: 1 (`notebooks/era5_ncei_bias_correction.ipynb`)
**Files modified**: 2 (`config/paths.py`, `utils/data_loader.py`)

---

## Step 1 — Add percentile Zarr paths to `config/paths.py`

> Add `NCEI_P95_MS`, `NCEI_P98_MS`, `ERA5_P95`, `ERA5_P98` as named `Path` constants.

### 1.1 — Append four constants to `config/paths.py`

- [x] **Implementation**

**Edit file**: `config/paths.py`

After the line `PROCESSED_DATA = ROOT / "data/processed"`, insert:

```python
# Percentile Zarr stores (ONDJFM monthly, 1990–2024)
NCEI_P95_MS = PROCESSED_DATA / "ncei_percentiles_ondjfm_p95_ms.zarr"
NCEI_P98_MS = PROCESSED_DATA / "ncei_percentiles_ondjfm_p98_ms.zarr"
ERA5_P95    = PROCESSED_DATA / "era5_percentiles_ondjfm_p95.zarr"
ERA5_P98    = PROCESSED_DATA / "era5_percentiles_ondjfm_p98.zarr"
```

Also add them to the verification block in `if __name__ == "__main__":`:

```python
    for name, p in [("NCEI_P95_MS", NCEI_P95_MS), ("NCEI_P98_MS", NCEI_P98_MS),
                     ("ERA5_P95", ERA5_P95), ("ERA5_P98", ERA5_P98)]:
        print(f"{name}: {'Valid' if p.exists() else 'MISSING'}")
```

### 1.2 — Verify via `python config/paths.py`

- [ ] **Run verification**

```bash
conda run -n datascience python config/paths.py
```

Expected: All four new path names print "Valid".

---

## Step 2 — Add `extract_era5_at_stations()` to `utils/data_loader.py`

> Nearest-neighbour colocation of ERA5 grid onto NCEI station positions.

### 2.1–2.4 — Add function

- [ ] **Implementation**
 - [x] **Implementation**

**Edit file**: `utils/data_loader.py`

Add `import pandas as pd` to the top-level imports.

Append at the end of the file (before the closing `# endregion` or at EOF):

```python
def extract_era5_at_stations(
    ds_era5: "xr.Dataset",
    station_meta: "pd.DataFrame",
    era5_var: str = "10fg",
) -> "xr.DataArray":
    """Extract ERA5 grid values at NCEI station locations via nearest-neighbour.

    Parameters
    ----------
    ds_era5 : xr.Dataset
        ERA5 percentile dataset with dims (time, lat, lon).
        Longitude must be in 0–360 convention.
    station_meta : pd.DataFrame
        DataFrame with columns 'station', 'latitude', 'longitude'.
        Longitude in -180–180 convention (will be converted internally).
    era5_var : str
        Name of the ERA5 variable to extract (default '10fg').

    Returns
    -------
    xr.DataArray
        Shape (time, station) with ERA5 values at each station location.
    """
    results = []
    for _, row in station_meta.iterrows():
        lat_i = row["latitude"]
        lon_i = row["longitude"]
        # Normalise longitude from -180..180 to 0..360
        lon_360 = lon_i % 360
        val = ds_era5[era5_var].sel(lat=lat_i, lon=lon_360, method="nearest")
        val = val.assign_coords(station=str(row["station"]))
        results.append(val)

    da = xr.concat(results, dim="station")
    logging.info(
        f"Extracted ERA5 '{era5_var}' at {len(station_meta)} stations -> shape {da.shape}"
    )
    return da
```

### Step 2 — Verification

- [ ] **Run verification**

```bash
conda run -n datascience python -c "
import sys; sys.path.insert(0, '.')
import xarray as xr, pandas as pd
from config import paths
from utils.data_loader import extract_era5_at_stations
ds_era5 = xr.open_zarr(paths.ERA5_P95)
meta = pd.read_csv(paths.TABLES / 'ncei_station_meta.csv')
da = extract_era5_at_stations(ds_era5, meta)
assert da.shape == (210, 131), f'Unexpected shape: {da.shape}'
assert da.isnull().all('time').sum() == 0, 'Some stations are all-NaN'
print('OK: shape', da.shape, '-- no all-NaN stations')
"
```

Expected: `OK: shape (210, 131) -- no all-NaN stations`

---

## Step 3 — Scaffold comparison notebook

> Create `notebooks/era5_ncei_bias_correction.ipynb` with setup, imports, data loading,
> pooled scatterplot, per-station α computation, and diagnostic figures.

### 3.1–3.4 — Create notebook

- [x] **Implementation**

**Create file**: `notebooks/era5_ncei_bias_correction.ipynb`

Full notebook content (JSON) — see the companion Python script below that generates it.

**Create file**: `notebooks/_create_era5_ncei_bias_correction_notebook.py`

```python
"""Generate the ERA5–NCEI bias-correction notebook programmatically."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata["kernelspec"] = {
    "display_name": "datascience",
    "language": "python",
    "name": "python3",
}

cells = []

# ── Markdown: title ──────────────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell(
    "# ERA5–NCEI Percentile Comparison & Bias-Correction α\n"
    "\n"
    "**Purpose**: Compare monthly ONDJFM 95th-percentile wind-gust values from\n"
    "131 NCEI stations against their nearest ERA5 grid cell.  Assess linearity\n"
    "and compute per-station rescaling factor α = P_NCEI / P_ERA5.\n"
    "\n"
    "**Datasets**:\n"
    "- NCEI: `data/processed/ncei_percentiles_ondjfm_p95_ms.zarr` — (time=210, station=131), GUST in m/s\n"
    "- ERA5: `data/processed/era5_percentiles_ondjfm_p95.zarr` — (time=210, lat=721, lon=1440), 10fg in m/s\n"
    "- Station metadata: `results/tables/ncei_station_meta.csv`\n"
    "\n"
    "**Period**: ONDJFM 1990–2024 (210 monthly time steps)  \n"
    "**Quantile**: 0.95"
))

# ── Code: imports ────────────────────────────────────────────────
cells.append(nbf.v4.new_code_cell(
    'import sys\n'
    'sys.path.insert(0, "..")\n'
    '\n'
    'import numpy as np\n'
    'import pandas as pd\n'
    'import xarray as xr\n'
    'import matplotlib.pyplot as plt\n'
    'from scipy import stats\n'
    'import cartopy.crs as ccrs\n'
    'import cartopy.feature as cfeature\n'
    '\n'
    'from config import paths\n'
    'from utils.data_loader import extract_era5_at_stations'
))

# ── Code: data loading ──────────────────────────────────────────
cells.append(nbf.v4.new_code_cell(
    '# Load datasets\n'
    'ds_ncei = xr.open_zarr(paths.NCEI_P95_MS)\n'
    'ds_era5 = xr.open_zarr(paths.ERA5_P95)\n'
    'station_meta = pd.read_csv(paths.TABLES / "ncei_station_meta.csv")\n'
    '\n'
    'print("NCEI:", ds_ncei.dims)\n'
    'print("ERA5:", ds_era5.dims)\n'
    'print("Stations:", len(station_meta))'
))

# ── Code: extract ERA5 at stations ──────────────────────────────
cells.append(nbf.v4.new_code_cell(
    '# Extract ERA5 at station locations\n'
    'era5_at_stations = extract_era5_at_stations(ds_era5, station_meta)\n'
    'ncei_gust = ds_ncei["GUST"]\n'
    '\n'
    'print("ERA5 at stations:", era5_at_stations.shape)\n'
    'print("NCEI GUST:       ", ncei_gust.shape)'
))

# ── Markdown: scatterplot header ─────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("---\n## 1. Pooled Scatterplot"))

# ── Code: flatten + valid pairs ──────────────────────────────────
cells.append(nbf.v4.new_code_cell(
    '# Flatten to 1-D and drop NaN pairs\n'
    'era5_flat = era5_at_stations.values.ravel()\n'
    'ncei_flat = ncei_gust.values.ravel()\n'
    '\n'
    'mask = np.isfinite(era5_flat) & np.isfinite(ncei_flat)\n'
    'x = era5_flat[mask]\n'
    'y = ncei_flat[mask]\n'
    'print(f"Valid pairs: {mask.sum():,} / {len(mask):,}")'
))

# ── Code: OLS ────────────────────────────────────────────────────
cells.append(nbf.v4.new_code_cell(
    '# OLS fit\n'
    'slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)\n'
    'r2 = r_value ** 2\n'
    'print(f"OLS: y = {slope:.3f}x + {intercept:.3f}")\n'
    'print(f"R² = {r2:.4f}, p = {p_value:.2e}, n = {len(x):,}")'
))

# ── Code: hexbin scatterplot ─────────────────────────────────────
cells.append(nbf.v4.new_code_cell(
    'fig, ax = plt.subplots(figsize=(7, 7), dpi=150)\n'
    '\n'
    '# Hexbin scatter\n'
    'hb = ax.hexbin(x, y, gridsize=60, cmap="viridis", mincnt=1)\n'
    'cb = fig.colorbar(hb, ax=ax, label="Count")\n'
    '\n'
    '# 1:1 line\n'
    'lims = [min(x.min(), y.min()), max(x.max(), y.max())]\n'
    'ax.plot(lims, lims, "k--", lw=1, label="1:1")\n'
    '\n'
    '# OLS line\n'
    'x_fit = np.linspace(lims[0], lims[1], 100)\n'
    'ax.plot(x_fit, slope * x_fit + intercept, "r-", lw=1.5,\n'
    '        label=f"OLS: y={slope:.2f}x+{intercept:.2f}  R²={r2:.3f}")\n'
    '\n'
    'ax.set_xlabel("ERA5 p95 wind gust (m/s)")\n'
    'ax.set_ylabel("NCEI p95 wind gust (m/s)")\n'
    'ax.set_title("ERA5 vs NCEI — Monthly 95th-Percentile Wind Gust (ONDJFM 1990–2024)")\n'
    'ax.legend(loc="upper left")\n'
    'ax.set_aspect("equal")\n'
    '\n'
    'fig.tight_layout()\n'
    'fig.savefig(paths.FIGURES / "era5_ncei_p95_scatter.png", dpi=300, bbox_inches="tight")\n'
    'print(f"Saved -> {paths.FIGURES / \'era5_ncei_p95_scatter.png\'}")\n'
    'plt.show()'
))

# ── Markdown: interpretation placeholder ─────────────────────────
cells.append(nbf.v4.new_markdown_cell("**Interpretation**: *(fill after running)*"))

# ── Markdown: alpha header ───────────────────────────────────────
cells.append(nbf.v4.new_markdown_cell("---\n## 2. Per-Station α Computation"))

# ── Code: per-station alpha loop ─────────────────────────────────
cells.append(nbf.v4.new_code_cell(
    'records = []\n'
    'for i, row in station_meta.iterrows():\n'
    '    sid = str(row["station"])\n'
    '    lat_i = row["latitude"]\n'
    '    lon_i = row["longitude"]\n'
    '\n'
    '    e = era5_at_stations.sel(station=sid).values\n'
    '    n = ncei_gust.sel(station=sid).values\n'
    '\n'
    '    valid = np.isfinite(e) & np.isfinite(n)\n'
    '    n_valid = int(valid.sum())\n'
    '\n'
    '    if n_valid < 10:\n'
    '        records.append(dict(\n'
    '            station=sid, latitude=lat_i, longitude=lon_i,\n'
    '            alpha=np.nan, slope=np.nan, intercept=np.nan,\n'
    '            r2=np.nan, n_valid=n_valid, qm_flag=True,\n'
    '        ))\n'
    '        continue\n'
    '\n'
    '    ev, nv = e[valid], n[valid]\n'
    '    sl, ic, rv, pv, se = stats.linregress(ev, nv)\n'
    '    r2_i = rv ** 2\n'
    '\n'
    '    # Robust alpha: median ratio (exclude near-zero ERA5 values)\n'
    '    ratio_mask = ev > 0.5  # avoid division by near-zero\n'
    '    alpha_i = float(np.median(nv[ratio_mask] / ev[ratio_mask])) if ratio_mask.sum() > 5 else np.nan\n'
    '\n'
    '    records.append(dict(\n'
    '        station=sid, latitude=lat_i, longitude=lon_i,\n'
    '        alpha=alpha_i, slope=sl, intercept=ic,\n'
    '        r2=r2_i, n_valid=n_valid, qm_flag=(r2_i < 0.5),\n'
    '    ))\n'
    '\n'
    'df_alpha = pd.DataFrame(records)\n'
    'print(f"Stations: {len(df_alpha)}")\n'
    'print(f"QM-flagged (R²<0.5): {df_alpha[\'qm_flag\'].sum()}")\n'
    'print(f"Alpha range: {df_alpha[\'alpha\'].min():.3f} – {df_alpha[\'alpha\'].max():.3f}")\n'
    'print(f"Alpha median: {df_alpha[\'alpha\'].median():.3f}")\n'
    'df_alpha.head(10)'
))

# ── Code: save CSV ───────────────────────────────────────────────
cells.append(nbf.v4.new_code_cell(
    '# Save to CSV with provenance header\n'
    'out_csv = paths.TABLES / "bias_alpha_p95.csv"\n'
    'with open(out_csv, "w") as f:\n'
    '    f.write("# Bias-correction alpha for ERA5 vs NCEI p95 wind gust (ONDJFM 1990-2024)\\n")\n'
    '    f.write("# Generated: 2026-04-10\\n")\n'
    '    f.write(f"# ERA5 source: {paths.ERA5_P95}\\n")\n'
    '    f.write(f"# NCEI source: {paths.NCEI_P95_MS}\\n")\n'
    '    f.write("# alpha = median(P_NCEI / P_ERA5), excluding ERA5 < 0.5 m/s\\n")\n'
    '    df_alpha.to_csv(f, index=False)\n'
    '\n'
    'print(f"Saved -> {out_csv}")'
))

# ── Markdown: diagnostic figures header ──────────────────────────
cells.append(nbf.v4.new_markdown_cell("---\n## 3. Diagnostic Figures"))

# ── Code: alpha histogram ────────────────────────────────────────
cells.append(nbf.v4.new_code_cell(
    '# 3a — Alpha histogram\n'
    'fig, ax = plt.subplots(figsize=(7, 4), dpi=150)\n'
    'ax.hist(df_alpha["alpha"].dropna(), bins=30, edgecolor="k", alpha=0.7)\n'
    'med = df_alpha["alpha"].median()\n'
    'ax.axvline(med, color="r", ls="--", lw=1.5, label=f"median = {med:.2f}")\n'
    'ax.axvline(1.0, color="k", ls=":", lw=1, label="α = 1 (no bias)")\n'
    'ax.set_xlabel("α  (P_NCEI / P_ERA5)")\n'
    'ax.set_ylabel("Count")\n'
    'ax.set_title("Distribution of per-station bias-correction α (p95)")\n'
    'ax.legend()\n'
    'fig.tight_layout()\n'
    'plt.show()'
))

# ── Code: alpha spatial map ──────────────────────────────────────
cells.append(nbf.v4.new_code_cell(
    '# 3b — Alpha spatial map\n'
    'fig = plt.figure(figsize=(12, 6), dpi=150)\n'
    'ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())\n'
    'ax.set_extent([-180, 180, 20, 80], crs=ccrs.PlateCarree())\n'
    'ax.add_feature(cfeature.COASTLINE, linewidth=0.5)\n'
    'ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle=":")\n'
    '\n'
    'sc = ax.scatter(\n'
    '    df_alpha["longitude"], df_alpha["latitude"],\n'
    '    c=df_alpha["alpha"], cmap="RdBu_r", vmin=0.5, vmax=1.5,\n'
    '    edgecolors="k", linewidths=0.3, s=40,\n'
    '    transform=ccrs.PlateCarree(),\n'
    ')\n'
    'cb = fig.colorbar(sc, ax=ax, shrink=0.7, label="α")\n'
    'ax.set_title("Per-station α = P_NCEI / P_ERA5  (p95 ONDJFM 1990–2024)")\n'
    'fig.tight_layout()\n'
    'fig.savefig(paths.FIGURES / "alpha_map_p95.png", dpi=300, bbox_inches="tight")\n'
    'print(f"Saved -> {paths.FIGURES / \'alpha_map_p95.png\'}")\n'
    'plt.show()'
))

# ── Code: R² spatial map ─────────────────────────────────────────
cells.append(nbf.v4.new_code_cell(
    '# 3c — R² spatial map\n'
    'fig = plt.figure(figsize=(12, 6), dpi=150)\n'
    'ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())\n'
    'ax.set_extent([-180, 180, 20, 80], crs=ccrs.PlateCarree())\n'
    'ax.add_feature(cfeature.COASTLINE, linewidth=0.5)\n'
    'ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle=":")\n'
    '\n'
    '# Good stations\n'
    'good = df_alpha[~df_alpha["qm_flag"]]\n'
    'flagged = df_alpha[df_alpha["qm_flag"]]\n'
    '\n'
    'sc = ax.scatter(\n'
    '    good["longitude"], good["latitude"],\n'
    '    c=good["r2"], cmap="YlGn", vmin=0, vmax=1,\n'
    '    edgecolors="k", linewidths=0.3, s=40, marker="o",\n'
    '    transform=ccrs.PlateCarree(), label="OK",\n'
    ')\n'
    'ax.scatter(\n'
    '    flagged["longitude"], flagged["latitude"],\n'
    '    c=flagged["r2"], cmap="YlGn", vmin=0, vmax=1,\n'
    '    edgecolors="red", linewidths=1.2, s=60, marker="x",\n'
    '    transform=ccrs.PlateCarree(), label=f"QM-flagged (n={len(flagged)})",\n'
    ')\n'
    'cb = fig.colorbar(sc, ax=ax, shrink=0.7, label="R²")\n'
    'ax.legend(loc="lower left")\n'
    'ax.set_title("Per-station R² of ERA5 vs NCEI  (p95 ONDJFM 1990–2024)")\n'
    'fig.tight_layout()\n'
    'fig.savefig(paths.FIGURES / "r2_map_p95.png", dpi=300, bbox_inches="tight")\n'
    'print(f"Saved -> {paths.FIGURES / \'r2_map_p95.png\'}")\n'
    'plt.show()'
))

# ── Markdown: spatial patterns placeholder ───────────────────────
cells.append(nbf.v4.new_markdown_cell("**Spatial patterns summary**: *(fill after running)*"))

nb.cells = cells

out = "../notebooks/era5_ncei_bias_correction.ipynb"
nbf.write(nb, out)
print(f"Wrote {out}")
```

### Step 3 — Verification

- [ ] **Run verification**

```bash
cd notebooks && conda run -n datascience python _create_era5_ncei_bias_correction_notebook.py && cd ..
```

Then open the notebook in VS Code / JupyterLab and run cells 1–3 (imports + data loading).

Expected: Cell outputs show `NCEI: Frozen({'time': 210, 'station': 131})`,
`ERA5: Frozen({'time': 210, 'lat': 721, 'lon': 1440})`, `ERA5 at stations: (210, 131)`.

---

## Step 4 — Pooled scatterplot

> Already implemented inside notebook cells 5–8 (markdown + flatten + OLS + hexbin plot).

### 4.1–4.6 — All implemented in Step 3 notebook creation

- [x] **Verification**: Run cells 5–8 in the notebook.

Expected: Hexbin scatterplot renders with 1:1 and OLS lines. Figure saved to
`results/figures/era5_ncei_p95_scatter.png`. R² printed in cell output.

---

## Step 5 — Per-station α and CSV

> Already implemented in notebook cells 10–11 (loop + CSV save).

### 5.1–5.4 — All implemented in Step 3 notebook creation

- [x] **Verification**: Run cells 10–11.

Expected: 131 rows printed, α range and median shown, CSV saved to
`results/tables/bias_alpha_p95.csv`.

```bash
head -10 results/tables/bias_alpha_p95.csv
wc -l results/tables/bias_alpha_p95.csv
```

Expected: 137 lines (5 comment lines + 1 header + 131 data rows).

---

## Step 6 — Diagnostic figures

> Already implemented in notebook cells 13–15 (histogram + α map + R² map).

### 6.1–6.4 — All implemented in Step 3 notebook creation

- [x] **Verification**: Run cells 13–15.

Expected:
- α histogram with median and α=1 reference lines.
- `results/figures/alpha_map_p95.png` — NH map with diverging color (centred on 1.0).
- `results/figures/r2_map_p95.png` — NH map with R² colouring; QM-flagged stations in red ×.

---

## Step 7 — Update milestone & TODOs

### 7.1 — Mark TODOs complete in `data-engineer.todo.md`

- [x] **Implementation**

**Edit file**: `.github/todos/data-engineer.todo.md`

Replace the Active section:

```markdown
## Active

- [ ] **[HIGH]** Scatterplot of NCEI vs ERA5 percentiles for each station/grid-cell pair
- [ ] **[HIGH]** Compute the scaling factor $\alpha$ for each station/grid-cell pair if the scatterplot is a line
- [ ] **[HIGH]** Rescale the ERA5 wind gust data with $\alpha$ and compute the calibrated percentiles to use as impact thresholds if the scatterplot is a line
```

With:

```markdown
## Active

- [ ] **[HIGH]** Rescale the ERA5 wind gust data with $\alpha$ and compute the calibrated percentiles to use as impact thresholds if the scatterplot is a line
```

And add to the Completed section:

```markdown
- [x] ~~**[HIGH]** Scatterplot of NCEI vs ERA5 percentiles for each station/grid-cell pair~~ — completed: YYYY-MM-DD — commit: {SHA}
- [x] ~~**[HIGH]** Compute the scaling factor α for each station/grid-cell pair if the scatterplot is a line~~ — completed: YYYY-MM-DD — commit: {SHA}
```

*(Replace YYYY-MM-DD and {SHA} with actual values at commit time.)*

### 7.2 — Add processing log entry to `milestones/01-generating-impact-data/era5-calibration.md`

- [x] **Implementation**

**Edit file**: `milestones/01-generating-impact-data/era5-calibration.md`

Insert at the **top** of the `# Processing Log` section:

```markdown
## YYYY-MM-DD — ERA5–NCEI percentile comparison and bias-correction α

- **Agent**: data-engineer
- **Task**: Compared monthly ONDJFM p95 wind-gust percentiles from ERA5 (nearest grid cell) and 131 NCEI stations via scatterplot. Computed per-station rescaling factor α = median(P_NCEI / P_ERA5).
- **Inputs**: `data/processed/era5_percentiles_ondjfm_p95.zarr`, `data/processed/ncei_percentiles_ondjfm_p95_ms.zarr`, `results/tables/ncei_station_meta.csv`.
- **Parameters**: quantile=0.95, period=ONDJFM 1990–2024, nearest-neighbour colocation, ERA5 lon normalised 0–360, min ERA5 threshold for ratio=0.5 m/s, QM flag threshold R²<0.5.
- **Method**: xr.sel(method='nearest') for station–grid colocation; scipy.stats.linregress for OLS; median ratio for robust α.
- **Outputs**: `results/figures/era5_ncei_p95_scatter.png`, `results/figures/alpha_map_p95.png`, `results/figures/r2_map_p95.png`, `results/tables/bias_alpha_p95.csv`.
- **Validation**: Pooled R² reported; per-station α range and QM-flag count checked; figures visually inspected.
- **Scripts**: `notebooks/era5_ncei_bias_correction.ipynb`, `utils/data_loader.py::extract_era5_at_stations`
- **Commit**: `{SHA}`
```

Also update `# Summary` by appending:

```markdown
- Compared ERA5 and NCEI p95 percentiles at 131 stations; computed per-station bias-correction α and diagnostic maps.
```

And mark the scatterplot task in `# Open Tasks`:

```markdown
- [x] For each NCEI station choose closest ERA5 grid-cell to that station and
     - [x] Scatter plot these pairs of percentiles
```

### 7.3 — Update `global.todos.md`

- [ ] **Implementation**

No change needed — milestone `generating-impact-data` is already `🟡 In progress`.
Progress continues with the rescaling step.

### Step 7 — Verification

- [ ] **Run verification**

```bash
grep -c "completed:" .github/todos/data-engineer.todo.md
grep "Scatter plot" milestones/01-generating-impact-data/era5-calibration.md
```

Expected: Completed count increases by 2; scatterplot task shows `[x]`.

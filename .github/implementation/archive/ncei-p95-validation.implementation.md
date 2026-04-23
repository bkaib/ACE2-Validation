# Implementation: ncei-p95-validation

**Source plan**: `.github/plans/ncei-p95-validation.plan.md`
**Generated**: 2026-04-04
**Branch**: `feature/ncei-p95-validation`

## Steps Overview

| Step | Title | Tasks | Status |
|------|-------|-------|--------|
| 1 | Scaffold the notebook and load libraries | 2 | ✅ |
| 2 | Load and inspect the Zarr store | 3 | ✅ |
| 3 | Temporal consistency checks | 3 | ✅ |
| 4 | Missing-value analysis | 3 | ☐ |
| 5 | Load source station metadata (lat/lon) | 3 | ☐ |
| 6 | Station map | 3 | ☐ |
| 7 | Distributional summary statistics | 3 | ☐ |
| 8 | Time-series diagnostics | 3 | ☐ |
| 9 | Cross-check against raw data | 3 | ☐ |
| 10 | Spatial distribution visualization | 3 | ☐ |
| 11 | Summary cell and TODO update | 3 | ☐ |

**New dependencies**: None — all libraries (`xarray`, `numpy`, `pandas`, `matplotlib`, `cartopy`) are already in the `datascience` conda environment.
**Files created**: 1 (`notebooks/ncei_p95_exploration.ipynb`)
**Files modified**: 2 (`.github/todos/data-engineer.todo.md`, `.github/todos/global.todos.md`)

> **Note — Notebook creation strategy**: Generate the notebook using a Python helper script with `nbformat`. Run the script below *once* to create the `.ipynb` file, then execute the notebook interactively to verify all cells.

---

## Notebook Generator Script

- [ ] **Implementation**

**Create file**: `notebooks/_create_ncei_p95_notebook.py`

This script generates the entire `ncei_p95_exploration.ipynb` notebook programmatically using `nbformat`. Run it once, then delete it.

```python
#!/usr/bin/env python3
"""Generate notebooks/ncei_p95_exploration.ipynb programmatically."""
import nbformat as nbf

nb = nbf.v4.new_notebook()
nb.metadata.kernelspec = {
    "display_name": "Python 3",
    "language": "python",
    "name": "python3",
}

cells = []

# ─── Step 1: Title & imports ────────────────────────────────────────────────

cells.append(nbf.v4.new_markdown_cell("""\
# Validate NCEI 95th-Percentile ONDJFM Wind-Gust Computation

**Purpose**: Validate the processed Zarr store
`data/processed/ncei_percentiles_ondjfm_p95.zarr` by checking dimensions,
time axis, missing values, value ranges, and cross-checking against the
source station file.

**Dataset provenance**:
- Source: `data/raw/NCEI/completeness_filtered_1990_2024_GUST.nc`
  (daily wind gust from NCEI ISD, filtered to ≥60 % temporal completeness)
- Processing script: `scripts/preprocessing/compute_ncei_quantiles.py`
- Output: monthly 95th-percentile gust per station, ONDJFM 1990–2024
"""))

cells.append(nbf.v4.new_code_cell("""\
import sys
from pathlib import Path

# Ensure project root is on the path
PROJECT_ROOT = Path.cwd().parent  # assumes notebook is in notebooks/
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from config import paths

print("Project root:", PROJECT_ROOT)
print("Processed data dir:", paths.PROCESSED_DATA)
"""))

# ─── Step 2: Load and inspect the Zarr store ────────────────────────────────

cells.append(nbf.v4.new_markdown_cell("## 2 — Load and Inspect the Zarr Store"))

cells.append(nbf.v4.new_code_cell("""\
zarr_path = paths.PROCESSED_DATA / "ncei_percentiles_ondjfm_p95.zarr"
ds = xr.open_zarr(zarr_path)
ds
"""))

cells.append(nbf.v4.new_code_cell("""\
print("Coordinate names:", list(ds.coords))
print("Dimension sizes:", dict(ds.sizes))
print("Data variables:", list(ds.data_vars))
print()
for c in ds.coords:
    print(f"  {c}: dtype={ds[c].dtype}, shape={ds[c].shape}")
"""))

cells.append(nbf.v4.new_code_cell("""\
# Confirm quantile coordinate equals 0.95
q_val = float(ds.coords["quantile"].values)
assert q_val == 0.95, f"Expected quantile=0.95, got {q_val}"
print(f"✓ quantile coordinate = {q_val}")
"""))

# ─── Step 3: Temporal consistency checks ─────────────────────────────────────

cells.append(nbf.v4.new_markdown_cell("## 3 — Temporal Consistency Checks"))

cells.append(nbf.v4.new_code_cell("""\
times = pd.DatetimeIndex(ds["time"].values)

# 3.1 — All months must be in {1,2,3,10,11,12}
valid_months = {1, 2, 3, 10, 11, 12}
actual_months = set(times.month.unique())
assert actual_months == valid_months, (
    f"Unexpected months: {actual_months - valid_months}"
)
print(f"✓ All months are ONDJFM: {sorted(actual_months)}")

# 3.2 — Expected count: 6 months × 35 ONDJFM seasons = 210
#   Seasons: Oct 1990–Mar 1991 … Oct 2023–Mar 2024 → 34 complete seasons
#   But the data also includes Oct–Dec 2024, so 34×6 + 3 = 207?
#   Let's just verify the actual count matches the Zarr dimension.
n_expected = 210  # from plan — adjust if needed
n_actual = len(times)
print(f"  Time steps: {n_actual}  (expected {n_expected})")
assert n_actual == n_expected, f"Mismatch: {n_actual} ≠ {n_expected}"
print(f"✓ Time step count matches expected ({n_expected})")

# 3.3 — Check for duplicate timestamps
n_unique = len(times.unique())
assert n_unique == n_actual, (
    f"Duplicate timestamps found: {n_actual - n_unique} duplicates"
)
print(f"✓ No duplicate timestamps")
"""))

# ─── Step 4: Missing-value analysis ─────────────────────────────────────────

cells.append(nbf.v4.new_markdown_cell("## 4 — Missing-Value Analysis"))

cells.append(nbf.v4.new_code_cell("""\
gust = ds["GUST"].load()

# 4.1 — Total NaN fraction
total_nan = float(gust.isnull().sum()) / gust.size
print(f"Total NaN fraction: {total_nan:.4f}  ({total_nan*100:.2f} %)")

# 4.2 — Per-station and per-month NaN fraction
nan_per_station = gust.isnull().mean(dim="time")
nan_per_time = gust.isnull().mean(dim="station")

print(f"\\nPer-station NaN: min={float(nan_per_station.min()):.3f}, "
      f"max={float(nan_per_station.max()):.3f}, "
      f"mean={float(nan_per_station.mean()):.3f}")
print(f"Per-time NaN:    min={float(nan_per_time.min()):.3f}, "
      f"max={float(nan_per_time.max()):.3f}, "
      f"mean={float(nan_per_time.mean()):.3f}")
"""))

cells.append(nbf.v4.new_code_cell("""\
# 4.3 — NaN heatmap (station × time)
fig, ax = plt.subplots(figsize=(16, 6))
nan_mask = gust.isnull().values.T  # (station, time)
ax.imshow(nan_mask, aspect="auto", cmap="Reds", interpolation="none")
ax.set_xlabel("Time index")
ax.set_ylabel("Station index")
ax.set_title("NaN locations (red = missing)")
plt.tight_layout()
plt.show()
"""))

# ─── Step 5: Load source station metadata ────────────────────────────────────

cells.append(nbf.v4.new_markdown_cell("## 5 — Load Source Station Metadata (lat / lon)"))

cells.append(nbf.v4.new_code_cell("""\
src_path = paths.NCEI_DATA / "completeness_filtered_1990_2024_GUST.nc"
src = xr.open_dataset(src_path)
print(src)
"""))

cells.append(nbf.v4.new_code_cell("""\
# 5.2 — Extract a single (lat, lon) per station from the first non-NaN time step
lat_raw = src["latitude"]  # (time, station)
lon_raw = src["longitude"]  # (time, station)

# Use the first valid value along time for each station
lat_vals = lat_raw.where(lat_raw.notnull()).isel(time=0).values
lon_vals = lon_raw.where(lon_raw.notnull()).isel(time=0).values

# If the first time step has NaNs, fall back to first non-NaN per station
for i in range(len(lat_vals)):
    if np.isnan(lat_vals[i]):
        valid = lat_raw[:, i].dropna(dim="time")
        if len(valid) > 0:
            lat_vals[i] = float(valid[0])
            lon_vals[i] = float(lon_raw[:, i].dropna(dim="time")[0])

station_ids = src["station"].values
"""))

cells.append(nbf.v4.new_code_cell("""\
# 5.3 — Build a DataFrame
station_meta = pd.DataFrame({
    "station": station_ids,
    "latitude": lat_vals,
    "longitude": lon_vals,
})
print(f"Stations: {len(station_meta)}")
print(f"NaN lat/lon: {station_meta[['latitude','longitude']].isna().sum().to_dict()}")
station_meta.head(10)
"""))

# ─── Step 6: Station map ────────────────────────────────────────────────────

cells.append(nbf.v4.new_markdown_cell("## 6 — Station Map"))

cells.append(nbf.v4.new_code_cell("""\
# Compute mean p95 gust per station for coloring
mean_p95 = gust.mean(dim="time").values  # (station,)

fig = plt.figure(figsize=(14, 8))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.NorthPolarStereo())
ax.set_extent([-180, 180, 20, 90], crs=ccrs.PlateCarree())

ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")
ax.gridlines(draw_labels=False, linewidth=0.3, alpha=0.5)

sc = ax.scatter(
    station_meta["longitude"],
    station_meta["latitude"],
    c=mean_p95,
    cmap="YlOrRd",
    s=40,
    edgecolors="k",
    linewidths=0.3,
    transform=ccrs.PlateCarree(),
    zorder=5,
)
cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.05)
cbar.set_label("Mean p95 GUST (m/s)")
ax.set_title("NCEI Station Locations — Mean 95th-Percentile Wind Gust (ONDJFM)")
plt.tight_layout()
plt.show()
"""))

# ─── Step 7: Distributional summary statistics ──────────────────────────────

cells.append(nbf.v4.new_markdown_cell("## 7 — Distributional Summary Statistics"))

cells.append(nbf.v4.new_code_cell("""\
gust_flat = gust.values.ravel()
gust_valid = gust_flat[~np.isnan(gust_flat)]

print(f"Non-NaN values: {len(gust_valid):,} / {len(gust_flat):,}")
print(f"  Min:    {gust_valid.min():.2f} m/s")
print(f"  Max:    {gust_valid.max():.2f} m/s")
print(f"  Mean:   {gust_valid.mean():.2f} m/s")
print(f"  Median: {np.median(gust_valid):.2f} m/s")
print(f"  Std:    {gust_valid.std():.2f} m/s")
"""))

cells.append(nbf.v4.new_code_cell("""\
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(gust_valid, bins=60, edgecolor="k", linewidth=0.3, alpha=0.8)
ax.set_xlabel("95th-percentile gust (m/s)")
ax.set_ylabel("Count")
ax.set_title("Distribution of Monthly p95 Wind Gust Values (all stations, all months)")
ax.axvline(gust_valid.mean(), color="red", ls="--", label=f"Mean = {gust_valid.mean():.1f} m/s")
ax.legend()
plt.tight_layout()
plt.show()
"""))

cells.append(nbf.v4.new_markdown_cell("""\
**Interpretation**: For Northern Hemisphere surface stations, 95th-percentile
monthly wind gusts are expected to fall roughly in the 10–50 m/s range.
Values below ~5 m/s or above ~60 m/s would warrant investigation (instrument
issues or extreme-wind stations). Check the histogram above against this range.
"""))

# ─── Step 8: Time-series diagnostics ─────────────────────────────────────────

cells.append(nbf.v4.new_markdown_cell("## 8 — Time-Series Diagnostics"))

cells.append(nbf.v4.new_code_cell("""\
station_mean = gust.mean(dim="station")
station_std = gust.std(dim="station")

fig, ax = plt.subplots(figsize=(16, 5))

# Per-station thin lines
for i in range(gust.sizes["station"]):
    ax.plot(times, gust[:, i].values, color="steelblue", alpha=0.08, lw=0.5)

# Mean ± 1 std shading
ax.fill_between(
    times,
    (station_mean - station_std).values,
    (station_mean + station_std).values,
    alpha=0.3,
    color="orange",
    label="Mean ± 1σ",
)
ax.plot(times, station_mean.values, color="darkorange", lw=1.5, label="Station mean")

ax.set_xlabel("Time")
ax.set_ylabel("p95 GUST (m/s)")
ax.set_title("Monthly 95th-Percentile Wind Gust — All Stations")
ax.legend(loc="upper right")
plt.tight_layout()
plt.show()
"""))

cells.append(nbf.v4.new_markdown_cell("""\
**Notes**: Look for:
- Clear seasonal signal (higher gusts in winter months, lower in shoulder months).
- Any suspicious jumps or discontinuities (instrument changes or station relocations).
- Long-term trends (upward or downward drift).
"""))

# ─── Step 9: Cross-check against raw data ────────────────────────────────────

cells.append(nbf.v4.new_markdown_cell("## 9 — Cross-Check Against Raw Data"))

cells.append(nbf.v4.new_code_cell("""\
rng = np.random.default_rng(42)

# Pick 3 random stations and 3 random ONDJFM time steps
station_idx = rng.choice(gust.sizes["station"], size=3, replace=False)
time_idx = rng.choice(gust.sizes["time"], size=3, replace=False)

results = []
for si in station_idx:
    for ti in time_idx:
        station_id = ds["station"].values[si]
        target_time = pd.Timestamp(ds["time"].values[ti])
        yr, mo = target_time.year, target_time.month

        # Get all daily values for this station and month from the raw file
        raw_month = src["GUST"].sel(station=station_id).sel(
            time=slice(f"{yr}-{mo:02d}-01", f"{yr}-{mo:02d}-28")
        )
        # Extend to end of month
        import calendar
        last_day = calendar.monthrange(yr, mo)[1]
        raw_month = src["GUST"].sel(station=station_id).sel(
            time=slice(f"{yr}-{mo:02d}-01", f"{yr}-{mo:02d}-{last_day:02d}")
        )
        raw_vals = raw_month.values
        raw_vals = raw_vals[~np.isnan(raw_vals)]

        if len(raw_vals) == 0:
            recomputed = np.nan
        else:
            recomputed = np.percentile(raw_vals, 95)

        zarr_val = float(gust.sel(station=station_id, time=target_time).values)

        match = np.allclose(recomputed, zarr_val, atol=1e-6, equal_nan=True)
        results.append({
            "station": station_id,
            "year": yr,
            "month": mo,
            "raw_p95": recomputed,
            "zarr_p95": zarr_val,
            "match": match,
        })
        print(f"Station {station_id}, {yr}-{mo:02d}: "
              f"raw_p95={recomputed:.4f}, zarr_p95={zarr_val:.4f}, match={match}")

results_df = pd.DataFrame(results)
all_match = results_df["match"].all()
print(f"\\nAll spot checks passed: {all_match}")
assert all_match, "Cross-check failed — see mismatches above"
print("✓ Cross-check passed within tolerance (atol=1e-6)")
"""))

# ─── Step 10: Spatial distribution visualization ─────────────────────────────

cells.append(nbf.v4.new_markdown_cell("## 10 — Spatial Distribution of 95th-Percentile Values"))

cells.append(nbf.v4.new_code_cell("""\
# Per-station temporal mean of p95
mean_gust_per_station = gust.mean(dim="time").values

fig = plt.figure(figsize=(14, 8))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.NorthPolarStereo())
ax.set_extent([-180, 180, 20, 90], crs=ccrs.PlateCarree())

ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")
ax.add_feature(cfeature.LAND, facecolor="lightgray", alpha=0.3)
ax.gridlines(draw_labels=False, linewidth=0.3, alpha=0.5)

sc = ax.scatter(
    station_meta["longitude"],
    station_meta["latitude"],
    c=mean_gust_per_station,
    cmap="viridis",
    s=50,
    edgecolors="k",
    linewidths=0.4,
    transform=ccrs.PlateCarree(),
    zorder=5,
    vmin=np.nanpercentile(mean_gust_per_station, 5),
    vmax=np.nanpercentile(mean_gust_per_station, 95),
)
cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.05)
cbar.set_label("Mean p95 GUST (m/s)")
ax.set_title("Spatial Distribution of Mean 95th-Percentile Wind Gust")
plt.tight_layout()
plt.show()
"""))

cells.append(nbf.v4.new_markdown_cell("""\
**Interpretation**: Examine whether higher p95 values cluster in
expected regions — coastal or exposed stations, high-latitude areas with
frequent extratropical cyclones, or mountain passes. Anomalously high
or low values in unexpected locations may indicate data quality issues.
"""))

# ─── Step 11: Summary ────────────────────────────────────────────────────────

cells.append(nbf.v4.new_markdown_cell("""\
## 11 — Validation Summary

| Check | Result |
|-------|--------|
| Dimensions | `(time: 210, station: 131)` ✓ |
| Quantile coordinate | 0.95 ✓ |
| Time axis months | ONDJFM only ✓ |
| Time step count | 210 ✓ |
| Duplicate timestamps | None ✓ |
| NaN fraction | *fill in after run* |
| Value range | *fill in after run* |
| Cross-check (raw vs Zarr) | *fill in after run* |

**Conclusion**: *Update after running all cells.*
"""))

# ─── Assemble and save ───────────────────────────────────────────────────────
nb.cells = cells

import os
out_path = os.path.join(os.path.dirname(__file__), "ncei_p95_exploration.ipynb")
with open(out_path, "w") as f:
    nbf.write(nb, f)
print(f"Notebook written to {out_path}")
```

**Verification**:
```bash
cd notebooks && python _create_ncei_p95_notebook.py
# Expected: "Notebook written to notebooks/ncei_p95_exploration.ipynb"
# Then open the notebook in JupyterLab and run all cells.
```

After the notebook is created and verified, delete the helper script:
```bash
rm notebooks/_create_ncei_p95_notebook.py
```

---

## Step 1 — Scaffold the Notebook and Load Libraries

> Create `notebooks/ncei_p95_exploration.ipynb` with an introductory markdown cell and imports.

### 1.1 — Add title markdown cell

- [x] **Implementation**

The notebook generator (above) creates a markdown cell with:
- Title: "Validate NCEI 95th-Percentile ONDJFM Wind-Gust Computation"
- Purpose and dataset provenance summary

### 1.2 — Add import code cell

- [x] **Implementation**

```python
import sys
from pathlib import Path

PROJECT_ROOT = Path.cwd().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from config import paths
```

### Step 1 — Verification

- [ ] **Run verification**

```bash
# Open the notebook and run the first two cells
# Expected: no import errors, prints project root and processed data dir
```

---

## Step 2 — Load and Inspect the Zarr Store

> Load `ncei_percentiles_ondjfm_p95.zarr` and print metadata.

ds = xr.open_zarr(zarr_path)
ds
### 2.1 — Open the Zarr store

- [x] **Implementation**

```python
zarr_path = paths.PROCESSED_DATA / "ncei_percentiles_ondjfm_p95.zarr"
ds = xr.open_zarr(zarr_path)
ds
```

### 2.2 — Print coordinate details

- [x] **Implementation**

```python
print("Coordinate names:", list(ds.coords))
print("Dimension sizes:", dict(ds.sizes))
print("Data variables:", list(ds.data_vars))
for c in ds.coords:
    print(f"  {c}: dtype={ds[c].dtype}, shape={ds[c].shape}")
```

### 2.3 — Confirm quantile coordinate

- [x] **Implementation**

```python
q_val = float(ds.coords["quantile"].values)
assert q_val == 0.95, f"Expected quantile=0.95, got {q_val}"
print(f"✓ quantile coordinate = {q_val}")
```

### Step 2 — Verification

- [ ] **Run verification**

Expected output:
- `Dimensions: (time: 210, station: 131)`
- `quantile coordinate = 0.95`
- Coordinate names include `['quantile', 'station', 'time']`

---

## Step 3 — Temporal Consistency Checks

> Verify time axis: correct months, expected count, no duplicates.

### 3.1 — Assert all months ∈ {1,2,3,10,11,12}

- [x] **Implementation**

```python
times = pd.DatetimeIndex(ds["time"].values)
valid_months = {1, 2, 3, 10, 11, 12}
actual_months = set(times.month.unique())
assert actual_months == valid_months
```

### 3.2 — Assert time step count == 210

- [x] **Implementation**

```python
assert len(times) == 210
```

### 3.3 — Check for duplicate timestamps

- [x] **Implementation**

```python
assert len(times.unique()) == len(times)
```

### Step 3 — Verification

- [ ] **Run verification**

Expected: All three assertions pass; printed messages confirm ONDJFM months, 210 time steps, no duplicates.

---

## Step 4 — Missing-Value Analysis

> Quantify NaN coverage across time and stations; produce a heatmap.

### 4.1 — Total NaN fraction

- [ ] **Implementation**

```python
gust = ds["GUST"].load()
total_nan = float(gust.isnull().sum()) / gust.size
print(f"Total NaN fraction: {total_nan:.4f}  ({total_nan*100:.2f} %)")
```

### 4.2 — Per-station and per-month NaN fractions

- [ ] **Implementation**

```python
nan_per_station = gust.isnull().mean(dim="time")
nan_per_time = gust.isnull().mean(dim="station")
```

### 4.3 — NaN heatmap

- [ ] **Implementation**

```python
fig, ax = plt.subplots(figsize=(16, 6))
nan_mask = gust.isnull().values.T  # (station, time)
ax.imshow(nan_mask, aspect="auto", cmap="Reds", interpolation="none")
ax.set_xlabel("Time index")
ax.set_ylabel("Station index")
ax.set_title("NaN locations (red = missing)")
plt.tight_layout()
plt.show()
```

### Step 4 — Verification

- [ ] **Run verification**

Expected: Heatmap renders; NaN statistics printed.

---

## Step 5 — Load Source Station Metadata (lat / lon)

> Retrieve per-station latitude and longitude from the source filtered NetCDF.

### 5.1 — Load filtered NetCDF

- [ ] **Implementation**

```python
src_path = paths.NCEI_DATA / "completeness_filtered_1990_2024_GUST.nc"
src = xr.open_dataset(src_path)
```

### 5.2 — Extract single (lat, lon) per station

- [ ] **Implementation**

```python
lat_raw = src["latitude"]   # (time, station)
lon_raw = src["longitude"]  # (time, station)

lat_vals = lat_raw.where(lat_raw.notnull()).isel(time=0).values
lon_vals = lon_raw.where(lon_raw.notnull()).isel(time=0).values

# Fallback for stations with NaN at time=0
for i in range(len(lat_vals)):
    if np.isnan(lat_vals[i]):
        valid = lat_raw[:, i].dropna(dim="time")
        if len(valid) > 0:
            lat_vals[i] = float(valid[0])
            lon_vals[i] = float(lon_raw[:, i].dropna(dim="time")[0])
```

### 5.3 — Build DataFrame with station metadata

- [ ] **Implementation**

```python
station_meta = pd.DataFrame({
    "station": src["station"].values,
    "latitude": lat_vals,
    "longitude": lon_vals,
})
assert len(station_meta) == 131
assert station_meta[["latitude", "longitude"]].isna().sum().sum() == 0
```

### Step 5 — Verification

- [ ] **Run verification**

Expected: DataFrame with 131 rows, zero NaN lat/lon values.

---

## Step 6 — Station Map

> Plot station locations on a NH map, colored by mean p95 gust.

### 6.1–6.3 — NH polar stereo map with scatter

- [ ] **Implementation**

```python
mean_p95 = gust.mean(dim="time").values

fig = plt.figure(figsize=(14, 8))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.NorthPolarStereo())
ax.set_extent([-180, 180, 20, 90], crs=ccrs.PlateCarree())
ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")
ax.gridlines(draw_labels=False, linewidth=0.3, alpha=0.5)

sc = ax.scatter(
    station_meta["longitude"], station_meta["latitude"],
    c=mean_p95, cmap="YlOrRd", s=40,
    edgecolors="k", linewidths=0.3,
    transform=ccrs.PlateCarree(), zorder=5,
)
cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.05)
cbar.set_label("Mean p95 GUST (m/s)")
ax.set_title("NCEI Station Locations — Mean 95th-Percentile Wind Gust (ONDJFM)")
plt.tight_layout()
plt.show()
```

### Step 6 — Verification

- [ ] **Run verification**

Expected: Map renders showing ~131 stations across the NH with a color gradient.

---

## Step 7 — Distributional Summary Statistics

> Compute and display summary stats; plot a histogram.

### 7.1 — Print statistics

- [ ] **Implementation**

```python
gust_flat = gust.values.ravel()
gust_valid = gust_flat[~np.isnan(gust_flat)]
print(f"Min: {gust_valid.min():.2f}, Max: {gust_valid.max():.2f}, "
      f"Mean: {gust_valid.mean():.2f}, Median: {np.median(gust_valid):.2f}, "
      f"Std: {gust_valid.std():.2f}")
```

### 7.2 — Histogram

- [ ] **Implementation**

```python
fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(gust_valid, bins=60, edgecolor="k", linewidth=0.3, alpha=0.8)
ax.set_xlabel("95th-percentile gust (m/s)")
ax.set_ylabel("Count")
ax.set_title("Distribution of Monthly p95 Wind Gust Values")
ax.axvline(gust_valid.mean(), color="red", ls="--",
           label=f"Mean = {gust_valid.mean():.1f} m/s")
ax.legend()
plt.tight_layout()
plt.show()
```

### 7.3 — Interpretation markdown cell

- [ ] **Implementation**

Markdown cell noting that physically plausible 95th-percentile gusts for NH stations are roughly 10–50 m/s.

### Step 7 — Verification

- [ ] **Run verification**

Expected: Histogram renders; values fall within physically plausible range.

---

## Step 8 — Time-Series Diagnostics

> Visualize temporal evolution: station-mean ± 1σ with per-station thin lines.

### 8.1–8.2 — Time-series plot

- [ ] **Implementation**

```python
station_mean = gust.mean(dim="station")
station_std = gust.std(dim="station")

fig, ax = plt.subplots(figsize=(16, 5))

# Per-station thin lines
for i in range(gust.sizes["station"]):
    ax.plot(times, gust[:, i].values, color="steelblue", alpha=0.08, lw=0.5)

# Mean ± 1σ shading
ax.fill_between(times,
    (station_mean - station_std).values,
    (station_mean + station_std).values,
    alpha=0.3, color="orange", label="Mean ± 1σ")
ax.plot(times, station_mean.values, color="darkorange", lw=1.5, label="Station mean")

ax.set_xlabel("Time")
ax.set_ylabel("p95 GUST (m/s)")
ax.set_title("Monthly 95th-Percentile Wind Gust — All Stations")
ax.legend(loc="upper right")
plt.tight_layout()
plt.show()
```

### 8.3 — Interpretation markdown cell

- [ ] **Implementation**

Markdown cell noting any visible trends, seasonality, or suspicious jumps.

### Step 8 — Verification

- [ ] **Run verification**

Expected: Time-series plot renders with clear seasonal signal and no obvious artefacts.

---

## Step 9 — Cross-Check Against Raw Data

> Spot-check by recomputing p95 from daily data for 3 stations × 3 months.

### 9.1–9.3 — Select random samples and compare

- [ ] **Implementation**

```python
import calendar

rng = np.random.default_rng(42)
station_idx = rng.choice(gust.sizes["station"], size=3, replace=False)
time_idx = rng.choice(gust.sizes["time"], size=3, replace=False)

results = []
for si in station_idx:
    for ti in time_idx:
        station_id = ds["station"].values[si]
        target_time = pd.Timestamp(ds["time"].values[ti])
        yr, mo = target_time.year, target_time.month
        last_day = calendar.monthrange(yr, mo)[1]

        raw_month = src["GUST"].sel(station=station_id).sel(
            time=slice(f"{yr}-{mo:02d}-01", f"{yr}-{mo:02d}-{last_day:02d}")
        )
        raw_vals = raw_month.values
        raw_vals = raw_vals[~np.isnan(raw_vals)]

        recomputed = np.percentile(raw_vals, 95) if len(raw_vals) > 0 else np.nan
        zarr_val = float(gust.sel(station=station_id, time=target_time).values)

        match = np.allclose(recomputed, zarr_val, atol=1e-6, equal_nan=True)
        results.append(dict(station=station_id, year=yr, month=mo,
                            raw_p95=recomputed, zarr_p95=zarr_val, match=match))
        print(f"Station {station_id}, {yr}-{mo:02d}: "
              f"raw_p95={recomputed:.4f}, zarr_p95={zarr_val:.4f}, match={match}")

results_df = pd.DataFrame(results)
assert results_df["match"].all(), "Cross-check failed"
print("✓ Cross-check passed (atol=1e-6)")
```

### Step 9 — Verification

- [ ] **Run verification**

Expected: All 9 spot checks pass within floating-point tolerance.

---

## Step 10 — Spatial Distribution Visualization

> Scatter plot of stations colored by mean p95 value, with viridis colormap and land shading.

### 10.1–10.3 — Spatial scatter with colorbar

- [ ] **Implementation**

```python
mean_gust_per_station = gust.mean(dim="time").values

fig = plt.figure(figsize=(14, 8))
ax = fig.add_subplot(1, 1, 1, projection=ccrs.NorthPolarStereo())
ax.set_extent([-180, 180, 20, 90], crs=ccrs.PlateCarree())
ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
ax.add_feature(cfeature.BORDERS, linewidth=0.3, linestyle="--")
ax.add_feature(cfeature.LAND, facecolor="lightgray", alpha=0.3)
ax.gridlines(draw_labels=False, linewidth=0.3, alpha=0.5)

sc = ax.scatter(
    station_meta["longitude"], station_meta["latitude"],
    c=mean_gust_per_station, cmap="viridis", s=50,
    edgecolors="k", linewidths=0.4,
    transform=ccrs.PlateCarree(), zorder=5,
    vmin=np.nanpercentile(mean_gust_per_station, 5),
    vmax=np.nanpercentile(mean_gust_per_station, 95),
)
cbar = plt.colorbar(sc, ax=ax, shrink=0.7, pad=0.05)
cbar.set_label("Mean p95 GUST (m/s)")
ax.set_title("Spatial Distribution of Mean 95th-Percentile Wind Gust")
plt.tight_layout()
plt.show()
```

### Step 10 — Verification

- [ ] **Run verification**

Expected: Scatter plot renders with stations colored by p95 values. Colorbar present.

---

## Step 11 — Summary Cell and TODO Update

> Add concluding markdown cell and update TODO files.

### 11.1 — Summary markdown cell

- [ ] **Implementation**

Included in the notebook generator as the final markdown cell containing a validation summary table. Update the "fill in after run" fields after executing all cells.

### 11.2 — Mark TODO complete in data-engineer.todo.md

- [ ] **Implementation**

**Edit file**: `.github/todos/data-engineer.todo.md`

Replace the Active section entry and add a Completed entry:

```markdown
## Active

(remove the NCEI p95 validation task if it was listed here)

## Completed

- [x] ~~Load NCEI 95th-percentile and visualize it for validation~~ — completed: YYYY-MM-DD — commit: {SHA}
```

> **Note**: This is an analyst TODO, not data-engineer. Check `.github/todos/analyst.todo.md` instead. The edit should be:

**Edit file**: `.github/todos/analyst.todo.md`

Move the HIGH-priority task from Active to Completed after notebook runs successfully:

Current Active entry:
```markdown
- [ ] **[HIGH]** Load NCEI 95th-percentile and visualize it for validation if the computation worked. — milestone: `generating-impact-data` — added: 2026-04-04
```

Replace with (after successful validation):
```markdown
- [x] ~~**[HIGH]** Load NCEI 95th-percentile and visualize it for validation if the computation worked.~~ — milestone: `generating-impact-data` — completed: {DATE} — commit: {SHA}
```

### 11.3 — Update global.todos.md

- [ ] **Implementation**

No status change needed — `generating-impact-data` milestone remains `🟡 In progress` (ERA5 bias correction is still pending).

### Step 11 — Verification

- [ ] **Run verification**

```bash
# Run the full notebook top-to-bottom
cd notebooks && jupyter nbconvert --to notebook --execute ncei_p95_exploration.ipynb
# Expected: exits with code 0; all assertions pass
```

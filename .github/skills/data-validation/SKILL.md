---
name: data-validation
description: "Verify data completeness, coordinate consistency, and metadata integrity for raw and processed datasets. Use when asked to 'validate data', 'check data quality', 'verify dataset completeness', or 'inspect data dimensions'. Keywords: validation, data quality, completeness, coordinates, metadata, xarray, NetCDF, Zarr."
---

# data-validation

Validate raw and processed datasets for completeness, coordinate consistency, and metadata integrity. Ensures data is analysis-ready before downstream pipeline stages consume it.

## When to Use This Skill

- "Validate the NCEI station data for completeness."
- "Check that the ERA5 Zarr store has the correct dimensions."
- "Verify metadata integrity of processed percentile files."
- "Inspect data quality before running the bias correction."

## Workflow

### Step 1 — Check file existence and symlink validity

Verify that all expected data files exist on disk using `config.paths`:

```python
from config.paths import ERA5_DATA, NCEI_DATA, PROCESSED_DATA
from pathlib import Path

# Check symlinks resolve
for p in [ERA5_DATA, NCEI_DATA]:
    assert p.exists() and p.resolve().exists(), f"Broken symlink or missing: {p}"
```

Report any broken symlinks or missing directories as structured warnings.

### Step 2 — Open datasets and validate dimensions/coordinates/dtypes

Open each dataset with xarray and verify:

- Expected dimensions exist (e.g. `time`, `lat`, `lon` for ERA5; `time`, `station` for NCEI).
- Coordinate values are within physically plausible ranges (lat: -90 to 90, lon: -180 to 360).
- Data variables have expected dtypes (float32/float64 for wind gust).

```python
import xarray as xr

ds = xr.open_zarr(PROCESSED_DATA / "era5_percentiles_ondjfm_p95.zarr")
assert "time" in ds.dims
assert "lat" in ds.dims
assert "lon" in ds.dims
assert ds["10fg"].dtype in ("float32", "float64")
```

### Step 3 — Compute completeness statistics

For each variable, compute the fraction of non-NaN values:

```python
completeness = ds["10fg"].notnull().mean(dim="time").compute()
```

Flag grid cells or stations with completeness below a configurable threshold (default: 80%).

### Step 4 — Report issues via project logger

Use `config.custom_logging` to emit structured warnings:

```python
from config.custom_logging import setup_logging
import logging

setup_logging(log_filename="data_validation.log")
logger = logging.getLogger(__name__)

if (completeness < 0.8).any():
    n_bad = int((completeness < 0.8).sum())
    logger.warning(f"{n_bad} grid cells have completeness below 80%")
```

## Output Artifacts

- Console/log output with validation summary (pass/fail per dataset).
- Structured warnings for any issues found.
- No files are created or modified — this is a read-only diagnostic skill.

## References

- Path helper: `config/paths.py`
- Logging: `config/custom_logging.py`
- Existing preprocessing scripts: `scripts/preprocessing/`

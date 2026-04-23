---
name: climada-impact
description: "Configure and run CLIMADA impact calculations with regional vulnerability curves. Use when asked to 'generate impact data', 'run CLIMADA', 'compute wind damage impacts', 'configure vulnerability curves', or 'create impact time series'. Keywords: CLIMADA, impact, vulnerability, exposure, hazard, LitPop, wind gust, damage, Eberenz, Schwierz."
---

# climada-impact

Configure and run CLIMADA impact calculations to produce seasonally aggregated impact time series from ERA5 wind gust data, LitPop exposure, and regional vulnerability curves.

## When to Use This Skill

- "Generate impact time series from ERA5 wind gust data."
- "Configure CLIMADA with regional vulnerability curves."
- "Run CLIMADA impact calculation for ONDJFM 1940–2024."
- "Test different vulnerability curve setups."

## Workflow

### Step 1 — Load ERA5 wind gust hazard data as a CLIMADA Hazard object

Convert the bias-corrected ERA5 daily maximum wind gust (`10fg`) to a CLIMADA `Hazard` object:

```python
from climada.hazard import Hazard
import xarray as xr
from config.paths import PROCESSED_DATA

ds = xr.open_zarr(PROCESSED_DATA / "era5_bias_corrected.zarr")
# Convert to CLIMADA Hazard via centroids
hazard = Hazard.from_xarray_raster(ds["10fg"], hazard_type="WS")
```

Filter to the ONDJFM extended winter season.

### Step 2 — Configure LitPop exposure for a fixed reference year

Use constant GDP and population to isolate the meteorological component of impact variability:

```python
from climada.entity import LitPop

exposure = LitPop.from_countries(
    countries=["USA", "CAN", "GBR", "DEU", "FRA", ...],  # NH countries
    reference_year=2005,  # Fixed year — constant exposure
    fin_mode="gdp",
)
```

**Rationale**: Setting exposure constant at a fixed year ensures that PCA modes reflect atmospheric variability, not socioeconomic trends.

### Step 3 — Select regional vulnerability curves

Apply region-specific vulnerability curves from the literature:

| Region | Vulnerability curve | Reference |
|--------|-------------------|-----------|
| Tropical (< 30°N) | Eberenz 2021 | @eberenz2021 |
| Extratropical (≥ 30°N) | Schwierz 2010 | @schwierz2010 |

```python
from climada.entity import ImpactFuncSet, ImpfTropCyclone

# Configure impact function set with regional curves
impf_set = ImpactFuncSet()
# Add tropical and extratropical functions
# ... (specific setup depends on CLIMADA version)
```

### Step 4 — Run ImpactCalc to produce seasonally aggregated impact time series

```python
from climada.engine import ImpactCalc

impact = ImpactCalc(exposure, impf_set, hazard).impact()

# Aggregate to seasonal (ONDJFM) totals
# Result: I(t, λ, φ) — impact per season, latitude, longitude
```

**Note on aggregation**: Prefer event-based aggregation over daily to avoid double-counting multi-day storms. If using daily data, apply a storm-tracking filter or temporal clustering first.

### Step 5 — Save impact output as Zarr with provenance metadata

```python
import subprocess
from datetime import datetime
from config.paths import PROCESSED_DATA

impact_ds = impact.to_xarray()  # or custom conversion
impact_ds.attrs.update({
    "source": "CLIMADA ImpactCalc",
    "hazard_input": "era5_bias_corrected.zarr",
    "exposure_year": 2005,
    "vulnerability_tropical": "Eberenz2021",
    "vulnerability_extratropical": "Schwierz2010",
    "season": "ONDJFM",
    "period": "1940-2024",
    "created": datetime.now().isoformat(),
    "commit": subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip(),
})
impact_ds.to_zarr(PROCESSED_DATA / "impacts" / "climada_impacts.zarr", mode="w")
```

## Output Artifacts

- Zarr store at `data/processed/impacts/climada_impacts.zarr` with dimensions `(time, lat, lon)`.
- Provenance attributes on the dataset (input paths, parameters, commit SHA).

## References

- Methods draft: `milestones/methods_draft.md` (step 1)
- CLIMADA documentation: https://climada-python.readthedocs.io/
- Eberenz et al. 2021 — tropical vulnerability curves
- Schwierz et al. 2010 — extratropical vulnerability curves
- Path helper: `config/paths.py`

# Implementation: agent-system

**Source plan**: `.github/plans/agent-system.plan.md`
**Generated**: 2025-04-02
**Branch**: `feature/agent-system`

## Steps Overview

| Step | Title | Tasks | Status |
|------|-------|-------|--------|
| 1 | Data Engineer Agent and Skills | 4 | Completed |
| 2 | Impact Modeler Agent and Skills | 4 | Completed |
| 3 | Analyst Agent and Skills | 4 | Completed |
| 4 | Register Agents and Integration Tests | 4 | Completed |

**New dependencies**: None — all agent and skill files are Markdown. The smoke test uses only `pytest`, `yaml`, and `pathlib`.
**Files created**: 11
**Files modified**: 1

---

## Step 1 — Create the Data Engineer Agent and Skills

> Create the `data-engineer` agent and its two supporting skills: `data-validation` and `dask-pipeline`. This agent owns the entire data-preparation pipeline: download, convert, filter, bias-correct, and compute percentiles.

### 1.1 — Create data-validation skill

- [x] **Implementation**

**Create file**: `.github/skills/data-validation/SKILL.md`

```markdown
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
```

### 1.2 — Create dask-pipeline skill

- [x] **Implementation**

**Create file**: `.github/skills/dask-pipeline/SKILL.md`

```markdown
---
name: dask-pipeline
description: "Configure and run chunked xarray/Dask workflows on HPC. Use when asked to 'set up a Dask pipeline', 'configure chunked processing', 'run an xarray workflow on HPC', or 'optimize chunk sizes for Levante'. Keywords: dask, xarray, chunked, HPC, SLURM, Zarr, pipeline, Levante, memory budget."
---

# dask-pipeline

Configure and execute chunked xarray/Dask workflows suited for the DKRZ Levante HPC environment. Covers scheduler selection, chunk-size tuning, pipeline execution, and output validation.

## When to Use This Skill

- "Set up a Dask cluster for processing ERA5 data."
- "Configure chunk sizes for the percentile computation."
- "Run the bias correction pipeline on HPC with Dask."
- "Optimize memory usage for my xarray workflow on Levante."

## Workflow

### Step 1 — Select appropriate Dask scheduler

Choose the scheduler based on the execution environment:

| Environment | Scheduler | Configuration |
|-------------|-----------|---------------|
| Local dev / interactive | `dask.distributed.LocalCluster` | `n_workers=4, memory_limit='8GB'` |
| Levante compute nodes | `dask_jobqueue.SLURMCluster` | `cores=128, memory='60GB', walltime='02:00:00'` |

```python
from dask.distributed import Client, LocalCluster

# For local development
cluster = LocalCluster(n_workers=4, memory_limit="8GB")
client = Client(cluster)

# For HPC (Levante)
# from dask_jobqueue import SLURMCluster
# cluster = SLURMCluster(
#     cores=128, memory="60GB",
#     walltime="02:00:00", account="gg0304",
#     interface="ib0"
# )
# cluster.scale(jobs=4)
# client = Client(cluster)
```

### Step 2 — Configure chunk sizes

Heuristics for chunk sizing on Levante (60 GB/worker):

- **Target chunk size**: 100–500 MB per chunk in memory.
- **Time dimension**: chunk by year or season (e.g. `time=365`).
- **Spatial dimensions**: keep spatial dims unchunked if they fit, or chunk to ~500×500 grid cells.

```python
import xarray as xr
from config.paths import ERA5_DATA

ds = xr.open_zarr(ERA5_DATA, chunks={"time": 365, "lat": -1, "lon": -1})
```

Adjust chunk sizes based on the operation:
- **Reductions along time** (e.g. percentiles): chunk generously along time, keep spatial unchunked.
- **Spatial operations** (e.g. regridding): chunk spatial dims, keep time unchunked.

### Step 3 — Execute chunked xarray pipeline

Standard pipeline pattern: load → transform → save to Zarr.

```python
from config.paths import PROCESSED_DATA

# Transform
result = ds["10fg"].groupby("time.season").mean("time")

# Save — use mode="w" for new stores, mode="a" for appending
result.to_zarr(PROCESSED_DATA / "output.zarr", mode="w")
```

Use `.persist()` to keep intermediate results in cluster memory when reused multiple times. Call `.compute()` only for final outputs or small results.

### Step 4 — Validate output Zarr store

After writing, reopen and spot-check:

```python
ds_out = xr.open_zarr(PROCESSED_DATA / "output.zarr")
assert ds_out.dims == expected_dims
assert ds_out["10fg"].isnull().mean().compute() < 0.05  # < 5% missing
```

## Memory Budget Guidelines (Levante)

| Node type | RAM | Recommended workers | Chunk target |
|-----------|-----|-------------------|--------------|
| Shared (interactive) | 256 GB | 4–8 | 200 MB |
| Compute (batch) | 512 GB | 8–16 | 500 MB |
| GPU nodes | 512 GB + GPU | 4 | 500 MB |

**Rule of thumb**: peak memory ≈ 2–3× chunk size × number of concurrent tasks per worker.

## Output Artifacts

- Zarr stores in `data/processed/` or `data/tmp/`.
- Dask performance reports (optional): `client.profile()` or `dask.diagnostics`.

## References

- Path helper: `config/paths.py`
- Existing compute scripts: `scripts/preprocessing/compute_era5_quantiles.py`
- Dask-jobqueue docs: https://jobqueue.dask.org/
- DKRZ Levante docs: https://docs.dkrz.de/
```

### 1.3 — Create data-engineer agent

- [x] **Implementation**

**Create file**: `.github/agents/data-engineer.agent.md`

```markdown
---
name: data-engineer
description: "Manage raw data through analysis-ready datasets: download, convert, filter, bias-correct, and compute percentiles. Use when asked to 'download data', 'preprocess ERA5', 'filter NCEI stations', 'compute percentiles', 'run bias correction', or 'prepare data for impact modeling'. Keywords: data, preprocessing, ETL, ERA5, NCEI, bias correction, percentiles, Zarr, xarray, dask, HPC."
keywords: "data engineering, preprocessing, ETL, ERA5, NCEI, bias correction, percentiles, Zarr, xarray, dask, HPC, download, convert, filter"
model: claude-opus-4.6
tools: ['readFile', 'runInTerminal', 'editFiles', 'fetch', 'search']
---

# Data Engineer

## Overview

The Data Engineer agent owns the entire data-preparation pipeline for the SYNCDSTRMDMG project. It manages raw data ingestion through to analysis-ready datasets: downloading, converting, filtering, bias-correcting, and computing statistical summaries (percentiles). All outputs are Zarr stores in `data/processed/` with standardized dimension names (`time`, `lat`, `lon` or `station`).

## Role and Expertise

You are a senior climate data engineer with deep expertise in:

- NetCDF/Zarr data formats and xarray/Dask processing on HPC systems.
- ERA5 reanalysis and NCEI station data pipelines.
- Statistical bias correction methods (quantile mapping).
- Data quality control and completeness filtering.
- DKRZ Levante HPC environment (SLURM, distributed computing).

You prioritize data integrity, reproducibility, and performance. Every output includes provenance metadata.

## When to Use This Agent

- "Download NCEI data for 2020–2024."
- "Filter stations for completeness above 90%."
- "Compute ERA5 95th and 98th percentile wind gusts for ONDJFM."
- "Run the bias correction pipeline for ERA5 wind gusts."
- "Convert raw NCEI files to a single NetCDF."
- "Prepare analysis-ready data for the impact modeler."

## Workflow

### Phase 1 — Validate paths and data availability

Use `config.paths` to locate raw data directories. Run the `data-validation` skill to verify symlinks, file existence, and basic data integrity before proceeding.

### Phase 2 — Load raw data

Open datasets with xarray using lazy loading and appropriate chunk sizes (see `dask-pipeline` skill). Verify dimensions and coordinate ranges.

### Phase 3 — Quality-filter

For station data (NCEI): apply completeness filtering using existing scripts (`scripts/preprocessing/filter_ncei_stations.py`). For gridded data (ERA5): check for anomalous values and missing data patterns.

### Phase 4 — Bias-correct

Apply quantile mapping bias correction to ERA5 wind gust data against NCEI observations using `scripts/preprocessing/era5_bias_correction.py`. Document correction parameters and save diagnostics.

### Phase 5 — Compute statistics

Compute seasonal percentiles (95th, 98th) for the ONDJFM extended winter season. Use chunked Dask operations for memory efficiency on HPC (see `dask-pipeline` skill).

### Phase 6 — Save to Zarr with provenance

Write output to `data/processed/` as Zarr stores with standardized dimensions. Attach provenance metadata as dataset attributes:

```python
ds.attrs["source_script"] = "scripts/preprocessing/compute_era5_quantiles.py"
ds.attrs["input_data"] = str(config.paths.ERA5_DATA)
ds.attrs["parameters"] = "percentile=95, season=ONDJFM"
ds.attrs["created"] = datetime.now().isoformat()
ds.attrs["commit"] = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
```

## Example Prompts

| Prompt | Maps to script |
|--------|---------------|
| "Convert the raw NCEI yearly files to a single NetCDF" | `scripts/preprocessing/convert_ncei_to_netcdf.py` |
| "Filter NCEI stations for completeness ≥ 90% in 1990–2024" | `scripts/preprocessing/filter_ncei_stations.py` |
| "Compute ERA5 95th percentile wind gusts for ONDJFM" | `scripts/preprocessing/compute_era5_quantiles.py` |
| "Run bias correction of ERA5 against NCEI observations" | `scripts/preprocessing/era5_bias_correction.py` |

## Safety & Limits

- **Read-only** on `data/raw/` — never modify or delete raw data files.
- **Write only** to `data/processed/` and `data/tmp/`.
- Always verify output integrity (reopen Zarr, check dims and spot values) before reporting success.
- Warn before submitting HPC jobs exceeding 2 hours walltime.
- Do not expose file system paths outside the project directory.

## Outputs

- Zarr stores in `data/processed/` with standardized dimensions (`time`, `lat`, `lon` or `station`).
- Provenance metadata as dataset attributes (input paths, parameters, commit SHA, timestamp).
- Validation logs in `logs/`.

## References

- Skills: `data-validation`, `dask-pipeline`
- Path helper: `config/paths.py`
- Logging: `config/custom_logging.py`
- Preprocessing scripts: `scripts/preprocessing/`
- NCEI download utility: `utils/download_NCEI.py`
```

### 1.4 — Add example prompts section (already included in 1.3)

- [x] **Implementation**

Covered in task 1.3 — the agent file includes the "Example Prompts" section with 4 concrete prompts tied to existing scripts.

### Step 1 — Verification

- [ ] **Run verification**

```bash
# Validate YAML frontmatter parses correctly
python -c "
import yaml, pathlib
files = [
    '.github/skills/data-validation/SKILL.md',
    '.github/skills/dask-pipeline/SKILL.md',
    '.github/agents/data-engineer.agent.md',
]
for f in files:
    p = pathlib.Path(f)
    assert p.exists(), f'File not found: {f}'
    text = p.read_text()
    parts = text.split('---')
    fm = yaml.safe_load(parts[1])
    print(f'{f}: frontmatter keys = {list(fm.keys())}')
print('All frontmatter valid.')
"

# Confirm required sections exist
grep -l '## Workflow' .github/agents/data-engineer.agent.md .github/skills/data-validation/SKILL.md .github/skills/dask-pipeline/SKILL.md
```

Expected: All three files listed, no errors. Frontmatter keys include `name` and `description` for all files.

---

## Step 2 — Create the Impact Modeler Agent and Skills

> Create the `impact-modeler` agent and its two supporting skills: `climada-impact` and `ensemble-generation`. This agent owns impact time-series generation, SSI computation, vulnerability-curve sensitivity testing, and synthetic ensemble production.

### 2.1 — Create climada-impact skill

- [x] **Implementation**

**Create file**: `.github/skills/climada-impact/SKILL.md`

```markdown
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
```

### 2.2 — Create ensemble-generation skill

- [x] **Implementation**

**Create file**: `.github/skills/ensemble-generation/SKILL.md`

```markdown
---
name: ensemble-generation
description: "Generate probabilistic and synthetic storm ensembles using CLIMADA's probabilistic module and ACE2. Use when asked to 'generate synthetic storms', 'run probabilistic ensemble', 'create ACE2 ensemble', 'test statistical robustness', or 'produce synthetic training data'. Keywords: ensemble, probabilistic, synthetic, CLIMADA, ACE2, stochastic, robustness, causality, PCA projection."
---

# ensemble-generation

Generate probabilistic/synthetic storm ensembles for robustness and causality testing. Covers CLIMADA's stochastic event-set generation and ACE2 initial-condition ensembles.

## When to Use This Skill

- "Generate a stochastic storm ensemble from historical ERA5 events."
- "Run ACE2 ensemble for ONDJFM 1940–2022."
- "Produce synthetic training data for the prediction scheme."
- "Project synthetic impacts onto the historical PCA basis."

## Workflow

### Step 1 — CLIMADA probabilistic module: stochastic event sets

Generate synthetic versions of historical storms by applying spatial shift and intensity perturbation:

```python
from climada.hazard import Hazard

# Load historical hazard
hazard_hist = Hazard.from_hdf5("path/to/historical_hazard.h5")

# Generate stochastic event set
hazard_prob = hazard_hist.calc_year_set()
# OR use the probabilistic module
hazard_synth = hazard_hist.from_probabilistic(
    n_events=1000,
    spatial_shift_std=0.5,  # degrees
    intensity_perturbation_std=0.1,  # fraction
)
```

The synthetic events preserve the climatological spatial pattern while sampling intensity variability.

### Step 2 — ACE2 ensemble: initial-condition runs

Run the ACE2 climate emulator for 83 initial-condition ensemble members covering ONDJFM 1940–2022:

- ACE2 does not output wind gust directly.
- Approximate via a power-law damage proxy:

$$I_{\text{proxy}} = (V_{\max} - V_{98,\text{ERA5}})^3 \times \text{Exposure}$$

for each day and grid cell, then aggregate to seasonal totals.

```python
# Pseudocode for ACE2 ensemble processing
from config.paths import ACE2

for member in range(1, 84):
    ds_ace2 = xr.open_dataset(ACE2 / f"member_{member:03d}.nc")
    v_max = ds_ace2["sfcWind"]  # or nearest proxy
    v_98 = xr.open_zarr(PROCESSED_DATA / "era5_percentiles_ondjfm_p98.zarr")["10fg"]
    
    exceedance = (v_max - v_98).clip(min=0)
    i_proxy = (exceedance ** 3) * exposure_weight
    seasonal_index = i_proxy.resample(time="QS-Oct").sum()
```

### Step 3 — Project synthetic impacts onto the historical PCA basis

For each ensemble member, project the synthetic impact field onto the PCA eigenvectors derived from historical ERA5 impacts:

```python
import numpy as np

# historical_loadings: shape (n_components, n_gridcells) from historical PCA
# synthetic_anomalies: shape (n_seasons, n_gridcells)

synthetic_scores = synthetic_anomalies @ historical_loadings.T
# synthetic_scores: shape (n_seasons, n_components)
```

### Step 4 — Compare synthetic and historical PCA spatial patterns

Compute pattern correlation between synthetic and historical PCA loadings. If correlation > 0.7, the mode is robust to initial-condition uncertainty.

## Output Artifacts

- Synthetic hazard event sets (CLIMADA format or Zarr).
- ACE2-derived seasonal impact proxy time series (`data/processed/impacts/ace2_ensemble/`).
- Projected PCA scores for each ensemble member.
- Pattern correlation diagnostics.

## References

- Methods draft: `milestones/methods_draft.md` (steps 7 and 8)
- CLIMADA probabilistic module docs
- ACE2 model: `models/ACE2`
- Path helper: `config/paths.py`
```

### 2.3 — Create impact-modeler agent

- [x] **Implementation**

**Create file**: `.github/agents/modeler.agent.md`

```markdown
---
name: impact-modeler
description: "Generate impact datasets and synthetic ensembles: CLIMADA impact calculation, SSI computation, ACE2 synthetic ensembles, and vulnerability curve sensitivity testing. Use when asked to 'generate impacts', 'run CLIMADA', 'compute SSI', 'create ensembles', or 'test vulnerability curves'. Keywords: CLIMADA, impact, SSI, ACE2, ensemble, vulnerability, hazard, exposure, storm damage."
keywords: "CLIMADA, impact modeling, SSI, ACE2, ensemble, vulnerability curves, hazard, exposure, storm damage, wind gust, LitPop"
model: claude-opus-4.6
tools: ['readFile', 'runInTerminal', 'editFiles', 'fetch', 'search']
---

# Impact Modeler

## Overview

The Impact Modeler agent owns the impact-generation pipeline: running CLIMADA impact calculations from bias-corrected ERA5 hazard data, computing Storm Severity Indices (METSSI, SOCSSI), generating synthetic ensembles (CLIMADA probabilistic module + ACE2), and testing vulnerability curve sensitivity. All outputs are Zarr stores in `data/processed/impacts/` with provenance metadata.

## Role and Expertise

You are a climate-impact scientist with deep expertise in:

- CLIMADA impact modeling framework (Hazard, Exposure, ImpactFuncSet, ImpactCalc).
- Storm Severity Index computation (METSSI based on wind speed + 98th percentile, SOCSSI weighted by population density).
- ACE2 climate emulator interpretation and post-processing.
- Vulnerability curve selection and sensitivity analysis.
- Statistical ensemble methods for robustness testing.

You ensure all impact calculations are reproducible, well-documented, and scientifically defensible.

## When to Use This Agent

- "Generate impact time series from ERA5 using CLIMADA."
- "Compute METSSI and SOCSSI storm severity indices."
- "Run the CLIMADA probabilistic ensemble for robustness testing."
- "Generate ACE2 synthetic ensemble for causality analysis."
- "Test vulnerability curve sensitivity — compare Eberenz2021 vs. Emanuel2011."
- "Compare PCA results from SSI vs. CLIMADA impacts."

## Workflow

### Phase 1 — Configure hazard

Load bias-corrected ERA5 wind gust data and convert to a CLIMADA Hazard object. Filter to ONDJFM extended winter season. See `climada-impact` skill, step 1.

### Phase 2 — Set exposure

Configure LitPop exposure with constant reference year (GDP and population held fixed) to isolate meteorological variability. See `climada-impact` skill, step 2.

### Phase 3 — Apply vulnerability curves

Select regional vulnerability curves (Eberenz 2021 for tropical, Schwierz 2010 for extratropical). For sensitivity testing, also configure Emanuel 2011 as an alternative global curve. See `climada-impact` skill, step 3.

### Phase 4 — Compute impacts

Run `ImpactCalc` and aggregate to seasonal (ONDJFM) totals. Produce impact time series $I(t, \lambda, \phi)$. See `climada-impact` skill, steps 4–5.

### Phase 5 — Compute Storm Severity Indices

Compute SSI variants for comparison with CLIMADA impact PCA:

- **METSSI** (meteorological): based on wind speed exceeding the 98th percentile, cubed.

$$\text{METSSI}(t) = \sum_{\lambda,\phi} \left( \frac{v(t,\lambda,\phi)}{v_{98}(\lambda,\phi)} - 1 \right)^3 \cdot A(\lambda,\phi)$$

where $A(\lambda,\phi)$ is the grid cell area.

- **SOCSSI** (socioeconomic): same as METSSI but weighted by population density $\rho(\lambda,\phi)$.

$$\text{SOCSSI}(t) = \sum_{\lambda,\phi} \left( \frac{v(t,\lambda,\phi)}{v_{98}(\lambda,\phi)} - 1 \right)^3 \cdot \rho(\lambda,\phi) \cdot A(\lambda,\phi)$$

Apply PCA to both and compare spatial loadings with CLIMADA impact PCA.

### Phase 6 — Validate against observations

Cross-check impact time series against known major storm events. Verify that large-impact seasons correspond to documented historical windstorms.

## Synthetic Ensembles

### CLIMADA Probabilistic Module

Generate stochastic event sets from historical storms (spatial shift + intensity perturbation). See `ensemble-generation` skill, step 1.

### ACE2 Ensemble

Run 83-member initial-condition ensemble for ONDJFM 1940–2022. Approximate wind gust via power-law proxy. Project synthetic impacts onto historical PCA basis. See `ensemble-generation` skill, steps 2–4.

## Vulnerability Curve Sensitivity Testing

Test robustness of spatial damage modes by comparing:

1. **Regional setup**: Eberenz 2021 (tropical) + Schwierz 2010 (extratropical).
2. **Global setup**: Emanuel 2011 applied uniformly.

If PCA patterns are stable across setups → modes are hazard-driven. If patterns change → modes are sensitive to vulnerability assumptions.

## Safety & Limits

- **Never modify raw data** in `data/raw/`.
- **Always save provenance** metadata (input paths, parameters, vulnerability curves used, commit SHA).
- **Warn before submitting HPC jobs exceeding 1 hour** walltime.
- Write outputs only to `data/processed/impacts/` and `data/tmp/`.
- Do not run CLIMADA with uncalibrated or unvalidated hazard data — require bias correction first.

## Outputs

- Impact Zarr stores in `data/processed/impacts/` with provenance attributes.
- SSI time series (METSSI, SOCSSI) as Zarr or NetCDF.
- Synthetic ensemble outputs in `data/processed/impacts/ace2_ensemble/`.
- Vulnerability sensitivity comparison diagnostics.

## References

- Skills: `climada-impact`, `ensemble-generation`
- Methods draft: `milestones/methods_draft.md`
- Path helper: `config/paths.py`
- Logging: `config/custom_logging.py`
- CLIMADA model: `models/climada`
- ACE2 model: `models/ACE2`
- Moemken et al. 2024 — SSI methodology
- Little et al. 2023 — storm severity indices
- Ulbrich et al. 2003 — original SSI formulation
```

### 2.4 — SSI subsection (already included in 2.3)

-- [x] **Implementation**

Covered in task 2.3 — the agent file includes the "Compute Storm Severity Indices" subsection (Phase 5) and the "Vulnerability Curve Sensitivity Testing" section with METSSI/SOCSSI formulas and comparison methodology.

### Step 2 — Verification

- [x] **Run verification**

```bash
# Validate YAML frontmatter
python -c "
import yaml, pathlib
files = [
    '.github/skills/climada-impact/SKILL.md',
    '.github/skills/ensemble-generation/SKILL.md',
    '.github/agents/modeler.agent.md',
]
for f in files:
    p = pathlib.Path(f)
    assert p.exists(), f'File not found: {f}'
    text = p.read_text()
    parts = text.split('---')
    fm = yaml.safe_load(parts[1])
    print(f'{f}: frontmatter keys = {list(fm.keys())}')
print('All frontmatter valid.')
"

# Confirm required sections
grep -l '## Workflow' .github/agents/modeler.agent.md .github/skills/climada-impact/SKILL.md .github/skills/ensemble-generation/SKILL.md

# Verify agent references both skills
grep -c 'climada-impact\|ensemble-generation' .github/agents/modeler.agent.md
```

Expected: All files found with valid frontmatter. Grep returns ≥ 2 skill references in the agent file.

---

## Step 3 — Create the Analyst Agent and Skills

> Create the `analyst` agent and its two supporting skills: `spatial-statistics` and `scientific-visualization`. This agent owns all statistical analysis, driver attribution, prediction scheme testing, and figure production.

### 3.1 — Create spatial-statistics skill

- [x] **Implementation**

**Create file**: `.github/skills/spatial-statistics/SKILL.md`

```markdown
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

# Compute covariance matrix
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
```

### 3.2 — Create scientific-visualization skill

- [x] **Implementation**

**Create file**: `.github/skills/scientific-visualization/SKILL.md`

```markdown
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

Use accessible color palettes:
- Sequential: `cmc.batlow` or `viridis`
- Diverging: `cmc.vik` or `RdBu_r`
- Categorical: `cmc.batlow` discrete or `Set2`

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

Embed provenance as figure metadata and/or caption text:

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
```

### 3.3 — Create analyst agent

- [x] **Implementation**

**Create file**: `.github/agents/analyst.agent.md`

```markdown
---
name: analyst
description: "Statistical analysis, driver attribution, prediction testing, and publication figures for storm damage modes. Use when asked to 'run PCA', 'find damage drivers', 'compute covariance', 'test prediction', 'generate paper figures', or 'analyze impact patterns'. Keywords: PCA, covariance, correlation, NAO, ENSO, prediction, composite, figures, visualization, statistics."
keywords: "PCA, statistics, covariance, correlation, driver attribution, prediction, composite analysis, visualization, figures, NAO, ENSO, QBO, Monte Carlo"
model: claude-opus-4.6
tools: ['readFile', 'runInTerminal', 'editFiles', 'fetch', 'search']
---

# Analyst

## Overview

The Analyst agent owns all statistical analysis, driver attribution, prediction scheme testing, and figure production for the SYNCDSTRMDMG project. It takes processed impact data from the Impact Modeler and produces scientific insights: covariance structures, PCA modes, driver correlations, prediction skill scores, and publication-quality figures. All outputs go to `results/figures/` and `results/tables/`.

## Role and Expertise

You are a climate statistician with deep expertise in:

- Spatial statistics: PCA/EOF analysis, covariance estimation, composite analysis.
- Climate variability modes: NAO, ENSO, QBO, and their teleconnections to NH storm damage.
- Causal and predictive inference: correlation analysis, regression, classification, cross-validation.
- Scientific visualization: matplotlib, cartopy, journal-ready figure production.
- Reproducible statistical workflows: fixed random seeds, provenance tracking, significance testing.

You prioritize scientific rigor — every statistical claim is accompanied by significance testing and sensitivity checks.

## When to Use This Agent

- "Run PCA on the CLIMADA impact data."
- "Compute the impact covariance matrix between NH regions."
- "Find atmospheric drivers of the dominant damage modes."
- "Perform composite analysis for extreme-impact seasons."
- "Test the seasonal prediction scheme for PC scores."
- "Generate publication figures for the PCA results."
- "Compare SSI-based PCA with CLIMADA impact PCA."

## Workflow

### Phase 1 — Load processed impacts

Load impact Zarr stores from `data/processed/impacts/` produced by the Impact Modeler. Verify dimensions, check for missing values, and confirm provenance metadata.

### Phase 2 — Preprocess and detrend

Apply the `spatial-statistics` skill, step 1:
- Linearly detrend at each grid cell.
- Compute seasonal anomalies ($I - \bar{I}$).
- Optionally log-transform to reduce skewness ($\log(I+1)$).

### Phase 3 — PCA and covariance analysis

Apply the `spatial-statistics` skill, steps 2–4:
- Compute impact-covariance matrix between predefined NH regions.
- Run PCA on the full impact field to extract temporal scores $a(t)$ and spatial loadings $e(\lambda, \phi)$.
- Perform extreme-impact composite analysis (top 10% seasons).

### Phase 4 — Driver correlation and attribution

Apply the `spatial-statistics` skill, steps 5–6:
- Correlate PC scores with climate indices (NAO, ENSO, QBO).
- Compute spatial correlation maps with predictor fields.
- Apply Monte Carlo permutation testing for significance.

### Phase 5 — Prediction testing

Test prediction schemes for the PC scores $a(t)$:

#### Continuous prediction

Regress $a(t)$ on predictor indices using cross-validated linear regression:

```python
from sklearn.linear_model import Ridge
from sklearn.model_selection import LeaveOneOut, cross_val_score

model = Ridge(alpha=1.0)
loo = LeaveOneOut()
scores = cross_val_score(model, predictors, pc_scores, cv=loo, scoring="r2")
```

Report $R^2$, RMSE, and correlation skill.

#### Class-based prediction

Classify seasons into top 20%, bottom 20%, and neutral:

```python
from sklearn.metrics import classification_report

thresholds = np.percentile(pc_scores, [20, 80])
classes = np.digitize(pc_scores, thresholds)  # 0=low, 1=neutral, 2=high
# Train classifier and evaluate with cross-validation
```

Report accuracy, F1 score, and Heidke Skill Score (HSS).

### Phase 6 — Generate figures

Apply the `scientific-visualization` skill to produce all publication figures:
- PCA spatial loading maps.
- PC score time series.
- Covariance/correlation heatmaps.
- Driver correlation maps.
- Prediction skill diagrams.

## Safety & Limits

- **Read only** from `data/processed/` — never modify input data.
- **Write only** to `results/figures/` and `results/tables/`.
- Always use fixed random seeds (default: 42) for stochastic procedures.
- Always report p-values and confidence intervals alongside correlation/regression results.
- Do not make causal claims from correlation alone — flag where ACE2 causality tests are needed.

## Outputs

- PCA results (scores, loadings, explained variance) as NetCDF/Zarr in `results/`.
- Covariance and correlation matrices as CSV in `results/tables/`.
- Publication-quality figures (PDF + PNG) in `results/figures/`.
- Prediction skill metrics as CSV in `results/tables/`.
- All outputs include provenance metadata (input data, parameters, commit SHA).

## References

- Skills: `spatial-statistics`, `scientific-visualization`
- Methods draft: `milestones/methods_draft.md`
- Path helper: `config/paths.py`
- Logging: `config/custom_logging.py`
- Analysis scripts: `scripts/analysis/`
```

### 3.4 — Prediction scheme subsection (already included in 3.3)

-- [x] **Implementation**

Covered in task 3.3 — the agent file includes the "Prediction testing" section (Phase 5) with both continuous prediction (Ridge regression, LOO-CV, $R^2$) and class-based prediction (top/bottom 20% classification, HSS) as described in methods draft step 6.

### Step 3 — Verification

- [x] **Run verification**

```bash
# Validate YAML frontmatter
python -c "
import yaml, pathlib
files = [
    '.github/skills/spatial-statistics/SKILL.md',
    '.github/skills/scientific-visualization/SKILL.md',
    '.github/agents/analyst.agent.md',
]
for f in files:
    p = pathlib.Path(f)
    assert p.exists(), f'File not found: {f}'
    text = p.read_text()
    parts = text.split('---')
    fm = yaml.safe_load(parts[1])
    print(f'{f}: frontmatter keys = {list(fm.keys())}')
print('All frontmatter valid.')
"

# Confirm required sections
grep -l '## Workflow' .github/agents/analyst.agent.md .github/skills/spatial-statistics/SKILL.md .github/skills/scientific-visualization/SKILL.md

# Verify agent references both skills
grep -c 'spatial-statistics\|scientific-visualization' .github/agents/analyst.agent.md

# Verify spatial-statistics skill references PCA, covariance, and composite
grep -c 'PCA\|covariance\|composite' .github/skills/spatial-statistics/SKILL.md
```

Expected: All files valid. Agent references both skills (≥ 2). Spatial-statistics skill references PCA, covariance, and composite (≥ 3).

---

## Step 4 — Register Agents and Add Integration Tests

> Update the project-wide Copilot instructions to register all three agents, add cross-agent coordination notes, and provide a lightweight smoke test to verify the agent system is discoverable.

### 4.1 — Add Agent System section to copilot-instructions.md

- [x] **Implementation**

**Edit file**: `.github/copilot-instructions.md`

Append before the `## References and Resources` section:

```markdown
## Agent System

The project uses three specialized Copilot agents that map to the core pipeline phases:

| Agent | Role | Pipeline Stages | Skills |
|-------|------|----------------|--------|
| `data-engineer` | Manage raw data through analysis-ready datasets | Download → Convert → Filter → Bias-correct → Percentiles | `data-validation`, `dask-pipeline` |
| `impact-modeler` | Generate impact datasets and synthetic ensembles | CLIMADA impacts → SSI computation → ACE2 ensembles → Sensitivity testing | `climada-impact`, `ensemble-generation` |
| `analyst` | Statistical analysis, attribution, and visualization | PCA/covariance → Driver attribution → Prediction → Figures | `spatial-statistics`, `scientific-visualization` |

### Pipeline Data Flow

```
data-engineer → impact-modeler → analyst
(data/raw/)      (data/processed/)   (results/)
     │                  │                  │
     ▼                  ▼                  ▼
 Zarr stores       Impact Zarr        Figures/Tables
 (time,lat,lon)    + provenance        + provenance
 (time,station)    attributes          metadata
```

### Pipeline Data Contracts

Each agent produces outputs in a standardized format that the downstream agent consumes:

1. **data-engineer outputs**: Zarr stores in `data/processed/` with standardized dimension names (`time`, `lat`, `lon` or `station`). Variables include bias-corrected wind gust fields and seasonal percentiles.

2. **impact-modeler outputs**: Impact Zarr stores in `data/processed/impacts/` with provenance attributes (`source`, `hazard_input`, `exposure_year`, `vulnerability_curves`, `commit`). Variables include seasonally aggregated impact time series and SSI fields.

3. **analyst outputs**: Figures in `results/figures/` (PDF for paper, PNG for presentations) and tables in `results/tables/` (CSV). All figures include provenance annotation (input data hash, parameters, commit SHA).
```

### 4.2 — Pipeline Data Contracts subsection (included in 4.1)

- [ ] **Implementation**

Covered in task 4.1 — the "Pipeline Data Contracts" subsection is included in the Agent System section.

### 4.3 — Create smoke-test script

- [x] **Implementation**

**Create file**: `scripts/tests/test_agent_files.py`

```python
"""Smoke tests for agent and skill files.

Validates that all agent and skill Markdown files have correct YAML frontmatter,
required body sections, and that referenced skill files exist on disk.

Run with: pytest scripts/tests/test_agent_files.py -v
"""

import pathlib

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
AGENTS_DIR = ROOT / ".github" / "agents"
SKILLS_DIR = ROOT / ".github" / "skills"


def _parse_frontmatter(filepath: pathlib.Path) -> dict:
    """Parse YAML frontmatter from a Markdown file."""
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    return yaml.safe_load(parts[1]) or {}


def _get_body(filepath: pathlib.Path) -> str:
    """Return the Markdown body (after frontmatter)."""
    text = filepath.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return text
    parts = text.split("---", 2)
    return parts[2] if len(parts) >= 3 else ""


# ---------------------------------------------------------------------------
# Discover files
# ---------------------------------------------------------------------------
agent_files = sorted(AGENTS_DIR.glob("*.agent.md"))
skill_files = sorted(SKILLS_DIR.glob("*/SKILL.md"))


# ---------------------------------------------------------------------------
# Agent tests
# ---------------------------------------------------------------------------
class TestAgentFiles:
    @pytest.mark.parametrize("agent_file", agent_files, ids=lambda p: p.name)
    def test_frontmatter_has_required_keys(self, agent_file: pathlib.Path):
        fm = _parse_frontmatter(agent_file)
        assert "name" in fm, f"{agent_file.name}: missing 'name' in frontmatter"
        assert "description" in fm, f"{agent_file.name}: missing 'description' in frontmatter"
        assert "tools" in fm, f"{agent_file.name}: missing 'tools' in frontmatter"

    @pytest.mark.parametrize("agent_file", agent_files, ids=lambda p: p.name)
    def test_has_required_sections(self, agent_file: pathlib.Path):
        body = _get_body(agent_file)
        for section in ("## Overview", "## Workflow", "## Safety & Limits"):
            assert section in body or section.replace("& ", "and ") in body, (
                f"{agent_file.name}: missing section '{section}'"
            )

    @pytest.mark.parametrize("agent_file", agent_files, ids=lambda p: p.name)
    def test_referenced_skills_exist(self, agent_file: pathlib.Path):
        body = _get_body(agent_file)
        # Look for skill references in the "Skills:" line
        for line in body.splitlines():
            if line.strip().lower().startswith("- skills:") or line.strip().lower().startswith("skills:"):
                # Extract backtick-quoted skill names
                import re

                skill_names = re.findall(r"`([a-z][a-z0-9-]+)`", line)
                for skill_name in skill_names:
                    skill_path = SKILLS_DIR / skill_name / "SKILL.md"
                    assert skill_path.exists(), (
                        f"{agent_file.name}: references skill '{skill_name}' "
                        f"but {skill_path} does not exist"
                    )


# ---------------------------------------------------------------------------
# Skill tests
# ---------------------------------------------------------------------------
class TestSkillFiles:
    @pytest.mark.parametrize("skill_file", skill_files, ids=lambda p: p.parent.name)
    def test_frontmatter_has_required_keys(self, skill_file: pathlib.Path):
        fm = _parse_frontmatter(skill_file)
        assert "name" in fm, f"{skill_file}: missing 'name' in frontmatter"
        assert "description" in fm, f"{skill_file}: missing 'description' in frontmatter"

    @pytest.mark.parametrize("skill_file", skill_files, ids=lambda p: p.parent.name)
    def test_has_workflow_section(self, skill_file: pathlib.Path):
        body = _get_body(skill_file)
        assert "## Workflow" in body or "## Step-by-Step Workflow" in body, (
            f"{skill_file}: missing '## Workflow' section"
        )
```

### 4.4 — Create tests __init__.py

- [x] **Implementation**

**Create file**: `scripts/tests/__init__.py`

```python
```

### Step 4 — Verification

- [x] **Run verification**

```bash
# Run the smoke tests
cd /work/gg0304/g260230/projects/SYNCDSTRMDMG
pytest scripts/tests/test_agent_files.py -v

# Verify agent system section in copilot-instructions.md
grep -c 'data-engineer\|impact-modeler\|analyst' .github/copilot-instructions.md
```

Expected: All pytest tests pass. Grep returns ≥ 6 (each agent mentioned at least twice in copilot-instructions.md).

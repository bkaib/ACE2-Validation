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

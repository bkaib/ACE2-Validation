## Plan: Compute ETCCDI Indices for ERA5 and ACE2

This plan implements the computation of absolute and relative ETCCDI climate indices for both ERA5 (1981-2010) and ACE2 ensemble data (2001-2010). The workflow uses xclim library for WMO-compliant computations with day-of-year percentile thresholds computed from the ERA5 baseline period. All indices are computed at annual temporal resolution on the ACE2 grid (1° × 1°).

### Branch Strategy

- Base branch: `main`
- Feature branch: `feature/compute-etccdi-indices`

---

### Step 1 — Setup dependencies and verify data availability

Set up the Python environment with xclim and verify that preprocessed ERA5 and ACE2 data are available and CF-compliant.

- [ ] 1.1 Add xclim to `environment.yml` (version ≥0.47 for full ETCCDI support)
- [ ] 1.2 Create verification script `scripts/02-compute-etccdi/verify_inputs.py` to check:
  - ERA5 regridded data in `data/processed/ERA5/1D/ACE2GRID/{TMP2m,PRATEsfc,10si}/`
  - ACE2 daily data in `data/raw/ace2-ensembles/1D/{scenario}/ensemble_{N}.nc`
  - CF-compliance of variable names, units, and metadata
- [ ] 1.3 Create output directories: `data/processed/ETCCDI/ERA5/`, `data/processed/ETCCDI/ACE2/`, `data/processed/ETCCDI/THRESHOLDS/`
- [ ] 1.4 Update `config/paths.py` with ETCCDI output paths

**Verification**: Run verification script; all datasets found and CF-compliant.

**Files touched**:
- `environment.yml`
- `scripts/02-compute-etccdi/verify_inputs.py`
- `config/paths.py`

---

### Step 2 — Fix ACE2 precipitation units

Convert ACE2 PRATEsfc from kg/m²/s (6-hourly rate) to mm (daily total) by multiplying the daily sum by the timestep duration (21600s for 6H).

- [ ] 2.1 Create conversion utility function in `scripts/02-compute-etccdi/convert_ace2_units.py`:
  - Read ACE2 daily ensemble file with `pr` variable
  - Multiply `pr` by 21600 (6H in seconds) to convert kg/m²/s → kg/m² ≈ mm
  - Update units attribute to 'mm'
  - Add processing_note to global attributes
- [ ] 2.2 Process all ACE2 ensemble files (48 files: 4 scenarios × 12 members)
- [ ] 2.3 Save converted files to `data/processed/ace2-ensembles/1D/{scenario}/ensemble_{N}_corrected.nc`
- [ ] 2.4 Create validation check: compare sample daily totals before/after conversion

**Verification**: Spot-check converted files; pr units are 'mm', values are ~4× original (× 21600 / 4 timestamps).

**Files touched**:
- `scripts/02-compute-etccdi/convert_ace2_units.py`
- `data/processed/ace2-ensembles/1D/` (new files)

---

### Step 3 — Compute ERA5 percentile thresholds (baseline: 1981-2010)

Calculate day-of-year percentiles (10th, 90th, 95th) for temperature and wind from ERA5 baseline period following WMO bootstrap method. Save thresholds for use in relative indices.

- [ ] 3.1 Create `scripts/02-compute-etccdi/compute_percentiles.py` with functions:
  - Load ERA5 tasmax, tasmin, sfcWind_mean for 1981-2010 from `data/processed/ERA5/1D/ACE2GRID/`
  - Use `xclim.core.calendar.percentile_doy()` with 5-day window for each grid cell
  - Compute 10th percentile for TN (TNn10p), TX (TXn10p)
  - Compute 90th percentile for TN (TNn90p), TX (TXn90p)
  - Compute 95th percentile for sfcWind_mean (FG95p threshold)
- [ ] 3.2 Apply bootstrap method for in-base period (Zhang et al. 2005) to avoid inhomogeneity
- [ ] 3.3 Save thresholds to `data/processed/ETCCDI/THRESHOLDS/`:
  - `TN_p10_doy.nc` (shape: [365, lat, lon])
  - `TX_p10_doy.nc`
  - `TN_p90_doy.nc`
  - `TX_p90_doy.nc`
  - `sfcWind_p95_doy.nc`
- [ ] 3.4 Create diagnostic plots: spatial maps of Jan 1 and Jul 1 percentiles

**Verification**: Check threshold files exist with shape (365, lat, lon); percentile values are realistic (e.g., TX_p90 > TX_p10 everywhere).

**Files touched**:
- `scripts/02-compute-etccdi/compute_percentiles.py`
- `data/processed/ETCCDI/THRESHOLDS/*.nc` (created)
- `results/figures/02-compute-etccdi/thresholds_diagnostics.png`

---

### Step 4 — Compute absolute ETCCDI indices for ERA5

Compute absolute indices (TXx, TNn, Rx1day, FXx) from ERA5 data for the baseline period (1981-2010). These indices do not require percentile thresholds.

- [ ] 4.1 Create `scripts/02-compute-etccdi/compute_absolute_indices.py` using xclim indicators:
  - **TXx**: `xclim.atmos.tx_max()` — annual max of daily max temperature
  - **TNn**: `xclim.atmos.tn_min()` — annual min of daily min temperature
  - **Rx1day**: `xclim.atmos.max_1day_precipitation_amount()` — annual max 1-day precipitation
  - **FXx**: `xclim.atmos.wind_speed_from_vector()` + max — annual max of daily max wind speed
- [ ] 4.2 Load ERA5 daily data: tasmax, tasmin, pr (multiply by 1000 to convert m→mm), sfcWind_max
- [ ] 4.3 Apply `resample(time='YE')` for annual aggregation
- [ ] 4.4 Save to `data/processed/ETCCDI/ERA5/{index}_1981-2010.nc` (one file per index)
- [ ] 4.5 Add CF-compliant metadata (long_name, units, references)

**Verification**: Check output files have shape (30, lat, lon); TXx > TNn everywhere; Rx1day ≥ 0.

**Files touched**:
- `scripts/02-compute-etccdi/compute_absolute_indices.py`
- `data/processed/ETCCDI/ERA5/TXx_1981-2010.nc`
- `data/processed/ETCCDI/ERA5/TNn_1981-2010.nc`
- `data/processed/ETCCDI/ERA5/Rx1day_1981-2010.nc`
- `data/processed/ETCCDI/ERA5/FXx_1981-2010.nc`

---

### Step 5 — Compute relative ETCCDI indices for ERA5

Compute relative indices (TX90p, TN10p, FG95p, WSDI, R10, CWD) from ERA5 data using the percentile thresholds computed in Step 3.

- [ ] 5.1 Create `scripts/02-compute-etccdi/compute_relative_indices.py` using xclim indicators:
  - **TX90p**: `xclim.atmos.tx90p()` — fraction of days when tasmax > 90th percentile
  - **TN10p**: `xclim.atmos.tn10p()` — fraction of days when tasmin < 10th percentile
  - **FG95p**: `xclim.atmos.windy_days()` — count of days when sfcWind_mean > 95th percentile
  - **WSDI**: `xclim.atmos.warm_spell_duration_index()` — consecutive days (≥6) with tasmax > 90th percentile
  - **R10**: `xclim.atmos.wetdays()` with threshold=10mm — count of days with pr ≥ 10mm
  - **CWD**: `xclim.atmos.maximum_consecutive_wet_days()` with threshold=1mm
- [ ] 5.2 Load ERA5 daily data and percentile thresholds from Step 3
- [ ] 5.3 Apply per_doy parameter for TX90p, TN10p, FG95p, WSDI to use day-of-year thresholds
- [ ] 5.4 Aggregate to annual resolution: `resample(time='YE')`
- [ ] 5.5 Save to `data/processed/ETCCDI/ERA5/{index}_1981-2010.nc`

**Verification**: TX90p and TN10p values are fractions in [0,1]; R10 ≥ 0; CWD ≥ 0 and < 365.

**Files touched**:
- `scripts/02-compute-etccdi/compute_relative_indices.py`
- `data/processed/ETCCDI/ERA5/TX90p_1981-2010.nc`
- `data/processed/ETCCDI/ERA5/TN10p_1981-2010.nc`
- `data/processed/ETCCDI/ERA5/FG95p_1981-2010.nc`
- `data/processed/ETCCDI/ERA5/WSDI_1981-2010.nc`
- `data/processed/ETCCDI/ERA5/R10_1981-2010.nc`
- `data/processed/ETCCDI/ERA5/CWD_1981-2010.nc`

---

### Step 6 — Compute absolute ETCCDI indices for ACE2 ensembles

Compute absolute indices for all 48 ACE2 ensemble members (4 scenarios × 12 members) for the period 2001-2010.

- [ ] 6.1 Adapt `compute_absolute_indices.py` to process ACE2 ensemble files:
  - Loop over scenarios: `2000v1940`, `2000v1950`, `2000v1979`, `2000v2020`
  - Loop over ensemble members: 0-11
  - Load corrected daily data: tasmax, tasmin, pr (already in mm), sfcWind_max
- [ ] 6.2 Compute TXx, TNn, Rx1day, FXx using same xclim functions as Step 4
- [ ] 6.3 Save per-member results to `data/processed/ETCCDI/ACE2/{scenario}/ensemble_{N}/{index}_2001-2010.nc`
- [ ] 6.4 Add ensemble member and scenario to global attributes
- [ ] 6.5 Implement parallel processing with dask.distributed for efficiency on HPC

**Verification**: Check output structure: 4 scenarios × 12 members × 4 indices × (10 years, lat, lon).

**Files touched**:
- `scripts/02-compute-etccdi/compute_absolute_indices.py` (extended)
- `data/processed/ETCCDI/ACE2/{scenario}/ensemble_{N}/{index}_2001-2010.nc` (48×4 files)

---

### Step 7 — Compute relative ETCCDI indices for ACE2 ensembles

Compute relative indices for ACE2 ensembles using the ERA5 percentile thresholds from Step 3 (same baseline for fair comparison).

- [ ] 7.1 Adapt `compute_relative_indices.py` to process ACE2 ensemble files:
  - Load ERA5 percentile thresholds from Step 3
  - Load ACE2 daily data (tasmax, tasmin, pr, sfcWind_mean) for each ensemble member
  - Ensure time coordinates align with day-of-year thresholds
- [ ] 7.2 Compute TX90p, TN10p, FG95p, WSDI, R10, CWD using ERA5 thresholds
- [ ] 7.3 Save per-member results to `data/processed/ETCCDI/ACE2/{scenario}/ensemble_{N}/{index}_2001-2010.nc`
- [ ] 7.4 Handle leap years correctly (xclim handles noleap calendars)
- [ ] 7.5 Use dask for memory-efficient processing on HPC

**Verification**: TX90p and TN10p are in [0,1]; WSDI and CWD are non-negative integers.

**Files touched**:
- `scripts/02-compute-etccdi/compute_relative_indices.py` (extended)
- `data/processed/ETCCDI/ACE2/{scenario}/ensemble_{N}/{index}_2001-2010.nc` (48×6 files)

---

### Step 8 — Compute ACE2 ensemble statistics

Calculate ensemble mean, standard deviation, and 5th-95th percentile range across the 12 members for each scenario and index.

- [ ] 8.1 Create `scripts/02-compute-etccdi/compute_ensemble_stats.py`:
  - Load all 12 ensemble members for each scenario and index
  - Compute ensemble mean: `xarray.concat(..., dim='member').mean(dim='member')`
  - Compute ensemble std: `.std(dim='member')`
  - Compute ensemble percentiles: `.quantile([0.05, 0.95], dim='member')`
- [ ] 8.2 Save statistics to `data/processed/ETCCDI/ACE2/{scenario}/ensemble_stats/{index}_{statistic}_2001-2010.nc`
  - Files: `{index}_mean.nc`, `{index}_std.nc`, `{index}_p05.nc`, `{index}_p95.nc`
- [ ] 8.3 Optionally create multi-index NetCDF with all statistics in one file
- [ ] 8.4 Parallelize over scenarios and indices using dask

**Verification**: Ensemble mean is within [min, max] of individual members; std ≥ 0; p05 < mean < p95.

**Files touched**:
- `scripts/02-compute-etccdi/compute_ensemble_stats.py`
- `data/processed/ETCCDI/ACE2/{scenario}/ensemble_stats/{index}_{statistic}_2001-2010.nc`

---

### Step 9 — Validation and sanity checks

Implement automated validation checks to ensure computed indices meet physical constraints and CF conventions.

- [ ] 9.1 Create `scripts/02-compute-etccdi/validate_indices.py` with checks:
  - **Physical constraints**: TXx > TNn everywhere, R10 ≥ 0, Rx1day ≥ R10, CWD < 366
  - **Range checks**: TX90p and TN10p in [0,1], FG95p ≥ 0
  - **Spatial coherence**: No NaN values in land areas, expected patterns (e.g., TXx higher in tropics)
  - **Temporal consistency**: No jumps > 3σ between consecutive years
  - **CF compliance**: Check standard_name, units, coordinates
- [ ] 9.2 Run validation on ERA5 indices (1981-2010)
- [ ] 9.3 Run validation on ACE2 ensemble members and statistics (2001-2010)
- [ ] 9.4 Generate validation report: `results/tables/etccdi_validation_report.txt`
- [ ] 9.5 Create diagnostic plots: histograms of index values, spatial maps of outliers

**Verification**: Validation script completes without critical errors; all indices pass physical constraint checks.

**Files touched**:
- `scripts/02-compute-etccdi/validate_indices.py`
- `results/tables/etccdi_validation_report.txt`
- `results/figures/02-compute-etccdi/validation_diagnostics.png`

---

### Step 10 — HPC batch processing script

Create SLURM batch script for efficient computation on DKRZ Levante HPC cluster.

- [ ] 10.1 Create `jobs/compute_etccdi.sh` SLURM script:
  - Request compute node with ≥256GB RAM (for xclim with dask)
  - Set environment: load conda, activate environment
  - Run scripts in sequence: verify → convert units → percentiles → absolute → relative → ensemble stats → validate
  - Set dask worker configuration for memory efficiency
- [ ] 10.2 Add logging to `logs/02-compute-etccdi/`
- [ ] 10.3 Test on subset (1 scenario, 2 members) before full run
- [ ] 10.4 Document expected runtime and resource usage in script header

**Verification**: Test job completes successfully on subset; full job can be queued.

**Files touched**:
- `jobs/compute_etccdi.sh`
- `logs/02-compute-etccdi/compute_etccdi_{timestamp}.log`

---

### Step 11 — Documentation

Document the ETCCDI computation methodology, assumptions, and results in the project documentation.

- [ ] 11.1 Add detailed entry to `docs/02-compute-etccdi-documentation.md` under "Quick Notes" with date 2026-07-02:
  - Library used: xclim v{version}
  - Percentile method: WMO bootstrap method with day-of-year 5-day window
  - Baseline period: ERA5 1981-2010
  - Evaluation period: ACE2 2001-2010
  - Unit conversions applied (ACE2 pr: kg/m²/s × 21600s → mm)
  - Output structure and file naming conventions
  - Validation results summary
- [ ] 11.2 Update `milestones/02-compute-etccdi.md` to mark steps as completed
- [ ] 11.3 Create README in `data/processed/ETCCDI/` explaining directory structure
- [ ] 11.4 Document WSD threshold choice (95th percentile) and comparison to WSDI

**Verification**: Documentation is complete, clear, and references all key decisions and data sources.

**Files touched**:
- `docs/02-compute-etccdi-documentation.md`
- `milestones/02-compute-etccdi.md`
- `data/processed/ETCCDI/README.md` (created)

---

## Quality Checklist

- [x] Every step has checkboxes
- [x] Every step has a Verification section
- [x] Every step has Files touched section
- [x] Steps are ordered for independent commits
- [x] New dependencies noted (xclim)
- [x] Exact file paths from config.paths referenced
- [x] Web research cited (xclim docs, WMO ETCCDI definitions)

## Notes

- **Parallelization**: Steps 6-8 benefit from dask.distributed on HPC
- **Memory**: xclim uses lazy evaluation with dask; configure chunk sizes for 256GB RAM
- **ACE2 unit conversion**: Critical step — verify multiplier (21600s for 6H) before proceeding
- **Percentile computation**: Most computationally expensive step; consider caching
- **WSD definition**: Non-standard index, defined analogously to WSDI with 95th percentile threshold
- **Leap years**: xclim handles noleap calendars automatically; verify ERA5 and ACE2 calendar types

# Milestone 02 — Preprocess ERA5 & ACE2 Data

## Goal
Prepare ERA5 and ACE2 simulation output into a clean, analysis-ready format on a common grid.

## Background
ERA5 is the reference dataset covering 1941–2022. ACE2 output must be regridded to the ERA5 grid (or vice versa) so that grid-cell-level comparisons are valid. Consistent units, calendar handling, and variable naming are essential before any index computation.

## Target
- ERA5 and ACE2 data on a common grid, same variable names and units
- Daily time series for T2m, pr, sfcWind for the full available period of each dataset
- Processed files stored in `data/processed/`

## Steps

### ERA5
- [ ] Confirm available ERA5 variables, resolution, and time coverage (`data/raw/ERA5/`)
- [ ] Check calendar and missing values
- [ ] Regrid ERA5 to ACE2 native grid (or vice versa) — document chosen target grid
- [ ] Standardise variable names and units (K → °C for T2m; check pr units kg m⁻² s⁻¹ vs mm/day)
- [ ] Save processed ERA5 as Zarr/NetCDF to `data/processed/ERA5/`

### ACE2 ensemble
- [ ] Validate raw output files (completeness, time axis, variable units)
- [ ] Rechunk / convert to Zarr for efficient Dask access
- [ ] Apply any necessary unit conversions
- [ ] Save processed ensemble to `data/processed/ACE2/`

### Quality control
- [ ] Global mean time series plots for T2m, pr, sfcWind — ERA5 vs ACE2 ensemble mean
- [ ] Flag any outlier members or time steps

## Outputs
- `data/processed/ERA5/` — regridded, unit-standardised ERA5
- `data/processed/ACE2/` — rechunked, unit-standardised ACE2 ensemble
- `scripts/preprocessing/` — preprocessing scripts

## Dependencies
- Milestone 01 completed (ACE2 raw output available)
- ERA5 raw data downloaded to `data/raw/ERA5/`

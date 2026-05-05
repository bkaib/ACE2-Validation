# Milestone 05 — Extreme Value Analysis

## Goal
Fit extreme value distributions to ERA5 and ACE2 data and estimate return levels to assess whether ACE2 reproduces the far tail of the climate distribution.

## Background
This milestone addresses Research Question 2: *How does ACE2's representation of extreme value tail behavior—specifically 50- and 100-year return levels—compare to ERA5?*

The ACE2 ensemble compensates for the shorter validation window: pooling N members × T years provides an effective sample of N × T years for return level estimation.

## Methods

| Variable | Distribution | Input |
|---|---|---|
| T2m, sfcWind | GEV (block maxima) | Annual maxima per grid cell |
| pr | GPD (threshold exceedances) | Daily pr > 95th percentile |

Return periods: 10, 50, and 100 years.

## Steps

### ERA5
- [ ] Extract annual block maxima (T2m, sfcWind) and threshold exceedances (pr) for 1941–2022
- [ ] Fit GEV / GPD per grid cell using MLE (e.g. `lmoments3`, `scipy.stats`, or `xarray-extremes`)
- [ ] Estimate 10-, 50-, 100-year return levels with 95% bootstrap confidence intervals
- [ ] Save GEV/GPD parameters and return level fields

### ACE2 ensemble
- [ ] Pool annual maxima / exceedances across all ensemble members (treating each member-year as independent)
- [ ] Fit GEV / GPD per grid cell to the pooled sample
- [ ] Estimate return levels and ensemble uncertainty (bootstrap over pooled sample + ensemble spread)
- [ ] Save GEV/GPD parameters and return level fields

### Comparison
- [ ] Return level maps: ERA5 vs ACE2 (bias maps for each return period and variable)
- [ ] Return level plots at selected grid cells / regions: ERA5 (+ CI) vs ACE2 (+ CI)
- [ ] Scatter plots: ERA5 vs ACE2 return levels across all grid cells (coloured by latitude/region)
- [ ] Assess whether ERA5 return levels fall within ACE2 ensemble uncertainty bounds

## Outputs
- `data/processed/return_levels/` — GEV/GPD parameters and return level fields
- `results/figures/return_levels/` — maps, return level plots, scatter plots
- `results/tables/return_level_metrics.csv`
- `scripts/analysis/extreme_value_analysis.py`
- `notebooks/05-extreme-value-analysis.ipynb`

## Dependencies
- Milestone 02 completed (processed daily data available)

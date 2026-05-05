# Milestone 06 — Wind Extremes Analysis

## Goal
Dedicated analysis of wind extremes in ACE2 vs ERA5, supporting both this validation project and the companion wind sensitivity analysis project.

## Background
This milestone addresses Research Question 3: *Is ACE2 recovering wind extremes similar to ERA5?*

Wind extremes receive separate treatment because they are the primary variable of interest for the companion sensitivity project and because storm-track dynamics impose specific spatial coherence requirements beyond what scalar indices capture.

## Steps

### Distribution comparison
- [ ] Annual wind maxima distributions: ERA5 vs ACE2 ensemble (global and per region)
- [ ] Empirical CDFs and QQ-plots at selected representative grid cells
- [ ] GEV fit comparison (from Milestone 05) specifically for sfcWind

### Spatial coherence of extreme wind events
- [ ] Define extreme wind events: grid cells where sfcWind exceeds 99th percentile on the same day
- [ ] Compute extent and clustering of co-occurring extreme wind grid cells per event
- [ ] Compare event size distributions: ERA5 vs ACE2 ensemble members
- [ ] Storm track proxy: track spatial footprint of top-N annual wind events in ERA5 and ACE2

### Inter-annual variability
- [ ] Annual 99th percentile wind speed time series (2001–2010): ERA5 vs ACE2 ensemble mean ± spread
- [ ] Assess whether ERA5 inter-annual variability is within ACE2 ensemble spread

### Seasonal and regional breakdown
- [ ] Wind extreme frequency by season (DJF, MAM, JJA, SON): ERA5 vs ACE2
- [ ] Regional focus: North Atlantic, North Pacific, Southern Ocean storm tracks

## Outputs
- `results/figures/wind/` — CDFs, QQ-plots, spatial footprint maps, time series
- `results/tables/wind_metrics.csv`
- `notebooks/06-wind-extremes.ipynb`

## Dependencies
- Milestone 02 completed (processed sfcWind available)
- Milestone 05 useful but not strictly required

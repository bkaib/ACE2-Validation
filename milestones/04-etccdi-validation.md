# Milestone 04 — ETCCDI Validation

## Goal
Quantitatively compare ACE2 and ERA5 ETCCDI index climatologies to assess ACE2's ability to reproduce spatial patterns and magnitudes of climate extremes.

## Background
This milestone addresses Research Question 1: *To what extent does ACE2 accurately reproduce the spatial and temporal patterns of IPCC ETCCDI indices compared to ERA5?*

The comparison is restricted to the held-out test period (2001–2010) to avoid evaluating ACE2 on its training data.

## Steps

### Spatial analysis
- [ ] Compute climatological mean of each ETCCDI index over 2001–2010 for ERA5 and ACE2 ensemble mean
- [ ] Spatial bias maps: ACE2 ensemble mean − ERA5 (for each index)
- [ ] Compute area-weighted global mean bias and RMSE per index
- [ ] Compute spatial correlation (pattern correlation) per index

### Taylor diagrams
- [ ] Produce Taylor diagrams per index showing ERA5 as reference and ACE2 ensemble members as dots
- [ ] Highlight ensemble mean and ensemble spread

### Regional analysis
- [ ] Define key regions (tropics, mid-latitudes, polar) for area-weighted regional means
- [ ] Box plots / violin plots of regional distributions: ERA5 vs ACE2 ensemble

### Temporal analysis
- [ ] Annual time series of global-mean index values (ERA5 vs ACE2 ensemble mean ± spread)

## Outputs
- `results/figures/etccdi/` — bias maps, Taylor diagrams, regional plots, time series
- `results/tables/etccdi_metrics.csv` — global/regional bias, RMSE, correlation per index
- `notebooks/04-etccdi-validation.ipynb`

## Dependencies
- Milestone 03 completed (ETCCDI indices computed)

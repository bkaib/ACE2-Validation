# Milestone 07 — Compound Extremes (Exploratory)

## Goal
Assess whether ACE2 preserves the multivariate dependencies required to simulate compound extremes.

## Background
This milestone addresses Research Question 4 (exploratory): *Does ACE2 maintain the multivariate dependencies required to simulate compound extremes, or does it exhibit a decoupling of physical variables compared to ERA5?*

Compound extremes (e.g. concurrent hot-dry or cold-wet events) depend on the joint tail behaviour of multiple variables. Even if each marginal distribution is well reproduced, incorrect dependence structure would invalidate ACE2 for compound event analysis.

> **Note**: This milestone is exploratory and contingent on variable availability and project capacity. It may be descoped if resources are limited.

## Steps

### Variable pairs
- Hot-dry: T2m (high) ∧ pr (low)
- Cold-wet: T2m (low) ∧ pr (high)
- Wind-temperature: sfcWind (high) ∧ T2m (low) — cold storm events

### Joint exceedance probabilities
- [ ] Compute empirical joint exceedance probabilities P(T2m > q₁ ∧ pr < q₂) per grid cell
- [ ] Compare ERA5 vs ACE2 ensemble mean joint exceedance maps
- [ ] Bias maps for joint exceedance probabilities

### Copula analysis
- [ ] Fit empirical copulas to (T2m, pr) and (T2m, sfcWind) at selected locations / regions
- [ ] Compare copula structure: ERA5 vs ACE2 ensemble
- [ ] Tail dependence coefficients (upper/lower) — ERA5 vs ACE2

### Temporal co-occurrence
- [ ] Event co-occurrence frequency: how often are two variables simultaneously extreme?
- [ ] Compare ERA5 and ACE2 ensemble co-occurrence rates globally and by region

## Outputs
- `results/figures/compound/` — joint exceedance maps, copula plots, co-occurrence maps
- `results/tables/compound_metrics.csv`
- `notebooks/07-compound-extremes.ipynb`

## Dependencies
- Milestone 02 completed (T2m, pr, sfcWind processed)
- Milestones 04 and 05 recommended (marginal validation completed first)

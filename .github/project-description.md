# Goal of the Project

1. ACE2 can reproduce basic statistics of the ERA5 climate well (see Watt-Meyer et al. 2025).
2. It is not yet shown how well ACE2 can reproducte extreme statistics of ERA5.
3. In order to use it for simulations and analysis of extremes, this validation is useful.

# Purpose of the Validation

- If ACE2 can reproduce the extreme value tail behavior of ERA5, then it can be used to run large ensembles of climate simulations to better understand the risks of extreme events under climate change at a fraction of the computational cost of running large ensembles of physical climate model simulations.
- If ACE2 cannot reproduce the extreme value tail behavior of ERA5, then it may not be suitable for simulating extreme events, and further development may be needed to improve its performance in this regard.


# Research Questions

1. To what extent does the ACE2 emulator accurately reproduce the spatial and temporal patterns of IPCC ETCCDI indices compared to ERA5 reanalysis?
2. How does the ACE2 emulator’s representation of extreme value tail behavior—specifically 50- and 100-year return levels—compare to the physical limits observed in ERA5?
3. Is ACE2 recovering wind extremes similar to ERA5?
4. (Does ACE2 maintain the multivariate dependencies required to simulate compound extremes (e.g., concurrent hot-dry or cold-wet events), or does it exhibit a decoupling of physical variables compared to ERA5?)

## Methodology / Approach

### 1. Data

- **ERA5**: ECMWF reanalysis, 1941–2022 (reference period). Variables: near-surface temperature (T2m), precipitation (pr), 10-m wind speed (sfcWind). Native resolution to be confirmed; regrid to ACE2 output grid for direct comparison.
- **ACE2**: Watt-Meyer et al. (2025) atmospheric emulator. Run as a large ensemble (target: ≥ 50 members) over the held-out test period **2001–2010**, initialised from ERA5 states. The test period is used as the primary validation window because ACE2 was not trained on it.

| Dataset | Period | Role |
|---|---|---|
| ERA5 | 1941–2022 | Reference for ETCCDI indices and return levels |
| ACE2 ensemble | 2001–2010 (held-out) | Primary validation window |
| ACE2 over training period | 1941–2000 | Sensitivity / supplementary only |

### 2. Extreme Indices (ETCCDI)

Compute a subset of IPCC ETCCDI indices from both ERA5 and ACE2 ensemble:

- **Temperature**: TXx (annual max Tmax), TNn (annual min Tmin), TX90p, TN10p, WSDI
- **Precipitation**: R10, Rx1day, CWD (Consecutive Wet Days)    
- **Wind** (non-standard extension): FG95p (Extreme Wind Days), FXx (Maximum Wind Gust / Wind Speed), WSD (Windy Spell Duration)

Spatial maps and area-weighted global/regional means will be compared. Metrics: bias, RMSE, spatial correlation (Taylor diagrams).

### 3. Extreme Value Analysis

- Fit **GEV distributions** to annual block maxima (temperature, wind) and **GPD** to threshold exceedances (precipitation) for each grid cell.
- Estimate **10-, 50-, and 100-year return levels** for ERA5 (1941–2022) and for the ACE2 ensemble (pooled across members, 2001–2010).
- The ensemble approach compensates for ACE2's shorter validation window: pooling $N$ ensemble members over $T$ years gives an effective sample of $N \times T$ years for return level estimation.
- Uncertainty bounds via bootstrap (ERA5) and ensemble spread (ACE2).

### 4. Wind Extremes (link to sensitivity analysis project)

Wind extremes receive dedicated analysis to support the companion sensitivity project:
- Compare annual wind maxima distributions (ERA5 vs ACE2 ensemble)
- Assess spatial coherence of extreme wind events (storm tracks, clustering)
- Evaluate whether ACE2 ensemble spread captures ERA5 inter-annual variability in wind extremes

### 5. Compound Extremes (exploratory)

If variable availability permits (T2m + pr or T2m + sfcWind):
- Compute joint exceedance probabilities for concurrent hot-dry and cold-wet events
- Compare empirical copulas between ERA5 and ACE2 ensemble
- Assess whether ACE2 preserves inter-variable dependencies in the tail

# Expected Outcomes
 
- Quantitative assessment of ACE2's ability to reproduce ETCCDI index climatologies (spatial patterns, magnitudes, biases)
- Return level maps for temperature, precipitation, and wind with uncertainty estimates, benchmarked against ERA5
- A clear statement on whether ACE2 is fit-for-purpose as an ensemble tool for extreme event analysis
- Guidance on which extremes ACE2 represents well vs. where it shows systematic biases

# Milestones

- 01-generate-ace2-simulations.md — Run ≥50-member ACE2 ensemble (2001–2010)
- 02-preprocess-data.md — Regrid, unit-standardise, rechunk ERA5 & ACE2
- 03-compute-etccdi-indices.md — Compute ETCCDI + wind-extension indices
- 04-etccdi-validation.md — Spatial/temporal comparison, Taylor diagrams (RQ1)
- 05-extreme-value-analysis.md — GEV/GPD fits; 10/50/100‑yr return levels (RQ2)
- 06-wind-extremes.md — Wind distributions, storm tracks, spatial coherence (RQ3)
- 07-compound-extremes.md — Joint exceedance & copula analysis (RQ4, exploratory)
- 08-synthesis-reporting.md — Final figures, tables, and conclusions

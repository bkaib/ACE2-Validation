# Goal of the Project

This project addresses the **extreme event and tail statistics** component of a comprehensive validation of the ACE2 atmospheric emulator. The supervisor concurrently validates broader climatic properties (seasonal climatology, mean circulation, low-frequency modes, surface fluxes, and stability). This document focuses specifically on extremes.

**Key objectives:**
1. ACE2 reproduces basic climate statistics well (Watt-Meyer et al. 2025)
2. It is not yet demonstrated whether ACE2 reproduces the **extreme value tail behavior** of ERA5
3. Large ensemble validation of extremes is essential for fitness-for-purpose as an ensemble tool for extreme risk analysis

# Purpose of This Validation (Extremes Component)

- **If ACE2 reproduces extreme tail behavior**: it is a viable tool for running large ensembles of climate simulations to assess risks of extreme events under climate change, at a fraction of the cost of traditional coupled model ensembles
- **If ACE2 fails to reproduce extreme tail behavior**: further development is needed to improve its performance in extreme event simulation, limiting its utility for ensemble risk studies
- The ensemble approach (≥50 members) compensates for ACE2's shorter validation window, enabling robust return-level estimation comparable to the long ERA5 record (1941–2022)


# Research Questions — Extremes Focus

This project addresses the extreme event and tail statistics component of the broader ACE2 validation. The supervisor is separately validating seasonal climatology, mean circulation, low-frequency modes (NAO, ENSO, IPO), and surface flux biases for coupled model embedding.

**Extremes-focused research questions:**

1. **ETCCDI Index Climatology (RQ1):** To what extent does ACE2 accurately reproduce the spatial and temporal patterns of IPCC ETCCDI extreme indices compared to ERA5 reanalysis?

2. **Extreme Value Tails (RQ2):** How does ACE2's representation of extreme value tail behavior—specifically 10-, 50-, and 100-year return levels—compare to ERA5?

3. **Wind Extremes (RQ3):** Is ACE2 recovering wind extremes (annual maxima distributions, spatial coherence of storm tracks) similar to ERA5?

4. **Compound Extremes (RQ4, exploratory):** Does ACE2 maintain the multivariate dependencies required to simulate compound extremes (e.g., concurrent hot-dry or cold-wet events), or does it exhibit decoupling compared to ERA5?

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

This project delivers the **extreme events validation** section of the broader ACE2 climate validation, including:

- Quantitative assessment of ACE2's ability to reproduce ETCCDI index climatologies (spatial patterns, magnitudes, biases) via bias maps and spatial correlation metrics
- Return level maps for temperature, precipitation, and wind (10-, 50-, 100-year) with uncertainty estimates, benchmarked against ERA5
- Analysis of wind extremes: annual maxima distributions, spatial coherence of extreme wind events, and inter-annual variability
- Assessment of compound extremes: joint exceedance probabilities and copula structure for temperature-precipitation and temperature-wind pairs
- A clear quantitative statement on whether ACE2 is fit-for-purpose for ensemble-based extreme event analysis
- Identification of which extremes ACE2 represents well vs. where it shows systematic biases

**Complementary validation by supervisor:** Seasonal climatology, mean circulation, low-frequency modes, surface flux biases, and long-term stability are covered separately to provide a complete picture of ACE2's climatic realism.

# Milestones

- 01-generate-ace2-simulations.md — Run ≥50-member ACE2 ensemble (2001–2010)
- 02-preprocess-data.md — Regrid, unit-standardise, rechunk ERA5 & ACE2
- 03-compute-etccdi-indices.md — Compute ETCCDI + wind-extension indices
- 04-etccdi-validation.md — Spatial/temporal comparison, Taylor diagrams (RQ1)
- 05-extreme-value-analysis.md — GEV/GPD fits; 10/50/100‑yr return levels (RQ2)
- 06-wind-extremes.md — Wind distributions, storm tracks, spatial coherence (RQ3)
- 07-compound-extremes.md — Joint exceedance & copula analysis (RQ4, exploratory)
- 08-synthesis-reporting.md — Final figures, tables, and conclusions

## Scope & Constraints

This project is **focused on extreme event and tail statistics validation**. The following important climate properties are covered **separately** by the supervisor as part of the broader ACE2 validation effort:

- Seasonal climatology and mean atmospheric circulation
- Low-frequency modes of variability (NAO, ENSO, IPO)
- Monsoon response to tropical SST variability
- Surface flux biases (critical for future ocean coupling)
- Long-term model stability and climate drift
- Stratospheric circulation

Taken together, the supervisor's analysis + this project's extremes validation provide a comprehensive assessment of ACE2's suitability for coupled climate emulation and ensemble-based extreme risk studies.

# Milestone 1: Generate ACE2 Simulations (2001–2010)

> **Milestone:** [01-generate-ace2-simulations.md](01-generate-ace2-simulations.md)  
> **Status:** In Progress
> **Started:** --
> **Completed:** —

---

# Simulation Setup

## Ensembles and Simulations

### Initial Conditions
We generate ensembles within the year 2001-2010 by applying the following steps

1. We start the simulation of ACE2 at each month in 2000, e.g., January 2000, February 2000, ..., December 2000. This gives us 12 initial conditions (ICs). 
2. We run the simulation until January 2011.
3. We extract only the period 2001-2010 from each simulation, which gives us 12 ensemble members for the period 2001-2010.

We repeat steps 1-3 for 4 versions of initial conditions, e.g. using the ICs of month 1940, 1950, 1979 and 2020 and redating them to the year 2000. This gives us 4 sets of 12 ensemble members, i.e., 48 ensemble members in total.

### Forcing

We use the original / observed forcing in the simulation period.

### Outputs

We have 48 ensemble members for the period 2001-2010, i.e. a total of 480 years of simulation with 6H temporal resolution on the ACE2 grid for the following variables:

| ETCCDI Category | Variables |	Use
|-----------------|-----------|-------------------------------
| Temperature     | TMP2m     | For TXx, TNn, TX90p, TN10p, WSDI indices
| Precipitation   | PRATEsfc  | For R10, Rx1day, CWD indices
| Wind            | UGRD10m, VGRD10m | Combine for wind speed (FG95p, FXx, WSD indices)

## Computation of Wind Speed

- Computed wind speed from `UGRD10m` and `VGRD10m` variables.

Script: `scripts/preprocessing/compute_windspeed_ensembles.py`
Output: `data/raw/ace2-ensembles/2000v*/ensemble_*.nc`

## Final Output before Validation

The ensemble data of each simulation after preprocessing contains the following variables

- TMP2m
- PRATEsfc
- UGRD10m, VGRD10m
- 10si (10m surface wind speed)

The data is stored at for the initialization of 1940

```
data/raw/ace2-ensembles/2000v1940
```

## Validation of Simulation Output

Script: [scripts/tests/validate-sim-output.py](scripts/tests/validate-sim-output.py)
Figures: `results/figures/ace2-sim-validation/`
Logs: `logs/01-generate-ace2-simulations/`

### Validation Approach

To ensure the quality and physical realism of the ACE2 ensemble simulations, we apply three complementary validation methods: physical consistency checks, temporal mean analysis, and spatial mean analysis. Each method targets different aspects of model behavior and helps identify potential issues in the generated climate data.

We base this analysis on ensemble members of the simulation version v1940.

### Physical Consistency Checks

**Purpose:** Verify that simulated variables fall within physically plausible ranges, catching any numerical instabilities, unit conversion errors, or unphysical artifacts early in the pipeline.

**Method:**
- **Temperature (TMP2m):** Check that values lie between 200 K and 330 K (covering extreme polar cold to desert heat).
- **Precipitation (PRATEsfc):** Ensure all values are non-negative, as negative precipitation is physically impossible.
- **Wind components (UGRD10m, VGRD10m):** Verify absolute values stay below 100 m/s, as higher values would indicate unrealistic hurricane-force winds or model errors.

**Rationale:** These hard bounds act as a first-pass quality control. Any violations immediately signal data corruption, incorrect forcing, or model instability requiring investigation before proceeding to climate extremes analysis.

### Grid-Weighted Temporal Mean Analysis

**Purpose:** Assess the spatial distribution and seasonal cycle of each variable to ensure the model produces climatologically realistic patterns.

**Method:**
- Compute grid-weighted temporal means using latitude-dependent area weights (`cos(lat)`) to properly account for meridional grid cell size variation.
- Generate two visualizations:
  1. **Overall temporal mean:** Full 2001–2010 average spatial field to identify systematic biases or unrealistic spatial patterns.
  2. **Monthly climatology:** 12-panel plot showing the seasonal cycle across all months to verify that seasonal transitions are smooth and physically consistent.

**Rationale:** Spatial patterns reveal whether the model captures expected climate features (e.g., ITCZ, storm tracks, polar amplification). Grid weighting prevents high-latitude regions from being over-represented in area averages. Monthly climatology checks ensure the model's seasonal cycle is realistic—critical for extreme event analysis, where many indices (e.g., warm spell duration) depend on seasonal context.

### Spatial Mean Timeseries Analysis

**Purpose:** Evaluate temporal variability, ensemble spread, and consistency across ensemble members to detect model drift, initialization shocks, or outlier members.

**Method:**
- Compute area-averaged spatial means for each variable, ensemble member, and 6-hourly timestep.
- Plot timeseries overlaying all ensemble members (thin lines) and the ensemble mean (thick black line).
- Visualize across three representative years (2003, 2005, 2009) to balance computational cost with temporal coverage.

**Rationale:** This analysis serves multiple purposes:
1. **Ensemble spread:** Quantifies internal climate variability—tight clustering indicates deterministic forcing dominance; wide spread suggests strong chaotic dynamics.
2. **Outlier detection:** Identifies rogue ensemble members with anomalous behavior requiring investigation.
3. **Temporal drift:** Reveals whether the model climatology remains stable over the decade or shows spurious trends unrelated to forcing.
4. **Initialization shock:** Checks for unrealistic transients in the first months after initialization (though these should be absent given our year-2000 spin-up period).

### Computational Setup

- **Parallelization:** Dask distributed client with 8 workers (8 threads each, 28 GB memory per worker) to handle the 48-member ensemble efficiently.
- **Chunking strategy:** `sample=1, time=100, lat=180, lon=360` optimizes for parallel processing across ensemble members while preserving spatial structure.
- **Sample selection:** Analysis focused on years 2003, 2005, and 2009 to balance validation thoroughness with computational expense.

---
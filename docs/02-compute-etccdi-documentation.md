# Milestone 2: Compute ETCCDI Indices

> **Milestone:** [02-compute-etccdi-indices.md](02-compute-etccdi-indices.md) 
> **Status:** In Progress
> **Started:** 29.05.2026
> **Completed:** -

---

# Datasets & Preprocessing for ETCCDI Computation

## ERA5

**Selected Period:** 1981-2010 (30 years)

**Selected Variables:**
We use the following variables of ERA5 to compute the ETCCDI indices:

| Variable | Param | Description | Related ETCCDI |
|----------|-------------|-----|---|            
| 2t       | 167 | 2m temperature | TXx, TNn, TX90p, TN10p, WSDI |
| tp       | 228 | Total precipitation | R10, Rx1day, CWD |
| 10si     | 207 | 10m wind speed | FG95p, FXx, WSD

**Preprocessing Steps of 1H ERA5 Data:**

- ERA5 data on Levante was given in 1H resolution but we need 1D.
- Adjust ERA5 to 6H resolution as in ACE2 (00:00, 06:00, 12:00, 18:00).
- Aggregate to 1D resolution depending on the ETCCDI index requirements (e.g., daily min/max for temperature & wind speed, daily sum for precipitation).
- Regrid from the reduced Gaussian Grid (ERA5 is stored on that grid on Levnate) to the 0.25° target grid of ERA5.

We computed the wind speed from the u10 and v10 components of the wind using the following formula:

```wind_speed = sqrt(u10^2 + v10^2)
```

for the 6H  temporal resolution of ACE2. We then aggregate the 6H wind speed to daily mean and daily max for the corresponding ETCCDI indices.

**Scripts:**
- `scripts/02-compute-etccdi/era5_for_etccdi.py` : preprocessing and remapping of the ERA5 data to 1D and the ERA5 target grid for ETCCDI computation.

**Final Datasets:** 

1. 1D ERA5 data on ERA5 grid:
- Temporal resolution: 1D in 1981-2010 (30 years)
- Spatial resolution: global 0.25° x 0.25°
- Format: netCDF
- Folder:
	- ERA5 Temperature: `data/raw/ERA5/1D/TMP2m/`
	- ERA5 Precipitation: `data/raw/ERA5/1D/PRATEsfc/`
	- ERA5 Wind Speed: `data/raw/ERA5/1D/10si/`

2. 1D ERA5 data on ACE2 grid:
- Temporal resolution: 1D in 1981-2010 (30 years)
- Spatial resolution: ACE2 grid (1° x 1°)
- Format: netCDF
- Folder:
	- ERA5 Temperature: `data/processed/ERA5/1D/ACE2GRID/TMP2m/`
	- ERA5 Precipitation: `data/processed/ERA5/1D/ACE2GRID/PRATEsfc/`
	- ERA5 Wind Speed: `data/processed/ERA5/1D/ACE2GRID/10si/`

## ACE2

We use the ACE2 ensembles from milestone 01. 

**Selected Period:** 2001-2010 (10 years)

The ETCCDIs are based on aggregated daily data, where the method of aggregation depends on the index.
Hence, we aggregate the 6H data of ACE2 to daily data using the following aggregations to account for the corresponding ETCCDIs

- TMP2m
	- tasmax
	- tasmin
- PRATEsfc
	- pr: sum over day
- 10m Wind Speed
	- sfcWind_mean
	- sfcWind_max

**Scripts:**

```
scripts/02-compute-etccdi/get_daily_ace2.py
```

**Final Datasets:*

- `data/raw/ace2-ensembles/1D/{scenario}/ensemble_{N}.nc` : daily aggregated ACE2 data for each ensemble member and scenario, ready for ETCCDI computation. Each ensembles contains the variables; tasmax, tasmin, pr (summed), sfcWind_mean, sfcWind_max.

## A Comment on the Units of ACE2 and ERA5

**ACE2 `PRATEsfc` (kg/m²/s) → Daily total (kg/m²)**
**ERA5** `tp` given in **m**.

Summing both over time leads to

**ACE2:**
- ACE2 has a 6H temporal resolution. At each timestep we have a precipitation rate in $kg/m^2/s$. We assume that each timestamp accounts for $\Delta t = 6h = 21600s$. 
- Hence we need to multiply the accumulated precipitation rate for each day with $21600s$ to convert the units from $kg/m^2/s$ to $kg/m^2$. 
- Given the density of water $\rho = 1000kg/m^3$ the unit of $1 kg/m^2 = 1 mm$ of water depth. 
**ERA5:**
- **Sum of m over time** = m

So for ETCCDI compatibility:

| Data            | Raw Unit | After Summation | Convert to mm    |
| --------------- | -------- | --------------- | ---------------- |
| ERA5 `tp`       | m        | m               | multiply by 1000 |
| ACE2 `PRATEsfc` | kg/m²/s  | kg/m²           | already ≈ mm     |


# Quick Notes

## 02.07.2026

**Planning: ETCCDI Computation Strategy**

Created comprehensive plan for computing ETCCDI indices for both ERA5 (1981-2010) and ACE2 ensembles (2001-2010).

**Key Decisions:**
- **Library**: xclim (v≥0.47) — modern xarray-based library with full WMO ETCCDI support, optimized for HPC with dask
- **Percentile method**: WMO bootstrap method (Zhang et al. 2005) with day-of-year specific percentiles (365 thresholds per grid cell) using 5-day centered window
- **Baseline period**: ERA5 1981-2010 for computing percentile thresholds
- **Output frequency**: Annual aggregation for all indices
- **Ensemble processing**: Compute indices per-member, then calculate ensemble statistics (mean, std, 5th-95th percentile)

**Index Categories:**
- **Absolute**: TXx, TNn, Rx1day, FXx — no threshold required
- **Relative**: TX90p, TN10p, FG95p, WSDI, R10, CWD — use ERA5 percentile thresholds

**Critical Unit Conversion:**
- ACE2 PRATEsfc: kg/m²/s (6H rate) → must multiply by 21600s (6H) to get daily total in kg/m² ≈ mm
- ERA5 tp: m → multiply by 1000 to get mm

**WSD (Wind Spell Duration) Definition:**
- Non-standard index analogous to WSDI (Warm Spell Duration Index)
- Threshold: 95th percentile of daily mean wind speed from ERA5 baseline
- Counts consecutive days (≥6) with sfcWind_mean > threshold

**Thresholds to be saved:**
- TN_p10_doy.nc, TX_p10_doy.nc — for TN10p, CSDI
- TN_p90_doy.nc, TX_p90_doy.nc — for TX90p, WSDI
- sfcWind_p95_doy.nc — for FG95p, WSD
- All shape: (365, lat, lon) for day-of-year percentiles

**Output Structure:**
- ERA5: `data/processed/ETCCDI/ERA5/{index}_1981-2010.nc`
- ACE2 per-member: `data/processed/ETCCDI/ACE2/{scenario}/ensemble_{N}/{index}_2001-2010.nc`
- ACE2 ensemble stats: `data/processed/ETCCDI/ACE2/{scenario}/ensemble_stats/{index}_{mean|std|p05|p95}_2001-2010.nc`
- Thresholds: `data/processed/ETCCDI/THRESHOLDS/{variable}_p{XX}_doy.nc`

**Plan file**: `.github/plans/compute-etccdi-indices.plan.md`

## 29.05.2026

**Script creation: `get_daily_ace2.py`**

Created preprocessing script to aggregate 6-hourly ACE2 ensemble data to daily values for ETCCDI computation.

**Key decisions:**
- Variable mapping: TMP2m → tasmax/tasmin, PRATEsfc → pr, 10si → sfcWind_mean/sfcWind_max
- Aggregation methods:
  - Temperature: Daily max and min (needed for TXx, TNn, TX90p, TN10p, WSDI)
  - Precipitation: Daily sum (needed for R10, Rx1day, CWD)
  - Wind: Daily mean AND max (FG95p/WSD need mean; FXx needs max)
- Output: Single netCDF per ensemble file containing all 5 aggregated variables (tasmax, tasmin, pr, sfcWind_mean, sfcWind_max)
- Folder structure preserved: `6H/{scenario}/ensemble_N.nc` → `1D/{scenario}/ensemble_N.nc`

**Features:**
- Comprehensive logging to `logs/get_daily_ace2/` with timestamps
- Automatic variable detection (handles multiple variable naming conventions)
- Error handling and summary statistics
- Skips already-processed files

**Status:** Ready to run on full 48-ensemble dataset (4 scenarios × 12 members)

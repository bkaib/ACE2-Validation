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


# Quick Notes



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

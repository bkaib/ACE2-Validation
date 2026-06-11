# Milestone 2: Compute ETCCDI Indices

> **Milestone:** [02-compute-etccdi-indices.md](02-compute-etccdi-indices.md) 
> **Status:** In Progress
> **Started:** 29.05.2026
> **Completed:** -

---

# ERA5

**Selected Period:** 1981-2010 (30 years)

**Selected Variables:**
We use the following variables of ERA5 to compute the ETCCDI indices:

| Variable | Param | Description | Related ETCCDI |
|----------|-------------|-----|---|            
| 2t       | 167 | 2m temperature | TXx, TNn, TX90p, TN10p, WSDI |
| tp       | 228 | Total precipitation | R10, Rx1day, CWD |
| 10si     | 207 | 10m wind speed | FG95p, FXx, WSD


# ACE2

We use the ACE2 ensembles from milestone 01. 

**Selected Period:** 2001-2010 (10 years)

The ETCCDIs are based on aggregated daily data, where the method of aggregation depends on the index.
Hence, we aggregate the 6H data of ACE2 to daily data using the following aggregations to account for the corresponding ETCCDIs

```
scripts/preprocessing/get_daily_ace2.py
```

- TMP2m
	- tasmax
	- tasmin
- PRATEsfc
	- pr: sum over day
- 10m Wind Speed
	- sfcWind_mean
	- sfcWind_max


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

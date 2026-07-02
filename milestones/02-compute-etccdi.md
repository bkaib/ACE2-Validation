# Milestone 03 — Compute ETCCDI Indices

## Goal
Compute the selected IPCC ETCCDI extreme climate indices from both ERA5 and the ACE2 ensemble.

## Background
ETCCDI indices are the standard framework for characterising the frequency, intensity, and duration of temperature and precipitation extremes. A non-standard wind extension is included to support the wind extremes research question.

## Target indices

| Category | Index | Description |
|---|---|---|
| Temperature | TXx | Annual maximum of daily maximum temperature |
| Temperature | TNn | Annual minimum of daily minimum temperature |
| Temperature | TX90p | Fraction of days when Tmax > 90th percentile |
| Temperature | TN10p | Fraction of days when Tmin < 10th percentile |
| Temperature | WSDI | Warm Spell Duration Index |
| Precipitation | R10 | Annual count of days with pr ≥ 10 mm |
| Precipitation | Rx1day | Annual maximum 1-day precipitation |
| Precipitation | CWD | Maximum annual consecutive wet days |
| Wind (ext.) | FG95p | The count of days where daily mean wind speed exceeds the 95th percentile. This validates the "frequency" of high-wind events. |
| Wind (ext.) | FXx | Maximum value of daily maximum wind speed (m/s).

Let $FX_{ij}$ be the daily maximum wind speed on day $i$ of period $j$. Then the maximum daily maximum wind speed for period $j$ is 
$$
FXx_j = max(FX_{ij})
$$ |
| Wind (ext.) | WSD |The number of consecutive days with wind speeds above a certain threshold. This tests if the emulator can "hold" a storm system in place or if it moves them too fast. |

## Steps

- [x] Preprocess ERA5 data similar to ACE2 (e.g. resample to 6H then daily, compute daily max/min/mean as needed, ensure consistent units)
- [x] Regrid ERA5 to the ACE2 grid with conservative remapping from xesmf
- [ ] Define percentile baselines (ERA5 1981–2010 (30y) climatological period for relative indices)
- [ ] Compute all indices from processed ERA5 (`data/processed/ERA5/`)
- [ ] Compute all indices for each ACE2 ensemble member based on ERA5 thresholds (`data/processed/ACE2/`)
- [ ] Compute ACE2 ensemble mean and spread (std, 5th–95th percentile range) across members
- [ ] Save annual index fields to `data/processed/indices/ERA5/` and `data/processed/indices/ACE2/`
- [ ] Unit and sanity checks (e.g. TXx > TNn everywhere, R10 ≥ 0)

## Outputs
- `data/processed/indices/ERA5/` — annual ETCCDI fields (one file per index)
- `data/processed/indices/ACE2/` — per-member annual fields + ensemble statistics
- `scripts/analysis/compute_etccdi.py`

## Dependencies
- Milestone 02 completed (processed ERA5 and ACE2 data available)

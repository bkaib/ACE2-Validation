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
| Wind (ext.) | FG95p | Fraction of days with wind speed > 95th percentile |
| Wind (ext.) | FXx | Annual maximum wind speed |
| Wind (ext.) | WSD | Windy Spell Duration |

## Steps

- [ ] Choose / implement index computation library (e.g. `xclim`, `climdex`, or custom)
- [ ] Define percentile baselines (ERA5 1981–2010 climatological period for TX90p, TN10p, FG95p)
- [ ] Compute all indices from processed ERA5 (`data/processed/ERA5/`)
- [ ] Compute all indices for each ACE2 ensemble member (`data/processed/ACE2/`)
- [ ] Compute ACE2 ensemble mean and spread (std, 5th–95th percentile range) across members
- [ ] Save annual index fields to `data/processed/indices/ERA5/` and `data/processed/indices/ACE2/`
- [ ] Unit and sanity checks (e.g. TXx > TNn everywhere, R10 ≥ 0)

## Outputs
- `data/processed/indices/ERA5/` — annual ETCCDI fields (one file per index)
- `data/processed/indices/ACE2/` — per-member annual fields + ensemble statistics
- `scripts/analysis/compute_etccdi.py`

## Dependencies
- Milestone 02 completed (processed ERA5 and ACE2 data available)

# Milestone 01 — Generate ACE2 Simulations

## Goal
Run the ACE2 large ensemble over the held-out test period (2001–2010) to produce the primary validation dataset.

## Background
ACE2 was not trained on the 2001–2010 period, making it the appropriate validation window. A large ensemble is needed so that pooling members provides an effective sample size comparable to the ERA5 record (1941–2022) for return-level estimation.

## Target
- ≥ 50 ensemble members, each initialised from ERA5 states at the start of 2001
- Output variables: near-surface temperature (T2m), precipitation (pr), 10-m wind speed (sfcWind)
- Native ACE2 output grid, daily resolution

## Steps

- [x] Set up ACE2 model environment and confirm software/version
- [x] Check what output variables of ACE2 we need to compute the ETCCDIs
- [x] Get ACE2 running: fme not found
- [x] Check Ensemble output of the test run. 
- [x] Define ensemble initialisation strategy (e.g. perturbed ERA5 initial conditions for 2001-01-01)
- [x] Write and test job scripts for a single ensemble member
- [x] Scale to ≥ 50 members using HPC job arrays
- [x] Monitor runs; resubmit any failed members
- [x] Collect and organise raw output (one file per member, consistent naming convention)
- [ ] Compute 10m Windspeed
- [ ] Basic sanity check: verify output completeness and plausibility (global mean T2m, total pr)

## Outputs
- `data/raw/ACE2-ERA5/` — raw simulation output, one file per member
- `data/raw/ace2-ensembles/` — organised ensemble of each simulation version.
- Job scripts in `jobs/`
- Run log in `logs/`

## Dependencies
- ACE2 model code and weights available
- ERA5 initial condition files for 2001 available

## Notes
- Training period simulations (1941–2000) may be run later as supplementary/sensitivity analysis only.

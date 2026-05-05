# Milestone 08 — Synthesis & Reporting

## Goal
Integrate results from all analysis milestones into a coherent, publication-ready synthesis that answers the four research questions.

## Background
This milestone produces the final outputs: a summary document (or paper draft), key figures, and a clear statement on ACE2's fitness for purpose as an ensemble tool for extreme event analysis.

## Steps

### Figure polish
- [ ] Finalise all key figures (consistent style, colorbars, projections, labels)
- [ ] Produce multi-panel summary figures per research question
- [ ] Ensure all figures are saved as vector (PDF/SVG) and raster (PNG 300 dpi) in `results/figures/`

### Tables
- [ ] Compile summary metrics table: bias, RMSE, spatial correlation per ETCCDI index
- [ ] Return level comparison table: ERA5 vs ACE2 for selected regions/variables
- [ ] Save to `results/tables/`

### Written synthesis
- [ ] Draft answers to each research question based on results:
  1. ETCCDI spatial and temporal patterns (Milestone 04)
  2. 50- and 100-year return levels (Milestone 05)
  3. Wind extremes (Milestone 06)
  4. Compound extremes (Milestone 07, if completed)
- [ ] Write conclusions: is ACE2 fit-for-purpose for extreme event ensemble analysis?
- [ ] Identify variables / regions where ACE2 shows systematic biases

### Documentation
- [ ] Update `docs/` with data provenance, processing steps, and software versions
- [ ] Ensure all scripts and notebooks are clean and reproducible
- [ ] Tag final analysis commit

## Outputs
- `results/figures/` — final publication-quality figures
- `results/tables/` — final summary tables
- `docs/synthesis.md` — written summary of findings
- `docs/reproducibility.md` — software environment and data provenance

## Dependencies
- Milestones 03–06 completed
- Milestone 07 completed (or explicitly descoped)

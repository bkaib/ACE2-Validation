---
description: 'Project Copilot rules: reproducible, HPC-ready workflows for NH storm-damage synchrony analysis'
applyTo: '**'
---

# Copilot Rules for SYNCDSTRMDMG

## Overview

Investigate storm damage variability in the Northern Hemisphere (ONDJFM season) using CLIMADA impact modeling and Python-based statistical analysis. Identify coherent PCA modes of impact and attribute them to large-scale atmospheric drivers (NAO, ENSO,...). Target: high-impact scientific publication.

## Technical Constraints

- **Paths**: Import all file paths from `config/paths.py`. Never hardcode absolute paths.
- **HPC**: Target DKRZ Levante (SLURM). Design all scripts for distributed/multi-node execution.
- **Data mounts**: `data/raw/ERA5`, `models/climada`, `models/ACE2` are read-only symlinks — treat as external.
- **Libraries**: Use `libraries/own_libraries` for project utilities.
- **Tools**: `xarray` + `dask` for large data; Zarr for intermediate storage; CLIMADA for impact modeling; ACE2 for attribution.

## Core Rules

- Ensure Reproducibility: fixed random seeds, documented parameters, provenance metadata on all outputs.
- Import paths from `config.paths`; document any external mounts.
- Record provenance (input sources, parameters, commit SHA) on every produced dataset.
- Scripts for production pipelines; notebooks for exploration only.
- Use fixed random seeds for stochastic methods and document them in outputs.
- Never expose secrets or credentials.

## Code Standards

-   **Naming**: Use `snake_case` for functions and variables, `CamelCase` for classes, and descriptive names for modules and scripts.
-   **Logging**: Use the project logger (`config/custom_logging.py`) rather than print statements.
-   **Testing**: Add unit tests for core utilities (use `pytest`). Validate data-loading and small deterministic functions.

## Data Handling and Performance

-   Use `dask` and chunked `xarray` operations for large datasets; prefer Zarr for intermediate storage.
-   Use lazy evaluation where possible; call `.compute()` only when necessary and on worker nodes suited to the job size.
-   Profile memory and I/O for scripts that run on HPC nodes and tune chunk sizes accordingly.

## Best Practices for Scientific Robustness

-   Record metadata for every produced dataset: input sources, processing steps, parameter values, and code commit.
-   Use fixed random seeds for stochastic procedures when producing reproducible results and report them in outputs.
-   Provide clear descriptions and references for statistical methods (e.g., PCA, significance testing) used in analyses.
-   Prefer mechanistic interpretations and sensitivity/causal checks (ACE2) over purely correlational claims.

## Copilot and Automated Agent Guidelines

### Research Context

-   **Topic:** Northern Hemisphere (NH) storm impacts & damage variability.
-   **Objectives:** Spatial covariance of impacts, drivers of damage (circulation patterns/climate modes), and seasonal predictability.
-   **Framework:** CLIMADA (impact modeling) & Python-based statistical analysis.
-   **Target:** High-impact scientific publication (Nature-style reasoning).

### Analytical Priorities

-   **Mechanistic understanding:** Prioritize physical drivers over pure correlation.
-   **Scale:** Connect synoptic dynamics to regional socioeconomic impacts.
-   **Spatial scope:** Focus on NH-wide modes of variability.

### Agent Code-Generation Rules

-   Use `precise`, `evidence-based` language in all outputs.
-   When generating code, ensure it handles `xarray` datasets and adheres to the folder hierarchy (`scripts/preprocessing/` for ETL, `scripts/analysis/` for modeling, `notebooks/` for exploration).
-   Suggest visualization methods suitable for academic publication.

### Instruction File References

-   DO: Use #file:./instructions/skills.instructions..md for skill-specific guidance.
-   DO: Use #file:./instructions/agent.instructions.md for agent-specific guidance.
-   DO: Use #file:./instructions/instructions.instructions.md for general instruction guidelines.

## Examples

### Good Example

```python
from config.paths import ERA5_RAWimport xarray as xrds = xr.open_zarr(ERA5_RAW)
```

### Bad Example

```python
# Hardcoded absolute path — avoidds = xr.open_dataset('/home/user/data/ERA5/era5.nc')
```

## Validation and Verification

-   Create the conda environment from the repository manifest: `conda env create -f environment.yml`.
-   Run small, deterministic scripts to validate the environment and data access (examples below):

```bash
conda activate datascience python scripts/preprocessing/convert_ncei_to_netcdf.py --helppython scripts/preprocessing/compute_era5_quantiles.py --help
```

-   Add checksums or lightweight tests for critical intermediate files (Zarr stores, NetCDF outputs).

## Guidance for Copilot and Automated Agents

-   Prefer suggestions that follow project constraints: use `config.paths`, avoid absolute paths, and use `libraries/own_libraries` when applicable.
-   When proposing code to process data, include suggested chunk sizes, and a brief note on memory/I/O considerations for HPC.
-   For code that produces results, include provenance metadata (input paths, parameters, commit hash) in outputs.

## Maintenance

-   Review and update these rules when dependencies or platform constraints change.
-   Keep examples and commands in sync with `environment.yml` and scripts in `scripts/`.

## Agent System

| Agent | Role | Pipeline stage | Skills |
|-------|------|----------------|--------|
| `data-engineer` | Raw → analysis-ready datasets | Download → Convert → Filter → Bias-correct → Percentiles | `data-validation`, `dask-pipeline` |
| `impact-modeler` | Impact datasets & synthetic ensembles | CLIMADA impacts → SSI → ACE2 ensembles | `climada-impact`, `ensemble-generation` |
| `analyst` | Statistics, attribution, figures | PCA → Driver attribution → Prediction → Figures | `spatial-statistics`, `scientific-visualization` |

**Pipeline data contracts** (each agent's output is the next agent's input):
- `data-engineer` → `data/processed/` Zarr `(time, lat, lon | station)` + provenance attrs.
- `impact-modeler` → `data/processed/impacts/` Zarr with attrs `source`, `hazard_input`, `exposure_year`, `vulnerability_curves`, `commit`.
- `analyst` → `results/figures/` (PDF/PNG) and `results/tables/` (CSV) with provenance annotation.

## Interaction Format

- One contextually relevant emoji per H1/H2 header (📂 data · 📊 analysis · 🛠 fixes). No emoji in body text.
- Use `- [ ]` / `- [x]` checkboxes for all multi-step plans and progress logs.
- Keep responses targeted; formatting should improve scannability, not increase length.

## Milestone and TODO Conventions

| Artifact | Path | Purpose |
|----------|------|---------|
| Milestone template | `milestones/TEMPLATE.md` | Canonical structure for all milestone `.md` files |
| Methods draft | `milestones/methods_draft.md` | Journal-ready methods narrative |
| Session-start briefing | `.github/instructions/session-start.instructions.md` | Required briefing at start of every session |
| TODO format | `.github/instructions/todo-conventions.instructions.md` | Format rules for all todo files |
| Global milestone board | `.github/todos/global.todos.md` | High-level milestone status |
| Agent TODO files | `.github/todos/{agent-name}.todo.md` | Per-agent task board |

After every task: (1) append a Processing Log entry to the milestone file, (2) update `# Summary` bullets, (3) mark the TODO complete with date + commit SHA, (4) update `global.todos.md` status.

## Instruction File References

- Skills: `#file:.github/instructions/skills.instructions.md`
- Agent authoring: `#file:.github/instructions/agent.instructions.md`
- Instruction authoring: `#file:.github/instructions/instructions.instructions.md`

## Key Files

- Environment: `environment.yml` · Paths: `config/paths.py` · Logging: `config/custom_logging.py`
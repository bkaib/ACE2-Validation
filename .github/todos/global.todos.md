# Milestones of the Project

# Templates
## Template for Milestone Table
| Milestone | Status | Owner Agent(s) | Description |
|-----------|--------|----------------|-------------|
| `milestone1` | 🟡 In progress | data-engineer, modeler, analyst | Bias-correct ERA5 wind gusts against NCEI observations; run CLIMADA impact calculations and compute METSSI/SOCSSI. |
| `milestone2` | ⏸ Blocked | analyst | PCA of seasonal damage index to identify co-varying NH impact regions. Depends on `generating-impact-data`. |

**Status legend**: 🔴 Not started · 🟡 In progress · 🟢 Complete · ⏸ Blocked

## Template for Todos
Indendation indicates sub-tasks. Use the following format for each task:

- [ ] **[HIGH/MED/LOW]** <task-description> — milestone: <milestone-name> — added: <yyyy-mm-dd>
    - [ ] **[HIGH/MED/LOW]** <sub-task-of-task-description> — milestone: <milestone-name> — added: <yyyy-mm-dd>

---

# Milestone Status

| Milestone | Status | Owner Agent(s) | Description |
|-----------|--------|----------------|-------------|
| `01-generate-ace2-simulations` | 🟡 In progress | modeler | Generate ACE2 Simulations for validation period. |
| `02-preprocess-data` | 🔴 Not started | data-engineer | Preprocess and prepare input data. |
| `03-compute-etccdi-indices` | 🔴 Not started | analyst | Compute ETCCDI extreme climate indices. |
| `04-etccdi-validation` | 🔴 Not started | analyst | Validate computed ETCCDI indices. |
| `05-extreme-value-analysis` | 🔴 Not started | analyst | Perform extreme value analysis. |
| `06-wind-extremes` | 🔴 Not started | analyst | Analyze wind extremes. |
| `07-compound-extremes` | 🔴 Not started | analyst | Analyze compound extreme events. |
| `08-synthesis-reporting` | 🔴 Not started | analyst | Synthesis and final reporting. |

---

# Active Tasks

## Milestone 1 - Generate ACE2 Simulations

- **Status**: 🟡 In progress

- [x] **[HIGH]** Check what output variables of ACE2 we need to compute the ETCCDIs — milestone: `milestone1` — added: 2024-06-01
- [ ] **[HIGH]** Run Ensemble simulations of ACE2 for the period 2001-2010 — milestone: `milestone1` — added: 2024-06-01
    - [x] **[HIGH]** Generate Initial conditions for the year 2000 from the ICs in 1940, 1950, 1979, 2001 and 2020 to later on start the ensembles. Save those in ACE2_INITIAL_CONDITIONS/ACE2-Validation — milestone: `milestone1` — added: 2024-06-01
    - [x] **[HIGH]** Adjust the config file to start ACE2. Let it run 12 ensembles for each simulation, starting in Jan 2000 up to Dec 2000. Each ensemble member should end in Dec 2010— milestone: `milestone1` — added: 2024-06-01
    - [x] **[HIGH]** For each set of ensembles (e.g. initialized in 2000 with ICs of 1940, 1950, 1979, 2020) save the output files on the corresponding scratch folder — milestone: `milestone1` — added: 2024-06-01
    - [x] **[HIGH]** Run ensemble with IC from 1950 — milestone: `milestone1` — added: 2024-06-01
    - [x] **[HIGH]** Run ensemble with IC from 1979 — milestone: `milestone1` — added: 2024-06-01
    - [ ] **[HIGH]** Run ensemble with IC from 2020 (its running) — milestone: `milestone1` — added: 2024-06-01
- [ ] **[HIGH]** Extract the period 2001-2010 from each simulation — milestone: `milestone1` — added: 2024-06-01
- [ ] **[HIGH]** Validate the simulation output based on the 1940 version — milestone: `milestone1` — added: 2024-06-01
- [ ] **[HIGH]** Collect relevant data of ERA5 to compute ETCCDIs #phd ⏫  — milestone: `milestone1` — added: 2024-06-01

    
## Backlog

- [ ] **[MED]** Compute ETCCDIs of ERA5 — milestone: `milestone03` — added: 2024-06-01
- [ ] **[MED]** Compute ETCCDIs of ACE2 simulations — milestone: `milestone03` — added: 2024-06-01
- [ ] **[MED]** Validate computed ETCCDIs — milestone: `milestone03` — added: 2024-06-01

## Completed
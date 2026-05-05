# Milestones of the Project

# Templates
## Template for Milestone Table
| Milestone | Status | Owner Agent(s) | Description |
|-----------|--------|----------------|-------------|
| `milestone1` | 🟡 In progress | data-engineer, modeler, analyst | Bias-correct ERA5 wind gusts against NCEI observations; run CLIMADA impact calculations and compute METSSI/SOCSSI. |
| `milestone2` | ⏸ Blocked | analyst | PCA of seasonal damage index to identify co-varying NH impact regions. Depends on `generating-impact-data`. |

**Status legend**: 🔴 Not started · 🟡 In progress · 🟢 Complete · ⏸ Blocked

## Template for Todos
- [ ] **[HIGH/MED/LOW]** <task-description> — milestone: <milestone-name> — added: <yyyy-mm-dd>

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

- [ ] **[HIGH]** Check what output variables of ACE2 we need to compute the ETCCDIs — milestone: `milestone1` — added: 2024-06-01
- [ ] **[HIGH]** Run Ensemble simulations of ACE2 for the period 2001-2010 — milestone: `milestone1` — added: 2024-06-01

## Backlog

## Completed
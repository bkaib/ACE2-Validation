# Milestones of the Project

| Milestone | Status | Owner Agent(s) | Description |
|-----------|--------|----------------|-------------|
| `generating-impact-data` | 🟡 In progress | data-engineer, modeler, analyst | Bias-correct ERA5 wind gusts against NCEI observations; run CLIMADA impact calculations and compute METSSI/SOCSSI. |
| `discover-covarying-impact-regions` | ⏸ Blocked | analyst | PCA of seasonal damage index to identify co-varying NH impact regions. Depends on `generating-impact-data`. |
| `predictor-analysis` | ⏸ Blocked | analyst | Correlate dominant PCA modes with large-scale atmospheric drivers (NAO, ENSO, QBO). Depends on `discover-covarying-impact-regions`. |
| `climada-vs-indices` | ⏸ Blocked | data-engineer,analyst | Compare CLIMADA coherent modes of impacts with the modes obtained from damage indices (e.g. SOCSSI). Depends on `discover-covarying-impact-regions`, `generating-impact-data`. |
| `synthetic-data` | ⏸ Blocked | modeler | Generate synthetic impact data for model validation and sensitivity analysis. |
| `sensitivity-analysis` | ⏸ Blocked | analyst | Perform sensitivity analysis on synthetic impact data to assess model robustness. |

**Status legend**: 🔴 Not started · 🟡 In progress · 🟢 Complete · ⏸ Blocked

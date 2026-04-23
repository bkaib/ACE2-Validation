# Data Engineer TODOs

## Active

- [ ] **[HIGH]** Rescale the raw ERA5 wind gust data with the ODR model parameters to correct for the bias — milestone: `generating-impact-data` — due: 2026-04-17

## Backlog


## Completed

- [x] ~~Load NCEI 95th-percentile and visualize it for validation if the computation worked.~~ — completed: 2026-04-04 — commit: 0bae39c1fb7e8a1c3c252375b38b6e94ec5e47a6
<!-- - [x] ~~{Task description}~~ — completed: YYYY-MM-DD — commit: {SHA} -->

- [x] **[HIGH]** Convert the units of the NCEI 95th-percentile data to m/s — milestone: `generating-impact-data` — completed: 2026-04-10 — commit: unknown

- [x] ~~**[HIGH]** Scatterplot of NCEI vs ERA5 percentiles for each station/grid-cell pair~~ — completed: 2026-04-10 — commit: 3cb9328
- [x] ~~**[HIGH]** Compute the scaling factor α for each station/grid-cell pair if the scatterplot is a line~~ — completed: 2026-04-10 — commit: 3cb9328
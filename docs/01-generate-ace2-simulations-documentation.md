# Milestone 1: Generate ACE2 Simulations (2001–2010)

> **Milestone:** [01-generate-ace2-simulations.md](01-generate-ace2-simulations.md)  
> **Status:** In Progress
> **Started:** --
> **Completed:** —

---

# Simulation Setup

## Output Variables

| ETCCDI Category | Variables |	Use
|-----------------|-----------|-------------------------------
| Temperature     | TMP2m     | For TXx, TNn, TX90p, TN10p, WSDI indices
| Precipitation   | PRATEsfc  | For R10, Rx1day, CWD indices
| Wind            | UGRD10m, VGRD10m | Combine for wind speed (FG95p, FXx, WSD indices)

## Ensembles

We generate ensembles within the year 2001-2010 by applying the following steps

1. We start the simulation of ACE2 at each month in 2000, e.g., January 2000, February 2000, ..., December 2000. This gives us 12 initial conditions (ICs). 
2. We run the simulation until January 2011.
3. We extract only the period 2001-2010 from each simulation, which gives us 12 ensemble members for the period 2001-2010.

We repeat steps 1-3 for 4 versions of initial conditions, e.g. using the ICs of month 1940, 1950, 1979 and 2020 and redating them to the year 2000. This gives us 4 sets of 12 ensemble members, i.e., 48 ensemble members in total.

Hence, we have 48 ensemble members for the period 2001-2010, i.e. a total of 480 years of simulation.
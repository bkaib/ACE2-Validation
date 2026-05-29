# Milestone 2: Preprocess Data of ERA5 and ACE2

> **Milestone:** [02-preprocess-data.md](02-preprocess-data.md)  
> **Status:** In Progress
> **Started:** 14.05.2026
> **Completed:** -

---

# ERA5

**Selected Period:** 1981-2010 (30 years)

**Selected Variables:**
We use the following variables of ERA5 to compute the ETCCDI indices:

| Variable | Param | Description | Related ETCCDI |
|----------|-------------|-----|---|            
| 2t       | 167 | 2m temperature | TXx, TNn, TX90p, TN10p, WSDI |
| tp       | 228 | Total precipitation | R10, Rx1day, CWD |
| 10si     | 207 | 10m wind speed | FG95p, FXx, WSD


# ACE2

From the ACE2 simulations done in Milestone 1, we extract the period 2001-2010. We then compute the 10m wind speed from the UGRD10m and VGRD10m variables. 
**Selected Period:** 2001-2010 (10 years)

**Selected Variables:**
We use the following variables of ACE2 to compute the ETCCDI indices:
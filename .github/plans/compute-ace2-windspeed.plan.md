# Plan: compute-ace2-windspeed

Compute 10-meter wind speed from the U and V wind components (UGRD10m, VGRD10m) for all ACE2 ensemble members across all simulation versions. The wind speed will be calculated using the standard formula `windspeed = sqrt(u² + v²)` and added as a new variable to each ensemble NetCDF file. This enables subsequent analysis of wind extremes and ETCCDI indices that require wind speed data.

## Branch Strategy

- Base branch: `main`
- Feature branch: `feat/windspeed` (already active)

All commits will be made directly to `feat/windspeed`, with one commit per step.

---

## Step 1 — Add wind speed computation utility function

Add a reusable function to compute wind speed from U and V components in the `xarray_tools.py` library. This function will handle xarray DataArrays and preserve coordinates, attributes, and metadata.

- [ ] 1.1 Add `compute_windspeed()` function to `libraries/own_libraries/xarray_tools.py`
  - Accept `u_component` and `v_component` as xarray DataArrays
  - Compute: `windspeed = np.sqrt(u**2 + v**2)`
  - Return xarray DataArray with proper name and attributes
  - Handle missing values (NaN) appropriately
- [ ] 1.2 Add docstring with description, parameters, returns, and example usage
- [ ] 1.3 Add unit test or inline example demonstrating the function

**Verification**: 
```bash
python3 -c "import sys; sys.path.append('libraries/own_libraries'); import xarray_tools; print(xarray_tools.compute_windspeed.__doc__)"
```

**Files touched**: 
- `libraries/own_libraries/xarray_tools.py`

**Commit message**: `Add compute_windspeed utility function to xarray_tools`

---

## Step 2 — Create processing script for ensemble files

Create a script to process all ensemble files, compute wind speed, and save the updated datasets back to the original files.

- [ ] 2.1 Create `scripts/preprocessing/compute_windspeed_ensembles.py`
- [ ] 2.2 Import required modules: xarray, numpy, logging, paths from config
- [ ] 2.3 Import `compute_windspeed` from `xarray_tools`
- [ ] 2.4 Set up logging to `logs/compute_windspeed_ensembles.log`
- [ ] 2.5 Implement `process_ensemble_file()` function:
  - Load ensemble NetCDF file
  - Extract UGRD10m and VGRD10m
  - Compute wind speed using the utility function
  - Add wind speed variable to dataset with name `10si`
  - Add attributes (description, units, computation_date)
  - Save back to the same file (overwrite)
  - Log success/failure
- [ ] 2.6 Implement `process_all_ensembles()` function:
  - Iterate over all simulation versions in `ACE2_ENSEMBLES`
  - For each version, iterate over all `ensemble_*.nc` files
  - Call `process_ensemble_file()` for each
  - Track and report statistics (total processed, failed, skipped)
- [ ] 2.7 Add `if __name__ == "__main__"` block with option to process single file or all files
- [ ] 2.8 Add error handling for missing files, corrupted data, or write failures

**Verification**: 
```bash
python3 scripts/preprocessing/compute_windspeed_ensembles.py --help
```

**Files touched**: 
- `scripts/preprocessing/compute_windspeed_ensembles.py` (new)

**Commit message**: `Create script to compute wind speed for all ensemble files`

---

## Step 3 — Test on single ensemble file

Validate the script on a single ensemble file before processing all files to catch any issues early.

- [ ] 3.1 Run script on a single test file: `data/raw/ace2-ensembles/2000v1940/ensemble_0.nc`
- [ ] 3.2 Verify the output file contains 10si variable
- [ ] 3.3 Check that 10si has correct dimensions (time, lat, lon)
- [ ] 3.4 Verify attributes are properly set
- [ ] 3.5 Spot-check values: ensure windspeed is non-negative and reasonable magnitude
- [ ] 3.6 Confirm original variables (UGRD10m, VGRD10m) are preserved
- [ ] 3.7 Check file size increase is reasonable (~25% for one new variable)

**Verification**: 
```bash
# Run the script on test file
python3 scripts/preprocessing/compute_windspeed_ensembles.py --file data/raw/ace2-ensembles/2000v1940/ensemble_0.nc

# Inspect the output
python3 -c "import xarray as xr; ds = xr.open_dataset('data/raw/ace2-ensembles/2000v1940/ensemble_0.nc'); print(ds); print(ds.10si)"
```

Expected: Dataset contains 10si with dimensions matching UGRD10m and VGRD10m.

**Files touched**: 
- `data/raw/ace2-ensembles/2000v1940/ensemble_0.nc` (modified - test file)

**Commit message**: `Test wind speed computation on single ensemble file`

---

## Step 4 — Process all ensemble files

Run the processing script on all ensemble files across all simulation versions.

- [ ] 4.1 Count total files to process:
  ```bash
  find data/raw/ace2-ensembles/ -name "ensemble_*.nc" | wc -l
  ```
- [ ] 4.2 Create backup strategy (optional but recommended):
  - Document original file checksums OR
  - Note that original files are in `data/raw/ACE2-ERA5/` if recovery is needed
- [ ] 4.3 Run processing script on all files:
  ```bash
  python3 scripts/preprocessing/compute_windspeed_ensembles.py --all
  ```
- [ ] 4.4 Monitor progress via log file: `tail -f logs/compute_windspeed_ensembles.log`
- [ ] 4.5 If any failures occur, debug and rerun on failed files only
- [ ] 4.6 Verify all files were processed successfully

**Verification**: 
```bash
# Check that all ensemble files contain 10si
for dir in data/raw/ace2-ensembles/*/; do
  for file in "$dir"ensemble_*.nc; do
    python3 -c "import xarray as xr; ds = xr.open_dataset('$file'); assert '10si' in ds.data_vars, 'Missing 10si in $file'"
  done
done

# Check log for summary
grep "Successfully processed" logs/compute_windspeed_ensembles.log | wc -l
```

Expected: All files processed successfully, no assertion errors.

**Files touched**: 
- `data/raw/ace2-ensembles/2000v1940/ensemble_*.nc` (12 files modified)
- `data/raw/ace2-ensembles/2000v1950/ensemble_*.nc` (12 files modified)
- `data/raw/ace2-ensembles/2000v1979/ensemble_*.nc` (12 files modified)
- `data/raw/ace2-ensembles/2000v2020/ensemble_*.nc` (12+ files modified)
- `logs/compute_windspeed_ensembles.log` (new)

**Commit message**: `Compute and add wind speed to all ensemble files`

---

## Step 5 — Validate outputs

Perform comprehensive validation to ensure data quality and completeness.

- [ ] 5.1 Create validation script `scripts/tests/validate_windspeed.py`
- [ ] 5.2 For each ensemble file, check:
  - 10si variable exists
  - 10si has same dimensions as UGRD10m and VGRD10m
  - 10si values are non-negative
  - 10si values are >= max(|UGRD10m|, |VGRD10m|) but <= sqrt(2)*max(|UGRD10m|, |VGRD10m|)
  - No unexpected NaN values (only where U or V are NaN)
  - Attributes are present and correct
- [ ] 5.3 Generate validation report with:
  - Number of files validated
  - Number of files passing all checks
  - Any anomalies or warnings
  - Basic statistics (min, mean, max wind speed per simulation version)
- [ ] 5.4 Compare wind speed statistics across simulation versions for consistency
- [ ] 5.5 Save validation report to `logs/windspeed_validation_report.txt`

**Verification**: 
```bash
python3 scripts/tests/validate_windspeed.py
cat logs/windspeed_validation_report.txt
```

Expected: All files pass validation, no critical errors.

**Files touched**: 
- `scripts/tests/validate_windspeed.py` (new)
- `logs/windspeed_validation_report.txt` (new)

**Commit message**: `Add validation script and report for wind speed computation`

---

## Step 6 — Document in milestone

Update milestone documentation to reflect completion of wind speed computation task.

- [ ] 6.1 Open `milestones/01-generate-ace2-simulations.md`
- [ ] 6.2 Update the "Compute 10m Windspeed" checkbox to completed: `- [x] Compute 10m Windspeed`
- [ ] 6.3 Add entry to the "Outputs" section noting that ensemble files now contain 10si
- [ ] 6.4 Add note in "Processing Log" or create one if it doesn't exist:
  - Date: 2026-05-20
  - Task: Computed 10m wind speed from UGRD10m and VGRD10m
  - Method: Standard formula sqrt(u² + v²)
  - Files processed: All ensemble members in all simulation versions
  - Validation: All files pass validation checks
  - Commit: [reference the git commit hash]
- [ ] 6.5 Update `.github/todos/global.todos.md`:
  - Move "Compute the ACE2-Windspeed based on UGRD10m and VGRD10m" from Active Tasks to Completed
  - Add completion date and commit reference

**Verification**: 
```bash
git diff milestones/01-generate-ace2-simulations.md
git diff .github/todos/global.todos.md
```

Expected: Both files show the wind speed task marked as complete.

**Files touched**: 
- `milestones/01-generate-ace2-simulations.md`
- `.github/todos/global.todos.md`

**Commit message**: `Document completion of wind speed computation in milestone`

---

## Dependencies and Risks

### Dependencies
- xarray, numpy, logging (already in project)
- netCDF4 library for file I/O (assumed available)
- Sufficient disk space for modified files (~25% increase per file)

### Risks and Mitigations
1. **File corruption during overwrite**: 
   - Mitigation: Write to temporary file first, then rename
   - Fallback: Original large files exist in `data/raw/ACE2-ERA5/`

2. **Memory issues with large files**: 
   - Mitigation: Process one file at a time, load with dask if needed
   
3. **Different file structures across simulation versions**: 
   - Mitigation: Test on one file from each version first
   - Add error handling for unexpected structures

4. **Long processing time (48 files)**: 
   - Mitigation: Add progress logging, consider parallel processing in future

### Quality Checklist
- [ ] Formula correctness: sqrt(u² + v²) is standard wind speed from components
- [ ] Units consistency: ensure all components have same units (m/s expected)
- [ ] Metadata preservation: original variables and global attributes retained
- [ ] Validation coverage: all files checked, statistical sanity confirmed

---

## References

- **Wind speed formula**: Standard meteorological practice, `windspeed = sqrt(u² + v²)`
- **xarray documentation**: https://docs.xarray.dev/en/stable/
- **Project paths**: `config/paths.py` defines ACE2_ENSEMBLES path
- **Existing pattern**: `scripts/tests/get-2001-2010-ace2.py` shows file processing pattern
- **Utility library**: `libraries/own_libraries/xarray_tools.py` for reusable functions

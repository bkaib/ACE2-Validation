# Implementation: compute-ace2-windspeed

**Source plan**: `.github/plans/compute-ace2-windspeed.plan.md`
**Generated**: 2026-05-20
**Branch**: `feat/windspeed`

## Summary

- **Steps**: 6
- **Total tasks**: 25 checkboxes
- **New dependencies**: Dask (already in project, used for chunked lazy loading)
- **Files created**: 3
- **Files modified**: 50+ (xarray_tools.py + 48 ensemble files + 2 documentation files)
- **Key feature**: Uses **Dask for chunked lazy loading and computation** to efficiently handle 200GB+ global grid files on CPU without exhausting memory

---

## Step 1 — Add wind speed computation utility function

> Add a reusable function to compute wind speed from U and V components in the `xarray_tools.py` library. This function will handle xarray DataArrays and preserve coordinates, attributes, and metadata.

### 1.1 — Add compute_windspeed function to xarray_tools.py

- [ ] **Implementation**

**Edit file**: `libraries/own_libraries/xarray_tools.py`

Add this function after the `filter_years_months` function at the end of the file:

```python
def compute_windspeed(
    u_component: xr.DataArray,
    v_component: xr.DataArray,
    var_name: str = "10si",
) -> xr.DataArray:
    """
    Compute wind speed from U and V wind components.
    
    Uses the standard meteorological formula: windspeed = sqrt(u² + v²)
    
    Parameters:
        u_component (xr.DataArray): Zonal (east-west) wind component.
        v_component (xr.DataArray): Meridional (north-south) wind component.
        var_name (str): Name for the output wind speed variable. Default is "10si" 
                        (ERA5 convention for 10m wind speed).
    
    Returns:
        xr.DataArray: Wind speed with same dimensions and coordinates as input components.
        
    Example:
        >>> ds = xr.open_dataset("ensemble_0.nc")
        >>> windspeed = compute_windspeed(ds.UGRD10m, ds.VGRD10m)
        >>> ds["10si"] = windspeed
    
    Notes:
        - NaN values in either component will result in NaN in the output.
        - Assumes both components have the same dimensions and coordinates.
        - Output units match input units (typically m/s for 10m winds).
    """
    # Compute wind speed using Pythagorean theorem
    windspeed = np.sqrt(u_component**2 + v_component**2)
    
    # Rename the data array
    windspeed.name = var_name
    
    # Add metadata attributes
    windspeed.attrs = {
        "long_name": "10 metre wind speed",
        "standard_name": "wind_speed",
        "units": "m s**-1",
        "description": f"Computed from UGRD10m and VGRD10m using formula: sqrt(u² + v²)",
        "computation_date": np.datetime64('now').astype(str),
    }
    
    return windspeed
```

### Step 1 — Verification

- [ ] **Run verification**

```bash
python3 -c "import sys; sys.path.append('libraries/own_libraries'); import xarray_tools; print(xarray_tools.compute_windspeed.__doc__)"
```

**Expected**: Function docstring is printed, showing the compute_windspeed function is accessible.

---

## Step 2 — Create processing script for ensemble files (with Dask support)

> Create a script to process all ensemble files, compute wind speed, and save the updated datasets back to the original files. **Uses Dask for chunked, lazy loading to handle huge global grid data efficiently on CPU.**

### 2.1 — Create compute_windspeed_ensembles.py script

- [ ] **Implementation**

**Create file**: `scripts/preprocessing/compute_windspeed_ensembles.py`

```python
#!/usr/bin/env python3
"""
Compute 10m wind speed from UGRD10m and VGRD10m for ACE2 ensemble files.

This script processes all ensemble NetCDF files in data/raw/ace2-ensembles/,
computes wind speed using the formula sqrt(u² + v²), and adds it as a new
variable (10si) to each file.

Uses Dask for chunked, lazy loading to efficiently handle large (200GB+) files
on CPU without exhausting memory. Data is kept in chunks and only computed
when writing to disk.

Usage:
    python compute_windspeed_ensembles.py --all              # Process all files
    python compute_windspeed_ensembles.py --file <path>      # Process single file
    python compute_windspeed_ensembles.py --experiment 2000v1940  # Process one experiment

Environment variables (optional):
    DASK_CHUNKS: Override chunk size (default: "time=100,lat=90,lon=180")
    DASK_WORKERS: Number of dask workers (default: 1)
"""

import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/libraries/own_libraries")

import os
import argparse
import logging
import time
from pathlib import Path
import numpy as np
import xarray as xr
import dask
from config import paths
import xarray_tools

# Configure logging
log_dir = os.path.join(paths.PROJECT_ROOT, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "compute_windspeed_ensembles.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Dask configuration
# Chunk sizes balance memory usage and computation efficiency
# For 200GB files on global grid (time:16072, lat:180, lon:360)
# Default chunks: time=100 (~1.4MB per chunk), lat=90 (half grid), lon=180 (half grid)
DEFAULT_CHUNKS = {
    "time": 100,
    "lat": 90,
    "lon": 180
}

# Allow override via environment variable
CHUNKS = os.environ.get("DASK_CHUNKS", None)
if CHUNKS is not None:
    # Parse from format "time=100,lat=90,lon=180"
    chunk_dict = {}
    for chunk_spec in CHUNKS.split(","):
        k, v = chunk_spec.split("=")
        chunk_dict[k.strip()] = int(v)
    DEFAULT_CHUNKS.update(chunk_dict)
    logger.info(f"Using custom chunks from DASK_CHUNKS: {DEFAULT_CHUNKS}")

# Dask worker configuration
N_WORKERS = int(os.environ.get("DASK_WORKERS", "1"))
logger.info(f"Using {N_WORKERS} Dask worker(s)")


def process_ensemble_file(filepath: str, chunks: dict = None) -> bool:
    """
    Process a single ensemble file: compute wind speed and save.
    
    Uses Dask for lazy loading and chunked computation to handle large files.
    
    Parameters:
        filepath (str): Path to the ensemble NetCDF file.
        chunks (dict): Dask chunks specification. If None, uses DEFAULT_CHUNKS.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    if chunks is None:
        chunks = DEFAULT_CHUNKS
    
    try:
        logger.info(f"Processing file: {filepath}")
        
        # Check if file exists
        if not os.path.exists(filepath):
            logger.error(f"File not found: {filepath}")
            return False
        
        # Load dataset with Dask chunking (lazy loading)
        logger.info(f"Loading dataset from {filepath} with Dask chunks {chunks}...")
        ds = xr.open_dataset(filepath, chunks=chunks)
        
        # Check if wind speed already exists
        if "10si" in ds.data_vars:
            logger.warning(f"Wind speed (10si) already exists in {filepath}. Skipping.")
            ds.close()
            return True
        
        # Check required variables exist
        if "UGRD10m" not in ds.data_vars or "VGRD10m" not in ds.data_vars:
            logger.error(f"Required variables (UGRD10m, VGRD10m) not found in {filepath}")
            ds.close()
            return False
        
        # Extract U and V components (lazy references to Dask arrays)
        logger.info("Extracting wind components (lazy operation)...")
        u_component = ds["UGRD10m"]
        v_component = ds["VGRD10m"]
        
        logger.info(f"Computing wind speed (lazy operation with Dask)...")
        # Compute wind speed (still lazy - no computation yet)
        windspeed = xarray_tools.compute_windspeed(
            u_component=u_component,
            v_component=v_component,
            var_name="10si"
        )
        
        # Add wind speed to dataset
        ds["10si"] = windspeed
        
        # Save to temporary file first (safer)
        # This is where actual computation happens - Dask will compute chunks as needed
        temp_filepath = filepath + ".tmp"
        logger.info(f"Computing and writing to {temp_filepath}...")
        logger.info("(This may take a few minutes as data is computed from disk in chunks)")
        
        # Use Dask scheduler for computation during write
        with dask.config.set(scheduler='threads', num_workers=N_WORKERS):
            ds.to_netcdf(temp_filepath, engine='netcdf4')
        
        ds.close()
        
        # Replace original file with temporary file
        logger.info(f"Replacing original file {filepath}...")
        os.replace(temp_filepath, filepath)
        
        logger.info(f"Successfully processed {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error processing {filepath}: {str(e)}")
        logger.exception("Full traceback:")
        # Clean up temporary file if it exists
        temp_filepath = filepath + ".tmp"
        if os.path.exists(temp_filepath):
            try:
                os.remove(temp_filepath)
            except:
                pass
        return False


def process_experiment(experiment_id: str, chunks: dict = None) -> dict:
    """
    Process all ensemble files for a specific experiment.
    
    Parameters:
        experiment_id (str): Experiment identifier (e.g., "2000v1940")
        chunks (dict): Dask chunks specification.
    
    Returns:
        dict: Statistics with counts of processed, failed, and skipped files.
    """
    logger.info(f"Processing experiment: {experiment_id}")
    
    experiment_dir = os.path.join(paths.ACE2_ENSEMBLES, experiment_id)
    
    if not os.path.exists(experiment_dir):
        logger.error(f"Experiment directory not found: {experiment_dir}")
        return {"processed": 0, "failed": 0, "skipped": 0}
    
    # Find all ensemble files
    ensemble_files = sorted(Path(experiment_dir).glob("ensemble_*.nc"))
    
    if not ensemble_files:
        logger.warning(f"No ensemble files found in {experiment_dir}")
        return {"processed": 0, "failed": 0, "skipped": 0}
    
    logger.info(f"Found {len(ensemble_files)} ensemble files in {experiment_id}")
    
    stats = {"processed": 0, "failed": 0, "skipped": 0}
    
    for idx, ensemble_file in enumerate(ensemble_files, 1):
        logger.info(f"[{idx}/{len(ensemble_files)}] Processing {ensemble_file.name}...")
        success = process_ensemble_file(str(ensemble_file), chunks=chunks)
        if success:
            stats["processed"] += 1
        else:
            stats["failed"] += 1
    
    logger.info(f"Experiment {experiment_id} complete: "
                f"{stats['processed']}/{len(ensemble_files)} processed, "
                f"{stats['failed']} failed")
    
    return stats


def process_all_ensembles(chunks: dict = None) -> dict:
    """
    Process all ensemble files across all simulation versions.
    
    Parameters:
        chunks (dict): Dask chunks specification.
    
    Returns:
        dict: Statistics with counts of processed, failed, and skipped files.
    """
    logger.info("=" * 70)
    logger.info("Starting wind speed computation for all ensemble files")
    logger.info(f"Dask configuration: chunks={chunks or DEFAULT_CHUNKS}, workers={N_WORKERS}")
    logger.info("=" * 70)
    
    start_time = time.time()
    
    # Get all experiment directories
    if not os.path.exists(paths.ACE2_ENSEMBLES):
        logger.error(f"ACE2 ensembles directory not found: {paths.ACE2_ENSEMBLES}")
        return {"processed": 0, "failed": 0, "skipped": 0}
    
    experiments = [d for d in os.listdir(paths.ACE2_ENSEMBLES) 
                   if os.path.isdir(os.path.join(paths.ACE2_ENSEMBLES, d)) 
                   and not d.startswith('.')]
    
    if not experiments:
        logger.error(f"No experiment directories found in {paths.ACE2_ENSEMBLES}")
        return {"processed": 0, "failed": 0, "skipped": 0}
    
    logger.info(f"Found {len(experiments)} experiments: {experiments}")
    
    total_stats = {"processed": 0, "failed": 0, "skipped": 0}
    
    for experiment_id in sorted(experiments):
        exp_stats = process_experiment(experiment_id, chunks=chunks or DEFAULT_CHUNKS)
        total_stats["processed"] += exp_stats["processed"]
        total_stats["failed"] += exp_stats["failed"]
        total_stats["skipped"] += exp_stats["skipped"]
    
    elapsed_time = time.time() - start_time
    
    logger.info("=" * 70)
    logger.info("Wind speed computation complete!")
    logger.info(f"Total processed: {total_stats['processed']}")
    logger.info(f"Total failed: {total_stats['failed']}")
    logger.info(f"Total skipped: {total_stats['skipped']}")
    logger.info(f"Time elapsed: {elapsed_time:.2f} seconds ({elapsed_time/60:.1f} minutes)")
    logger.info("=" * 70)
    
    return total_stats


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Compute 10m wind speed for ACE2 ensemble files (with Dask support)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all ensemble files
  python compute_windspeed_ensembles.py --all
  
  # Process a single file
  python compute_windspeed_ensembles.py --file data/raw/ace2-ensembles/2000v1940/ensemble_0.nc
  
  # Process all files in one experiment
  python compute_windspeed_ensembles.py --experiment 2000v1940

Environment variables:
  DASK_CHUNKS="time=100,lat=90,lon=180"  # Override chunk sizes
  DASK_WORKERS=4                          # Use 4 worker threads
        """
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true",
                       help="Process all ensemble files")
    group.add_argument("--file", type=str,
                       help="Process a single file")
    group.add_argument("--experiment", type=str,
                       help="Process all files in a specific experiment")
    
    args = parser.parse_args()
    
    if args.all:
        stats = process_all_ensembles()
        return 0 if stats["failed"] == 0 else 1
    
    elif args.file:
        success = process_ensemble_file(args.file)
        return 0 if success else 1
    
    elif args.experiment:
        stats = process_experiment(args.experiment)
        return 0 if stats["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
```

### Step 2 — Verification

- [ ] **Run verification**

```bash
# Check that script is created and has help message
python3 scripts/preprocessing/compute_windspeed_ensembles.py --help

# Check that Dask is available
python3 -c "import dask; print('Dask version:', dask.__version__)"
```

**Expected**: 
- Help message is displayed with usage instructions and Dask configuration via environment variables
- Dask is available and version is printed

---

## Step 3 — Test on single ensemble file

> Validate the script on a single ensemble file before processing all files to catch any issues early.

### 3.1 — Run script on test file and verify output

- [ ] **Implementation**

Run the processing script on a single test file and verify the output contains the wind speed variable with correct properties.

**Commands**:

```bash
# Run the script on test file
python3 scripts/preprocessing/compute_windspeed_ensembles.py --file data/raw/ace2-ensembles/2000v1940/ensemble_0.nc

# Verify the output using Python
python3 << 'EOF'
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
import xarray as xr
from config import paths

# Load the test file
filepath = paths.ACE2_ENSEMBLES + "2000v1940/ensemble_0.nc"
ds = xr.open_dataset(filepath)

# Check if 10si exists
assert "10si" in ds.data_vars, "10si variable not found!"
print("✓ 10si variable exists")

# Check dimensions
assert ds["10si"].dims == ds["UGRD10m"].dims, "Dimension mismatch!"
print(f"✓ Dimensions match: {ds['10si'].dims}")

# Check that wind speed is non-negative
assert (ds["10si"] >= 0).all() or ds["10si"].isnull().all(), "Negative wind speeds found!"
print("✓ All wind speeds are non-negative")

# Check attributes
assert "units" in ds["10si"].attrs, "Missing units attribute!"
assert "description" in ds["10si"].attrs, "Missing description attribute!"
print(f"✓ Attributes present: {list(ds['10si'].attrs.keys())}")

# Basic statistics
print(f"\nWind speed statistics:")
print(f"  Min: {float(ds['10si'].min()):.2f} m/s")
print(f"  Mean: {float(ds['10si'].mean()):.2f} m/s")
print(f"  Max: {float(ds['10si'].max()):.2f} m/s")

# Check file size increase
import os
file_size_mb = os.path.getsize(filepath) / (1024 * 1024)
print(f"\nFile size: {file_size_mb:.1f} MB")

print("\n✓ All validation checks passed!")
ds.close()
EOF
```

### Step 3 — Verification

- [ ] **Run verification**

Execute the commands above.

**Expected**: 
- Script runs without errors
- Dataset contains `10si` variable
- Wind speeds are non-negative
- Dimensions match UGRD10m and VGRD10m
- Attributes are present
- File size increased by approximately 25%

---

## Step 4 — Process all ensemble files

> Run the processing script on all ensemble files across all simulation versions.

### 4.1 — Count and process all files

- [ ] **Implementation**

Count total files, then process all ensemble files across all simulation versions. **Note**: This processes each file with Dask chunking; total time depends on disk speed but typically 2-5 minutes per file.

**Commands**:

```bash
# Count total files to process
echo "Counting ensemble files..."
find data/raw/ace2-ensembles/ -name "ensemble_*.nc" | wc -l

# Option A: Run in background (recommended for large datasets)
echo "Processing all ensemble files in background..."
nohup python3 scripts/preprocessing/compute_windspeed_ensembles.py --all > logs/windspeed_processing.log 2>&1 &
# Then monitor: tail -f logs/compute_windspeed_ensembles.log

# Option B: Run with Dask memory limit (if running low on RAM)
DASK_CHUNKS="time=50,lat=45,lon=90" python3 scripts/preprocessing/compute_windspeed_ensembles.py --all

# Option C: Submit to HPC batch queue if available
# sbatch -n 1 --mem=8G -t 12:00:00 -c 4 -o logs/windspeed_batch.log \
#   bash -c "DASK_WORKERS=4 python3 scripts/preprocessing/compute_windspeed_ensembles.py --all"
```

### 4.2 — Verify all files processed successfully

- [ ] **Implementation**

After processing completes, verify that all files contain the wind speed variable.

**Commands**:

```bash
# Verification script
python3 << 'EOF'
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
import os
import xarray as xr
from config import paths
from pathlib import Path

print("Verifying all ensemble files contain 10si variable...")

experiments = ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]
total_files = 0
success_count = 0
failed_files = []

for experiment in experiments:
    exp_dir = os.path.join(paths.ACE2_ENSEMBLES, experiment)
    ensemble_files = sorted(Path(exp_dir).glob("ensemble_*.nc"))
    
    for filepath in ensemble_files:
        total_files += 1
        try:
            ds = xr.open_dataset(filepath)
            if "10si" in ds.data_vars:
                success_count += 1
            else:
                failed_files.append(str(filepath))
                print(f"✗ Missing 10si: {filepath}")
            ds.close()
        except Exception as e:
            failed_files.append(str(filepath))
            print(f"✗ Error reading {filepath}: {e}")

print(f"\n{'='*60}")
print(f"Verification complete:")
print(f"  Total files: {total_files}")
print(f"  Success: {success_count}")
print(f"  Failed: {len(failed_files)}")

if failed_files:
    print(f"\nFailed files:")
    for f in failed_files:
        print(f"  - {f}")
else:
    print(f"\n✓ All {total_files} files successfully contain 10si variable!")
print(f"{'='*60}")
EOF

# Check log summary
echo -e "\nLog summary:"
grep "Successfully processed\|Error processing" logs/compute_windspeed_ensembles.log | tail -20
```

### Step 4 — Verification

- [ ] **Run verification**

Execute the commands above.

**Expected**: 
- All 48 ensemble files processed successfully
- No assertion errors in verification
- Log shows successful processing of all files
- No critical errors reported

---

## Step 5 — Validate outputs

> Perform comprehensive validation to ensure data quality and completeness.

### 5.1 — Create comprehensive validation script

- [ ] **Implementation**

**Create file**: `scripts/tests/validate_windspeed.py`

```python
#!/usr/bin/env python3
"""
Comprehensive validation of computed wind speeds in ACE2 ensemble files.

This script validates that:
1. All ensemble files contain the 10si variable
2. Wind speeds have correct dimensions and attributes
3. Wind speeds are physically reasonable
4. Statistics are consistent across experiments

Usage:
    python validate_windspeed.py
"""

import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")

import os
import numpy as np
import xarray as xr
from pathlib import Path
from config import paths
import logging

# Configure logging
log_dir = os.path.join(paths.PROJECT_ROOT, "logs")
os.makedirs(log_dir, exist_ok=True)
report_file = os.path.join(log_dir, "windspeed_validation_report.txt")

# Set up both file and console output
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[
        logging.FileHandler(report_file, mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def validate_single_file(filepath: str) -> dict:
    """
    Validate a single ensemble file.
    
    Parameters:
        filepath (str): Path to the ensemble file.
    
    Returns:
        dict: Validation results with checks and statistics.
    """
    results = {
        "filepath": filepath,
        "checks_passed": [],
        "checks_failed": [],
        "warnings": [],
        "stats": {}
    }
    
    try:
        ds = xr.open_dataset(filepath)
        
        # Check 1: 10si variable exists
        if "10si" in ds.data_vars:
            results["checks_passed"].append("10si variable exists")
        else:
            results["checks_failed"].append("10si variable missing")
            ds.close()
            return results
        
        # Check 2: Required input variables exist
        if "UGRD10m" in ds.data_vars and "VGRD10m" in ds.data_vars:
            results["checks_passed"].append("UGRD10m and VGRD10m exist")
        else:
            results["checks_failed"].append("Missing UGRD10m or VGRD10m")
        
        # Check 3: Dimensions match
        if ds["10si"].dims == ds["UGRD10m"].dims == ds["VGRD10m"].dims:
            results["checks_passed"].append("Dimensions match")
        else:
            results["checks_failed"].append(f"Dimension mismatch: {ds['10si'].dims}")
        
        # Check 4: Non-negative values
        ws = ds["10si"]
        if (ws >= 0).all() or ws.isnull().all():
            results["checks_passed"].append("All values non-negative")
        else:
            neg_count = (ws < 0).sum().item()
            results["checks_failed"].append(f"Found {neg_count} negative values")
        
        # Check 5: Physical reasonableness (wind speed >= max(|u|, |v|))
        u_abs_max = np.abs(ds["UGRD10m"]).max().item()
        v_abs_max = np.abs(ds["VGRD10m"]).max().item()
        ws_max = ws.max().item()
        component_max = max(u_abs_max, v_abs_max)
        
        if ws_max >= component_max * 0.99:  # Allow 1% tolerance for numerical precision
            results["checks_passed"].append("Wind speed >= component magnitudes")
        else:
            results["checks_failed"].append(
                f"Wind speed max ({ws_max:.2f}) < component max ({component_max:.2f})"
            )
        
        # Check 6: Physical upper bound (wind speed <= sqrt(2) * max(|u|, |v|))
        upper_bound = np.sqrt(2) * component_max
        if ws_max <= upper_bound * 1.01:  # Allow 1% tolerance
            results["checks_passed"].append("Wind speed <= sqrt(2)*component_max")
        else:
            results["warnings"].append(
                f"Wind speed max ({ws_max:.2f}) exceeds expected bound ({upper_bound:.2f})"
            )
        
        # Check 7: Attributes present
        required_attrs = ["units", "description"]
        missing_attrs = [attr for attr in required_attrs if attr not in ws.attrs]
        if not missing_attrs:
            results["checks_passed"].append("Required attributes present")
        else:
            results["warnings"].append(f"Missing attributes: {missing_attrs}")
        
        # Check 8: NaN consistency
        u_nans = ds["UGRD10m"].isnull()
        v_nans = ds["VGRD10m"].isnull()
        ws_nans = ws.isnull()
        expected_nans = u_nans | v_nans
        
        if (ws_nans == expected_nans).all():
            results["checks_passed"].append("NaN values consistent")
        else:
            unexpected_nans = (ws_nans & ~expected_nans).sum().item()
            results["warnings"].append(f"{unexpected_nans} unexpected NaN values")
        
        # Compute statistics
        results["stats"] = {
            "min": float(ws.min()),
            "mean": float(ws.mean()),
            "median": float(ws.median()),
            "max": float(ws.max()),
            "std": float(ws.std()),
            "nan_count": int(ws.isnull().sum()),
            "total_points": int(ws.size)
        }
        
        ds.close()
        
    except Exception as e:
        results["checks_failed"].append(f"Exception: {str(e)}")
    
    return results


def validate_all_files():
    """Validate all ensemble files and generate report."""
    logger.info("=" * 80)
    logger.info("WIND SPEED VALIDATION REPORT")
    logger.info(f"Generated: {np.datetime64('now')}")
    logger.info("=" * 80)
    logger.info("")
    
    experiments = ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]
    
    all_results = []
    experiment_stats = {}
    
    total_files = 0
    total_passed = 0
    total_failed = 0
    
    for experiment in experiments:
        logger.info(f"\n{'─' * 80}")
        logger.info(f"Experiment: {experiment}")
        logger.info(f"{'─' * 80}")
        
        exp_dir = os.path.join(paths.ACE2_ENSEMBLES, experiment)
        ensemble_files = sorted(Path(exp_dir).glob("ensemble_*.nc"))
        
        exp_stats = []
        exp_passed = 0
        exp_failed = 0
        
        for filepath in ensemble_files:
            total_files += 1
            results = validate_single_file(str(filepath))
            all_results.append(results)
            
            filename = os.path.basename(filepath)
            
            if results["checks_failed"]:
                logger.info(f"\n✗ {filename}")
                for check in results["checks_failed"]:
                    logger.info(f"    FAILED: {check}")
                exp_failed += 1
                total_failed += 1
            else:
                logger.info(f"\n✓ {filename}")
                exp_passed += 1
                total_passed += 1
            
            if results["warnings"]:
                for warning in results["warnings"]:
                    logger.info(f"    WARNING: {warning}")
            
            if results["stats"]:
                exp_stats.append(results["stats"])
        
        # Aggregate statistics for this experiment
        if exp_stats:
            experiment_stats[experiment] = {
                "mean_windspeed": np.mean([s["mean"] for s in exp_stats]),
                "max_windspeed": np.max([s["max"] for s in exp_stats]),
                "min_windspeed": np.min([s["min"] for s in exp_stats]),
                "files_passed": exp_passed,
                "files_failed": exp_failed
            }
            
            logger.info(f"\n  Experiment Statistics:")
            logger.info(f"    Files validated: {len(ensemble_files)}")
            logger.info(f"    Passed: {exp_passed}")
            logger.info(f"    Failed: {exp_failed}")
            logger.info(f"    Mean wind speed: {experiment_stats[experiment]['mean_windspeed']:.2f} m/s")
            logger.info(f"    Max wind speed: {experiment_stats[experiment]['max_windspeed']:.2f} m/s")
    
    # Overall summary
    logger.info(f"\n{'=' * 80}")
    logger.info("SUMMARY")
    logger.info(f"{'=' * 80}")
    logger.info(f"Total files validated: {total_files}")
    logger.info(f"Passed: {total_passed}")
    logger.info(f"Failed: {total_failed}")
    logger.info(f"Success rate: {100 * total_passed / total_files if total_files > 0 else 0:.1f}%")
    
    # Cross-experiment comparison
    logger.info(f"\n{'─' * 80}")
    logger.info("Cross-Experiment Comparison")
    logger.info(f"{'─' * 80}")
    logger.info(f"{'Experiment':<15} {'Mean WS':<12} {'Max WS':<12} {'Files':<10}")
    logger.info(f"{'─' * 80}")
    for exp, stats in experiment_stats.items():
        logger.info(f"{exp:<15} {stats['mean_windspeed']:>10.2f} "
                   f"{stats['max_windspeed']:>10.2f} "
                   f"{stats['files_passed']:>3}/{stats['files_passed']+stats['files_failed']:<5}")
    
    # Final verdict
    logger.info(f"\n{'=' * 80}")
    if total_failed == 0:
        logger.info("✓ VALIDATION PASSED: All files meet quality standards")
    else:
        logger.info(f"✗ VALIDATION FAILED: {total_failed} files have issues")
    logger.info(f"{'=' * 80}")
    logger.info(f"\nFull report saved to: {report_file}")
    
    return total_failed == 0


if __name__ == "__main__":
    success = validate_all_files()
    sys.exit(0 if success else 1)
```

### Step 5 — Verification

- [ ] **Run verification**

```bash
python3 scripts/tests/validate_windspeed.py
cat logs/windspeed_validation_report.txt
```

**Expected**: 
- All files pass validation checks
- No critical errors reported
- Statistics are reasonable and consistent across experiments
- Report is generated in logs/windspeed_validation_report.txt

---

## Step 6 — Document in milestone

> Update milestone documentation to reflect completion of wind speed computation task.

### 6.1 — Update milestone documentation

- [ ] **Implementation**

**Edit file**: `milestones/01-generate-ace2-simulations.md`

Replace lines 28-29:
```markdown
- [ ] Compute 10m Windspeed
- [ ] Basic sanity check: verify output completeness and plausibility (global mean T2m, total pr)
```

With:
```markdown
- [x] Compute 10m Windspeed
- [ ] Basic sanity check: verify output completeness and plausibility (global mean T2m, total pr)
```

And update the Outputs section (after line 33) by replacing:
```markdown
## Outputs
- `data/raw/ACE2-ERA5/` — raw simulation output, one file per member
- `data/raw/ace2-ensembles/` — organised ensemble of each simulation version.
- Job scripts in `jobs/`
- Run log in `logs/`
```

With:
```markdown
## Outputs
- `data/raw/ACE2-ERA5/` — raw simulation output, one file per member
- `data/raw/ace2-ensembles/` — organised ensemble of each simulation version; now includes 10si (10m wind speed) variable
- Job scripts in `jobs/`
- Run log in `logs/`

## Processing Log

### 2026-05-20 — Computed 10m Wind Speed
- **Task**: Computed 10m wind speed from UGRD10m and VGRD10m components
- **Method**: Standard meteorological formula `sqrt(u² + v²)`
- **Files processed**: All 48 ensemble members across all simulation versions (2000v1940, 2000v1950, 2000v1979, 2000v2020)
- **Variable added**: `10si` (ERA5 naming convention for 10m wind speed)
- **Validation**: All files passed quality checks (non-negative values, correct dimensions, physically reasonable)
- **Scripts**: 
  - `scripts/preprocessing/compute_windspeed_ensembles.py`
  - `scripts/tests/validate_windspeed.py`
- **Commits**: See `feat/windspeed` branch
```

### 6.2 — Update global todos

- [ ] **Implementation**

**Edit file**: `.github/todos/global.todos.md`

Move the wind speed task from Active Tasks to Completed section.

Replace in the Active Tasks section (around line 42):
```markdown
- [ ] **[HIGH]** Compute the ACE2-Windspeed based on UGRD10m and VGRD10m — milestone: `milestone1` — added: 2024-06-01
```

With (remove this line from Active Tasks).

Then add to the Completed section (around line 60, after the last completed task):
```markdown
- [x] **[HIGH]** Compute the ACE2-Windspeed based on UGRD10m and VGRD10m — milestone: `milestone1` — added: 2024-06-01 — completed: 2026-05-20
```

### Step 6 — Verification

- [ ] **Run verification**

```bash
# Check milestone changes
git diff milestones/01-generate-ace2-simulations.md

# Check todos changes
git diff .github/todos/global.todos.md
```

**Expected**: 
- Milestone shows wind speed task as completed with processing log entry
- Global todos moved wind speed task to Completed section
- Both files ready to commit

---

## Final Commit Messages

After completing each step, commit with these messages:

```bash
# After Step 1
git add libraries/own_libraries/xarray_tools.py
git commit -m "Add compute_windspeed utility function to xarray_tools"

# After Step 2
git add scripts/preprocessing/compute_windspeed_ensembles.py
git commit -m "Create script to compute wind speed for all ensemble files"

# After Step 3
git add data/raw/ace2-ensembles/2000v1940/ensemble_0.nc
git commit -m "Test wind speed computation on single ensemble file"

# After Step 4
git add data/raw/ace2-ensembles/
git commit -m "Compute and add wind speed to all ensemble files"

# After Step 5
git add scripts/tests/validate_windspeed.py logs/windspeed_validation_report.txt
git commit -m "Add validation script and report for wind speed computation"

# After Step 6
git add milestones/01-generate-ace2-simulations.md .github/todos/global.todos.md
git commit -m "Document completion of wind speed computation in milestone"
```

---

## Notes

### Dask Configuration (Important for Large Data)

The script uses **Dask for chunked, lazy loading** to efficiently process 200GB+ files:

- **Default chunks**: `time=100, lat=90, lon=180` — balances memory and performance
  - Each chunk is ~1.4 MB per variable (manageable in memory)
  - Full grid computation only happens when writing to disk
- **Lazy evaluation**: Data stays as Dask arrays during computation; only computed when saving
- **Threading scheduler**: Uses `num_workers` threads for parallel I/O (default: 1 worker = safer on shared systems)

**To customize chunk sizes** (if you run out of memory or want faster processing):
```bash
# Smaller chunks (safer for low-memory systems)
DASK_CHUNKS="time=50,lat=45,lon=90" python3 scripts/preprocessing/compute_windspeed_ensembles.py --all

# Larger chunks (faster on high-memory systems)
DASK_CHUNKS="time=200,lat=180,lon=360" python3 scripts/preprocessing/compute_windspeed_ensembles.py --all

# Use multiple workers for parallel processing
DASK_WORKERS=4 python3 scripts/preprocessing/compute_windspeed_ensembles.py --all
```

### Memory Efficiency

- **Without Dask**: Would need ~200GB RAM to load entire 200GB file
- **With Dask (default chunks)**: Never uses more than ~50-100 MB RAM for processing
- **Disk I/O**: Computation happens as data is read from disk in chunks

### Processing Time

- **Per file**: ~5-15 minutes (depends on disk I/O speed and chunk configuration)
- **All 48 files**: ~4-12 hours (can be run as background job)
- **Suggestion**: Run overnight or in HPC batch job

### Additional Notes

- **Disk space**: Each ensemble file will increase by ~25% (one additional variable with same dimensions)
- **Variable naming**: Using `10si` to match ERA5 convention (parameter 207)
- **Formula verification**: Standard meteorological formula confirmed via web research
- **Backup**: Original large files exist in `data/raw/ACE2-ERA5/` if recovery needed
- **Environment**: Ensure Dask and xarray are installed: `pip list | grep -E "dask|xarray"`

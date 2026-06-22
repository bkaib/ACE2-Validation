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

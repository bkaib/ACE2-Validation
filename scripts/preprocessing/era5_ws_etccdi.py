"""
1. Load the ERA5 data of t2m, prate and 10si from Levante.
2. Convert it from hourly resolution to 6H resolution as in ACE2.
3. Save the data in .nc format.
"""

# %% Modules
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from libraries.own_libraries import visualisation as vis
import numpy as np
import pandas as pd
from config import constants
from libraries.own_libraries import levante_manager
import importlib
import warnings
from pathlib import Path
from datetime import datetime
from config.project_logging import setup_logger, setup_parallel_logger
importlib.reload(constants)
import argparse
import time
from dask import delayed, compute, config as dask_config
import os

# %% Setup Parser
def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Correlate EOF PC scores with monthly climate anomalies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # PC1 for all domains, default months
  %(prog)s --pc-mode 2                        # Analyze PC2 instead of PC1
  %(prog)s --months 8 9 10 11 12 1 2 3        # Specify months explicitly
  %(prog)s --domains Europe Asia              # Only Europe and Asia
  %(prog)s --validate                         # Data validation only
  %(prog)s --skip-viz                         # Compute without figures
  %(prog)s --output-dir /custom/path          # Custom output location
        """
    )

    # parser.add_argument(
    #     '--pc-mode',
    #     type=int,
    #     default=1,
    #     help='Which PC mode to analyze (1=PC1, 2=PC2, etc.). Default: 1'
    # )

    # parser.add_argument(
    #     '--climate-vars',
    #     type=str,
    #     nargs='+',
    #     default=CLIMATE_VARIABLES,
    #     choices=CLIMATE_VARIABLES,
    #     help=f'Climate variables to analyze. Default: all ({", ".join(CLIMATE_VARIABLES)})'
    # )

    # parser.add_argument(
    #     '--validate',
    #     action='store_true',
    #     help='Run data validation checks only, do not compute correlations'
    # )

    # parser.add_argument(
    #     '--output-dir',
    #     type=Path,
    #     default=None,
    #     help='Custom output directory for NetCDF files'
    # )

    return parser.parse_args()

# %% Setup logger
logger, queue_listener = setup_parallel_logger("era5_preprocessing", use_queue_listener=True)

# %% Functions

def preprocess_wind_speed(yyyy):

    import glob

    # Step 1: Load u10 and v10 of given year in 1H res
    u10_files = glob.glob(f"/pool/data/ERA5/E5/sf/an/1H/165/E5sf00_1H_{yyyy}-*.grb")
    v10_files = glob.glob(f"/pool/data/ERA5/E5/sf/an/1H/166/E5sf00_1H_{yyyy}-*.grb")
    u10 = xr.open_mfdataset(u10_files, engine='cfgrib')
    v10 = xr.open_mfdataset(v10_files, engine='cfgrib')

    # Step 2: Filter the ace2 timestamps for that year
    ace2_hours = [0, 6, 12, 18]
    u10_mask = u10.valid_time.dt.hour.isin(ace2_hours).compute()  # Compute the boolean mask to avoid lazy evaluation issues
    v10_mask = v10.valid_time.dt.hour.isin(ace2_hours).compute()  # Compute the boolean mask to avoid lazy evaluation issues
    u10_filtered = u10.where(u10_mask, drop=True)
    v10_filtered = v10.where(v10_mask, drop=True)

    # Step 3: Compute windspeed for the filtered ACE2 timesteps
    w = (u10_filtered['u10']**2 + v10_filtered['v10']**2)**0.5

    # Step 4: Resample to daily max
    w_daily_max = w.resample(time='1D').max()

    # Save w_daily_max to NetCDF
    output_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/10si/daily_max_{yyyy}_tmp.nc"
    w_daily_max.to_netcdf(output_path)

def remap_wind_with_cdo(yyyy):
    from cdo import Cdo
    logger.info(f"Starting CDO remapping of the preprocessed WIND SPEED data")
    cdo = Cdo()
    target_grid_file = "/work/gg0304/g260230/GRIDS/era5_grid.txt" # Target grid for remapping
    input_file_sum = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/10si/daily_max_{yyyy}_tmp.nc"
    temp_output_file_sum = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/10si/remapped_daily_max_{yyyy}_tmp.nc" # Temporary output file for remapped data

    # Remap Max
    try:
        logger.info(f"Remapping daily max for year {yyyy} with CDO...")
        cdo.remapnn(
            target_grid_file, 
            input=input_file_sum, 
            output=temp_output_file_sum,
            options='-f nc', # Convert to netCDF
        )
        logger.info(f"Successfully remapped {input_file_sum} to {temp_output_file_sum}")

    except Exception as e:
        logger.error(f"Error during CDO remapping of {input_file_sum}: {e}", exc_info=True)
        raise

    # Delete original files after remapping & rename remapped files to original file names
    try:
        os.remove(input_file_sum)
        os.rename(temp_output_file_sum, input_file_sum)
        logger.info(f"Replaced original file {input_file_sum} with remapped file {temp_output_file_sum}")

    except Exception as e:
        logger.error(f"Error during cleanup of original and remapped files for year {yyyy}: {e}", exc_info=True)
        raise

# %% Main
def main():
    #-------------------------
    # Constants
    #-------------------------
    years = np.arange(1981, 2011).astype(str)

    # remapped_years = [1984, 1988, 1990, 1993, 2005, 2007, 2008,] # These years were already converted during a previous run.
    # remapped_years = [str(year) for year in remapped_years]
    # undone_years = np.setdiff1d(years, remapped_years)
    # years = undone_years
    logger.info(f"Years to process: {years}")
    
    # Configure Dask for Levante HPC environment
    n_workers = 30  # Limit to 10 workers instead of all available CPUs
    logger.info(f"Configured Dask to use {n_workers} workers")
    
    # Configure Dask to use threads scheduler (good for I/O-bound tasks like file reading)
    dask_config.set(scheduler='threads', num_workers=n_workers)
    logger.info(f"Configured Dask with threads scheduler and {n_workers} workers")

    #--------------------------------------
    # WIND SPEED
    #--------------------------------------

    # # Preprocess Wind Speed with Dask parallelization
    # #-------------------------
    start_time = time.time()
    logger.info(f"Start preprocessing of WIND with Dask parallelization")
    logger.info(f"Processing {len(years)} years in parallel")
    
    ## Create delayed tasks for each year
    delayed_tasks = [delayed(preprocess_wind_speed)(yyyy) for yyyy in years]
    logger.info(f"Created {len(delayed_tasks)} delayed tasks for years {years[0]}-{years[-1]}")
    
    ## Execute all tasks in parallel
    try:
        compute(*delayed_tasks)
        logger.info(f"Successfully completed all {len(delayed_tasks)} tasks")
    except Exception as e:
        logger.error(f"Error during Dask computation: {e}", exc_info=True)
        raise
    
    elapsed = time.time() - start_time
    logger.info(f"Preprocessing of WIND completed in {elapsed:.2f} seconds")

    # Remap the Wind Speed data with CDO
    #-------------------------
    for yyyy in years:
        logger.info(f"Remapping daily wind speed for year {yyyy} with CDO...")
        remap_wind_with_cdo(yyyy)

    
    # Computation time
    
    # Clean up logging queue listener
    if queue_listener is not None:
        logger.info("Shutting down logging queue listener...")
        queue_listener.stop()
        logger.info("Logging queue listener stopped successfully")
    
if __name__ == "__main__":
    main()

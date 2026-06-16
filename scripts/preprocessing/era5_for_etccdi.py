"""
1. Load the ERA5 data of t2m, prate and 10si from Levante.
2. Convert it from hourly resolution to 6H resolution as in ACE2.
3. Save the data in .nc format.
"""

# %% Modules
import logging
import sys
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
from config.project_logging import setup_logger
importlib.reload(constants)
import argparse
import time

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
logger = setup_logger("era5_preprocessing")

# %% Functions

def load_era5_data(
        param: str, 
        family: str, 
        level: str, 
        type_: str, 
        tres: str, 
        yyyy: str, 
        mm: str, 
        dd: str,
        hh: str) -> xr.Dataset:
    """Load ERA5 data for a specific parameter and timestamp from Levante."""
    path = f"/pool/data/ERA5/{family}/{level}/{type_}/{tres}/{constants.era5_params[param]}/E5{level}00_{tres}_{yyyy}-{mm}-{dd}_{constants.era5_params[param]}.grb"
    try:
        data = xr.open_dataset(path, engine='cfgrib')
        logger.info(f"Successfully loaded ERA5 data from {path}")
        return data
    except Exception as e:
        logger.error(f"Error loading ERA5 data from {path}: {e}")
        raise

def select_ace2_6H_timestamps(era5_1H_ds: xr.Dataset) -> xr.Dataset:
    """Select only the timestamps from the ERA5 dataset that correspond to the 6-hourly timestamps used in ACE2.
    ACE2 uses 6-hourly data at 00:00, 06:00, 12:00, and 18:00 UTC. 
    This function filters the ERA5 dataset to include only these timestamps, 
    ensuring that the resulting dataset is directly comparable to the ACE2 data."""

    # Define the 6-hourly timestamps (in hours)
    ace2_hours = [0, 6, 12, 18]

    # Select only the timestamps that correspond to the ACE2 6-hourly timestamps
    era5_6H_ds = era5_1H_ds.sel(time=era5_1H_ds.time.dt.hour.isin(ace2_hours))

    return era5_6H_ds

def preprocess_prate():
    
    # Load data
    var = "PRATEsfc"
    yyyy = "2010"
    mm = "01"
    dd = "01"
    path_prefix = constants.era5_params[var]["1H"]
    PARAM = constants.era5_params[var]["PARAM"]
    filetype = constants.era5_params[var]["filetype"]
    d = xr.open_dataset(f"{path_prefix}{yyyy}-{mm}-{dd}_{PARAM}.{filetype}", engine='cfgrib' if filetype == "grb" else None)

 def preprocess_tmp2m(data):

    data = data.copy()  # Avoid modifying the original dataset

    # Select only ACE2 6-hourly timestamps
    ace2_hours = [0, 6, 12, 18]
    data = data.where(data.valid_time.dt.hour.isin(ace2_hours), drop=True)

    # Compute daily min and max
    daily_min = data.resample(time='1D').min()
    daily_max = data.resample(time='1D').max()  

    # Convert s.t. dims are time, lat, lon
    TODO


# Select the min and max
d_ace2_min = d_ace2.min(dim="time")
d_ace2_max = d_ace2.max(dim="time")

# %% Main
def main():
    # Constants
    start_time = time.time()

    # Main processing logic
    



    # Computation time
    elapsed = time.time() - start_time
    logger.info(f"Main completed in {elapsed:.2f} seconds")
if __name__ == "__main__":
    main()

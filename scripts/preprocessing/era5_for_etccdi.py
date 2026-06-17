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


def preprocess_tmp2m(yyyy):
    """Preprocesses the daily temperature for each year separately.
    Applies the following steps
    1. Load the ERA5 data of t2m from Levante.
    2. Convert it from hourly resolution to 6H resolution as in ACE2
    3. Compute the daily min and max across those timesteps globally
    4. Convert the lon/lat coordinates to dimensions and remove unnecessary coordinates
    5. Add the current max and min to a dataset that contains the daily min and max as separate variables with a time dimension
    6. Concatenate all daily datasets along the time dimension to create a final dataset for the whole year
    7. Save the final dataset to a NetCDF file.
    """

    # Parameters
    var = "TMP2m"
    ace2_hours = [0, 6, 12, 18]
    path_prefix = constants.era5_params[var]["1H"]
    PARAM = constants.era5_params[var]["PARAM"]
    filetype = constants.era5_params[var]["filetype"]

    # Create date range to loop over (example: Jan 1-5, 2010)
    date_range = pd.date_range(start=f"{yyyy}-01-01", end=f"{yyyy}-12-31", freq="D")
    
    # Initialize empty list to store daily datasets
    daily_min_datasets = []
    daily_max_datasets = []

    # Loop over each day in the given year
    logger.info(f"Starting preprocessing for year {yyyy} with {len(date_range)} days to process...")
    for current_date in date_range:
        yyyy = yyyy
        mm = f"{current_date.month:02d}"
        dd = f"{current_date.day:02d}"
        
        # Step 1: Load data of the day
        logger.info(f"Processing {var} for {current_date.strftime('%Y-%m-%d')}")
        data = xr.open_dataset(
            f"{path_prefix}{yyyy}-{mm}-{dd}_{PARAM}.{filetype}", 
            engine='cfgrib' if filetype == "grb" else None
        )
        
        # Step 2: Filter ACE2 timestamps
        logger.info(f"Filtering ACE2 timestamps")
        filtered_data = data.where(
            data.valid_time.dt.hour.isin(ace2_hours), drop=True
        )

        ## Validate if the filtered timestamp correspond to the given day:
        if not all(filtered_data.valid_time.dt.date == current_date.date()):
            logger.warning(f"Some timestamps in the filtered data do not correspond to the current date {current_date.strftime('%Y-%m-%d')}")
        logger.info(f"Filtered data contains {len(filtered_data.valid_time)} timestamps corresponding to ACE2 6-hourly data")

        # Step 3: Compute min and max for the selected hours
        logger.info(f"Computing daily min and max across ACE2 timestamps for the whole globe...")
        daily_min = filtered_data.min(dim="time")
        daily_max = filtered_data.max(dim="time")
        logger.info(f"Computed daily min and max for {current_date.strftime('%Y-%m-%d')}")
        logger.info(f"Dimension of the daily min datasets: {daily_min.dims}, shape: {daily_min.shape}")
        logger.info(f"Dimension of the daily max datasets: {daily_max.dims}, shape: {daily_max.shape}")
        
        # Step 4: Convert lon/lat coordinates to dimensions
        logger.info(f"Converting lon/lat coordinates to dimensions...")
        daily_min = daily_min.assign_coords(
            lat=('values', daily_min['latitude'].values),
            lon=('values', daily_min['longitude'].values)
        ).set_index(values=['lat', 'lon']).unstack('values')
        
        daily_max = daily_max.assign_coords(
            lat=('values', daily_max['latitude'].values),
            lon=('values', daily_max['longitude'].values)
        ).set_index(values=['lat', 'lon']).unstack('values')
        
        # Remove unnecessary coordinates
        unnecessary_coords = ['latitude', 'longitude', "step", "surface", "number"]
        logger.info(f"Removing unnecessary coordinates from dataset: {unnecessary_coords}")
        daily_min = daily_min.drop_vars(unnecessary_coords)
        daily_max = daily_max.drop_vars(unnecessary_coords)
        
        # Step 5: Add to dataset with time dimension
        logger.info(f"Adding daily min and max to dataset with time dimension...")
        daily_min = daily_min.expand_dims(time=[current_date])
        daily_max = daily_max.expand_dims(time=[current_date])
        
        # Create dataset for this day and add to list
        logger.info(f"Creating dataset for daily min and max and adding to list...")
        min_ds = xr.Dataset({'tasmin': daily_min["t2m"]})
        max_ds = xr.Dataset({'tasmax': daily_max["t2m"]})
        daily_min_datasets.append(min_ds)
        daily_max_datasets.append(max_ds)

    # Step 6: Concatenate all daily datasets along time dimension
    logger.info(f"Concatenating all daily datasets for year {yyyy} along time dimension...")
    daily_min_ds = xr.concat(daily_min_datasets, dim="time")
    daily_max_ds = xr.concat(daily_max_datasets, dim="time")
    logger.info(f"Concatenated daily datasets for year {yyyy}, final time dimension length: {len(daily_min_ds.time)}")

    # Step 7: Save the final dataset to a NetCDF file
    logger.info(f"Saving the final dataset to NetCDF files...")
    folder = f"data/processed/era5/1D/{var}/"
    Path(folder).mkdir(parents=True, exist_ok=True)
    logger.info(f"Created folder {folder} for saving NetCDF files if it did not exist")

    file_min = f"{folder}daily_min_{yyyy}.nc"
    file_max = f"{folder}daily_max_{yyyy}.nc"
    daily_min_ds.to_netcdf(file_min)
    daily_max_ds.to_netcdf(file_max)
    logger.info(f"Saved daily min dataset to {file_min}")
    logger.info(f"Saved daily max dataset to {file_max}")



# %% Main
def main():
    # Constants
    years = range(1981, 2011).astype(str)

    # Preprocess Temperature
    start_time_tmp2m = time.time()
    logger.info(f"Start preprocessing of TMP2m")
    for yyyy in years:
        preprocess_tmp2m(yyyy)
    elapsed = time.time() - start_time_tmp2m
    logger.info(f"Preprocessing of TMP2m completed in {elapsed:.2f} seconds")

    # Preprocess Precipitation
    
    
    # Computation time
    
if __name__ == "__main__":
    main()

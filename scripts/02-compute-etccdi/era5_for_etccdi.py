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
import gc  # Add garbage collection


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

def preprocess_tmp2m_mfdata(yyyy):

    import glob

    # Load tmp2m of given year in 1H res
    logger.info(f"Loading TMP2m data for year {yyyy}...")
    tmp2m_files = glob.glob(f"/pool/data/ERA5/E5/sf/an/1H/167/E5sf00_1H_{yyyy}-*.grb")
    tmp2m = xr.open_mfdataset(tmp2m_files, engine='cfgrib')

    # Filter the ace2 timestamps for that year
    logger.info(f"Filtering ACE2 timestamps for year {yyyy}...")
    ace2_hours = [0, 6, 12, 18]
    tmp2m_mask = tmp2m.valid_time.dt.hour.isin(ace2_hours).compute()  # Compute the boolean mask to avoid lazy evaluation issues
    tmp2m_filtered = tmp2m.where(tmp2m_mask, drop=True)

    # Resample to daily min and max
    logger.info(f"Resampling TMP2m to daily max for year {yyyy}...")
    tmp2m_daily_max = tmp2m_filtered.resample(time='1D').max()
    tmp2m_daily_min = tmp2m_filtered.resample(time='1D').min()

    # Rename the variable to tasmax and tasmin to be consistent with the naming convention of the other datasets
    tmp2m_daily_max = tmp2m_daily_max.rename('tasmax')
    tmp2m_daily_min = tmp2m_daily_min.rename('tasmin')

    # Convert to dataset
    tmp2m_daily_max = tmp2m_daily_max.to_dataset(name='tasmax')
    tmp2m_daily_min = tmp2m_daily_min.to_dataset(name='tasmin')

    # Save TMP2m to NetCDF
    logger.info(f"Saving daily max and min temperature to NetCDF for year {yyyy}...")
    output_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/daily_max_{yyyy}_tmp.nc"
    tmp2m_daily_max.to_netcdf(output_path)
    output_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/daily_min_{yyyy}_tmp.nc"
    tmp2m_daily_min.to_netcdf(output_path)
    logger.info(f"Saved daily max and min temperature to {output_path}")

def preprocess_tmp2m(
        yyyy,
        ace2_hours = [0, 6, 12, 18],
        ):
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
        try:
            data = xr.open_dataset(
                f"{path_prefix}{yyyy}-{mm}-{dd}_{PARAM}.{filetype}", 
                engine='cfgrib' if filetype == "grb" else None
            )
        except Exception as e:
            logger.warning(f"Failed to load data for {current_date.strftime('%Y-%m-%d')}: {str(e)}. Skipping this date.")
            continue
        
        # Step 2: Filter ACE2 timestamps
        logger.info(f"Filtering ACE2 timestamps")
        filtered_data = data.where(
            data.valid_time.dt.hour.isin(ace2_hours), drop=True
        )

        ## Validate if the filtered timestamp correspond to the given day:
        if not all(filtered_data.valid_time.dt.date == current_date.date()):
            logger.warning(f"Some timestamps in the filtered data do not correspond to the current date {current_date.strftime('%Y-%m-%d')}")
        logger.info(f"Filtered data contains {len(filtered_data.valid_time)} timestamps corresponding to ACE2 6-hourly data")
        logger.info(f"Timestamps are: {filtered_data.valid_time.values}")

        # Step 3: Compute min and max for the selected hours
        logger.info(f"Computing daily min and max across ACE2 timestamps for the whole globe...")
        daily_min = filtered_data.min(dim="time")
        daily_max = filtered_data.max(dim="time")
        logger.info(f"Computed daily min and max for {current_date.strftime('%Y-%m-%d')}")
        logger.info(f"Dimension of the daily min datasets: {daily_min.dims}")
        logger.info(f"Dimension of the daily max datasets: {daily_max.dims}")
        
        # Step 4: Add to dataset with time dimension
        logger.info(f"Adding daily min and max to dataset with time dimension...")
        daily_min = daily_min.expand_dims(time=[current_date])
        daily_max = daily_max.expand_dims(time=[current_date])
        
        # Create dataset for this day and add to list
        logger.info(f"Creating dataset for daily min and max and adding to list...")
        min_ds = xr.Dataset({'tasmin': daily_min["t2m"]})
        max_ds = xr.Dataset({'tasmax': daily_max["t2m"]})
        daily_min_datasets.append(min_ds)
        daily_max_datasets.append(max_ds)

    # Step 5: Concatenate all daily datasets along time dimension
    logger.info(f"Concatenating all daily datasets for year {yyyy} along time dimension...")
    daily_min_ds = xr.concat(daily_min_datasets, dim="time")
    daily_max_ds = xr.concat(daily_max_datasets, dim="time")
    logger.info(f"Concatenated daily datasets for year {yyyy}, final time dimension length: {len(daily_min_ds.time)}")

    # Step 6: Save the final dataset to a NetCDF file
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

def remap_temperature_with_cdo(yyyy):
    from cdo import Cdo
    logger.info(f"Starting CDO remapping of the preprocessed TMP2m data")
    cdo = Cdo()
    target_grid_file = "/work/gg0304/g260230/GRIDS/era5_grid.txt" # Target grid for remapping
    input_file_max = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/daily_max_{yyyy}.nc"
    temp_output_file_max = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/remapped_daily_max_{yyyy}.nc" # Temporary output file for remapped data
    input_file_min = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/daily_min_{yyyy}.nc"
    temp_output_file_min = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/remapped_daily_min_{yyyy}.nc" # Temporary output file for remapped data

    # Remap Maxima
    try:
        logger.info(f"Remapping daily max for year {yyyy} with CDO...")
        cdo.remapnn(
            target_grid_file, 
            input=input_file_max, 
            output=temp_output_file_max,
            options='-f nc', # Convert to netCDF
        )
        logger.info(f"Successfully remapped {input_file_max} to {temp_output_file_max}")

    except Exception as e:
        logger.error(f"Error during CDO remapping of {input_file_max}: {e}", exc_info=True)
        raise

    # Remap Minima
    try:
        logger.info(f"Remapping daily min for year {yyyy} with CDO...")
        cdo.remapnn(
            target_grid_file, 
            input=input_file_min, 
            output=temp_output_file_min,
            options='-f nc', # Convert to netCDF
        )
        logger.info(f"Successfully remapped {input_file_min} to {temp_output_file_min}")

    except Exception as e:
        logger.error(f"Error during CDO remapping of {input_file_min}: {e}", exc_info=True)
        raise

    # Delete original files after remapping & rename remapped files to original file names
    try:
        os.remove(input_file_max)
        os.rename(temp_output_file_max, input_file_max)
        logger.info(f"Replaced original file {input_file_max} with remapped file {temp_output_file_max}")

        os.remove(input_file_min)
        os.rename(temp_output_file_min, input_file_min)
        logger.info(f"Replaced original file {input_file_min} with remapped file {temp_output_file_min}")

    except Exception as e:
        logger.error(f"Error during cleanup of original and remapped files for year {yyyy}: {e}", exc_info=True)
        raise

def preprocess_prate(
        yyyy,
        ace2_hours = [0, 6, 12, 18],
        ):
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
    var = "PRATEsfc"
    ace2_hours = [0, 6, 12, 18]
    path_prefix = constants.era5_params[var]["1H"]
    PARAM = constants.era5_params[var]["PARAM"]
    filetype = constants.era5_params[var]["filetype"]

    # Create date range to loop over (example: Jan 1-5, 2010)
    date_range = pd.date_range(start=f"{yyyy}-01-01", end=f"{yyyy}-12-31", freq="D")
    
    # Initialize empty list to store daily datasets
    daily_sum_datasets = []

    # Loop over each day in the given year
    logger.info(f"Starting preprocessing for year {yyyy} with {len(date_range)} days to process...")
    for current_date in date_range:
        yyyy = yyyy
        mm = f"{current_date.month:02d}"
        dd = f"{current_date.day:02d}"
        
        # Step 1: Load data of the day
        logger.info(f"Processing {var} for {current_date.strftime('%Y-%m-%d')}")
        try:
            # Load data with cfgrib engine for grb files, and default engine for nc files
            data = xr.open_dataset(
                f"{path_prefix}{yyyy}-{mm}-{dd}_{PARAM}.{filetype}", 
                engine='cfgrib' if filetype == "grb" else None
            )
            logger.info(f"Content of the data: {data}")
        except Exception as e:
            logger.warning(f"Failed to load data for {current_date.strftime('%Y-%m-%d')}: {str(e)}. Skipping this date.")
            continue
        
        # Step2: Filter ACE2 timestamp
        logger.info(f"Filtering ACE2 timestamps")
        ace2_dates = current_date + pd.to_timedelta(ace2_hours, unit='h')
        stacked = data.stack(ts=('time', 'step'))
        stacked_filtered = stacked.where(stacked.valid_time.isin(ace2_dates), drop=True)
        filtered_data = stacked_filtered.swap_dims({'ts': 'valid_time'}).drop_vars('ts')

        ## Remove the time and steps & Rename valid_time to time
        filtered_data = filtered_data.drop_vars(['time', 'step'], errors='ignore')
        filtered_data = filtered_data.rename({'valid_time': 'time'})
        logger.info(f"Filtered data: {filtered_data}")


        # Step 3: Compute daily sum for the selected hours
        logger.info(f"Computing daily sum across ACE2 timestamps for the whole globe...")
        daily_sum = filtered_data.sum(dim="time")
        logger.info(f"Computed daily sum for {current_date.strftime('%Y-%m-%d')}")
        logger.info(f"Dimension of the daily sum datasets: {daily_sum.dims}")
        
        # Step 4: Add to dataset with time dimension
        logger.info(f"Adding daily sum to dataset with time dimension...")
        daily_sum = daily_sum.expand_dims(time=[current_date])      
        
        # Create dataset for this day and add to list
        logger.info(f"Creating dataset for daily sum and adding to list...")
        sum_ds = xr.Dataset({'prate': daily_sum["tp"]})
        daily_sum_datasets.append(sum_ds)

    # Step 5: Concatenate all daily datasets along time dimension
    logger.info(f"Concatenating all daily datasets for year {yyyy} along time dimension...")
    daily_sum_ds = xr.concat(daily_sum_datasets, dim="time")
    logger.info(f"Concatenated daily datasets for year {yyyy}, final time dimension length: {len(daily_sum_ds.time)}")

    # Step 6: Save the final dataset to a NetCDF file
    logger.info(f"Saving the final dataset to NetCDF files...")
    folder = f"data/processed/era5/1D/{var}/"
    Path(folder).mkdir(parents=True, exist_ok=True)
    logger.info(f"Created folder {folder} for saving NetCDF files if it did not exist")

    file_sum = f"{folder}daily_sum_{yyyy}.nc"
    daily_sum_ds.to_netcdf(file_sum)
    logger.info(f"Saved daily sum dataset to {file_sum}")

def remap_prate_with_cdo(yyyy):
    from cdo import Cdo
    logger.info(f"Starting CDO remapping of the preprocessed PRATE data")
    cdo = Cdo()
    target_grid_file = "/work/gg0304/g260230/GRIDS/era5_grid.txt" # Target grid for remapping
    input_file_sum = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/PRATEsfc/daily_sum_{yyyy}.nc"
    temp_output_file_sum = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/PRATEsfc/remapped_daily_sum_{yyyy}.nc" # Temporary output file for remapped data

    # Remap Sum
    try:
        logger.info(f"Remapping daily sum for year {yyyy} with CDO...")
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

def preprocess_wind_speed(yyyy):

    import glob

    # Load u10 and v10 of given year in 1H res
    logger.info(f"Loading U10 and V10 data for year {yyyy}...")
    u10_files = glob.glob(f"/pool/data/ERA5/E5/sf/an/1H/165/E5sf00_1H_{yyyy}-*.grb")
    v10_files = glob.glob(f"/pool/data/ERA5/E5/sf/an/1H/166/E5sf00_1H_{yyyy}-*.grb")
    u10 = xr.open_mfdataset(u10_files, engine='cfgrib')
    v10 = xr.open_mfdataset(v10_files, engine='cfgrib')

    # Filter the ace2 timestamps for that year
    logger.info(f"Filtering ACE2 timestamps for year {yyyy}...")
    ace2_hours = [0, 6, 12, 18]
    u10_mask = u10.valid_time.dt.hour.isin(ace2_hours).compute()  # Compute the boolean mask to avoid lazy evaluation issues
    v10_mask = v10.valid_time.dt.hour.isin(ace2_hours).compute()  # Compute the boolean mask to avoid lazy evaluation issues
    u10_filtered = u10.where(u10_mask, drop=True)
    v10_filtered = v10.where(v10_mask, drop=True)

    # Compute windspeed for the filtered ACE2 timesteps
    logger.info(f"Computing wind speed for the filtered ACE2 timesteps for year {yyyy}...")
    w = (u10_filtered['u10']**2 + v10_filtered['v10']**2)**0.5

    # Resample to daily max
    logger.info(f"Resampling wind speed to daily max for year {yyyy}...")
    w_daily_max = w.resample(time='1D').max()

    # Rename the variable to 10si_max to be consistent with the naming convention of the other datasets
    w_daily_max = w_daily_max.rename('10si_max')

    # Convert to dataset
    w_daily_max = w_daily_max.to_dataset(name='10si_max')

    # Save w_daily_max to NetCDF
    logger.info(f"Saving daily max wind speed to NetCDF for year {yyyy}...")
    output_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/10si/daily_max_{yyyy}.nc"
    w_daily_max.to_netcdf(output_path)
    logger.info(f"Saved daily max wind speed to {output_path}")

    # Free RAM
    u10.close()
    v10.close()
    u10_filtered.close()
    v10_filtered.close()
    w.close()
    w_daily_max.close()
    del u10, v10, u10_filtered, v10_filtered, w, w_daily_max
    gc.collect()

def remap_10si_with_cdo(yyyy):
    from cdo import Cdo
    cdo = Cdo()
    folder = "/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ERA5/1D/10si/"
    target_grid_file = "/work/gg0304/g260230/GRIDS/era5_grid.txt" # Target grid for remapping
    input_file_sum = f"{folder}daily_max_{yyyy}.nc"
    temp_output_file_sum = f"{folder}remapped_daily_max_{yyyy}_tmp.nc" # Temporary output file for remapped data

    logger.info(f"Remapping daily max for year {yyyy} with CDO...")
    cdo.remapnn(
            target_grid_file, 
            input=input_file_sum, 
            output=temp_output_file_sum,
            options='-f nc', # Convert to netCDF
        )
    
    logger.info(f"Replacing original file {input_file_sum} with remapped file {temp_output_file_sum}...")
    os.remove(input_file_sum)
    os.rename(temp_output_file_sum, input_file_sum)

# %% Main
def process_single_year(yyyy):
    """Process a single year - wraps preprocess and remap."""
    try:
        logger.info(f"Starting processing for year {yyyy}")
        #preprocess_wind_speed(yyyy)
        remap_10si_with_cdo(yyyy)
        logger.info(f"Successfully completed processing for year {yyyy}")
        return yyyy, True
    except Exception as e:
        logger.error(f"Failed processing year {yyyy}: {e}", exc_info=True)
        return yyyy, False

def main():
    # TODO: The preprocessing functions of tmp2m and prate need to be adjusted to the idea of the preprocessing of windspeed.
    # e.g. loading all files of one year at once and then computing to maximize RAM.
    years = range(1981, 2010 + 1)
    
    # Configure Dask for HPC environment
    n_workers = 10  # Increase if memory permits; decrease if you hit memory limits
    dask_config.set(scheduler='processes', num_workers=n_workers)
    logger.info(f"Starting parallel processing of {len(years)} years with {n_workers} workers")
    delayed_tasks = [delayed(process_single_year)(yyyy) for yyyy in years]
    
    # Compute all tasks in parallel
    results = compute(*delayed_tasks)
    
    # Report results
    successful = [year for year, success in results if success]
    failed = [year for year, success in results if not success]
    
    logger.info(f"Processing complete: {len(successful)} successful, {len(failed)} failed")
    if failed:
        logger.warning(f"Failed years: {failed}")

if __name__ == "__main__":
    main()

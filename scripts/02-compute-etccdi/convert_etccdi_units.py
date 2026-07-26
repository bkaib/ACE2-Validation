#%% Modules
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
from config import constants
from config.project_logging import setup_parallel_logger
from dask import delayed, compute, config as dask_config
import xarray as xr
import xclim.indices as xci
import xclim as xc
import glob
import pandas as pd
import os

#%% Setup Logger
current_filename = __file__.split("/")[-1].replace(".py", "")
logger, queue_listener = setup_parallel_logger(current_filename, use_queue_listener=True)

#%% Global Constants
etccdi_names = [
    # Temperatur related
    "ETR",
    "TN10p",
    "TNn",
    "TX90p",
    "TXx",
    "WSDI", 
    # Precipitation related
    "CWD",
    "R10",
    "Rx1day",
    # Wind related
    "FXx",
    "WSD",
    "FG95p",
]

#%% Functions
def load_era5_etccdi(name, timeperiod="1981-2010"):
    base_path = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5"
    file = os.path.join(base_path, f"{name}_1981-2010.nc")
    ds = xr.open_dataset(file)

    # Slice timeperiod
    ds = ds.sel(time=slice(f"{timeperiod.split('-')[0]}-01-01", f"{timeperiod.split('-')[1]}-12-31"))
    return ds, file

def load_ace2_etccdi(name, scenario, ensemble_number):
    base_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/{scenario}"
    file = os.path.join(base_path, f"{name}_ensemble_{ensemble_number}.nc")
    ds = xr.open_dataset(file)
    return ds, file

def convert_era5():
    for name in etccdi_names:
        # Load ERA5 data
        era5_ds, era5_file = load_era5_etccdi("TX90p")
        
        # Convert timedelta to days
        for var in era5_ds.data_vars:
            if pd.api.types.is_timedelta64_dtype(era5_ds[var].dtype):
                print("Converting timedelta to days for variable:", var)
                era5_ds[var] = era5_ds[var].dt.days
                
        # Save the converted dataset
        output_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/{name}_1981-2010_converted.nc"
        era5_ds.to_netcdf(output_path)
        logger.info(f"Converted and saved ERA5 ETCCDI index {name} to {output_path}")
        os.rename(output_path, era5_file)

def convert_ace2_dates_to_datetime():
    """Converts the time dimension of ACE2 ETCCDI datasets from int64 to pd.datetime64 type."""
    for name in etccdi_names:
        for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]:
            for ensemble_number in range(12):
                # Load ACE2 data
                print(f"Loading ACE2 ETCCDI index {name} for scenario {scenario} ensemble {ensemble_number}")
                ace2_ds, ace2_file = load_ace2_etccdi(name, scenario, ensemble_number)
                
                # Convert the time dimension from int64 to a pd.datetime64 type
                # ACE2 dates go from 2001 - 2010 yearly. make a constant of dates and set the time coordiante to those years
                ace2_date_range = pd.date_range(start="2001-01-01", end="2010-12-31", freq="Y")
                ace2_ds = ace2_ds.assign_coords(time=ace2_date_range)
                
                # Save the converted dataset
                output_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/{scenario}/{name}_ensemble_{ensemble_number}_converted.nc"
                ace2_ds.to_netcdf(output_path)
                logger.info(f"Converted and saved ACE2 ETCCDI index {name} for scenario {scenario} ensemble {ensemble_number} to {output_path}")
                os.rename(output_path, ace2_file)

def convert_ace2_timedelta_to_days():
    """Converts the timedelta variables in ACE2 ETCCDI datasets to days."""
    for name in etccdi_names:
        for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]:
            for ensemble_number in range(12):
                ace2_ds, ace2_file = load_ace2_etccdi(name=name, scenario=scenario, ensemble_number=ensemble_number)
                
                # Convert all variables in the dataset
                for var in ace2_ds.data_vars:
                    if pd.api.types.is_timedelta64_dtype(ace2_ds[var].dtype):
                        logger.info(f"Converting timedelta to days for variable: {var}")
                        ace2_ds[var] = ace2_ds[var].dt.days
                    elif pd.api.types.is_float_dtype(ace2_ds[var].dtype):
                        logger.info(f"Converting float to int for variable: {var}")
                        ace2_ds[var] = ace2_ds[var].astype(int)
                
                # Save once after all conversions
                output_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/{scenario}/{name}_ensemble_{ensemble_number}_converted.nc"
                ace2_ds.to_netcdf(output_path)
                logger.info(f"Converted and saved ACE2 ETCCDI index {name} for scenario {scenario} ensemble {ensemble_number}")
                # os.rename(output_path, ace2_file)

def check_if_data_var_exists():
    """Checks if the data variable exists in the dataset."""
    erroneous_files = []
    for name in etccdi_names:
        for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]:
            for ensemble_number in range(12):
                # Load ACE2 data
                ace2_ds, ace2_file = load_ace2_etccdi(name=name, scenario=scenario, ensemble_number=ensemble_number)
                
                # Check if the data variable exists
                if len(ace2_ds.data_vars) == 0:
                    # logger.warning(f"Data variable {name} does not exist in ACE2 ETCCDI index for scenario {scenario} ensemble {ensemble_number}")
                    erroneous_files.append(ace2_file)
                else:
                    continue
                    # logger.info(f"Data variable {name} exists in ACE2 ETCCDI index for scenario {scenario} ensemble {ensemble_number}")
    return erroneous_files

#%% Main Execution
def main():
    # convert_era5()
    # convert_ace2_dates_to_datetime()
    convert_ace2_timedelta_to_days()

if __name__ == "__main__":
    main()


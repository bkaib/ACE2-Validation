#%% Modules
import os
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
#%% Setup Logger
current_filename = __file__.split("/")[-1].replace(".py", "")
logger, queue_listener = setup_parallel_logger(current_filename, use_queue_listener=True)

#%% Functions
def load_era5_etccdi(name, timeperiod="1981-2010"):
    base_path = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5"
    file = os.path.join(base_path, f"{name}_1981-2010.nc")
    ds = xr.open_dataset(file)

    # Slice timeperiod
    ds = ds.sel(time=slice(f"{timeperiod.split('-')[0]}-01-01", f"{timeperiod.split('-')[1]}-12-31"))
    return ds

def load_ace2_etccdi(name, scenario, ensemble_number):
    base_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/{scenario}"
    file = os.path.join(base_path, f"{name}_ensemble_{ensemble_number}.nc")
    ds = xr.open_dataset(file)
    return ds

#%% Scratch
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
name = etccdi_names[0]
scenarios = [
    "2000v1940",
    "2000v1950", 
    "2000v1979",
    "2000v2020",
    ]
era5_index = load_era5_etccdi(name, timeperiod="2001-2010")
ace2_index = load_ace2_etccdi(name, scenarios[0], ensemble_number=1)

#%% Main
def main():
    pass

if __name__ == "__main__":
    main()
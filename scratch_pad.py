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
importlib.reload(constants)



# %%

# Parameters
var = "TMP2m"
ace2_hours = [0, 6, 12, 18]
path_prefix = constants.era5_params[var]["1H"]
PARAM = constants.era5_params[var]["PARAM"]
filetype = constants.era5_params[var]["filetype"]

# Create date range to loop over (example: Jan 1-5, 2010)
date_range = pd.date_range(start="2010-01-01", end="2010-01-05", freq="D")

# Initialize empty list to store daily datasets
daily_min_datasets = []
daily_max_datasets = []

# Loop over each day
for current_date in date_range:
    yyyy = str(current_date.year)
    mm = f"{current_date.month:02d}"
    dd = f"{current_date.day:02d}"
    
    # Step 1: Load data of the day
    data = xr.open_dataset(
        f"{path_prefix}{yyyy}-{mm}-{dd}_{PARAM}.{filetype}", 
        engine='cfgrib' if filetype == "grb" else None
    )
    
    # Step 2: Filter ACE2 timestamps
    filtered_data = data.where(
        data.valid_time.dt.hour.isin(ace2_hours), drop=True
    )
    
    # Step 3: Compute min and max for the selected hours
    daily_min = filtered_data.isel(values=[0, 1, 2]).min(dim="time")
    daily_max = filtered_data.isel(values=[0, 1, 2]).max(dim="time")
    
    # Step 4: Convert lon/lat coordinates to dimensions
    daily_min = daily_min.assign_coords(
        lat=('values', daily_min['latitude'].values),
        lon=('values', daily_min['longitude'].values)
    ).set_index(values=['lat', 'lon']).unstack('values')
    
    daily_max = daily_max.assign_coords(
        lat=('values', daily_max['latitude'].values),
        lon=('values', daily_max['longitude'].values)
    ).set_index(values=['lat', 'lon']).unstack('values')
    
    # Remove unnecessary coordinates
    daily_min = daily_min.drop_vars(['latitude', 'longitude', "step", "surface", "number"])
    daily_max = daily_max.drop_vars(['latitude', 'longitude', "step", "surface", "number"])
    
    # Step 5: Add to dataset with time dimension
    daily_min = daily_min.expand_dims(time=[current_date])
    daily_max = daily_max.expand_dims(time=[current_date])
    
    # Create dataset for this day and add to list
    min_ds = xr.Dataset({'tasmin': daily_min["t2m"]})
    max_ds = xr.Dataset({'tasmax': daily_max["t2m"]})
    daily_min_datasets.append(min_ds)
    daily_max_datasets.append(max_ds)

# Step 6: Concatenate all daily datasets along time dimension
daily_min_ds = xr.concat(daily_min_datasets, dim="time")
daily_max_ds = xr.concat(daily_max_datasets, dim="time")

daily_min_ds

# Step 7: Save the final dataset to a NetCDF file
daily_min_ds.to_netcdf(f"daily_min_{yyyy}.nc")
daily_max_ds.to_netcdf(f"daily_max_{yyyy}.nc")
# %%

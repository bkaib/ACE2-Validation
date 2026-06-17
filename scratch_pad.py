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



# %%

# Parameters
var = "TMP2m"
ace2_hours = [0, 6, 12, 18]
path_prefix = constants.era5_params[var]["1H"]
PARAM = constants.era5_params[var]["PARAM"]
filetype = constants.era5_params[var]["filetype"]

# Create date range to loop over (example: Jan 1-3, 2010)
date_range = pd.date_range(start="2010-01-01", end="2010-01-03", freq="D")

# Initialize empty list to store daily datasets
daily_min_datasets = []
daily_max_datasets = []

# Loop over each day
for current_date in date_range:
    print(f"Processing date: {current_date.strftime('%Y-%m-%d')}")
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
    daily_min = filtered_data.min(dim="time")
    daily_max = filtered_data.max(dim="time")
    
    # Step 4: Add to dataset with time dimension
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

# Step 7: Save the final dataset to a NetCDF file
folder = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/"
daily_min_ds.to_netcdf(f"{folder}daily_min_{yyyy}.nc")
daily_max_ds.to_netcdf(f"{folder}daily_max_{yyyy}.nc")
print(f"Saved daily min and max datasets for {yyyy} to NetCDF files.")


# CDO Remapping %%
from cdo import Cdo
cdo = Cdo()
target_grid_file = "/work/gg0304/g260230/GRIDS/era5_grid.txt" # Target grid for remapping
input_file = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/daily_max_2010.nc"
temp_output_file = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/remapped_daily_max_2010.nc" # Temporary output file for remapped data

ds = xr.open_dataset(input_file)
print(ds)

print("Remap CDO")
cdo.remapnn(
        target_grid_file, 
        input=input_file, 
        output=temp_output_file,
        options='-f nc', # Convert to netCDF
    )

# %%
p = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/daily_max_1981.nc"
ds = xr.open_dataset(p)
print(ds)

# Visualize data on global map
plt.figure(figsize=(10, 5))
ax = plt.axes(projection=ccrs.PlateCarree())
ds.tasmax.isel(time=0).plot(ax=ax, transform=ccrs.PlateCarree(), cmap='coolwarm', vmin=250, vmax=320)
ax.coastlines()
ax.set_title('Remapped Daily Max Temperature (K) (1981-01-01)')
plt.show()

p = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/daily_min_1981.nc"
ds = xr.open_dataset(p)
print(ds)

# Visualize data on global map
plt.figure(figsize=(10, 5))
ax = plt.axes(projection=ccrs.PlateCarree())
ds.tasmin.isel(time=0).plot(ax=ax, transform=ccrs.PlateCarree(), cmap='coolwarm', vmin=250, vmax=320)
ax.coastlines()
ax.set_title('Remapped Daily Min Temperature (K) (1981-01-01)')
plt.show()


# %% Preprocess PRATEsfc

# Parameters
var = "PRATEsfc"
ace2_hours = [0, 6, 12, 18]
path_prefix = constants.era5_params[var]["1H"]
PARAM = constants.era5_params[var]["PARAM"]
filetype = constants.era5_params[var]["filetype"]

# Create date range to loop over (example: Jan 1-3, 2010)
date_range = pd.date_range(start="2010-01-01", end="2010-01-03", freq="D")

# Initialize empty list to store daily datasets
daily_sum_datasets = []

for current_date in date_range:
    print(f"Processing date: {current_date.strftime('%Y-%m-%d')}")
    yyyy = str(current_date.year)
    mm = f"{current_date.month:02d}"
    dd = f"{current_date.day:02d}"
    
    # Step 1: Load data of the day
    data = xr.open_dataset(
        f"{path_prefix}{yyyy}-{mm}-{dd}_{PARAM}.{filetype}", 
        engine='cfgrib' if filetype == "grb" else None
    )
    
    # Step2: Filter ACE2 timestamp
    ace2_dates = current_date + pd.to_timedelta(ace2_hours, unit='h')
    stacked = data.stack(ts=('time', 'step'))
    stacked_filtered = stacked.where(stacked.valid_time.isin(ace2_dates), drop=True)
    filtered_data = stacked_filtered.swap_dims({'ts': 'valid_time'}).drop_vars('ts')

    ## Remove the time and steps & Rename valid_time to time
    filtered_data = filtered_data.drop_vars(['time', 'step'], errors='ignore')
    filtered_data = filtered_data.rename({'valid_time': 'time'})

    # Step 3: Compute daily sum
    daily_sum = filtered_data.sum(dim="time")
    
    # Step 4: Add to dataset with time dimension
    daily_sum = daily_sum.expand_dims(time=[current_date])
    
    # Create dataset for this day and add to list
    sum_ds = xr.Dataset({'prate': daily_sum["tp"]})
    daily_sum_datasets.append(sum_ds)

# Step 5: Concatenate all daily datasets along time dimension
daily_sum_ds = xr.concat(daily_sum_datasets, dim="time")
file = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/PRATEsfc/daily_sum_2010.nc"
daily_sum_ds.to_netcdf(file)

# CDO Remapping %%
from cdo import Cdo
cdo = Cdo()
target_grid_file = "/work/gg0304/g260230/GRIDS/era5_grid.txt" # Target grid for remapping
input_file = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/PRATEsfc/daily_sum_2010.nc"
temp_output_file = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/PRATEsfc/remapped_daily_sum_2010.nc" # Temporary output file for remapped data

print("Remap CDO")
cdo.remapnn(
        target_grid_file, 
        input=input_file, 
        output=temp_output_file,
        options='-f nc', # Convert to netCDF
    )

# %%
p = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/PRATEsfc/remapped_daily_sum_2010.nc"
ds = xr.open_dataset(p)
print(ds)

# Visualize data on global map
precip_thresholds = dict(
    normal = 0.01,  # Normal precipitation range in m/s
    tropical = 0.05,
    extreme = 0.1,
)
plt.figure(figsize=(10, 5))
ax = plt.axes(projection=ccrs.PlateCarree())
ds.prate.isel(time=0).plot(ax=ax, transform=ccrs.PlateCarree(), cmap='viridis', vmin=0, vmax=precip_thresholds['tropical'])
ax.coastlines()
ax.set_title('Remapped Daily Sum Precipitation (m) (2010-01-01)')
plt.show()

# %%

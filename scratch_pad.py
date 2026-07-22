# %% Modules
import logging
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation")
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
from pathlib import Path
import os
import glob


# %% Load ensemble data
p = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/FG95p_1981-2010.nc"
ds = xr.open_dataset(p)

mean = ds["FG95p"].isel(percentiles=0).sel(time=slice("2001-01-01", "2010-12-31")).mean("time").dt.days # convert time delta to days

fig, ax = plt.subplots(figsize=(10, 5), subplot_kw={'projection': ccrs.EqualEarth()})
mean.plot(ax=ax, transform=ccrs.PlateCarree(), cmap='viridis', alpha=0.5)
ax.coastlines() 
ax.gridlines()

#%% Check regridding of 10simean
var = "WSDI"
p = f"data/processed/ETCCDI/ACE2/2000v1940/{var}_ensemble_0.nc"
era5_p = f"data/processed/ETCCDI/ERA5/{var}_1981-2010.nc"
ds = xr.open_dataset(p)
era5_ds = xr.open_dataset(era5_p)

data_array_var = var
era5_ds[data_array_var].values

# Convert the values of the data array from timdelta64[ns] to days
era5_ds[data_array_var].values = era5_ds[data_array_var].dt.days
ds[data_array_var].values = ds[data_array_var].dt.days


#%% Plot ETCCDI of ERA5 and ACE2 in one figure with subplots for each variable
# Column 1: ERA5, Column 2: ACE2, Column 3: Difference (ACE2 - ERA5)
fig, axes = plt.subplots(nrows=1, ncols=3, figsize=(15, 5), subplot_kw={'projection': ccrs.EqualEarth()})
data_ace2 = ds[data_array_var].isel(percentiles=0).mean("time")
data_era5 = era5_ds[data_array_var].sel(time=slice("2001-01-01", "2010-12-31")).mean("time")
# Convert type of data from timedelta64[ns] to days
data_era5.plot(ax=axes[0], transform=ccrs.PlateCarree(), cmap='viridis', alpha=0.5)
data_ace2.plot(ax=axes[1], transform=ccrs.PlateCarree(), cmap='viridis', alpha=0.5)
difference = data_ace2 - data_era5
difference.plot(ax=axes[2], transform=ccrs.PlateCarree(), cmap='bwr', alpha=0.5)
axes[0].coastlines()
axes[0].gridlines()
axes[0].set_title("ERA5")
axes[1].coastlines()
axes[1].gridlines()
axes[1].set_title("ACE2")
axes[2].coastlines()
axes[2].gridlines()
axes[2].set_title("Difference (ACE2 - ERA5)")
fig.show()

# %% Visualize Absolute Indices

indices_temp = ["TXx", "TNn", "ETR"]
indices_precip = ["Rx1day", "R10", "CWD"]
indices_wind = ["FXx", "WSD",]
indices = indices_temp + indices_precip + indices_wind

vmin_vmax_ranges = dict(
    TXx=(250, 320),
    TNn=(200, 320),
    ETR=(0, 20),
    Rx1day=(0, 30),
    R10=(0, 5),
    CWD=(0, 20),
    FXx=(0, 30),
    WSD=(0, 3),
)

fig, axes = plt.subplots(nrows=3, ncols=3, figsize=(15, 12), subplot_kw={'projection': ccrs.EqualEarth()})

# Temperature indices (row 0)
for i, idx in enumerate(indices_temp):
    ds = xr.open_dataset(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/{idx}_1981-2010.nc")
    
    projection = ccrs.EqualEarth()
    ax = axes[0, i]
    (ds[idx]
     .mean(dim="time")
     .plot(
         ax=ax, 
         transform=ccrs.PlateCarree(), 
         cmap='viridis',
        vmin=vmin_vmax_ranges[idx][0],
        vmax=vmin_vmax_ranges[idx][1],
         )
     )
    ax.coastlines()
    ax.gridlines()
    ax.set_title(f"{idx} Index")

# Precipitation indices (row 1)
for i, idx in enumerate(indices_precip):
    ds = xr.open_dataset(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/{idx}_1981-2010.nc")
    
    projection = ccrs.EqualEarth()
    ax = axes[1, i]
    (ds[idx]
     .mean(dim="time")
     .plot(
         ax=ax, 
         transform=ccrs.PlateCarree(), 
         cmap='viridis',
        vmin=vmin_vmax_ranges[idx][0],
        vmax=vmin_vmax_ranges[idx][1],
         )
     )
    ax.coastlines()
    ax.gridlines()
    ax.set_title(f"{idx} Index")

# Wind indices (row 2)
for i, idx in enumerate(indices_wind):
    ds = xr.open_dataset(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/{idx}_1981-2010.nc")
    
    projection = ccrs.EqualEarth()
    ax = axes[2, i]
    (ds[idx]
     .mean(dim="time")
     .plot(
         ax=ax, 
         transform=ccrs.PlateCarree(), 
         cmap='viridis',
        vmin=vmin_vmax_ranges[idx][0],
        vmax=vmin_vmax_ranges[idx][1],
         )
     )
    ax.coastlines()
    ax.gridlines()
    ax.set_title(f"{idx} Index")

# Hide empty subplots in row 2 (wind row only has 2 indices)
axes[2, 2].set_visible(False)

fig.suptitle("ERA5 ETCCDI Indices | Temporal Mean over 1981-2010", fontsize=16)
plt.show()



#%% Look at 10si regridded
variables = ["10si", 
             #"TMP2m", 
             # "PRATEsfc",
             ]
PROJECT_ROOT = "/work/gg0304/g260230/projects/ACE2-Validation"
projection = ccrs.EqualEarth()
# Compare the regridded and original data for each variable 
# in one figure with subplots for each variable
fig, axes = plt.subplots(
    nrows=len(variables), ncols=2, figsize=(15, 5), 
    subplot_kw={'projection': projection}
    )
var_names = dict(
    "10si": "10si_max"
)
for i, variable in enumerate(variables):
    BASE_INPUT_REGRID = Path(PROJECT_ROOT) / "data/processed/ERA5/1D/ACE2GRID"
    BASE_INPUT_ORIG = Path(PROJECT_ROOT) / "data/raw/ERA5/1D/"
    input_path_regrid = BASE_INPUT_REGRID / variable
    input_path_orig = BASE_INPUT_ORIG / variable
    regrid_files = list(input_path_regrid.glob("*.nc"))
    orig_files = list(input_path_orig.glob("*.nc"))

    regrid_files.sort()
    orig_files.sort()

    # Load regridded and original data
    ds_original = xr.open_dataset(orig_files[0])
    ds_regridded = xr.open_dataset(regrid_files[0])

    data_var_orig = list(ds_original.data_vars)[0]
    data_var_regrid = list(ds_regridded.data_vars)[0]
    
    # Plot data into axes
    (ds_original[data_var_orig]
     .mean("time")
     .plot(ax=axes[i, 0], transform=ccrs.PlateCarree(), cmap='viridis')
    )
    axes[i, 0].coastlines()
    axes[i, 0].set_title(f"Original {variable}")    
    axes[i, 0].gridlines()

    (ds_regridded[data_var_regrid]
     .mean("time")
     .plot(ax=axes[i, 1], transform=ccrs.PlateCarree(), cmap='viridis')
    )
    axes[i, 1].coastlines()
    axes[i, 1].set_title(f"Regridded {variable}")
    axes[i, 1].gridlines()

fig.suptitle("Comparison of Original and Regridded Data", fontsize=16)
fig.show()











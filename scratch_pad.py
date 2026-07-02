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
from pathlib import Path
import os
import glob


# %% 


ds = xr.open_dataset("/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ace2-ensembles/1D/2000v1940/ensemble_0.nc")
ds

#%% Look at 10si
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









# %% Visualize yearly max windspeed
yyyy = 1981
p = f"data/processed/era5/1D/10si/daily_max_{yyyy}.nc"
ds = xr.open_dataset(p)
print(ds)

# Plot the yearly max wind speed on a global grid with equal earth
fig = plt.figure(figsize=(12, 6))
projection = ccrs.EqualEarth()
ax = plt.axes(projection=projection)
ds['__xarray_dataarray_variable__'].max("time").plot(ax=ax, transform=ccrs.PlateCarree(), cmap='viridis')
ax.coastlines()
ax.set_title(f"Yearly Max Wind Speed for {yyyy}")
plt.show()

# Plot the seasonal mean (DJF, MAM, JJA, SON) max wind speed
ds['season'] = ds['time.season']
print(ds.groupby('season'))
seasonal_mean = ds.groupby('season').mean('time')
fig, axes = plt.subplots(ncols=4, nrows=1, figsize=(15, 10), subplot_kw={'projection': projection})

axes = axes.flatten()
for i, season in enumerate(['DJF', 'MAM', 'JJA', 'SON']):
    seasonal_mean['__xarray_dataarray_variable__'].sel(season=season).plot(vmin=0, vmax=15,ax=axes[i], transform=ccrs.PlateCarree(), cmap='viridis', add_colorbar=False)
    axes[i].coastlines()
    axes[i].set_title(f"{season}")

# One colorbar for all subplots, horizontally under the subplots
cbar_ax = fig.add_axes([0.1, 0.05, 0.8, 0.02])  # [left, bottom, width, height]
norm = plt.Normalize(vmin=0, vmax=15)
sm = plt.cm.ScalarMappable(cmap='viridis', norm=norm)
sm.set_array([])
fig.colorbar(sm, cax=cbar_ax, orientation='horizontal', label='(m/s)')
fig.suptitle(f"Seasonal Mean Max Wind Speed for {yyyy}", fontsize=16)
plt.tight_layout()
plt.show()

# %%
seasonal_mean
# %%

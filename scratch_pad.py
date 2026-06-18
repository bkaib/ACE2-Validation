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

# %% Visualize Mean of Precipitation for Different Months
yyyy = 2010
months = [1, 6, 12]
p = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/PRATEsfc/daily_sum_{yyyy}.nc"
ds = xr.open_dataset(p)

# Visualize data on global map
precip_thresholds = dict(
    normal = 0.01,  # Normal precipitation range in m/s
    tropical = 0.05,
    extreme = 0.1,
)
month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
vmax = precip_thresholds['normal'] / 2
projection = ccrs.EqualEarth()
fig, axes = plt.subplots(
    nrows=1, ncols=3, figsize=(18, 6), subplot_kw={'projection': projection})
axes = axes.flatten()

for i, month in enumerate(months):
    ax = axes[i]
    # Select data only for the current month
    month_mean = ds['prate'].sel(time=ds.time.dt.month==month).mean(dim='time')
    
    # Plot the data of each month
    im = month_mean.plot(ax=ax, transform=ccrs.PlateCarree(), cmap='Blues', vmin=0, vmax=vmax, add_colorbar=False)    
    ax.set_title(f'Month: {month}')
    ax.coastlines()
    ax.gridlines(draw_labels=True)
    ax.legend(loc='upper right')


# Add colorbar for the entire figure
cbar = fig.colorbar(plt.cm.ScalarMappable(cmap='Blues', norm=plt.Normalize(vmin=0, vmax=vmax)),
                    ax=axes, orientation='vertical', fraction=0.02, pad=0.04)
cbar.set_label('Total Precipitation (m)')
plt.show()


# %% Visualize Mean of Temperature Min and Max for Different Months
yyyy = 2010
months = [1, 6, 12]
p = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/daily_min_{yyyy}.nc"
ds_min = xr.open_dataset(p)
p = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/TMP2m/daily_max_{yyyy}.nc"
ds_max = xr.open_dataset(p)

print(ds_max)
# Visualize data on global map
vmin, vmax = 250, 320  # Temperature range in Kelvin
projection = ccrs.EqualEarth()
fig, axes = plt.subplots(
    nrows=2, ncols=3, figsize=(18, 6), subplot_kw={'projection': projection})
axes = axes.flatten()

for i, month in enumerate(months):
    if i < 3: # Plot the maxima
        ax = axes[i]
        # Select data only for the current month
        month_mean = ds_max['tasmax'].sel(time=ds_max.time.dt.month==month).mean(dim='time')
        
        # Plot the data of each month
        im = month_mean.plot(ax=ax, transform=ccrs.PlateCarree(), cmap='Reds', vmin=vmin, vmax=vmax, add_colorbar=False)    
        ax.set_title(f'Month: {month} - Max Temp')
        ax.coastlines()
        ax.gridlines(draw_labels=True)
        ax.legend(loc='upper right')
    else: # Plot the minima
        ax = axes[i]
        # Select data only for the current month
        month_mean = ds_min['tasmin'].sel(time=ds_min.time.dt.month==month).mean(dim='time')
        
        # Plot the data of each month
        im = month_mean.plot(ax=ax, transform=ccrs.PlateCarree(), cmap='Reds', vmin=vmin, vmax=vmax, add_colorbar=False)    
        ax.set_title(f'Month: {month} - Max Temp')
        ax.coastlines()
        ax.gridlines(draw_labels=True)
        ax.legend(loc='upper right')
    
# Add colorbar for the entire figure
cbar = fig.colorbar(plt.cm.ScalarMappable(cmap='Reds', norm=plt.Normalize(vmin=vmin, vmax=vmax)),
                    ax=axes, orientation='vertical', fraction=0.02, pad=0.04)
cbar.set_label('Temperature (K)')
fig.tight_layout()
p = "results/figures/02-compute-etccdi/tmp2m_min_max_month_means.png"
fig.savefig()

# %%

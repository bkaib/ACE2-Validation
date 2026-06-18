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

for i, month in enumerate(months):
    # Add Maxima
    ax = axes[0, i]
    ## Select data only for the current month
    month_mean = ds_max['tasmax'].sel(time=ds_max.time.dt.month==month).mean(dim='time')
    
    ## Plot the data of each month
    im = month_mean.plot(ax=ax, transform=ccrs.PlateCarree(), cmap='Reds', vmin=vmin, vmax=vmax, add_colorbar=False)    
    ax.set_title(f'Month: {month} - Max Temp')
    ax.coastlines()
    ax.gridlines(draw_labels=True)
    ax.legend(loc='upper right')

    # Add Minima
    ax = axes[1, i]
    ## Select data only for the current month
    month_mean = ds_min['tasmin'].sel(time=ds_min.time.dt.month==month).mean(dim='time')
    
    ## Plot the data of each month
    im = month_mean.plot(ax=ax, transform=ccrs.PlateCarree(), cmap='Reds', vmin=vmin, vmax=vmax, add_colorbar=False)    
    ax.set_title(f'Month: {month} - Min Temp')
    ax.coastlines()
    ax.gridlines(draw_labels=True)
    ax.legend(loc='upper right')
    
# Add colorbar for the entire figure
cbar = fig.colorbar(plt.cm.ScalarMappable(cmap='YlOrRd', norm=plt.Normalize(vmin=vmin, vmax=vmax)),
                    ax=axes, orientation='vertical', fraction=0.02, pad=0.04)
cbar.set_label('Temperature (K)')
fig.tight_layout()
p = "results/figures/02-compute-etccdi/tmp2m_min_max_month_means.png"
fig.savefig(p)  

# %% Load ERA5 Wind Speed Data 

p = "/work/gg0304/g260230/data/ERA5/E5/sf/an/1D/207/E5sf00_1D_2024-02_207.nc"
ds = xr.open_dataset(p)
print(ds)


# %% Check how i resampled ACE2
p = "/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ace2-ensembles/1D/2000v1940/ensemble_0.nc"
ds = xr.open_dataset(p)
print(ds)

# %%

# Constants
yyyy = 2010
daily_max_dataset = []
u_var = "U10"
v_var = "V10"
u_path_prefix = constants.era5_params[u_var]["1H"]
v_path_prefix = constants.era5_params[v_var]["1H"]
u_PARAM = constants.era5_params[u_var]["PARAM"]
v_PARAM = constants.era5_params[v_var]["PARAM"]
filetype = "grb"
ace2_hours = [0, 6, 12, 18]

date_range = pd.date_range(start=f"{yyyy}-01-01", end=f"{yyyy}-01-03", freq="D")
for current_date in date_range:
    yyyy = yyyy
    mm = f"{current_date.month:02d}"
    dd = f"{current_date.day:02d}"

    # Step 1: Load the U and V Components of the Current Day
    print(f"Processing Wind Speed for {current_date.strftime('%Y-%m-%d')}")
    try:
        # Load data with cfgrib engine for grb files, and default engine for nc files
        u10 = xr.open_dataset(
            f"{u_path_prefix}{yyyy}-{mm}-{dd}_{u_PARAM}.{filetype}", 
            engine='cfgrib' if filetype == "grb" else None
        )
        v10 = xr.open_dataset(
            f"{v_path_prefix}{yyyy}-{mm}-{dd}_{v_PARAM}.{filetype}", 
            engine='cfgrib' if filetype == "grb" else None
        )
        
        print(f"Content of U10 data: {u10}")
        print(f"Content of V10 data: {v10}")
    except Exception as e:
        print(f"Failed to load data for {current_date.strftime('%Y-%m-%d')}: {str(e)}. Skipping this date.")
        continue

    # Step 2: Select only the ACE2 Timestamps
    print(f"Filtering ACE2 timestamps")
    u10_filtered = u10.where(
            u10.valid_time.dt.hour.isin(ace2_hours), drop=True
        )
    v10_filtered = v10.where(
            v10.valid_time.dt.hour.isin(ace2_hours), drop=True
        )
    print(f"Filtered U10 data: {u10_filtered}")
    print(f"Filtered V10 data: {v10_filtered}")

    ## Check if the values dimension of u10 and v10 have the same longitude and latitude coordinates
    if not (u10_filtered.longitude.equals(v10_filtered.longitude) and u10_filtered.latitude.equals(v10_filtered.latitude)):
        print(f"Longitude and latitude coordinates of U10 and V10 do not match for {current_date.strftime('%Y-%m-%d')}. Skipping this date.")
    else: 
        print(f"Longitude and latitude coordinates of U10 and V10 match for {current_date.strftime('%Y-%m-%d')}. Proceeding with wind speed calculation.")
        print(f"Proceed computing the wind speed for {current_date.strftime('%Y-%m-%d')}...")
    
    # Step 3: Calculate the Wind Speed from U and V Components at Each ACE2 Timestamp using xarray
    w = u10_filtered['u10']**2 + v10_filtered['v10']**2
    w = w**0.5
    print(f"Calculated wind speed data: {w}")

    # Step 4: Resample the 6H Timesteps to 1D by Taking the Daily Maximum Wind Speed
    print(f"Resampling wind speed data to daily maximum for {current_date.strftime('%Y-%m-%d')}...")
    daily_max_w = w.resample(time='1D').max()
    print(f"Resampled daily maximum wind speed data: {daily_max_w}")

    # Step 5: Add the Daily Maximum Wind Speed to a Dataset with Time Dimension
    print(f"Adding daily maximum wind speed to dataset with time dimension...")
    # daily_max_w = daily_max_w.expand_dims(time=[current_date])
    # print(daily_max_w)

    # Create dataset for this day and add to list
    print(f"Creating dataset for daily min and max and adding to list...")
    max_ds = xr.Dataset({'10si_max': daily_max_w})
    daily_max_dataset.append(max_ds)
    print(max_ds)

# Concatenate all days into one ds
print(f"Concatenating all daily datasets for year {yyyy} along time dimension...")
daily_max_ds = xr.concat(daily_max_dataset, dim="time")
print(daily_max_ds)

# Step 6: Save the final dataset to a NetCDF file
print(f"Saving the final dataset to NetCDF files...")
folder = f"data/processed/era5/1D/10si/"
Path(folder).mkdir(parents=True, exist_ok=True)
print(f"Created folder {folder} for saving NetCDF files if it did not exist")

file_sum = f"{folder}daily_max_{yyyy}.nc"
daily_max_ds.to_netcdf(file_sum)
print(f"Saved daily max dataset to {file_sum}")

# Step 6: Regrid the Data To the ERA5 Grid Using CDO
def remap_wind_with_cdo(yyyy):
    from cdo import Cdo
    print(f"Starting CDO remapping of the preprocessed PRATE data")
    cdo = Cdo()
    target_grid_file = "/work/gg0304/g260230/GRIDS/era5_grid.txt" # Target grid for remapping
    input_file_sum = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/10si/daily_max_{yyyy}.nc"
    temp_output_file_sum = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/10si/remapped_daily_max_{yyyy}.nc" # Temporary output file for remapped data

    # Remap Sum
    try:
        print(f"Remapping daily sum for year {yyyy} with CDO...")
        cdo.remapnn(
            target_grid_file, 
            input=input_file_sum, 
            output=temp_output_file_sum,
            options='-f nc', # Convert to netCDF
        )
        print(f"Successfully remapped {input_file_sum} to {temp_output_file_sum}")

    except Exception as e:
        print(f"Error during CDO remapping of {input_file_sum}: {e}")
        raise

    # Delete original files after remapping & rename remapped files to original file names
    try:
        os.remove(input_file_sum)
        os.rename(temp_output_file_sum, input_file_sum)
        print(f"Replaced original file {input_file_sum} with remapped file {temp_output_file_sum}")

    except Exception as e:
        print(f"Error during cleanup of original and remapped files for year {yyyy}: {e}")
        raise

remap_wind_with_cdo(yyyy)


# %% Visualize the remapped data

p = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/10si/daily_max_2010.nc"
ds = xr.open_dataset(p)
print(ds)

# Plot the mean data over time on a global map with equal earth
fig, ax = plt.subplots(figsize=(10, 5), subplot_kw={'projection': ccrs.EqualEarth()})
ds['10si_max'].mean(dim='time').plot(ax=ax, transform=ccrs.PlateCarree(), cmap='viridis')
ax.coastlines()
ax.set_title('Mean Daily Max Wind Speed for 2010')
plt.show()  

# %% Load the data of a full year into memory

def preprocess_wind_speed(yyyy):

    import glob

    # Load u10 and v10 of given year in 1H res
    print(f"Loading U10 and V10 data for year {yyyy}...")
    u10_files = glob.glob(f"/pool/data/ERA5/E5/sf/an/1H/165/E5sf00_1H_{yyyy}-*.grb")
    v10_files = glob.glob(f"/pool/data/ERA5/E5/sf/an/1H/166/E5sf00_1H_{yyyy}-*.grb")
    u10 = xr.open_mfdataset(u10_files, engine='cfgrib')
    v10 = xr.open_mfdataset(v10_files, engine='cfgrib')

    # Filter the ace2 timestamps for that year
    print(f"Filtering ACE2 timestamps for year {yyyy}...")
    ace2_hours = [0, 6, 12, 18]
    u10_mask = u10.valid_time.dt.hour.isin(ace2_hours).compute()  # Compute the boolean mask to avoid lazy evaluation issues
    v10_mask = v10.valid_time.dt.hour.isin(ace2_hours).compute()  # Compute the boolean mask to avoid lazy evaluation issues
    u10_filtered = u10.where(u10_mask, drop=True)
    v10_filtered = v10.where(v10_mask, drop=True)

    # Compute windspeed for the filtered ACE2 timesteps
    print(f"Computing wind speed for the filtered ACE2 timesteps for year {yyyy}...")
    w = (u10_filtered['u10']**2 + v10_filtered['v10']**2)**0.5

    # Resample to daily max
    print(f"Resampling wind speed to daily max for year {yyyy}...")
    w_daily_max = w.resample(time='1D').max()

    # Rename the variable to 10si_max to be consistent with the naming convention of the other datasets
    w_daily_max = w_daily_max.rename('10si_max')

    # Convert to dataset
    w_daily_max = w_daily_max.to_dataset(name='10si_max')

    # # Save w_daily_max to NetCDF
    # print(f"Saving daily max wind speed to NetCDF for year {yyyy}...")
    # output_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/10si/daily_max_{yyyy}_tmp.nc"
    # w_daily_max.to_netcdf(output_path)
    # print(f"Saved daily max wind speed to {output_path}")

def remap_with_cdo(yyyy):
    from cdo import Cdo
    cdo = Cdo()
    target_grid_file = "/work/gg0304/g260230/GRIDS/era5_grid.txt" # Target grid for remapping
    input_file_sum = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/10si/daily_max_{yyyy}_tmp.nc"
    temp_output_file_sum = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/era5/1D/10si/remapped_daily_max_{yyyy}_tmp.nc" # Temporary output file for remapped data

    print(f"Remapping daily max for year {yyyy} with CDO...")
    cdo.remapnn(
            target_grid_file, 
            input=input_file_sum, 
            output=temp_output_file_sum,
            options='-f nc', # Convert to netCDF
        )
    
    print(f"Replacing original file {input_file_sum} with remapped file {temp_output_file_sum}...")
    os.remove(input_file_sum)
    os.rename(temp_output_file_sum, input_file_sum)

for yyyy in range(1981, 2010 + 1):
    preprocess_wind_speed(yyyy)
    # remap_with_cdo(yyyy)
    break
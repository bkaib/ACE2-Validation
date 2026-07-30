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

#%% Cell
#%% Investigate precipitation units of ERA5 and ACE2

# ERA5 Precipitation and Conversion of Units
era5_prate_files = glob.glob(
        "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/PRATEsfc/daily_sum_*.nc"
        )
era5_prate = xr.open_mfdataset(era5_prate_files, combine="by_coords",)
# era5_prate = era5_prate["prate"] * 1000.0  # Convert from m to mm
# era5_prate.attrs["units"] = "1 mm/d"

# ACE2 Precipitation and conversion of units
ensemble_file = "/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ace2-ensembles/1D/2000v1940/ensemble_0.nc"
ensemble_member = xr.open_dataset(ensemble_file)
ace2_prate = ensemble_member["pr"]  
# ace2_prate = ace2_prate * 21600  # Convert to 1 mm/d

# Print some values of both
era5_prate_values = era5_prate["tp"].isel(time=slice(0, 2)).values
ace2_prate_values = ace2_prate.isel(time=slice(0, 2)).values
print("ERA5 Precipitation values (first 2 days):", era5_prate_values)
print("ACE2 Precipitation values (first 2 days):", ace2_prate_values)

# %% Visualize Absolute Indices
def load_ace2_etccdi(name, scenario, ensemble_number):
    base_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/{scenario}"
    file = os.path.join(base_path, f"{name}_ensemble_{ensemble_number}.nc")
    ds = xr.open_dataset(file)
    return ds

indices_temp = ["TXx", "TNn", "ETR"]
indices_precip = ["Rx1day", "R10", "CWD"]
indices_wind = ["FXx", "WSD",]
indices = indices_temp + indices_precip + indices_wind

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

vmin_vmax_ranges = dict(
    TXx=(250, 320),
    TNn=(200, 320),
    ETR=(0, 20),
    Rx1day=(0, 30),
    R10=(0, 5),
    CWD=(0, 20),
    FXx=(0, 30),
    WSD=(0, 3),
    TN10p = (0, 20),
    TX90p = (0, 20),
    WSDI = (0, 20),
    FG95p = (0, 20),
)

# Plot the indices of ERA5 and ACE2 next to each other. Colum1 ERA5: COlumn2 ACE2. Each row one index.

fig, axes = plt.subplots(nrows=len(etccdi_names), ncols=3, figsize=(15, 12), subplot_kw={'projection': ccrs.EqualEarth()})

# Loop all indices
for i, idx in enumerate(etccdi_names[:2]):
    # Load ERA5
    ds = xr.open_dataset(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/{idx}_1981-2010.nc", decode_times=False)
    ds = ds.sel(time=slice("2001-01-01", "2010-12-31"))
    era5_mean = ds.mean(dim="time")
    print(ds.time.values.dtype)

    # Load ACE2 and compute ensemble mean
    ace2 = xr.concat(
        [load_ace2_etccdi(idx, scenario, ensemble_number=i) for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"] for i in range(12)], dim="ensemble_member"
    )
    ensemble_mean = ace2.mean(dim="ensemble_member").mean(dim="time")

    projection = ccrs.EqualEarth()
    ax = axes[i, 0]
    (era5_mean[idx]
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
    ax.set_title(f"{idx} Index | ERA5")

    # ACE2 Ensemble Mean
    ax = axes[i, 1]
    (ensemble_mean[idx]
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
    ax.set_title(f"{idx} Index | ACE2 Ensemble Mean")

    # Bias (ACE2 - ERA5)
    ax = axes[i, 2]
    bias = ensemble_mean[idx] - era5_mean[idx]
    (bias
     .plot(
         ax=ax, 
         transform=ccrs.PlateCarree(),
         cmap='bwr',
        vmin=-vmin_vmax_ranges[idx][1],
        vmax=vmin_vmax_ranges[idx][1],
         )
     )
    ax.coastlines()
    ax.gridlines()
    ax.set_title(f"{idx} Index | Bias (ACE2 - ERA5)")

fig.suptitle("ETCCDI Indices | Temporal Mean over 2001-2010", fontsize=16)
plt.show()




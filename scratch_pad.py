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
yyyy = "1961"
mm = "07"
dd = "24"
PARAM = "TMP2m"
TRES = "1H"
FAMILY = "E5"
LEVEL = "sf"
TYPE = "an"

path = f"/pool/data/ERA5/{FAMILY}/{LEVEL}/{TYPE}/{TRES}/{constants.era5_params[PARAM]}/E5{LEVEL}00_{TRES}_{yyyy}-{mm}-{dd}_{constants.era5_params[PARAM]}.grb"
data = xr.open_dataset(path, engine='cfgrib')
data



# %%
var = "TMP2m"
yyyy = "2010"
mm = "01"
dd = "01"
path_prefix = constants.era5_params[var]["1H"]
PARAM = constants.era5_params[var]["PARAM"]
filetype = constants.era5_params[var]["filetype"]
d = xr.open_dataset(f"{path_prefix}{yyyy}-{mm}-{dd}_{PARAM}.{filetype}", engine='cfgrib' if filetype == "grb" else None)

print(d)
# Only select data where the coordinate valid_times corresponds to the ACE2 timesteps
ace2_hours = [0, 6, 12, 18]
d_ace2 = d.where(d.valid_time.dt.hour.isin(ace2_hours), drop=True)
d_ace2

# Select the min and max
d_ace2_min = d_ace2.isel(values=[0,1,2]).min(dim="time")
d_ace2_max = d_ace2.isel(values=[0,1,2]).max(dim="time")

print(d_ace2_max)

# Add the current max and min to a dataset that contains the daily min and max as separate variables
date = pd.to_datetime(f"{yyyy}-{mm}-{dd}")
daily_ds = xr.Dataset({
    "daily_min": d_ace2_min["t2m"].expand_dims(time=[date]),
    "daily_max": d_ace2_max["t2m"].expand_dims(time=[date]),
})
daily_ds



# %%
ace2 = xr.open_dataset("data/raw/ace2-ensembles/6H/2000v1940/ensemble_0.nc")
ace2.time.values[:5]

# %%

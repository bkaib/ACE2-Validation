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
d2 = xr.open_dataset("/work/gg0304/g260230/data/ERA5/E5/sf/an/1D/165/E5sf00_1D_2016-01_165.nc")
d2

# %%

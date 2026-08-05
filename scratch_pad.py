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
import xclim.indices as xci
from libraries.own_libraries import xarray_tools as xrt


#%% Load ACE2 data 1940-2022
p = "data/raw/ACE2-ERA5/1D/"
name = "PRATEsfc"
f = f"{name}_day_1941-2022.nc"
file = os.path.join(p,f)
ds = xr.open_dataset(file)
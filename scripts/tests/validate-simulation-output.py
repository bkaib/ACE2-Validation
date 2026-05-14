#%% Load Modules
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
import numpy as np
import xarray as xr
from config import paths
import importlib
importlib.reload(paths)

#%% Load Simulation Data
experiment_id = "2000v1940"
pred = xr.open_dataset(paths.ACE2_RAW + experiment_id +  "/autoregressive_predictions.nc")

#%% Adjust timeperiod to only 2001-2010

#%% Validate the simulation output based on the 1940 version


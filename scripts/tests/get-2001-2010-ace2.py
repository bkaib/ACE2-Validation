#%% Load Modules
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
import os
import logging
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from config import paths
import importlib
importlib.reload(paths)
import dask
from dask.diagnostics import ProgressBar
import time
import zarr
import shutil

# Configure logging
log_dir = os.path.join(paths.PROJECT_ROOT, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "get-2001-2010-ace2.log")
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s',
	handlers=[
		logging.FileHandler(log_file),
		logging.StreamHandler()
	]
)
logger = logging.getLogger(__name__)

# Get Analysis Period
def get_analysis_period(experiment_id, start_date="2001-01-01", end_date="2010-12-31"):
	"""Slices the period 2001-2010 from the ACE2 simulation output."""
	# Load Data of Simulation
	filepath = paths.ACE2_RAW + experiment_id + "/autoregressive_predictions.nc"
	prediction = xr.open_dataset(filepath)
	logger.info(f"Loaded ACE2 simulation output for experiment {experiment_id}: \n {prediction}")

	# Slice the Period 2001-2010
	for n_ensemble in range(prediction.sample.size):
		# Select one ensemble member
		prediction_ens = prediction.isel(sample=n_ensemble)

		# Overwrite time dimension with valid_times
		logging.info(f"Overwriting time dimension with valid_time for ensemble member {n_ensemble}...")
		prediction_ens = prediction_ens.assign_coords(time=prediction_ens.valid_time)

		# Select period
		logging.info(f"Slicing period {start_date} to {end_date} for ensemble member {n_ensemble}...")	
		selected_period = prediction_ens.sel(time=slice(start_date, end_date))

		# Add Attributes 
		logging.info(f"Adding attributes to the selected period for ensemble member {n_ensemble}...")
		## Delete all old attributes
		selected_period.attrs = {}
		## Attribute: Created Date
		selected_period.attrs["created_date"] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
		## Attribute: Experiment ID
		selected_period.attrs["experiment_id"] = experiment_id
		## Attribute: Ensemble Member
		selected_period.attrs["ensemble_member"] = n_ensemble

		# Save the current ensemble member to netcdf
		output_dir = os.path.join(paths.ACE2_RAW, experiment_id)
		os.makedirs(output_dir, exist_ok=True)
		output_file = os.path.join(output_dir, f"ensemble_{n_ensemble}.nc")

		logger.info(f"Saving sliced period 2001-2010 for ensemble member {n_ensemble} to {output_file}...")
		# selected_period.to_netcdf(output_file)
		logger.info(f"{output_file} saved successfully.")

if __name__ == "__main__":
	experiment_id = "2000v1940"
	get_analysis_period(experiment_id)



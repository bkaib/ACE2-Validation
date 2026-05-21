#%% Load Modules
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
import os
import logging
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from config import paths
from config import constants
import importlib
importlib.reload(paths)
from libraries.own_libraries import visualisation as vis

#%% Configure logging
log_dir = os.path.join(paths.PROJECT_ROOT, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "validate-sim-output.log")
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s',
	handlers=[
		logging.FileHandler(log_file),
		logging.StreamHandler()
	]
)
logger = logging.getLogger(__name__)

def check_physical_consistency(experiment_id):
    """Checks the physical consistency of the ACE2 simulation output for the period 2001-2010."""

    # Load ensemble data into one dataset
    #files = glob.glob(os.path.join(paths.ACE2_RAW, experiment_id, "ensemble_*.nc"))
    files = [
          os.path.join(paths.ACE2_RAW, experiment_id, f"ensemble_0.nc"),
          os.path.join(paths.ACE2_RAW, experiment_id, f"ensemble_1.nc"),
    ]
    ensembles = xr.open_mfdataset(files, combine="nested", concat_dim="sample")
    logging.info(f"Loaded ensemble data for experiment {experiment_id}: \n {ensembles}")
    ensembles = ensembles.chunk({'sample': 1, 'time': 365, 'lat': 180, 'lon': 360})

    # Check physical consistency for each variable
    ## 2m Temperature (TMP2m)
    if "TMP2m" in ensembles:
        # Check if temperature values are within a reasonable range (Kelvin)
        temp_min = ensembles["TMP2m"].min().compute().item()
        temp_max = ensembles["TMP2m"].max().compute().item()
        if temp_min < 200 or temp_max > 330:
            logging.warning(f"Temperature values out of range: min={temp_min}, max={temp_max}")
        else:
            logging.info(f"Temperature values are within the expected range: min={temp_min}, max={temp_max}")

    ## Surface Precipitation (PRATEsfc)
    if "PRATEsfc" in ensembles:
        # Check if precipitation values are non-negative
        prate_min = ensembles["PRATEsfc"].min().compute().item()
        if prate_min < 0:
            logging.warning(f"Precipitation values contain negative values: min={prate_min}")
        else:
            logging.info(f"Precipitation values are non-negative: min={prate_min}")

    ## UGRD10m and VGRD10m (10m Wind Components)
    if "UGRD10m" in ensembles and "VGRD10m" in ensembles:
        # Check absolute values of wind components
        ugrd_min = ensembles["UGRD10m"].min().compute().item()
        ugrd_max = ensembles["UGRD10m"].max().compute().item()
        vgrd_min = ensembles["VGRD10m"].min().compute().item()    
        vgrd_max = ensembles["VGRD10m"].max().compute().item()
        if abs(ugrd_min) > 100 or abs(ugrd_max) > 100:
            logging.warning(f"UGRD10m values out of range: min={ugrd_min}, max={ugrd_max}")
        else:
            logging.info(f"UGRD10m values are within the expected range: min={ugrd_min}, max={ugrd_max}")
        if abs(vgrd_min) > 100 or abs(vgrd_max) > 100:
            logging.warning(f"VGRD10m values out of range: min={vgrd_min}, max={vgrd_max}")
        else:
            logging.info(f"VGRD10m values are within the expected range: min={vgrd_min}, max={vgrd_max}")

def temporal_mean(experiment_id, n_ens, variable):
    """Plots the grid-weighted temporal mean field of a given variable for a given ensemble member."""

    # Load Data
    logging.info(f"Loading data for experiment {experiment_id}, ensemble {n_ens}, variable {variable}")
    prediction = xr.open_dataset(
        os.path.join(paths.ACE2_ENSEMBLES, experiment_id, f"ensemble_{n_ens}.nc")
        )
    prediction = prediction.chunk({'time': -1, 'lat': 180, 'lon': 360})
    
    # Compute latitude weights (cosine weighting for grid cells)
    logging.info(f"Computing latitude weights for variable {variable}")
    weights = np.cos(np.deg2rad(prediction[variable].lat))
    
    # Apply grid-weighted temporal mean using xarray's weighted utility
    logging.info(f"Applying grid-weighted temporal mean for variable {variable}")
    mean_field = prediction[variable].weighted(xr.DataArray(weights, dims="lat")).mean(dim="time").compute()

    fig, ax = vis.world_map(
        data=mean_field,
        title=f"""Grid-Weighted Temporal Mean | {variable}
        2001-2010 | Ensemble {n_ens}""",
        cbar_label=constants.ace2_units[variable],
        cmap=constants.colormaps[variable]
    )

    # Save the figure
    fig.tight_layout()
    output_dir = os.path.join(paths.FIGURES, "ace2-sim-validation")
    os.makedirs(output_dir, exist_ok=True)
    fig_path = os.path.join(output_dir, f"{variable}_ensemble_{n_ens}.png")
    fig.savefig(fig_path)
    logging.info(f"Saved figure to {fig_path}")

if __name__ == "__main__":
    experiment_id = "2000v1940"

    # Physical Boundaries
    # check_physical_consistency(experiment_id)

    # Temporal Mean / Spatial Field
    for var in ["TMP2m", "PRATEsfc", "UGRD10m", "VGRD10m"]:
        temporal_mean(experiment_id=experiment_id, n_ens=0, variable=var)

    # Spatial Mean / Timeseries

    ## Ensemble Spread & Mean

    # Climate drift between two distinct periods?
    


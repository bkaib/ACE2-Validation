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
import cartopy.crs as ccrs
importlib.reload(paths)
from libraries.own_libraries import visualisation as vis
from libraries.own_libraries import xarray_tools as xrt
import glob

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

#%% Functions
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

def analyse_temp_mean(
        da: xr.DataArray, 
        n_ens: int,
        lat_dim: str="lat",
        time_dim: str="time",
        ):
    """
    1. Computes grid-weighted temporal mean field
    2. Plots the temporal mean over the whole timeperiod
    3. Plots the monthly mean for all months in one figures
    """
    # 1. Compute grid-weighted temporal mean field
    logging.info(f"Computing grid-weighted temporal mean for variable {da.name}")
    weights = np.cos(np.deg2rad(da[lat_dim]))
    temporal_mean = (
        da.weighted(xr.DataArray(weights, dims=lat_dim))
          .mean(dim=time_dim)
          .compute()
    )

    # 2. Plot the temporal mean over the whole timeperiod
    fig, ax = vis.world_map(
        data=temporal_mean,
        title=f"""Grid-Weighted Temporal Mean | {da.name}
        2001-2010 | Ensemble {n_ens}""",
        cbar_label=constants.ace2_units[str(da.name)],
        cmap=constants.colormaps[str(da.name)]
    )

    ## Save the figure
    fig.tight_layout()
    output_dir = os.path.join(paths.FIGURES, "ace2-sim-validation")
    os.makedirs(output_dir, exist_ok=True)
    fig_path = os.path.join(output_dir, f"temp_mean_{da.name}.png")
    fig.savefig(fig_path)
    logging.info(f"Saved figure to {fig_path}")

    # 3. Plot the monthly mean for all months in one figures

    ## Compute the monthly mean for all months
    logging.info(f"Computing grid-weighted monthly mean for variable {da.name}")
    weighted_data = da * xr.DataArray(weights, dims=lat_dim)
    monthly_mean = (
        weighted_data
        .groupby(f"{time_dim}.month")
        .mean(dim=time_dim)
        .compute()
    )

    ## Plot monthly mean for all months in one figure
    fig, axes = (
        plt.subplots(
            3, 4, 
            figsize=(15, 12), 
            subplot_kw={'projection': ccrs.EqualEarth()}
            )
    )
    axes = axes.flatten()
    im = None
    for month in range(1, 13):
        ax = axes[month-1]
        monthly_data = monthly_mean.sel(month=month)
        im = (
            ax.contourf(
                monthly_data.lon, 
                monthly_data.lat, 
                monthly_data, 
                cmap=constants.colormaps[str(da.name)], 
                transform=ccrs.PlateCarree(),
                )
        )

        ## Add coastlines and gridlines
        ax.coastlines()
        ax.gridlines(draw_labels=True)  
        ax.set_title(f"Month: {month}")

    ## Add shared colorbar
    cbar_ax = fig.add_axes([0.2, 0.08, 0.6, 0.02])
    plt.colorbar(im, cax=cbar_ax, label=constants.ace2_units[str(da.name)], orientation="horizontal")
    fig.suptitle(f"Monthly Mean {da.name} (2001-2010) | Ensemble {n_ens}", fontsize=16)

    ## Save figure to figures/tmp
    fig.tight_layout()
    output_path = f"results/figures/ace2-sim-validation/monthly_mean_{str(da.name)}.png"
    fig.savefig(output_path, dpi=300)
    logging.info(f"Saved figure to {output_path}")


#%% Main Execution
if __name__ == "__main__":
    # Constants
    experiment_id = "2000v1940"
    n_ens = 0

    # Physical Boundaries
    # check_physical_consistency(experiment_id)

    # Temporal Mean / Spatial Field

    ## Load Data of one ensemble member
    p = (
        os.path.join(
            paths.ACE2_ENSEMBLES, 
            experiment_id, 
            f"ensemble_{n_ens}.nc",
            )
    )
    ensemble_files = (
        glob.glob(
            os.path.join(
                paths.ACE2_ENSEMBLES, 
                experiment_id, 
                f"ensemble_*.nc",
                )
        )
    )
    logging.info(f"Loading ensemble members of experiment {experiment_id}: {ensemble_files}")
    # ensemble_member = xr.open_dataset(p)
    # ensemble_member = ensemble_member.chunk({'time': -1, 'lat': -1, 'lon': -1})
    ensembles = xr.open_mfdataset(ensemble_files, combine="nested", concat_dim="sample")
    ensembles = ensembles.chunk({'sample': 1, 'time': 365*4, 'lat': -1, 'lon': -1})
    logging.info(f"Dataset: {ensembles}")
    logging.info(f"Compute mean over all ensemble members...")
    ensemble_mean = ensembles.mean(dim="sample").compute()

    ## Analyse the temporal mean
    for var in ensemble_mean.data_vars:
        analyse_temp_mean(ensemble_mean[var], n_ens)

    # Spatial Mean / Timeseries

    ## Ensemble Spread & Mean

    # Climate drift between two distinct periods?
    


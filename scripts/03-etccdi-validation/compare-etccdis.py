#%% Modules
import os
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
from config import constants
from config.project_logging import setup_parallel_logger
from dask import delayed, compute, config as dask_config
import xarray as xr
import xclim.indices as xci
import xclim as xc
import glob
import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
import cartopy.crs as ccrs

import importlib
importlib.reload(constants)

#%% Setup Logger
current_filename = __file__.split("/")[-1].replace(".py", "")
logger, queue_listener = setup_parallel_logger(current_filename, use_queue_listener=True)

#%% Global Constants
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
#%% Functions
def load_era5_etccdi(name, timeperiod="1981-2010"):
    base_path = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5"
    file = os.path.join(base_path, f"{name}_1981-2010.nc")
    ds = xr.open_dataset(file)

    # Slice timeperiod
    ds = ds.sel(time=slice(f"{timeperiod.split('-')[0]}-01-01", f"{timeperiod.split('-')[1]}-12-31"))
    return ds

def load_ace2_etccdi(name, scenario, ensemble_number):
    base_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/{scenario}"
    file = os.path.join(base_path, f"{name}_ensemble_{ensemble_number}_converted.nc")
    ds = xr.open_dataset(file)
    return ds

def ace2_ensemble_mean(name):
    """Computes ensemble mean for one ETCCDI index denoted by the `name` argument across all scenarios and ensemble members."""
    # Load index data across all ensemble members and scenarios
    all_scenarios_ds = []
    for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]:
        _members_ds = xr.concat(
            [load_ace2_etccdi(name, scenario, ensemble_number=i) for i in range(0, 12)], dim="ensemble_member"
            )
        all_scenarios_ds.append(_members_ds)
    all_scenarios_ds = xr.concat(all_scenarios_ds, dim="scenario")

    # Compute mean across ensemble members
    ensemble_mean = all_scenarios_ds.mean(dim=["ensemble_member", "scenario"])

    # Save the mean to a new netcdf file 
    ensemble_mean.to_netcdf(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/ensemble_mean/{name}_ensemble_mean.nc")

def aggregate_index_over_domain(ds, lat_weights=True):
    """
    """
    # Optional: weight by latitude to account for grid cell area
    if lat_weights:
        weights = np.cos(np.deg2rad(ds.lat))
        weighted_ds = ds.weighted(xr.DataArray(weights, coords=[ds.lat], dims=['lat']))
        return weighted_ds.mean(dim=['lat', 'lon'])
    else:
        return ds.mean(dim=['lat', 'lon'])

def temporal_comparison(
        name: str,
        domain_name:str,
):
    """Compares the temporal evolution of an ETCCDI index between ERA5, 
    ACE2 ensemble mean and the spread across the 48 ensembles for a specified domain.
    The script does this:
    1. Load ERA5 data for the specified ETCCDI index.
    2. Load ACE2 ensemble mean data for the same index.
    3. Load ACE2 ensemble data for the same index.
    4. Select the domain of interest in all datasets.
    5. Aggregate the index over this domain (e.g., mean, sum, etc.).
    6. Save the timeserie data as .nc
    """
    # 1. Load ERA5 data
    name = "TX90p"
    era5_ds = load_era5_etccdi(name="TX90p")
    era5_ds = era5_ds.sel(time=slice("2001-01-01", "2010-12-31"))  # Ensure the time range matches ACE2 data

    # 2. Load ACE2 ensemble mean data
    ace2_ensemble_mean_ds = xr.open_dataset(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/ensemble_mean/{name}_ensemble_mean.nc")

    # 3. Load ACE2 ensemble data
    ace2_ensemble_ds = xr.concat(
        [load_ace2_etccdi(name, scenario, ensemble_number=i) for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"] for i in range(12)], dim="ensemble_member"
    )

    # 4. Select the domain of interest in all datasets
    domain_name = "Europe"
    domain = constants.domains[domain_name] # dictionary with keys e.g.: "lon": (-30, 40), "lat": (30, 75)
    era5_ds_domain = era5_ds.sel(lat=slice(domain["lat"][0], domain["lat"][1]), lon=slice(domain["lon"][0], domain["lon"][1]))
    ace2_ensemble_mean_ds_domain = ace2_ensemble_mean_ds.sel(lat=slice(domain["lat"][0], domain["lat"][1]), lon=slice(domain["lon"][0], domain["lon"][1]))
    ace2_ensemble_ds_domain = ace2_ensemble_ds.sel(lat=slice(domain["lat"][0], domain["lat"][1]), lon=slice(domain["lon"][0], domain["lon"][1]))

    # Plot the domain data of ERA5 for a quick check. Plot on equal earth projection with coastlines.
    import cartopy.crs as ccrs
    fig, ax = plt.subplots(figsize=(10, 6), subplot_kw={'projection': ccrs.EqualEarth()})
    data = era5_ds_domain[name.lower()].mean(dim="time")
    # Plot data on world map
    data.plot(ax=ax, transform=ccrs.PlateCarree(), cmap="coolwarm", cbar_kwargs={'label': f"{name} (ERA5)"})
    ax.coastlines()
    ax.gridlines(draw_labels=True)





    # 5. Aggregate the index over this domain via spatial mean
    era5_aggregated = aggregate_index_over_domain(era5_ds_domain, lat_weights=True)
    ace2_ensemble_mean_aggregated = aggregate_index_over_domain(ace2_ensemble_mean_ds_domain, lat_weights=True)
    ace2_ensemble_aggregated = aggregate_index_over_domain(ace2_ensemble_ds_domain, lat_weights=True)

    # 6. Save the timeserie data as .nc
    era5_folder = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/spatial_aggregation/{domain_name}/"
    ace2_folder = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/spatial_aggregation/{domain_name}/"

    ## Create folder if not existant
    os.makedirs(era5_folder, exist_ok=True)
    os.makedirs(ace2_folder, exist_ok=True)

    ## Save ERA5 aggregated data
    era5_aggregated.to_netcdf(os.path.join(era5_folder, f"{name}.nc"))
    ace2_ensemble_mean_aggregated.to_netcdf(os.path.join(ace2_folder, f"{name}_ensemble_mean.nc"))
    ace2_ensemble_aggregated.to_netcdf(os.path.join(ace2_folder, f"{name}_ensemble.nc"))

#%% Wrapper
def compute_ace2_ensemble_mean():
    """Computes ensemble mean of ACE2 simulations for all ETCCDI indices in parallel using Dask."""
    delayed_tasks = [delayed(ace2_ensemble_mean)(name) for name in etccdi_names]
    compute(*delayed_tasks, scheduler="processes", num_workers=4)
    logger.info(f"Completed processing all {len(etccdi_names)} indices")

#%% Main
def main():
    # Compute Ensemble Mean for all ETCCDI indices in parallel
    compute_ace2_ensemble_mean()


if __name__ == "__main__":
    main()


def plot_spatial_bias():#TODO
    name = "R10"
    ensemble_mean = xr.open_dataset(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/ensemble_mean/{name}_ensemble_mean.nc")
    var = list(ensemble_mean.data_vars.keys())[0]
    data = ensemble_mean[var].mean(dim="time")
    fig, ax = plt.subplots(figsize=(10, 6), subplot_kw={'projection': ccrs.EqualEarth()})
    # Plot data on world map
    data.plot(ax=ax, transform=ccrs.PlateCarree(), cmap="coolwarm", cbar_kwargs={'label': f"{name} (ACE2 Ensemble Mean)"})
    ax.coastlines()
    ax.gridlines(draw_labels=True)


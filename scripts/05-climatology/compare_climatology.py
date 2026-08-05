#%% Modules
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
from config import constants
from config.project_logging import setup_parallel_logger
import xarray as xr
import glob
import numpy as np
from matplotlib import pyplot as plt
import os
import cartopy.crs as ccrs

import importlib
importlib.reload(constants)

#%% Setup Logger
current_filename = __file__.split("/")[-1].replace(".py", "")
logger, queue_listener = setup_parallel_logger(current_filename, use_queue_listener=True)

#%% Functions

#---
# ERA5 Loading
#---
def load_era5_sfcWindmax(start_year, end_year, months=None):
    """
    Load ERA5 data for the sfcWindmax variable and time range.
    """
    files = glob.glob(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/10si/daily_max_*.nc")
    files.sort()
    ds = xr.open_mfdataset(files, combine="by_coords").sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
    if months is not None:
        ds = ds.sel(time=ds['time.month'].isin(months))

    return ds

def load_era5_sfcWindmean(start_year, end_year, months=None):
    """
    Load ERA5 data for the sfcWindmean variable and time range.
    """
    files = glob.glob(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/10si/daily_mean_*.nc")
    files.sort()
    ds = xr.open_mfdataset(files, combine="by_coords").sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
    if months is not None:
        ds = ds.sel(time=ds['time.month'].isin(months))

    return ds

def load_era5_prate(start_year, end_year, months=None):
    """
    Load ERA5 data for the prate variable and time range.
    """
    files = glob.glob(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/PRATEsfc/daily_sum_*.nc")
    files.sort()
    ds = xr.open_mfdataset(files, combine="by_coords").sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
    if months is not None:
        ds = ds.sel(time=ds['time.month'].isin(months))
    ds = ds * 1000  # Convert from m to mm

    return ds

def load_era5_tasmax(start_year, end_year, months=None):
    """
    Load ERA5 data for the tasmax variable and time range.
    """
    files = glob.glob(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/TMP2m/daily_max_*.nc")
    files.sort()
    ds = xr.open_mfdataset(files, combine="by_coords").sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
    if months is not None:
        ds = ds.sel(time=ds['time.month'].isin(months))

    return ds

def load_era5_tasmin(start_year, end_year, months=None):
    """
    Load ERA5 data for the tasmin variable and time range.
    """
    files = glob.glob(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/TMP2m/daily_min_*.nc")
    files.sort()
    ds = xr.open_mfdataset(files, combine="by_coords").sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
    if months is not None:
        ds = ds.sel(time=ds['time.month'].isin(months))

    return ds


#---
# ACE2 Loading
#---
def load_ace2_ensemble_member(var_name, scenario, ensemble_number, months=None):
    """Load a single ACE2 ensemble member."""
    base_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ace2-ensembles/1D/{scenario}"
    file = os.path.join(base_path, f"ensemble_{ensemble_number}.nc")
    ds = xr.open_dataset(file)
    if months is not None:
        ds = ds.sel(time=ds['time.month'].isin(months))
    da = ds[var_name]
    ds = da.to_dataset(name=var_name)
    return ds

def load_ace2_ensemble(var_name, n_members=12, months=None):
    """Loads all ensemble members of the ensemble into one dataset"""
    all_scenarios_ds = []
    for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]:
        _members_ds = xr.concat(
            [load_ace2_ensemble_member(var_name, scenario, ensemble_number=i, months=months) for i in range(0, n_members)], dim="ensemble_member"
            )
        all_scenarios_ds.append(_members_ds)
    all_scenarios_ds = xr.concat(all_scenarios_ds, dim="scenario")

    return all_scenarios_ds

def load_ace2_ensemble_mean(var_name, months=None):

    path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ace2-ensembles/1D/ensemble_mean/{var_name}_ensemble_mean.nc"
    ds = xr.open_dataset(path)
    if months is not None:
        ds = ds.sel(time=ds['time.month'].isin(months))
    if var_name == "pr":
        ds[var_name] = ds[var_name] * 21600  # Convert from m to mm

    return ds

#---
# Compare Climatology between ERA5 and ACE2
#---

def compute_climatology(var_name, start_year, end_year, months=None):
    """Compare climatology between ERA5 and ACE2 ensemble members."""
    # Load ERA5 data
    if var_name == "sfcWind_max":
        era5_data = load_era5_sfcWindmax(start_year, end_year, months=months)
    elif var_name == "sfcWind_mean":
        era5_data = load_era5_sfcWindmean(start_year, end_year, months=months)
    elif var_name == "pr":
        era5_data = load_era5_prate(start_year, end_year, months=months)
    elif var_name == "tasmax":
        era5_data = load_era5_tasmax(start_year, end_year, months=months)
    elif var_name == "tasmin":
        era5_data = load_era5_tasmin(start_year, end_year, months=months)
    else:
        raise ValueError(f"Variable {var_name} not recognized.")

    # Load ACE2 ensemble data
    try:
        ace2_ensemble_mean = load_ace2_ensemble_mean(var_name, months=months)
    except FileNotFoundError:
        logger.error(f"ACE2 ensemble data for variable {var_name} not found.")
        raise

    # Compute climatology (mean over time)
    era5_climatology = era5_data.mean(dim="time")
    ace2_climatology = ace2_ensemble_mean.mean(dim="time")

    return era5_climatology, ace2_climatology

def plot_climatology_comparison(era5_climatology, ace2_climatology, bias, var_name, output_dir, is_saved=True):
    """Plot climatology comparison between ERA5 and ACE2."""
    colormaps = {
        "tasmin": "coolwarm",
        "tasmax": "coolwarm",
        "pr": "Blues",
        "sfcWind_max": "viridis",
        "sfcWind_mean": "viridis",
    }
    bias_cmap = {
        "tasmin": "RdBu_r",
        "tasmax": "RdBu_r",
        "pr": "RdBu_r",
        "sfcWind_max": "RdBu_r",
        "sfcWind_mean": "RdBu_r",
    }
    units = {
        "tasmin": "K",
        "tasmax": "K",
        "pr": "mm/day",
        "sfcWind_max": "m/s",
        "sfcWind_mean": "m/s",
    }
    vmin_vmax_range = {
        "tasmin": (230, 300),
        "tasmax": (230, 300),
        "pr": (0, 30),
        "sfcWind_max": (0, 20),
        "sfcWind_mean": (0, 20),
    }
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), subplot_kw={'projection': ccrs.EqualEarth()})
    era5_var = list(era5_climatology.data_vars)[0]
    ace2_var = list(ace2_climatology.data_vars)[0]

    era5_climatology[era5_var].plot(
        ax=axes[0], 
        cmap=colormaps[var_name], 
        transform=ccrs.PlateCarree(), 
        cbar_kwargs={'label': f"ERA5 Climatology ({units[var_name]})"},
        vmin=vmin_vmax_range[var_name][0],
        vmax=vmin_vmax_range[var_name][1],
    )
    axes[0].set_title(f"ERA5 Climatology of {var_name}")
    axes[0].coastlines()
    axes[0].gridlines(draw_labels=True)
    
    ace2_climatology[ace2_var].plot(
        ax=axes[1], 
        cmap=colormaps[var_name], 
        transform=ccrs.PlateCarree(), 
        cbar_kwargs={'label': f"ACE2 Climatology ({units[var_name]})"},
        vmin=vmin_vmax_range[var_name][0],
        vmax=vmin_vmax_range[var_name][1],
    )
    axes[1].set_title(f"ACE2 Climatology of {var_name}")
    axes[1].coastlines()
    axes[1].gridlines(draw_labels=True)

    vmin = min(np.nanmin(bias), -np.nanmax(bias))
    vmax = max(np.nanmax(bias), -np.nanmin(bias))
    bias.plot(
        ax=axes[2], cmap=bias_cmap[var_name], 
        vmin=vmin, vmax=vmax, 
        transform=ccrs.PlateCarree(), 
        cbar_kwargs={'label': f"Bias ({units[var_name]})"}
    )
    axes[2].set_title(f"Bias (ACE2 - ERA5) of {var_name}")
    axes[2].coastlines()
    axes[2].gridlines(draw_labels=True)
    
    plt.tight_layout()
    if is_saved:
        plt.savefig(os.path.join(output_dir, f"{var_name}_climatology_comparison.png"))

    # Return both figure and data for later use
    return fig, {
        'era5_data': era5_climatology[era5_var],
        'ace2_data': ace2_climatology[ace2_var],
        'bias_data': bias,
        'var_name': var_name,
        'colormaps': colormaps,
        'bias_cmap': bias_cmap,
        'units': units,
        'vmin_vmax_range': vmin_vmax_range,
    }

def all_var_clim_comparison(all_figs_with_data, output_dir, is_saved=True):
    """Plot all figures into one combined plot using stored data."""
    fig, axes = plt.subplots(len(all_figs_with_data), 3, figsize=(18, 6 * len(all_figs_with_data)), 
                            subplot_kw={'projection': ccrs.EqualEarth()})

    for i, (source_fig, data_dict) in enumerate(all_figs_with_data):
        var_name = data_dict['var_name']
        
        # Plot ERA5
        data_dict['era5_data'].plot(
            ax=axes[i, 0],
            cmap=data_dict['colormaps'][var_name],
            transform=ccrs.PlateCarree(),
            cbar_kwargs={'label': f"ERA5 Climatology ({data_dict['units'][var_name]})"},
            vmin=data_dict['vmin_vmax_range'][var_name][0],
            vmax=data_dict['vmin_vmax_range'][var_name][1],
        )
        axes[i, 0].set_title(f"ERA5 Climatology of {var_name}")
        axes[i, 0].coastlines()
        axes[i, 0].gridlines(draw_labels=True)
        
        # Plot ACE2
        data_dict['ace2_data'].plot(
            ax=axes[i, 1],
            cmap=data_dict['colormaps'][var_name],
            transform=ccrs.PlateCarree(),
            cbar_kwargs={'label': f"ACE2 Climatology ({data_dict['units'][var_name]})"},
            vmin=data_dict['vmin_vmax_range'][var_name][0],
            vmax=data_dict['vmin_vmax_range'][var_name][1],
        )
        axes[i, 1].set_title(f"ACE2 Climatology of {var_name}")
        axes[i, 1].coastlines()
        axes[i, 1].gridlines(draw_labels=True)
        
        # Plot Bias
        vmin = min(np.nanmin(data_dict['bias_data']), -np.nanmax(data_dict['bias_data']))
        vmax = max(np.nanmax(data_dict['bias_data']), -np.nanmin(data_dict['bias_data']))
        data_dict['bias_data'].plot(
            ax=axes[i, 2],
            cmap=data_dict['bias_cmap'][var_name],
            vmin=vmin, vmax=vmax,
            transform=ccrs.PlateCarree(),
            cbar_kwargs={'label': f"Bias ({data_dict['units'][var_name]})"}
        )
        axes[i, 2].set_title(f"Bias (ACE2 - ERA5) of {var_name}")
        axes[i, 2].coastlines()
        axes[i, 2].gridlines(draw_labels=True)

    plt.tight_layout()
    if is_saved:
        plt.savefig(os.path.join(output_dir, "all_var_climatology_comparison.png"))
#%% Main

def main():
    var_names = ["pr", "tasmax", "tasmin", "sfcWind_max", "sfcWind_mean"]
    output_dir = "/work/gg0304/g260230/projects/ACE2-Validation/results/figures/05-climatology"
    start_year = 2001
    end_year = 2010
    all_figs_with_data = []  # Changed name

    logger.info("Starting climatology comparison between ERA5 and ACE2 ensemble members...")
    for var_name in var_names:
        logger.info(f"Processing variable: {var_name}")
        era5_climatology, ace2_climatology = compute_climatology(
            var_name=var_name, 
            start_year=start_year, end_year=end_year,
        )
        era5_data_var = list(era5_climatology.data_vars)[0]
        ace2_data_var = list(ace2_climatology.data_vars)[0]
        bias = ace2_climatology[ace2_data_var] - era5_climatology[era5_data_var]
        os.makedirs(output_dir, exist_ok=True)
        
        fig, data_dict = plot_climatology_comparison(  # Now returns both
            era5_climatology, ace2_climatology, bias, 
            var_name=var_name, 
            output_dir=output_dir,
            is_saved=True,
        )
        all_figs_with_data.append((fig, data_dict))

    logger.info("Plotting all variable climatology comparisons in one figure...")
    all_var_clim_comparison(all_figs_with_data, output_dir)
        
#%% Run
if __name__ == "__main__":
    main()
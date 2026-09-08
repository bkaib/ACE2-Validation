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

#%% Constants

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
    file = os.path.join(base_path, f"{name}_ensemble_{ensemble_number}.nc")
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

def temporal_comparison( #TODO
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

def plot_spatial_comparison():
    # Constants
    cbar_range = {
        # Temperature Indices
        "ETR": (0, 80),
        "TXx": (260, 310), # Kelvin
        "TNn": (230, 290), # Kelvin
        "TX90p": (40, 52),
        "TN10p": (40, 52),
        "WSDI": (0, 30),
        # Precipitation Indices
        "Rx1day": (0, 100), # TODO: Huge difference in quantity between ACE2 and ERA5
        "R10": (0, 30),
        "CWD": (0, 50), # TODO: Looks weird for ACE2
        # Wind indices
        "FXx": (0, 30),
        "FG95p": (20, 30),
        "WSD": (0, 5), # TODO: Quantitiave difernce ACE2
    }
    cbar_range_bias = {
        "ETR": (-8, 8),
        "TXx": (-8, 8),
        "TNn": (-8, 8),
        "TX90p": (-5, 5),
        "TN10p": (-8, 8),
        "WSDI": (-10, 10),
        "Rx1day": (-20, 20),    
        "R10": (-200, 200),
        "CWD": (-15, 15),
        "FXx": (-5, 5),
        "FG95p": (-5, 5),
        "WSD": (-4, 4),
    }

    figs = []
    for climate_var in constants.etccdi_indices.keys():
        indices = constants.etccdi_indices[climate_var]
        if "ETR" in indices:
            indices.remove("ETR")  # Remove ETR from the list of indices to plot, as it is not relevant for this comparison

        fig, axes = plt.subplots(
            nrows=len(indices), ncols=3,
            figsize=(21, 3.5 * len(indices)), 
            subplot_kw={'projection': ccrs.EqualEarth()},
            layout="constrained",
            )
        plt.subplots_adjust(hspace=0.35, wspace=0.3)

        for i, idx in enumerate(indices):
            # Load data and compute bias
            era5_ds = load_era5_etccdi(idx, timeperiod="2001-2010")
            ace2_ensemble_mean = xr.open_dataset(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/ensemble_mean/{idx}_ensemble_mean.nc")
            
            era5_var = list(era5_ds.data_vars.keys())[0]
            ace2_var = list(ace2_ensemble_mean.data_vars.keys())[0]

            # Compute mean over 2001-2010 and hte bias
            era5_temporal_mean = era5_ds[era5_var].mean(dim="time")
            ace2_temporal_mean = ace2_ensemble_mean[ace2_var].mean(dim="time")
            bias = ace2_temporal_mean - era5_temporal_mean

            # Plotting
            cmap = constants.etccdi_cmaps.get(idx, "coolwarm")
            cmap_bias = "RdBu_r"
            unit = constants.etccdi_units.get(idx, "")
            
            vmin_data, vmax_data = cbar_range.get(idx, (None, None))
            vmin_bias, vmax_bias = cbar_range_bias.get(idx, (None, None))
            
            # ERA5
            cbar_pad = 0.08
            era5_temporal_mean.plot(
                ax=axes[i, 0], transform=ccrs.PlateCarree(), 
                cmap=cmap, 
                cbar_kwargs={'label': f"{idx} ({unit})", "pad":cbar_pad},
                vmin=vmin_data, vmax=vmax_data,
            )
            axes[i, 0].coastlines()
            axes[i, 0].gridlines(draw_labels=True)
            axes[i, 0].set_title(f"ERA5 - {idx}")
            
            # ACE2 Ensemble Mean
            ace2_temporal_mean.plot(
                ax=axes[i, 1], transform=ccrs.PlateCarree(), 
                cmap=cmap, 
                cbar_kwargs={'label': f"{idx} ({unit})", "pad":cbar_pad},
                vmin=vmin_data, vmax=vmax_data,
            )
            axes[i, 1].coastlines()
            axes[i, 1].gridlines(draw_labels=True)
            axes[i, 1].set_title(f"ACE2 Ensemble Mean - {idx}")

            # Bias
            bias.plot(
                ax=axes[i, 2], transform=ccrs.PlateCarree(), 
                cmap=cmap_bias, 
                cbar_kwargs={'label': f"Bias ({unit})", "pad":cbar_pad},
                vmin=vmin_bias, vmax=vmax_bias,
            )
            axes[i, 2].coastlines()
            axes[i, 2].gridlines(draw_labels=True)
            axes[i, 2].set_title(f"Bias (ACE2 - ERA5) - {idx}")
        # fig.suptitle(f"Comparison of ERA5 and ACE2 Ensemble Mean for {climate_var.capitalize()} Indices", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        figs.append(fig)
    return figs

def plot_spatial_comparison_v01():
    # Constants
    cbar_range = {
        # Temperature Indices
        "ETR": (0, 80),
        "TXx": (260, 310), # Kelvin
        "TNn": (230, 290), # Kelvin
        "TX90p": (40, 52),
        "TN10p": (40, 52),
        "WSDI": (0, 30),
        # Precipitation Indices
        "Rx1day": (0, 100), 
        "R10": (0, 30),
        "CWD": (0, 50), 
        # Wind indices
        "FXx": (0, 30),
        "FG95p": (20, 30),
        "WSD": (0, 5), 
    }
    cbar_range_bias = {
        "ETR": (-8, 8),
        "TXx": (-8, 8),
        "TNn": (-8, 8),
        "TX90p": (-5, 5),
        "TN10p": (-8, 8),
        "WSDI": (-10, 10),
        "Rx1day": (-20, 20),    
        "R10": (-200, 200),
        "CWD": (-15, 15),
        "FXx": (-5, 5),
        "FG95p": (-5, 5),
        "WSD": (-4, 4),
    }
    levels = 20
    figs = []
    for j, climate_var in enumerate(constants.etccdi_indices.keys()):
        indices = constants.etccdi_indices[climate_var]
        if "ETR" in indices:
            indices.remove("ETR")  

        # 1D-Axes Absicherung, falls len(indices) == 1
        n_rows = len(indices)
        fig, axes = plt.subplots(
            nrows=n_rows, ncols=3,
            figsize=(21, 3.8 * n_rows), 
            subplot_kw={'projection': ccrs.EqualEarth()},
        )
        
        # Sicherstellen, dass axes immer 2D ist (n_rows, 3)
        if n_rows == 1:
            axes = np.expand_dims(axes, axis=0)

        for i, idx in enumerate(indices):
            # Load data and compute bias
            era5_ds = load_era5_etccdi(idx, timeperiod="2001-2010")
            ace2_ensemble_mean = xr.open_dataset(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/ensemble_mean/{idx}_ensemble_mean.nc")
            
            era5_var = list(era5_ds.data_vars.keys())[0]
            ace2_var = list(ace2_ensemble_mean.data_vars.keys())[0]

            era5_temporal_mean = era5_ds[era5_var].mean(dim="time")
            ace2_temporal_mean = ace2_ensemble_mean[ace2_var].mean(dim="time")
            bias = ace2_temporal_mean - era5_temporal_mean

            cmap = constants.etccdi_cmaps.get(idx, "coolwarm")
            cmap_bias = "RdBu_r"
            unit = constants.etccdi_units.get(idx, "")
            
            vmin_data, vmax_data = cbar_range.get(idx, (None, None))
            vmin_bias, vmax_bias = cbar_range_bias.get(idx, (None, None))
            
            # --- 1. ERA5 (Spalte 0) ---
            im_shared = era5_temporal_mean.plot(
                ax=axes[i, 0], transform=ccrs.PlateCarree(), 
                # levels=levels,
                cmap=cmap, add_colorbar=False,
                vmin=vmin_data, vmax=vmax_data,
                add_labels=False,
            )
            axes[i, 0].coastlines()
            axes[i, 0].gridlines(draw_labels=True)
            # axes[i, 0].set_title(f"ERA5 - {idx}")
            axes[i, 0].text(-0.15, 0.5, f"{idx}", transform=axes[i, 0].transAxes, 
                            fontsize=20, va='center', ha='right', rotation='horizontal')
            
            # --- 2. ACE2 Ensemble Mean (Spalte 1) ---
            ace2_temporal_mean.plot(
                ax=axes[i, 1], transform=ccrs.PlateCarree(), 
                # levels=levels,
                cmap=cmap, add_colorbar=False,
                vmin=vmin_data, vmax=vmax_data,
                add_labels=False,
            )
            axes[i, 1].coastlines()
            axes[i, 1].gridlines(draw_labels=True)
            # axes[i, 1].set_title(f"ACE2 Ensemble Mean - {idx}")

            # GEMEINSAME COLORBAR FÜR SPALTE 0 & 1 (Rechts neben Spalte 1)
            pos1 = axes[i, 1].get_position()
            # [left, bottom, width, height]
            cax_shared = fig.add_axes([pos1.x1 - 0.015, pos1.y0, 0.012, pos1.height])
            fig.colorbar(im_shared, cax=cax_shared, label=f"{unit}",)

            # --- 3. Bias (Spalte 2) ---
            im_bias = bias.plot(
                ax=axes[i, 2], transform=ccrs.PlateCarree(), 
                cmap=cmap_bias, add_colorbar=False,
                vmin=vmin_bias, vmax=vmax_bias,
            )
            axes[i, 2].coastlines()
            axes[i, 2].gridlines(draw_labels=True)
            axes[i, 2].set_title(f"Bias (ACE2 - ERA5) - {idx}")

            # SEPARATE COLORBAR FÜR BIAS (Rechts neben Spalte 2)
            pos2 = axes[i, 2].get_position()
            cax_bias = fig.add_axes([pos2.x1 + 0.008, pos2.y0, 0.012, pos2.height])
            fig.colorbar(im_bias, cax=cax_bias, label=f"{unit}",)
            # if i > 0:  # Limit to first 7 indices for demonstration
            #     break  

        # 1. Titel setzen (mit etwas Abstand pad=12 nach unten)
        axes[0, 0].set_title("ERA5", fontsize=20, pad=12)
        axes[0, 1].set_title("ACE2 Ensemble Mean", fontsize=20, pad=12)
        axes[0, 2].set_title("Bias (ACE2 - ERA5)", fontsize=20, pad=12)

        # 2. Manuelles Layout anwenden (KEIN plt.tight_layout() danach!)
        plt.subplots_adjust(left=0.08, right=0.88, wspace=0.35, hspace=0.25)

        # 3. Speichern (bbox_inches='tight' sorgt dafür, dass nichts abgeschnitten wird)
        fig.savefig(
            f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/03-etccdi-validation/spatial_comparison_{j}.png", 
            dpi=300, 
            bbox_inches="tight"
        )
        plt.close(fig)  # Speicher freigeben
#%% Wrapper
def compute_ace2_ensemble_mean():
    """Computes ensemble mean of ACE2 simulations for all ETCCDI indices in parallel using Dask."""
    etccdi_names = ["CWD"]
    delayed_tasks = [delayed(ace2_ensemble_mean)(name) for name in etccdi_names]
    compute(*delayed_tasks, scheduler="processes", num_workers=4)
    logger.info(f"Completed processing all {len(etccdi_names)} indices")

#%% Main
def main():
    # Compute Ensemble Mean for all ETCCDI indices in parallel
    # compute_ace2_ensemble_mean()

    # # Spatial Comparison of ERA5, ACE2 and Bias
    figs = plot_spatial_comparison_v01()
    for i, fig in enumerate(figs):
        fig.savefig(f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/03-etccdi-validation/spatial_comparison_{i}.png", dpi=300)
        plt.close(fig)


if __name__ == "__main__":
    main()


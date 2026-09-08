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

def aggregate_index_over_domain(ds, use_lat_weights=True):
    """
    Aggregate an ETCCDI index over a spatial domain.
    
    For precipitation indices (Rx1day, R10, CWD), compute area-weighted sum.
    For other indices, compute area-weighted mean.
    
    Parameters
    ----------
    ds : xr.Dataset
        Dataset containing the ETCCDI index
    index_name : str
        Name of the ETCCDI index (e.g., 'TXx', 'Rx1day')
    use_lat_weights : bool
        Whether to weight by latitude (cosine) for area correction
    
    Returns
    -------
    xr.Dataset
        Spatially aggregated dataset with only time dimension
    """
    if use_lat_weights:
        weights = np.cos(np.deg2rad(ds.lat))
        weighted_ds = ds.weighted(xr.DataArray(weights, coords=[ds.lat], dims=['lat']))
        return weighted_ds.mean(dim=['lat', 'lon'])
    else:
        return ds.mean(dim=['lat', 'lon'])

def load_all_ace2_ensembles(name):
    """
    Load all 48 ACE2 ensemble members for a given ETCCDI index.
    
    Parameters
    ----------
    name : str
        ETCCDI index name (e.g., 'TXx', 'Rx1day')
    
    Returns
    -------
    xr.Dataset
        Dataset with ensemble_member dimension (48 members total)
    """
    all_ensembles = []
    for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]:
        for i in range(12):
            try:
                ds = load_ace2_etccdi(name, scenario, ensemble_number=i)
                all_ensembles.append(ds)
            except FileNotFoundError:
                logger.warning(f"Could not find {name} for scenario {scenario}, ensemble {i}")
    
    # Concatenate all ensembles
    ace2_all = xr.concat(all_ensembles, dim="ensemble_member")
    return ace2_all

def compute_temporal_aggregation(name, domain_name=None):
    """
    Compute spatial aggregation of an ETCCDI index over a domain and save time series.
    
    Parameters
    ----------
    name : str
        ETCCDI index name
    domain_name : str or None
        Domain name from constants.domains, or None for global
    
    Returns
    -------
    tuple
        (era5_timeseries, ace2_mean_timeseries, ace2_all_timeseries)
    """
    logger.info(f"Processing {name} for domain: {domain_name if domain_name else 'Global'}")
    
    # 1. Load ERA5 data
    era5_ds = load_era5_etccdi(name, timeperiod="2001-2010")
    
    # 2. Load ACE2 ensemble mean
    ace2_mean_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/ensemble_mean/{name}_ensemble_mean.nc"
    if not os.path.exists(ace2_mean_path):
        logger.warning(f"Ensemble mean not found for {name}, computing it...")
        ace2_ensemble_mean(name)
    ace2_mean_ds = xr.open_dataset(ace2_mean_path)
    
    # 3. Load all ACE2 ensemble members (48 total)
    ace2_all_ds = load_all_ace2_ensembles(name)
    
    # 4. Select domain (if specified)
    if domain_name is not None:
        domain = constants.domains[domain_name]

        # First convert ERA5 and ACE2 longitudes from 0-360 to -180 to 180 if necessary
        if era5_ds.lon.max() > 180:
            era5_ds = era5_ds.assign_coords(lon=(((era5_ds.lon + 180) % 360) - 180)).sortby('lon')
        if ace2_mean_ds.lon.max() > 180:
            ace2_mean_ds = ace2_mean_ds.assign_coords(lon=(((ace2_mean_ds.lon + 180) % 360) - 180)).sortby('lon')
        if ace2_all_ds.lon.max() > 180:
            ace2_all_ds = ace2_all_ds.assign_coords(lon=(((ace2_all_ds.lon + 180) % 360) - 180)).sortby('lon')  

        # Slice domain
        era5_ds = era5_ds.sel(lat=slice(domain["lat"][0], domain["lat"][1]), 
                              lon=slice(domain["lon"][0], domain["lon"][1]))
        ace2_mean_ds = ace2_mean_ds.sel(lat=slice(domain["lat"][0], domain["lat"][1]), 
                                         lon=slice(domain["lon"][0], domain["lon"][1]))
        ace2_all_ds = ace2_all_ds.sel(lat=slice(domain["lat"][0], domain["lat"][1]), 
                                       lon=slice(domain["lon"][0], domain["lon"][1]))
    
    # 5. Aggregate spatially
    era5_agg = aggregate_index_over_domain(era5_ds, use_lat_weights=True)
    ace2_mean_agg = aggregate_index_over_domain(ace2_mean_ds, use_lat_weights=True)
    ace2_all_agg = aggregate_index_over_domain(ace2_all_ds, use_lat_weights=True)
    
    # 6. Save time series data
    domain_str = domain_name if domain_name else "Global"
    era5_folder = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/temporal_aggregation/{domain_str}/"
    ace2_folder = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/temporal_aggregation/{domain_str}/"
    
    os.makedirs(era5_folder, exist_ok=True)
    os.makedirs(ace2_folder, exist_ok=True)
    
    era5_agg.to_netcdf(os.path.join(era5_folder, f"{name}.nc"))
    ace2_mean_agg.to_netcdf(os.path.join(ace2_folder, f"{name}_ensemble_mean.nc"))
    ace2_all_agg.to_netcdf(os.path.join(ace2_folder, f"{name}_all_ensembles.nc"))
    
    logger.info(f"Saved time series for {name} in domain {domain_str}")
    
    return era5_agg, ace2_mean_agg, ace2_all_agg

def plot_temporal_comparison_for_domain(domain_name=None):
    """
    Plot temporal comparison of all ETCCDI indices for a specific domain.
    
    Creates one figure with subplots for each ETCCDI showing:
    - ERA5 (solid line)
    - ACE2 ensemble mean (solid line)
    - ACE2 ensemble spread (shaded region from min to max)
    
    Parameters
    ----------
    domain_name : str or None
        Domain name from constants.domains, or None for global
    """
    domain_str = domain_name if domain_name else "Global"
    logger.info(f"Plotting temporal comparison for domain: {domain_str}")
    
    # Get all ETCCDI indices
    all_indices = []
    for climate_var in constants.etccdi_indices.keys():
        all_indices.extend(constants.etccdi_indices[climate_var])
    
    # Create figure with subplots
    n_indices = len(all_indices)
    ncols = 3
    nrows = int(np.ceil(n_indices / ncols))
    
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(18, 4 * nrows))
    axes = axes.flatten() if n_indices > 1 else [axes]
    
    # Plot each ETCCDI
    handles = None
    for idx, name in enumerate(all_indices):
        ax = axes[idx]
        
        try:
            # Load time series data
            print(f"Loading time series for {name} in domain {domain_str}")
            era5_folder = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/temporal_aggregation/{domain_str}/"
            ace2_folder = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/temporal_aggregation/{domain_str}/"
            
            era5_ts = xr.open_dataset(os.path.join(era5_folder, f"{name}.nc"))
            ace2_mean_ts = xr.open_dataset(os.path.join(ace2_folder, f"{name}_ensemble_mean.nc"))
            ace2_all_ts = xr.open_dataset(os.path.join(ace2_folder, f"{name}_all_ensembles.nc"))

            # Drop percentiles dimension if present in ACE2 datasets
            if "percentiles" in ace2_all_ts.dims:
                ace2_all_ts = ace2_all_ts.isel(percentiles = 0)
            if "percentiles" in ace2_mean_ts.dims:
                ace2_mean_ts = ace2_mean_ts.isel(percentiles = 0)

            # Get variable names (they might differ between ERA5 and ACE2)
            era5_var = list(era5_ts.data_vars)[0]
            ace2_var = list(ace2_mean_ts.data_vars)[0]
            
            # Extract time and values
            time_dates = pd.date_range(start="2001-01-01", end="2010-12-31", freq="YS")
            
            era5_values = era5_ts[era5_var].values
            ace2_mean_values = ace2_mean_ts[ace2_var].values
            
            # Compute ensemble spread (min and max across all ensemble members)
            ace2_min = ace2_all_ts[ace2_var].min(dim='ensemble_member').values
            ace2_max = ace2_all_ts[ace2_var].max(dim='ensemble_member').values
            
            # Plot ERA5
            ax.plot(time_dates, era5_values, color='black', linewidth=2, label='ERA5', marker='o')
            
            # Plot ACE2 ensemble mean
            ax.plot(time_dates, ace2_mean_values, color='red', linewidth=2, label='ACE2 Ensemble Mean', marker='s')
            
            # Plot ensemble spread (shaded region)
            ax.fill_between(time_dates, ace2_min, ace2_max, color='red', alpha=0.3, label='ACE2 Ensemble Spread')
            
            # Capture handles and labels from first plot for shared legend
            if handles is None:
                handles, labels = ax.get_legend_handles_labels()
            
            # Formatting
            ax.set_xlabel('Year', fontsize=10)
            unit = constants.etccdi_units.get(name, '')
            ax.set_ylabel(f"{name} ({unit})", fontsize=10)
            ax.set_title(f"{name}", fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
        except FileNotFoundError as e:
            logger.warning(f"Could not plot {name} for {domain_str}: {e}")
            ax.text(0.5, 0.5, f"Data not available\nfor {name}", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f"{name}", fontsize=12)
    
    # Remove empty subplots
    for idx in range(n_indices, len(axes)):
        fig.delaxes(axes[idx])
    
    # Add single legend in the top right
    if handles is not None:
        fig.legend(
            handles, 
            labels, 
            loc='upper right', 
            fontsize=10, 
            bbox_to_anchor=(1.05, 1.0)
            )
    
    # Overall title
    fig.suptitle(f"Interannual variability of ETCCDI Indices - {domain_str}", 
                fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()
    
    return fig

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

        fig, axes = plt.subplots(
            nrows=len(indices), ncols=3,
            figsize=(21, 3.5 * len(indices)), 
            subplot_kw={'projection': ccrs.EqualEarth()}
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
        fig.suptitle(f"Comparison of ERA5 and ACE2 Ensemble Mean for {climate_var.capitalize()} Indices", fontsize=16)
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        figs.append(fig)
    return figs

#%% Main
def main():
    """
    Main workflow for temporal comparison of ETCCDI indices.
    
    For each domain (excluding Global initially):
    1. Compute spatial aggregation for all ETCCDI indices
    2. Save time series as NetCDF files
    3. Plot temporal comparison showing ERA5, ACE2 mean, and ensemble spread
    4. Save plots as PNG files
    
    Finally, process Global domain (heavy on RAM).
    """
    logger.info("Starting temporal comparison analysis")
    
    # Get all ETCCDI indices
    all_indices = []
    for climate_var in constants.etccdi_indices.keys():
        all_indices.extend(constants.etccdi_indices[climate_var])
    
    logger.info(f"Processing {len(all_indices)} ETCCDI indices: {all_indices}")
    
    # Get all domains except Global (save Global for last due to memory)
    domain_names = [d for d in constants.domains.keys()]
    
    logger.info(f"Processing {len(domain_names)} domains: {domain_names}")
    
    # Process each domain
    for domain_name in domain_names:
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing domain: {domain_name}")
        logger.info(f"{'='*60}")
        
        # Compute temporal aggregation for all ETCCDIs in this domain
        for name in all_indices:
            try:
                compute_temporal_aggregation(name, domain_name=domain_name)
            except Exception as e:
                logger.error(f"Error processing {name} for domain {domain_name}: {e}")
                continue
        
        # Plot temporal comparison for this domain
        try:
            fig = plot_temporal_comparison_for_domain(domain_name=domain_name)
            output_path = f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/03-etccdi-validation/temporal_comparison_{domain_name.replace(' ', '_')}.png"
            fig.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close(fig)
            logger.info(f"Saved plot to {output_path}")
        except Exception as e:
            logger.error(f"Error plotting for domain {domain_name}: {e}")
    
    # Process Global domain last (heavy on RAM)
    logger.info(f"\n{'='*60}")
    logger.info(f"Processing GLOBAL domain (may be memory intensive)")
    logger.info(f"{'='*60}")
    
    for name in all_indices:
        try:
            compute_temporal_aggregation(name, domain_name=None)
        except Exception as e:
            logger.error(f"Error processing {name} for Global domain: {e}")
            continue
    
    # Plot Global temporal comparison
    try:
        fig = plot_temporal_comparison_for_domain(domain_name=None)
        output_path = f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/03-etccdi-validation/temporal_comparison_Global.png"
        fig.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close(fig)
        logger.info(f"Saved plot to {output_path}")
    except Exception as e:
        logger.error(f"Error plotting for Global domain: {e}")
    
    logger.info("\nTemporal comparison analysis complete!")
    logger.info("Output saved to:")
    logger.info("  - Time series: data/processed/ETCCDI/{ERA5,ACE2}/temporal_aggregation/<domain>/")
    logger.info("  - Plots: results/figures/03-etccdi-validation/temporal_comparison_<domain>.png")


if __name__ == "__main__":
    main()


# Quick Vis Global
def temporal_comparison(domain_name="Global"):
    """
    Plot temporal comparison of all ETCCDI indices for a specific domain.
    
    Creates one figure with subplots for each ETCCDI showing:
    - ERA5 (solid line)
    - ACE2 ensemble mean (solid line)
    - ACE2 ensemble spread (shaded region from min to max)
    
    The legend is placed at position [0, 2] (first row, third column).
    ETR index is not plotted.
    
    Parameters
    ----------
    domain_name : str or None
        Domain name from constants.domains, or None for global
    """
    domain_str = domain_name if domain_name else "Global"
    logger.info(f"Plotting temporal comparison for domain: {domain_str}")
    
    # Get all ETCCDI indices, excluding ETR
    all_indices = []
    for climate_var in constants.etccdi_indices.keys():
        all_indices.extend(constants.etccdi_indices[climate_var])
    all_indices = [idx for idx in all_indices if idx != "ETR"]
    
    # Create figure with subplots
    n_indices = len(all_indices)
    ncols = 3
    nrows = int(np.ceil(n_indices / ncols))
    
    fig, axes = plt.subplots(nrows=nrows, ncols=ncols, figsize=(18, 4 * nrows))
    axes = axes.flatten() if n_indices > 1 else [axes]
    
    # Position for legend (first row, third column, index 2 when flattened)
    legend_ax_idx = 2
    
    # Plot each ETCCDI
    handles = None
    plot_idx = 0
    for name in all_indices:
        # Skip the legend position
        if plot_idx == legend_ax_idx:
            plot_idx += 1
        
        ax = axes[plot_idx]
        
        try:
            # Load time series data
            print(f"Loading time series for {name} in domain {domain_str}")
            era5_folder = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/temporal_aggregation/{domain_str}/"
            ace2_folder = f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2/temporal_aggregation/{domain_str}/"
            
            era5_ts = xr.open_dataset(os.path.join(era5_folder, f"{name}.nc"))
            ace2_mean_ts = xr.open_dataset(os.path.join(ace2_folder, f"{name}_ensemble_mean.nc"))
            ace2_all_ts = xr.open_dataset(os.path.join(ace2_folder, f"{name}_all_ensembles.nc"))

            # Drop percentiles dimension if present in ACE2 datasets
            if "percentiles" in ace2_all_ts.dims:
                ace2_all_ts = ace2_all_ts.isel(percentiles = 0)
            if "percentiles" in ace2_mean_ts.dims:
                ace2_mean_ts = ace2_mean_ts.isel(percentiles = 0)

            # Get variable names (they might differ between ERA5 and ACE2)
            era5_var = list(era5_ts.data_vars)[0]
            ace2_var = list(ace2_mean_ts.data_vars)[0]
            
            # Extract time and values
            time_dates = pd.date_range(start="2001-01-01", end="2010-12-31", freq="YS")
            
            era5_values = era5_ts[era5_var].values
            ace2_mean_values = ace2_mean_ts[ace2_var].values
            
            # Compute ensemble spread (min and max across all ensemble members)
            ace2_min = ace2_all_ts[ace2_var].min(dim='ensemble_member').values
            ace2_max = ace2_all_ts[ace2_var].max(dim='ensemble_member').values
            
            # Plot ERA5
            ax.plot(time_dates, era5_values, color='black', linewidth=2, label='ERA5', marker='o')
            
            # Plot ACE2 ensemble mean
            ax.plot(time_dates, ace2_mean_values, color='red', linewidth=2, label='ACE2 Ensemble Mean', marker='s')
            
            # Plot ensemble spread (shaded region)
            ax.fill_between(time_dates, ace2_min, ace2_max, color='red', alpha=0.3, label='ACE2 Ensemble Spread')
            
            # Capture handles and labels from first plot for shared legend
            if handles is None:
                handles, labels = ax.get_legend_handles_labels()
            
            # Formatting
            ax.set_xlabel('Year', fontsize=16)
            unit = constants.etccdi_units.get(name, '')
            ax.set_ylabel(f"{unit}", fontsize=16)
            ax.set_title(f"{name}", fontsize=16, fontweight='bold')
            ax.grid(True, alpha=0.3)
            
        except FileNotFoundError as e:
            logger.warning(f"Could not plot {name} for {domain_str}: {e}")
            ax.text(0.5, 0.5, f"Data not available\nfor {name}", 
                   ha='center', va='center', transform=ax.transAxes)
            ax.set_title(f"{name}", fontsize=12)
        
        plot_idx += 1
    
    # Remove empty subplots
    total_subplots = nrows * ncols
    for idx in range(plot_idx + 1, total_subplots):
        if idx != legend_ax_idx:
            fig.delaxes(axes[idx])
    
    # Add legend at axes[0, 2]
    if handles is not None:
        legend_ax = axes[legend_ax_idx]
        legend_ax.axis('off')
        legend_ax.legend(
            handles, 
            labels, 
            loc='upper center', 
            fontsize=18
        )
    
    # Overall title
    # fig.suptitle(f"Interannual variability of ETCCDI Indices - {domain_str}", 
    #             fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()

    # Save figure in results/figures/tmp
    output_path = f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/tmp/temporal_comparison_{domain_str.replace(' ', '_')}.png"
    fig.savefig(output_path, dpi=300, bbox_inches='tight')


    return fig

temporal_comparison()
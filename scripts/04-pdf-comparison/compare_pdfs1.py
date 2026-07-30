#%% Modules
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
import os

import importlib
importlib.reload(constants)

#%% Setup Logger
current_filename = __file__.split("/")[-1].replace(".py", "")
logger, queue_listener = setup_parallel_logger(current_filename, use_queue_listener=True)

#%% Global Cosntants
ace2_vars = [
    "tasmax", "tasmin",
    "pr",
    "sfcWind_mean", "sfcWind_max",
]

#%% Functions

#---
# ERA5 Loading
#---
def load_era5_sfcWindmax(start_year, end_year):
    """
    Load ERA5 data for the sfcWindmax variable and time range.
    """
    files = glob.glob(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/10si/daily_max_*.nc")
    files.sort()
    ds = xr.open_mfdataset(files, combine="by_coords").sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))

    return ds

def load_era5_sfcWindmean(start_year, end_year):
    """
    Load ERA5 data for the sfcWindmean variable and time range.
    """
    files = glob.glob(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/10si/daily_mean_*.nc")
    files.sort()
    ds = xr.open_mfdataset(files, combine="by_coords").sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))

    return ds

def load_era5_prate(start_year, end_year):
    """
    Load ERA5 data for the prate variable and time range.
    """
    files = glob.glob(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/PRATEsfc/daily_sum_*.nc")
    files.sort()
    ds = xr.open_mfdataset(files, combine="by_coords").sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
    ds = ds * 1000  # Convert from m to mm

    return ds

def load_era5_tasmax(start_year, end_year):
    """
    Load ERA5 data for the tasmax variable and time range.
    """
    files = glob.glob(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/TMP2m/daily_max_*.nc")
    files.sort()
    ds = xr.open_mfdataset(files, combine="by_coords").sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))

    return ds

def load_era5_tasmin(start_year, end_year):
    """
    Load ERA5 data for the tasmin variable and time range.
    """
    files = glob.glob(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/TMP2m/daily_min_*.nc")
    files.sort()
    ds = xr.open_mfdataset(files, combine="by_coords").sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))

    return ds

#---
# ACE2 Loading
#---
def load_ace2_ensemble_member(var_name, scenario, ensemble_number):
    base_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ace2-ensembles/1D/{scenario}"
    file = os.path.join(base_path, f"ensemble_{ensemble_number}.nc")
    ds = xr.open_dataset(file)
    da = ds[var_name]
    if var_name == "pr":
        da = da * 21600  # Convert from kg/m^2/s to mm/day
    ds = da.to_dataset(name=var_name)
    return ds

def ace2_ensemble_mean(var_name):
    """Computes ensemble mean of the 1D data across all ensemble members."""
    # Load index data across all ensemble members and scenarios
    all_scenarios_ds = []
    for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]:
        _members_ds = xr.concat(
            [load_ace2_ensemble_member(var_name, scenario, ensemble_number=i) for i in range(0, 12)], dim="ensemble_member"
            )
        all_scenarios_ds.append(_members_ds)
    all_scenarios_ds = xr.concat(all_scenarios_ds, dim="scenario")

    # Compute mean across ensemble members
    ensemble_mean = all_scenarios_ds.mean(dim=["ensemble_member", "scenario"])

    # Save the mean to a new netcdf file 
    file = f"/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ace2-ensembles/1D/{var_name}_ensemble_mean.nc"
    ensemble_mean.to_netcdf(file)
    logger.info(f"Saved ensemble mean for {var_name} to {file}")

def load_ace2_ensemble_mean(var_name):
    """Load the ensemble mean of the 1D data across all ensemble members."""
    file = f"/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ace2-ensembles/1D/ensemble_mean/{var_name}_ensemble_mean.nc"
    ds = xr.open_dataset(file)
    return ds

def load_ace2_ensemble(var_name, n_members=12):
    """Loads all ensemble members of the ensemble into one dataset"""
    all_scenarios_ds = []
    for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]:
        _members_ds = xr.concat(
            [load_ace2_ensemble_member(var_name, scenario, ensemble_number=i) for i in range(0, n_members)], dim="ensemble_member"
            )
        all_scenarios_ds.append(_members_ds)
    all_scenarios_ds = xr.concat(all_scenarios_ds, dim="scenario")
    return all_scenarios_ds

#---
# PDF Comparisons
#---
def plot_pdf_enveloped(var_name, domain=None, months=None, n_members=12):
    """
    plot the mean PDF (average the 48 member PDF lines) over all ensemble members as a solid line for a given variable,
    along with a shaded band showing the 5th–95th percentile envelope across all 48 members.
    Plot ERA5 PDF as a solid line for comparison.
    
    Parameters:
    -----------
    var_name : str
        Variable name to analyze
    domain : str or None
        Domain name from config.constants.domains. If None, use global domain.
    months : list of int or None
        List of months to filter (e.g., [12, 1, 2] for DJF). If None, use all months.
    """

    # Constants
    load_era5_func = {
        "sfcWind_max": load_era5_sfcWindmax,
        "sfcWind_mean": load_era5_sfcWindmean,
        "pr": load_era5_prate,
        "tasmax": load_era5_tasmax,
        "tasmin": load_era5_tasmin,
    }
    units = {
        "sfcWind_max": "m/s",
        "sfcWind_mean": "m/s",
        "pr": "mm/day",
        "tasmax": "K",
        "tasmin": "K",
    }
    xscale_pdf = {
        "sfcWind_max": (0, 40), # m/s
        "sfcWind_mean": (0, 40), # m/s
        "pr": (0, 100), # mm/day
        "tasmax": (180, 330), # K
        "tasmin": (180, 330), # K 
    }

    # Load ERA5
    era5_ds = load_era5_func[var_name](start_year=2001, end_year=2010)
    era5_var = list(era5_ds.data_vars)[0]
    
    # Load ALL ensemble members
    ace2_ensemble_ds = load_ace2_ensemble(var_name, n_members=n_members)
    ace2_var = list(ace2_ensemble_ds.data_vars)[0]

    # Convert dataset longitudes to -180 to 180 range for consistency
    era5_ds = era5_ds.assign_coords(lon=(((era5_ds.lon + 180) % 360) - 180)).sortby('lon')
    ace2_ensemble_ds = ace2_ensemble_ds.assign_coords(lon=(((ace2_ensemble_ds.lon + 180) % 360) - 180)).sortby('lon')

    # Apply temporal filtering (months)
    if months is not None:
        era5_ds = era5_ds.sel(time=era5_ds.time.dt.month.isin(months))
        ace2_ensemble_ds = ace2_ensemble_ds.sel(time=ace2_ensemble_ds.time.dt.month.isin(months))
    # Apply spatial filtering (domain)
    if domain is not None:
        domain_bounds = constants.domains[domain]
        lat_slice = slice(domain_bounds["lat"][0], domain_bounds["lat"][1])
        lon_slice = slice(domain_bounds["lon"][0], domain_bounds["lon"][1])
        era5_ds = era5_ds.sel(lat=lat_slice, lon=lon_slice)
        ace2_ensemble_ds = ace2_ensemble_ds.sel(lat=lat_slice, lon=lon_slice)

    # Compute PDFs for each ensemble member
    bins = np.linspace(xscale_pdf[var_name][0], xscale_pdf[var_name][1], 100)  # 100 bins from min to max of xscale_pdf
    pdfs = []
    for member in ace2_ensemble_ds.ensemble_member:
        member_data = ace2_ensemble_ds.sel(ensemble_member=member)[ace2_var].values.flatten()
        hist, _ = np.histogram(member_data, bins=bins, density=True)
        pdfs.append(hist)
    pdfs = np.array(pdfs)

    # Compute mean pdf of the ensemble
    mean_pdf = np.mean(pdfs, axis=0)

    # Plot the mean PDF, ERA5 PDF and the envelope as a shaded area
    fig, ax = plt.subplots(figsize=(8, 6))
    bin_centers = (bins[:-1] + bins[1:]) / 2
    ax.plot(bin_centers, mean_pdf, label="ACE2 Ensemble Mean PDF", linewidth=2, color='blue')

    # Plot ERA5 PDF
    era5_data = era5_ds[era5_var].values.flatten()
    hist_era5, _ = np.histogram(era5_data, bins=bins, density=True)
    ax.plot(bin_centers, hist_era5, label="ERA5 PDF", linewidth=2, color='red')

    # Plot the envelope as a shaded area
    lower = np.percentile(pdfs, 5, axis=0)
    upper = np.percentile(pdfs, 95, axis=0)
    max_spread = np.max(upper - lower)
    ax.fill_between(bin_centers, lower, upper, color='blue', alpha=0.3)
    # Add dashed boundary lines for the envelope
    ax.plot(bin_centers, lower, linestyle='--', color='blue', alpha=0.5, label='5th Percentile')
    ax.plot(bin_centers, upper, linestyle='--', color='blue', alpha=0.5, label='95th Percentile')

    ax.set_xlabel(f"{var_name} ({units[var_name]})")
    ax.set_ylabel("Probability Density")
    # Inside your plot function:
    if var_name == "pr":
        ax.set_yscale('log')  # Essential for precipitation heavy tails
    
    # Create title with domain and season info
    title_parts = [f"PDF {var_name}"]
    if domain is not None:
        title_parts.append(f"Domain: {domain}")
    if months is not None:
        season_name = "DJF" if months == [12, 1, 2] else f"Months {months}"
        title_parts.append(season_name)
    title_parts.append(f"max spread: {max_spread:.2f}")
    ax.set_title(" | ".join(title_parts))
    ax.legend()

    return fig

#%% Main
def main():
    #--- 
    # Compute ACE2-Ensembles
    #---
    # for var_name in ace2_vars:
    #     logger.info(f"Processing {var_name}...")
    #     ace2_ensemble_mean(var_name)
    #     logger.info(f"Completed processing {var_name}.")

    #---
    # 1. Global PDF comparison (all months)
    #---
    # logger.info("=" * 50)
    # logger.info("Starting Global PDF comparison (all months)")
    # logger.info("=" * 50)
    # all_figs = []
    # for var_name in ace2_vars:
    #     logger.info(f"Processing {var_name} (global, all months)...")
    #     fig = plot_pdf_enveloped(var_name, domain=None, months=None)
    #     fig.savefig(f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/{var_name}_pdf_global.png", dpi=300)
    #     all_figs.append(fig)

    # # Combine all variables into one summary figure
    # fig, axs = plt.subplots(3, 2, figsize=(15, 15))
    # axs = axs.flatten()
    # for i, var_name in enumerate(ace2_vars):
    #     fig_i = all_figs[i]
    #     axs[i].imshow(fig_i.canvas.buffer_rgba())
    #     axs[i].axis('off')
    #     axs[i].set_title(f"{var_name} PDF Comparison")
    # if len(ace2_vars) % 2 != 0:
    #     fig.delaxes(axs[-1])
    # plt.tight_layout()
    # plt.savefig(f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/all_vars_pdf_global.png", dpi=300)
    # plt.close('all')  # Close all figures to free memory
    # logger.info("Completed global PDF comparison (all months)")

    #---
    # 2. Global PDF Comparison for DJF only
    #---
    # logger.info("=" * 50)
    # logger.info("Starting Global PDF comparison (DJF only)")
    # logger.info("=" * 50)
    # all_figs_djf = []
    # for var_name in ace2_vars:
    #     logger.info(f"Processing {var_name} (global, DJF)...")
    #     fig = plot_pdf_enveloped(var_name, domain=None, months=[12, 1, 2])
    #     fig.savefig(f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/{var_name}_pdf_global_DJF.png", dpi=300)
    #     all_figs_djf.append(fig)

    # # Combine all variables into one summary figure
    # fig, axs = plt.subplots(3, 2, figsize=(15, 15))
    # axs = axs.flatten()
    # for i, var_name in enumerate(ace2_vars):
    #     fig_i = all_figs_djf[i]
    #     axs[i].imshow(fig_i.canvas.buffer_rgba())
    #     axs[i].axis('off')
    #     axs[i].set_title(f"{var_name} PDF Comparison (DJF)")
    # if len(ace2_vars) % 2 != 0:
    #     fig.delaxes(axs[-1])
    # plt.tight_layout()
    # plt.savefig(f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/all_vars_pdf_global_DJF.png", dpi=300)
    # plt.close('all')
    # logger.info("Completed global PDF comparison (DJF only)")

    #---
    # 3. Domain-specific PDF Comparison for DJF
    #---
    logger.info("=" * 50)
    logger.info("Starting Domain-specific PDF comparison (DJF only)")
    logger.info("=" * 50)
    
    for domain_name in constants.domains.keys():
        logger.info(f"Processing domain: {domain_name}")
        domain_figs = []
        
        for var_name in ace2_vars:
            logger.info(f"  - Processing {var_name} for {domain_name} (DJF)...")
            fig = plot_pdf_enveloped(var_name, domain=domain_name, months=[12, 1, 2])
            fig.savefig(f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/{var_name}_pdf_{domain_name.replace(' ', '_')}_DJF.png", dpi=300)
            domain_figs.append(fig)
        
        # Combine all variables for this domain into one summary figure
        fig, axs = plt.subplots(3, 2, figsize=(15, 15))
        axs = axs.flatten()
        for i, var_name in enumerate(ace2_vars):
            fig_i = domain_figs[i]
            axs[i].imshow(fig_i.canvas.buffer_rgba())
            axs[i].axis('off')
            axs[i].set_title(f"{var_name} PDF Comparison")
        if len(ace2_vars) % 2 != 0:
            fig.delaxes(axs[-1])
        plt.suptitle(f"PDF Comparison - {domain_name} - DJF", fontsize=16, y=0.995)
        plt.tight_layout()
        plt.savefig(f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/all_vars_pdf_{domain_name.replace(' ', '_')}_DJF.png", dpi=300)
        plt.close('all')
        logger.info(f"Completed domain: {domain_name}")
    
    logger.info("=" * 50)
    logger.info("All PDF comparisons completed successfully!")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
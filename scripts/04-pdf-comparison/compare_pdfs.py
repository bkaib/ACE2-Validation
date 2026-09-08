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
def plot_pdf_enveloped(var_name, is_legend=True,):
    """
    plot the mean PDF (average the 48 member PDF lines) over all ensemble members as a solid line for a given variable,
    along with a shaded band showing the 5th–95th percentile envelope across all 48 members.
    Plot ERA5 PDF as a solid line for comparison.
    """

    # Constants
    n_members = 12 # Ensemble members per scenario used.
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
    ax.plot(bin_centers, mean_pdf, label="ACE2 Ensemble Mean", linewidth=2, color='tab:blue')

    # Plot ERA5 PDF
    era5_data = era5_ds[era5_var].values.flatten()
    hist_era5, _ = np.histogram(era5_data, bins=bins, density=True)
    ax.plot(bin_centers, hist_era5, label="ERA5", linewidth=2, color='tab:orange')

    # Plot the envelope as a shaded area
    lower = np.percentile(pdfs, 5, axis=0)
    upper = np.percentile(pdfs, 95, axis=0)
    max_spread = np.max(upper - lower)
    ax.fill_between(bin_centers, lower, upper, color='blue', alpha=0.3)
    # # Add dashed boundary lines for the envelope
    # ax.plot(bin_centers, lower, linestyle='--', color='blue', alpha=0.5, label='5th Percentile')
    # ax.plot(bin_centers, upper, linestyle='--', color='blue', alpha=0.5, label='95th Percentile')

    ax.set_xlabel(f"{units[var_name]}", fontsize=16)
    ax.set_ylabel("Probability Density", fontsize=16)
    # Inside your plot function:
    if var_name == "pr":
        ax.set_yscale('log')  # Essential for precipitation heavy tails
    ax.set_title(f"{var_name}", fontsize=20)

    if is_legend:
        ax.legend(bbox_to_anchor=(1.05, 1.0), loc="upper left", borderaxespad=0)

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
    # Global PDF comparison
    #---
    # Create plot of all PDFs for each variable.   
    all_figs = []
    for i, var_name in enumerate(ace2_vars):
        is_legend = True if i == 1 else False  # Only show legend for the second plot
        # Generate figure of PDFs for current variable and save to file
        logger.info(f"Processing {var_name}...")
        fig = plot_pdf_enveloped(var_name, is_legend)
        fig.savefig(f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/{var_name}_pdf_global.png", dpi=300)
        all_figs.append(fig)

    # Put all the figures of all_figs into one plot and save to file
    fig, axs = plt.subplots(3, 2, figsize=(15, 15))
    axs = axs.flatten()
    for i, var_name in enumerate(ace2_vars):
        fig_i = all_figs[i]
        axs[i].imshow(fig_i.canvas.buffer_rgba())
        axs[i].axis('off')
        # axs[i].set_title(f"{var_name} PDF Comparison")
    # Delete the last empty subplot if the number of variables is odd
    if len(ace2_vars) % 2 != 0:
        fig.delaxes(axs[-1])
    # plt.tight_layout()
    plt.subplots_adjust(wspace=0.02, hspace=0.02, left=0.02, right=0.98, top=0.98, bottom=0.02)
    plt.savefig(f"/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/all_vars_pdf_global.png", dpi=300)

    #---
    # Global PDF Comparison for DJF only
    #---
    #TODO

    #---
    # Regional PDF Comparison for NH, SH, EU, NA, Asia
    #---
    #TODO

    #---
    # PDF Comparison in storm track regions of the North ATlatnic (see CWD regions where ACE2 overestimates storm days)
    #---
    #TODO

    #---
    # Bring all images into one figure
    #---
    from pathlib import Path
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D
    from PIL import Image

    png_files = [
    "/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/tasmax_pdf_global.png",
    "/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/tasmin_pdf_global.png",
    "/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/sfcWind_max_pdf_global.png",
    "/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/sfcWind_mean_pdf_global.png",
    "/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/pr_pdf_global.png",
    ]

    with Image.open(png_files[0]) as sample_img:
        img_w, img_h = sample_img.size

    nrows, ncols = 3, 2
    scale = 4
    fig_width = scale * ncols
    fig_height = scale * nrows * (img_h / img_w)

    fig, axs = plt.subplots(nrows, ncols, figsize=(fig_width, fig_height))
    axs = axs.flatten()

    for i, file_path in enumerate(png_files):
        img = Image.open(file_path)
        axs[i].imshow(img)
        axs[i].axis("off")

    # 1. Dummy-Linien für die Legende erstellen
    legend_elements = [
        Line2D([0], [0], color="tab:blue", lw=2.5, label="ACE2"),
        Line2D([0], [0], color="tab:orange", lw=2.5, label="ERA5"),  # Ggf. "tab:orange" oder Hex-Code anpassen
    ]

    # 2. Legende rechts neben axs[1] platzieren
    axs[1].legend(
        handles=legend_elements,
        loc="upper left",          # Die obere linke Ecke der Legende...
        bbox_to_anchor=(0.9, 0.9), # ...wird rechts neben die obere rechte Ecke von axs[1] angeheftet
        fontsize=10,
        frameon=True,
        borderaxespad=0
    )

    # 3. Den leeren Subplot unten rechts löschen
    for j in range(len(png_files), len(axs)):
        fig.delaxes(axs[j])

    plt.subplots_adjust(wspace=0.01, hspace=0.01, left=0, right=1, bottom=0, top=1)
    plt.savefig("/work/gg0304/g260230/projects/ACE2-Validation/results/figures/04-pdf-comparison/all_vars_pdf_global.png", dpi=300, bbox_inches="tight")
    plt.close()

if __name__ == "__main__":
    main()
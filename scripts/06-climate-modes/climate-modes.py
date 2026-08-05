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
from libraries.own_libraries import xarray_tools as xrt
from libraries.own_libraries import visualisation as vis
import xeofs as xe
import importlib
importlib.reload(constants)

#%% Setup Logger
current_filename = __file__.split("/")[-1].replace(".py", "")
logger, queue_listener = setup_parallel_logger(current_filename, use_queue_listener=True)


ds = xr.open_dataset("/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ACE2-ERA5/1D/PRESsfc_day_1941-2022.nc")
ds

#%% Functions
#---
# Loading of Data
#---
def load_ace2_1940_2022(name):
    """Loads ACE2 simulation data from 1940-2022. Temporal Res: 1D, SPatial Res: 1°x1°, globally"""
    p = "data/raw/ACE2-ERA5/1D/"
    f = f"{name}_day_1941-2022.nc"
    file = os.path.join(p,f)
    ds = xr.open_dataset(file)
    return ds

#---
# Climate Modes
#---
def compute_nao_index(da):
    # Select DJF months only
    da = da.sel(time=da.time.dt.month.isin([12,1,2]))

    # Select domain relevant for NAO index
    lon_min, lon_max = -70, 30 
    lat_min, lat_max = 30, 80
    da = da.assign_coords(lon=(((da.lon + 180) % 360) - 180)).sortby("lon")
    da = da.sel(lon=slice(lon_min, lon_max), lat=slice(lat_min, lat_max))

    # Compute Seasonal Mean over DJF where December of year y and JF of year y+1 are grouped
    da = da.assign_coords(
        season_year=da.time.dt.year.where(
            da.time.dt.month != 12, 
            da.time.dt.year + 1
            )
        )
    da = da.groupby("season_year").mean(dim="time")

    # 1. Initialize EOF model (specify standard deviation scaling if desired)
    # xeofs handles lat/lon area weighting natively via `use_coslat=True`
    model = xe.single.EOF(n_modes=5, use_coslat=True)

    # 2. Fit the model to your 3D DataArray (time, lat, lon)
    model.fit(da, dim="season_year")

    # 3. Retrieve EOFs (Spatial Loadings) in hPa
    eofs_hpa = model.components()  # Shape: (mode, lat, lon)

    # 4. Retrieve PCs (Index Time Series)
    # Normalized to unit variance (sigma = 1) -> Unitless NAO Index
    pcs_unitless = model.scores(normalized=True)  # Shape: (time, mode)

    # 5. Fraction of explained variance
    explained_variance_ratio = model.explained_variance_ratio()

    pca_metrics = {
        "loadings": eofs_hpa,
        "principal_components": pcs_unitless,
        "explained_variance_ratio": explained_variance_ratio
    }

    return pca_metrics


#---
# Visualisations
#---

def compare_climate_mode(
        ace2_metrics, era5_metrics, mode=1, 
        file="climate_mode_comparison", 
        output_dir = "/work/gg0304/g260230/projects/ACE2-Validation/results/figures/06-climate-modes",
        is_saved=True):
    """Compare the spatial pattern and timeseries of the NAO index based on PCA of ACE2 Pressure Data and ERA5 Pressure Data"""

    # Create figure with mixed subplot types
    fig = plt.figure(figsize=(18, 6))
    
    # Create two map subplots with projection
    ax0 = fig.add_subplot(1, 3, 1, projection=ccrs.EqualEarth())
    ax1 = fig.add_subplot(1, 3, 2, projection=ccrs.EqualEarth())
    
    # Create regular subplot for time series (no projection)
    ax2 = fig.add_subplot(1, 3, 3)

    # Check if spatial pattern has same sign
    ref_lat, ref_lon = 38.0, -28.0 # Azores region
    ace2_sign = np.sign(ace2_metrics["loadings"].sel(mode=mode).sel(lat=ref_lat, lon=ref_lon, method="nearest").values)
    era5_sign = np.sign(era5_metrics["loadings"].sel(mode=mode).sel(lat=ref_lat, lon=ref_lon, method="nearest").values)
    if ace2_sign != era5_sign:
        ace2_metrics["loadings"] = ace2_metrics["loadings"] * -1
        ace2_metrics["principal_components"] = ace2_metrics["principal_components"] * -1

    # Get data for plotting
    era5_loadings = era5_metrics["loadings"].sel(mode=mode)
    ace2_loadings = ace2_metrics["loadings"].sel(mode=mode)
    
    # Find common value range for consistent colorbar
    vmin = min(era5_loadings.min().values, ace2_loadings.min().values)
    vmax = max(era5_loadings.max().values, ace2_loadings.max().values)
    
    # Make symmetric around zero for diverging colormap
    vlim = max(abs(vmin), abs(vmax))
    
    # Compute spatial correlation
    # Flatten and compute correlation
    era5_flat = era5_loadings.values.flatten()
    ace2_flat = ace2_loadings.values.flatten()
    # Remove NaN values for correlation
    valid_mask = ~(np.isnan(era5_flat) | np.isnan(ace2_flat))
    spatial_corr = np.corrcoef(era5_flat[valid_mask], ace2_flat[valid_mask])[0, 1]
    
    # Spatial Pattern of NAO Index - ERA5
    era5_loadings.plot.contourf(
        ax=ax0, 
        transform=ccrs.PlateCarree(), 
        cmap="coolwarm", 
        levels=20,
        vmin=-vlim,
        vmax=vlim,
        add_colorbar=False
        )
    ax0.coastlines()
    gl0 = ax0.gridlines(draw_labels=True)
    gl0.top_labels = False
    gl0.right_labels = False
    ax0.set_title("ERA5 (PC1)", pad=20)

    # Spatial Pattern of NAO Index - ACE2
    im = ace2_loadings.plot.contourf(
        ax=ax1, 
        transform=ccrs.PlateCarree(), 
        cmap="coolwarm", 
        levels=20,
        vmin=-vlim,
        vmax=vlim,
        add_colorbar=False
        )
    ax1.coastlines()
    gl1 = ax1.gridlines(draw_labels=True)
    gl1.top_labels = False
    gl1.right_labels = False
    ax1.set_title("ACE2 (PC1)", pad=20)
    
    # Add shared colorbar below the spatial plots
    cbar_ax = fig.add_axes([0.1, 0.08, 0.5, 0.02])
    cbar = plt.colorbar(im, cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Pressure Loading (hPa)', fontsize=10)

    # Get temporal data
    ace2_pcs = ace2_metrics["principal_components"].sel(mode=mode)
    era5_pcs = era5_metrics["principal_components"].sel(mode=mode)
    
    # Compute temporal correlation
    temporal_corr = np.corrcoef(ace2_pcs.values, era5_pcs.values)[0, 1]
    
    # Plot Temporal Pattern
    ace2_pcs.plot(ax=ax2, label="ACE2", linewidth=1.5)
    era5_pcs.plot(ax=ax2, label="ERA5", linewidth=1.5)
    ax2.set_xlabel("Time")
    ax2.set_ylabel("PC1 (normalized)")
    ax2.set_title(f"PC-Scores (Temporal Corr: {temporal_corr:.3f})", pad=10)
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)
    
    # Add overall figure title with correlations
    fig.suptitle(f"Climate Mode Comparison (Mode {mode}) - Spatial Corr: {spatial_corr:.3f}", 
                 fontsize=14, y=0.98)
    
    plt.tight_layout(rect=[0, 0.12, 1, 0.96])

    if is_saved:
        os.makedirs(output_dir, exist_ok=True)
        fig.savefig(f"{output_dir}/{file}_mode{mode}.png", dpi=300, bbox_inches='tight')

    return fig

#%% Main
def main():
    # Constants:
    var_names = ["PRATEsfc", "PRESsfc", "TMP2m", "WINDSPEED",]

    # Compute NAO and NAO Index based on DJF seasonal means
    ace2_pressfc = load_ace2_1940_2022("PRESsfc")["PRESsfc"]
    era5_pressfc = xr.open_dataset("/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ERA5/1D/PRESsfc_day_1941-2022.nc")["sp"]
    ace2_pca_metrics = compute_nao_index(ace2_pressfc)
    era5_pca_metrics = compute_nao_index(era5_pressfc)

    # Create a figure to compare the modes of ACE2 and ERA5
    compare_climate_mode(ace2_pca_metrics, era5_pca_metrics, mode=1, file="nao-index-comparison")

    # Compute Teleconnections of NAO Index to PRATEsfc, TMP2m and WINDSPEED
#%% Run
if __name__ == "__main__":
    main()

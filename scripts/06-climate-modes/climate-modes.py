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
def plot_nao_index(pca_metrics):
    """Plot the spatial pattern and timeseries of the NAO index based on PCA of ACE2 Pressure Data"""

    fig, axes = plt.subplots(1, 2, figsize=(15, 5), subplot_kw={'projection': ccrs.EqualEarth()})

    # Spatial Pattern of NAO Index
    pca_metrics["loadings"].sel(mode=1).plot.contourf(
        ax=axes[0], 
        transform=ccrs.PlateCarree(), 
        cmap="coolwarm", 
        levels=20,
        cbar_ax = fig.add_axes([0.25, 0.1, 0.5, 0.02]),  # Put colorbar under the plot
        cbar_kwargs = {"orientation": "horizontal"}
        )
    axes[0].coastlines()
    axes[0].gridlines(draw_labels=True)

    # Plot Temporal Pattern
    pca_metrics["principal_components"].sel(mode=1).plot(ax=axes[1])
    axes[1].set_xlabel("Time") # plot time on x axis
    axes[1].set_ylabel("NAO Index (PC1)") # plot NAO index on y axis

    fig.show()

    return fig

def compare_climate_mode(
        ace2_metrics, era5_metrics, mode=1, 
        file="climate_mode_comparison", 
        output_dir = "/work/gg0304/g260230/projects/ACE2-Validation/results/figures/06-climate-modes",
        is_saved=True):
    """Compare the spatial pattern and timeseries of the NAO index based on PCA of ACE2 Pressure Data and ERA5 Pressure Data"""

    fig, axes = plt.subplots(1, 3, figsize=(15, 10), subplot_kw={'projection': ccrs.EqualEarth()})

    # Check if spatial pattern has same sign
    ref_lat, ref_lon = 38.0, -28.0 # Azores region
    ace2_sign = np.sign(ace2_metrics["loadings"].sel(mode=mode).sel(lat=ref_lat, lon=ref_lon, method="nearest").values)
    era5_sign = np.sign(era5_metrics["loadings"].sel(mode=mode).sel(lat=ref_lat, lon=ref_lon, method="nearest").values)
    if ace2_sign != era5_sign:
        ace2_metrics["loadings"] = ace2_metrics["loadings"] * -1
        ace2_metrics["principal_components"] = ace2_metrics["principal_components"] * -1

    # Spatial Pattern of NAO Index
    ace2_metrics["loadings"].sel(mode=mode).plot.contourf(
        ax=axes[1], 
        transform=ccrs.PlateCarree(), 
        cmap="coolwarm", 
        levels=20,
        cbar_ax = fig.add_axes([0.25, 0.1, 0.5, 0.02]),  # Put colorbar under the plot
        cbar_kwargs = {"orientation": "horizontal"}
        )
    axes[1].coastlines()
    axes[1].gridlines(draw_labels=True)
    axes[1].set_title("ACE2 (PC1)")

    era5_metrics["loadings"].sel(mode=mode).plot.contourf(
        ax=axes[0], 
        transform=ccrs.PlateCarree(), 
        cmap="coolwarm", 
        levels=20,
        cbar_ax = fig.add_axes([0.25, 0.1, 0.5, 0.02]),  # Put colorbar under the plot
        cbar_kwargs = {"orientation": "horizontal"}
        )
    axes[0].coastlines()
    axes[0].gridlines(draw_labels=True)
    axes[0].set_title("ERA5 (PC1)")

    # Plot Temporal Pattern
    ace2_metrics["principal_components"].sel(mode=mode).plot(ax=axes[2], label="ACE2")
    era5_metrics["principal_components"].sel(mode=mode).plot(ax=axes[2], label="ERA5")
    era5_metrics["principal_components"].sel(mode=mode).plot(ax=axes[2])
    axes[2].set_xlabel("Time") # plot time on x axis
    axes[2].set_ylabel("PC1") # plot NAO index on y axis
    axes[2].set_title("ACE2 and ERA5 PC-Scores")
    axes[2].legend(bbox_to_anchor=(1.0, 1.05), loc='upper right')

    if is_saved:
        os.makedirs(output_dir, exist_ok=True)
        fig.savefig(f"{output_dir}/{file}_{mode}.png", dpi=300)

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

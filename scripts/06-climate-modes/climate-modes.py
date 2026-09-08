#%% Modules
import sys
from xml.parsers.expat import model
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

#%% Functions
#---
# Loading of Data
#---
def load_ace2_1940_2022(name):
    """Loads ACE2 simulation data from 1940-2022. Temporal Res: 1D, SPatial Res: 1°x1°, globally"""
    p = "/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ACE2-ERA5/1D/"
    f = f"{name}_day_1941-2022.nc"
    file = os.path.join(p,f)
    ds = xr.open_dataset(file)
    return ds
#---
# Statistics
#---
def linear_detrend(da, dim="time"):
    """Detrends a DataArray along the specified dimension using linear regression."""
    # Get the time values as a numeric array
    x = np.arange(da[dim].size)
    
    # Calculate the slope and intercept for each grid point
    slope, intercept = np.polyfit(x, da.values, 1)
    
    # Create the trend line
    trend = slope * x + intercept
    
    # Subtract the trend from the original data
    detrended = da - trend
    
    return detrended
#---
# Climate Modes
#---
def compute_nao_index_monthly(da, n_modes=5):
    # Select domain relevant for NAO index
    lon_min, lon_max = -70, 30 
    lat_min, lat_max = 30, 80
    da = da.assign_coords(lon=(((da.lon + 180) % 360) - 180)).sortby("lon")
    da = da.sel(lon=slice(lon_min, lon_max), lat=slice(lat_min, lat_max))

    # Initialize EOF model (specify standard deviation scaling if desired)
    # X = U S V^T, where U = PCs, S = singular values, V = EOFs
    model = xe.single.EOF(
        n_modes=n_modes, 
        use_coslat=True, 
        center = True,
        standardize=False,
        ) # Latitude weighted, not centered (standardize=false)
    model.fit(da, dim="time")

    # Loadings (Spatial Patterns)
    eofs = model.components(normalized=True)  # V x S (normalized=False contains amplitude S)

    # Scores (Principal Components)
    scores = model.scores(normalized=False)  # U (normalized=True cancels out the amplitude S). Normalized by L2-norm, not stdev=1
        
    # Standardize to stdev = 1
    alpha = scores.std(dim="time")
    scores = scores / alpha # Scale to unit stdev=1
    eofs = eofs * alpha

    # Explained variance ratio
    explained_variance_ratio = model.explained_variance_ratio()

    pca_metrics = {
        "loadings": eofs,
        "principal_components": scores,
        "explained_variance_ratio": explained_variance_ratio,
    }

    return pca_metrics

def compute_nao_index(da, n_modes=5):
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

    # Initialize EOF model (specify standard deviation scaling if desired)
    # X = U S V^T, where U = PCs, S = singular values, V = EOFs
    model = xe.single.EOF(
        n_modes=n_modes, 
        use_coslat=True, 
        center = True,
        standardize=False,
        ) # Latitude weighted, not centered (standardize=false)
    model.fit(da, dim="season_year")

    # Loadings (Spatial Patterns)
    eofs = model.components(normalized=True)  # V x S (normalized=False contains amplitude S)

    # Scores (Principal Components)
    scores = model.scores(normalized=False)  # U (normalized=True cancels out the amplitude S). Normalized by L2-norm, not stdev=1
        
    # Standardize to stdev = 1
    alpha = scores.std(dim="season_year")
    scores = scores / alpha # Scale to unit stdev=1
    eofs = eofs * alpha

    # Explained variance ratio
    explained_variance_ratio = model.explained_variance_ratio()

    pca_metrics = {
        "loadings": eofs,
        "principal_components": scores,
        "explained_variance_ratio": explained_variance_ratio,
    }

    return pca_metrics

def compute_pna_index(
        da,
        lon_min = 120, # 120, 
        lon_max = 300, # 300, 
        lat_min = 20, 
        lat_max = 90,
        n_modes=5,
        ):
    # Select DJF months only
    da = da.sel(time=da.time.dt.month.isin([12,1,2]))

    # Select domain relevant for PNA index
    # da = da.assign_coords(lon=(((da.lon + 180) % 360) - 180)).sortby("lon")
    da = da.sel(lon=slice(lon_min, lon_max), lat=slice(lat_min, lat_max))

    # Compute Seasonal Mean over DJF where December of year y and JF of year y+1 are grouped
    da = da.assign_coords(
        season_year=da.time.dt.year.where(
            da.time.dt.month != 12, 
            da.time.dt.year + 1
            )
        )
    da = da.groupby("season_year").mean(dim="time")

    # Initialize EOF model (specify standard deviation scaling if desired)
    # X = U S V^T, where U = PCs, S = singular values, V = EOFs
    model = xe.single.EOF(
        n_modes=n_modes, 
        use_coslat=True, 
        center = True,
        standardize=False,
        ) # Latitude weighted, not centered (standardize=false)
    model.fit(da, dim="season_year")

    # Loadings (Spatial Patterns)
    eofs = model.components(normalized=True)  # V x S (normalized=False contains amplitude S)

    # Scores (Principal Components)
    scores = model.scores(normalized=False)  # U (normalized=True cancels out the amplitude S). Normalized by L2-norm, not stdev=1
        
    # Standardize to stdev = 1
    alpha = scores.std(dim="season_year")
    scores = scores / alpha # Scale to unit stdev=1
    eofs = eofs * alpha

    # Explained variance ratio
    explained_variance_ratio = model.explained_variance_ratio()

    pca_metrics = {
        "loadings": eofs,
        "principal_components": scores,
        "explained_variance_ratio": explained_variance_ratio,
    }

    return pca_metrics

def compute_pna_index_monthly(
        da,
        lon_min = 120, # 120, 
        lon_max = 300, # 300, 
        lat_min = 20, 
        lat_max = 90,
        n_modes=5,
        dim="time",
        ):
    # Select domain relevant for PNA index
    # da = da.assign_coords(lon=(((da.lon + 180) % 360) - 180)).sortby("lon")
    da = da.sel(lon=slice(lon_min, lon_max), lat=slice(lat_min, lat_max))

    # Initialize EOF model (specify standard deviation scaling if desired)
    # X = U S V^T, where U = PCs, S = singular values, V = EOFs
    model = xe.single.EOF(
        n_modes=n_modes, 
        use_coslat=True, 
        center = True,
        standardize=False,
        ) # Latitude weighted, not centered (standardize=false)
    model.fit(da, dim="time")

    # Loadings (Spatial Patterns)
    eofs = model.components(normalized=True)  # V x S (normalized=False contains amplitude S)

    # Scores (Principal Components)
    scores = model.scores(normalized=False)  # U (normalized=True cancels out the amplitude S). Normalized by L2-norm, not stdev=1
        
    # Standardize to stdev = 1
    alpha = scores.std(dim=dim)
    scores = scores / alpha # Scale to unit stdev=1
    eofs = eofs * alpha

    # Explained variance ratio
    explained_variance_ratio = model.explained_variance_ratio()

    pca_metrics = {
        "loadings": eofs,
        "principal_components": scores,
        "explained_variance_ratio": explained_variance_ratio,
    }

    return pca_metrics

#---
# Teleconnections
#---
def preprocess_variable_for_teleconnection(da):
    """
    Preprocess climate variable to seasonal DJF means matching NAO indexing.
    Assumes input is daily data with dims (time, lat, lon)
    """
    # Select DJF months only
    da = da.sel(time=da.time.dt.month.isin([12, 1, 2]))
    
    # Create same season_year indexing as NAO
    da = da.assign_coords(
        season_year=da.time.dt.year.where(
            da.time.dt.month != 12, 
            da.time.dt.year + 1
        )
    )
    
    # Compute seasonal mean (DJF)
    da_seasonal = da.groupby("season_year").mean(dim="time")
    
    return da_seasonal

def compute_teleconnection(pc_score, variable, lag=0):
    """Computes the teleconnection between a principal component score and a variable with an optional lag.
    Returns: A spatial map of correlations between the PC score and the variable at each grid point."""
    # Ensure the time dimension is aligned
    if lag != 0:
        pc_score = pc_score.shift(season_year=lag)
    
    # Compute correlation at each grid point
    correlation_map = xr.corr(pc_score, variable, dim="season_year")
    
    return correlation_map
#---
# Visualisations
#---

def compare_climate_mode_nao(
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
    era5_explained_variance_ratio = era5_metrics["explained_variance_ratio"].sel(mode=mode).values * 100 # in %
    ace2_explained_variance_ratio = ace2_metrics["explained_variance_ratio"].sel(mode=mode).values * 100
    
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
    ax0.set_title(f"ERA5 | PC{mode} ({era5_explained_variance_ratio:.2f}%)", pad=20)

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
    ax1.set_title(f"ACE2 | PC{mode} ({ace2_explained_variance_ratio:.2f}%)", pad=20)
    
    # Add shared colorbar below the spatial plots
    cbar_ax = fig.add_axes([0.1, 0.25, 0.5, 0.02]) # left, bottom, width, height
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
    ax2.set_xlabel("Seasons (DJF)")
    ax2.set_ylabel(f"PC{mode} (normalized)")
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
def compare_climate_mode_pna(
        ace2_metrics, era5_metrics, mode=1, 
        file="climate_mode_comparison", 
        output_dir = "/work/gg0304/g260230/projects/ACE2-Validation/results/figures/06-climate-modes",
        is_saved=True):
    """Compare the spatial pattern and timeseries of the PNA index based on PCA of ACE2 Pressure Data and ERA5 Pressure Data"""

    # Create figure with mixed subplot types
    fig = plt.figure(figsize=(18, 6))
    
    # Create two map subplots with projection
    ax0 = fig.add_subplot(1, 3, 1, projection=ccrs.EqualEarth())
    ax1 = fig.add_subplot(1, 3, 2, projection=ccrs.EqualEarth())
    
    # Create regular subplot for time series (no projection)
    ax2 = fig.add_subplot(1, 3, 3)

    # Check if spatial pattern has same sign
    ref_lat, ref_lon = 45.0, -120.0 # PNA region
    ace2_sign = np.sign(ace2_metrics["loadings"].sel(mode=mode).sel(lat=ref_lat, lon=ref_lon, method="nearest").values)
    era5_sign = np.sign(era5_metrics["loadings"].sel(mode=mode).sel(lat=ref_lat, lon=ref_lon, method="nearest").values)
    if ace2_sign != era5_sign:
        ace2_metrics["loadings"] = ace2_metrics["loadings"] * -1
        ace2_metrics["principal_components"] = ace2_metrics["principal_components"] * -1

    # Get data for plotting
    era5_loadings = era5_metrics["loadings"].sel(mode=mode)
    ace2_loadings = ace2_metrics["loadings"].sel(mode=mode)
    era5_explained_variance_ratio = era5_metrics["explained_variance_ratio"].sel(mode=mode).values * 100 # in %
    ace2_explained_variance_ratio = ace2_metrics["explained_variance_ratio"].sel(mode=mode).values * 100
    
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
    
    # Spatial Pattern of PNA Index - ERA5
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
    ax0.set_title(f"ERA5 | PC{mode} ({era5_explained_variance_ratio:.2f}%)", pad=20)

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
    ax1.set_title(f"ACE2 | PC{mode} ({ace2_explained_variance_ratio:.2f}%)", pad=20)
    
    # Add shared colorbar below the spatial plots
    cbar_ax = fig.add_axes([0.1, 0.35, 0.5, 0.02])
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
    ax2.set_ylabel(f"PC{mode} (normalized)")
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
def visualize_teleconnection(
        corr_map, 
        title="Teleconnection Map", 
        output_dir="/work/gg0304/g260230/projects/ACE2-Validation/results/figures/06-climate-modes", 
        file="teleconnection_map", 
        is_saved=True
        ):
    """Visualizes the teleconnection correlation map."""
    fig, ax = plt.subplots(figsize=(10, 5), subplot_kw={'projection': ccrs.EqualEarth()})
    
    # Plot the correlation map
    im = corr_map.plot.contourf(
        ax=ax, 
        transform=ccrs.PlateCarree(), 
        cmap="coolwarm", 
        levels=20,
        vmin=-1,
        vmax=1,
        add_colorbar=False
    )
    
    ax.coastlines()
    gl = ax.gridlines(draw_labels=True)
    gl.top_labels = False
    gl.right_labels = False
    ax.set_title(title, pad=20)
    
    # Add colorbar
    cbar_ax = fig.add_axes([0.1, 0.25, 0.5, 0.02])
    cbar = plt.colorbar(im, cax=cbar_ax, orientation='horizontal')
    cbar.set_label('Correlation Coefficient', fontsize=10)
    
    plt.tight_layout(rect=[0, 0.12, 1, 0.96])

    if is_saved:
        os.makedirs(output_dir, exist_ok=True)
        fig.savefig(f"{output_dir}/{file}.png", dpi=300, bbox_inches='tight')

    return fig

def modes_and_teleconnections(
        ace2_pca_metrics,
        era5_pca_metrics,
        corr_vars,
        climate_mode,
        mode=1,
        file="modes_and_teleconnections",
        output_dir="/work/gg0304/g260230/projects/ACE2-Validation/results/figures/06-climate-modes",
        is_saved=True,
        cbar_ax_kwargs={"cbar_ax_top": [0.125, 0.48, 0.775, 0.015]}, # [left, bottom, width, height]
        loading_projection = ccrs.EqualEarth(),
):
    """
    Generate one figure including the following:
    2 rows, 3 columns.
    Top row: Climate Mode ERA5, Climate Mode ACE2, Time Series of Climate Modes
    Bottom row: teleconnection maps for TMP2m, PRATEsfc, WINDSPEED with respect to the Climate Mode index
    """

    fig = plt.figure(figsize=(20, 12))
    
    # Create subplots
    ax0 = fig.add_subplot(2, 3, 1, projection=loading_projection)
    ax1 = fig.add_subplot(2, 3, 2, projection=loading_projection)
    ax2 = fig.add_subplot(2, 3, 3)
    ax3 = fig.add_subplot(2, 3, 4, projection=ccrs.EqualEarth())
    ax4 = fig.add_subplot(2, 3, 5, projection=ccrs.EqualEarth())
    ax5 = fig.add_subplot(2, 3, 6, projection=ccrs.EqualEarth())

    # Check if spatial pattern has same sign (align them)
    if climate_mode == "NAO":
        ref_lat, ref_lon = 38.0, -28.0  # Azores region for NAO
    elif climate_mode == "PNA":
        ref_lat, ref_lon = 45.0, -120.0  # PNA region
    ace2_sign = np.sign(ace2_pca_metrics["loadings"].sel(mode=mode).sel(lat=ref_lat, lon=ref_lon, method="nearest").values)
    era5_sign = np.sign(era5_pca_metrics["loadings"].sel(mode=mode).sel(lat=ref_lat, lon=ref_lon, method="nearest").values)
    if ace2_sign != era5_sign:
        ace2_pca_metrics["loadings"] = ace2_pca_metrics["loadings"] * -1
        ace2_pca_metrics["principal_components"] = ace2_pca_metrics["principal_components"] * -1

    # Get data for plotting
    era5_loading = era5_pca_metrics["loadings"].sel(mode=mode)
    ace2_loading = ace2_pca_metrics["loadings"].sel(mode=mode)
    era5_pcs = era5_pca_metrics["principal_components"].sel(mode=mode)
    ace2_pcs = ace2_pca_metrics["principal_components"].sel(mode=mode)
    
    era5_explained_variance_ratio = era5_pca_metrics["explained_variance_ratio"].sel(mode=mode).values * 100
    ace2_explained_variance_ratio = ace2_pca_metrics["explained_variance_ratio"].sel(mode=mode).values * 100

    # Find common value range for loadings colorbar
    vmin = min(era5_loading.min().values, ace2_loading.min().values)
    vmax = max(era5_loading.max().values, ace2_loading.max().values)
    vlim = max(abs(vmin), abs(vmax))

    # Compute spatial correlation
    era5_flat = era5_loading.values.flatten()
    ace2_flat = ace2_loading.values.flatten()
    valid_mask = ~(np.isnan(era5_flat) | np.isnan(ace2_flat))
    spatial_corr = np.corrcoef(era5_flat[valid_mask], ace2_flat[valid_mask])[0, 1]

    # Compute temporal correlation
    temporal_corr = np.corrcoef(ace2_pcs.values, era5_pcs.values)[0, 1]

    # TOP ROW: Plot Modes and PC-Scores
    
    # ERA5 loading
    era5_loading.plot.contourf(
        ax=ax0, 
        transform=ccrs.PlateCarree(), 
        cmap="coolwarm", 
        levels=20,
        vmin=-vlim,
        vmax=vlim,
        add_colorbar=False,
    )
    ax0.coastlines()
    gl0 = ax0.gridlines(draw_labels=True)
    gl0.top_labels = False
    gl0.right_labels = False
    ax0.set_title(f"ERA5 | PC{mode} ({era5_explained_variance_ratio:.2f}%)", pad=20)

    # ACE2 loading
    im_loading = ace2_loading.plot.contourf(
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
    ax1.set_title(f"ACE2 | PC{mode} ({ace2_explained_variance_ratio:.2f}%) | Spatial Corr: {spatial_corr:.3f}", pad=20)

    # PC scores time series
    ace2_pcs.plot(ax=ax2, label="ACE2", linewidth=1.5)
    era5_pcs.plot(ax=ax2, label="ERA5", linewidth=1.5)
    ax2.set_xlabel("Seasons (DJF)")
    ax2.set_ylabel(f"PC{mode} (normalized)")
    ax2.set_title(f"PC-Scores | Temporal Corr: {temporal_corr:.3f}", pad=10)
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3)

    # Add shared colorbar for loadings
    cbar_ax_top = fig.add_axes(cbar_ax_kwargs["cbar_ax_top"])  
    cbar_top = plt.colorbar(im_loading, cax=cbar_ax_top, orientation='horizontal')
    cbar_top.set_label('Pressure Loading (hPa)', fontsize=10)

    # BOTTOM ROW: Plot Teleconnections
    
    # Teleconnection for PRATEsfc
    im_precip = corr_vars["PRATEsfc"].plot.contourf(
        ax=ax3, 
        transform=ccrs.PlateCarree(), 
        cmap="coolwarm", 
        levels=20,
        vmin=-1,
        vmax=1,
        add_colorbar=False
    )
    ax3.coastlines()
    gl3 = ax3.gridlines(draw_labels=True)
    gl3.top_labels = False
    gl3.right_labels = False
    ax3.set_title("Teleconnection: Precipitation", pad=20)

    # Teleconnection for TMP2m
    corr_vars["TMP2m"].plot.contourf(
        ax=ax4, 
        transform=ccrs.PlateCarree(), 
        cmap="coolwarm", 
        levels=20,
        vmin=-1,
        vmax=1,
        add_colorbar=False
    )
    ax4.coastlines()
    gl4 = ax4.gridlines(draw_labels=True)
    gl4.top_labels = False
    gl4.right_labels = False
    ax4.set_title("Teleconnection: 2m Temperature", pad=20)

    # Teleconnection for WINDSPEED
    corr_vars["WINDSPEED"].plot.contourf(
        ax=ax5, 
        transform=ccrs.PlateCarree(), 
        cmap="coolwarm", 
        levels=20,
        vmin=-1,
        vmax=1,
        add_colorbar=False
    )
    ax5.coastlines()
    gl5 = ax5.gridlines(draw_labels=True)
    gl5.top_labels = False
    gl5.right_labels = False
    ax5.set_title("Teleconnection: Wind Speed", pad=20)

    # Add shared colorbar for teleconnections
    cbar_ax_bottom = fig.add_axes([0.125, 0.08, 0.775, 0.015])  # [left, bottom, width, height]
    cbar_bottom = plt.colorbar(im_precip, cax=cbar_ax_bottom, orientation='horizontal')
    cbar_bottom.set_label('Correlation Coefficient', fontsize=10)

    # Overall title
    fig.suptitle(f"Climate Mode: {climate_mode} | PC{mode}", fontsize=16, y=0.98)

    plt.tight_layout(rect=[0, 0.10, 1, 0.96])

    if is_saved:
        os.makedirs(output_dir, exist_ok=True)
        fig.savefig(f"{output_dir}/{file}_{climate_mode}_mode{mode}.png", dpi=300, bbox_inches='tight')

    return fig



#%% Main
def main():
    # Constants:
    var_names = ["PRATEsfc", "PRESsfc", "TMP2m", "WINDSPEED",]
    pna_mode = 1
    nao_mode = 1

    #---
    # Compute NAO Index based on DJF seasonal means
    #---
    ace2_pressfc = load_ace2_1940_2022("PRESsfc")["PRESsfc"]
    era5_pressfc = xr.open_dataset("/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ERA5/1D/PRESsfc_day_1941-2022.nc")["sp"]

    ## Convert from Pa to hPa
    ace2_pressfc = ace2_pressfc / 100.0
    era5_pressfc = era5_pressfc / 100.0

    ## Compute NAO Index
    ace2_nao_metrics = compute_nao_index(ace2_pressfc)
    era5_nao_metrics = compute_nao_index(era5_pressfc)

    ## Create a figure to compare the modes of ACE2 and ERA5
    # compare_climate_mode_nao(ace2_nao_metrics, era5_nao_metrics, mode=1, file="nao-index-comparison")

    #---
    # PNA Index
    #---
    ace2_pna_metrics = compute_pna_index(ace2_pressfc)
    era5_pna_metrics = compute_pna_index(era5_pressfc)

    ## Create a figure to compare the modes of ACE2 and ERA5
    # compare_climate_mode_pna(ace2_pna_metrics, era5_pna_metrics, mode=1, file="pna-index-comparison")

    #---
    # Teleconnections
    #---

    # Load the data of the variables of interest
    ace2_precip = load_ace2_1940_2022("PRATEsfc")["PRATEsfc"]
    ace2_tmp2m = load_ace2_1940_2022("TMP2m")["TMP2m"]  
    ace2_windspeed = load_ace2_1940_2022("WINDSPEED_10m")["WINDSPEED_10m"]

    # Preprocess variables to seasonal means
    ace2_tmp2m_seasonal = preprocess_variable_for_teleconnection(ace2_tmp2m)
    ace2_precip_seasonal = preprocess_variable_for_teleconnection(ace2_precip)
    ace2_windspeed_seasonal = preprocess_variable_for_teleconnection(ace2_windspeed)

    # Get NAO and PNA PC score
    ace2_nao_score = ace2_nao_metrics["principal_components"].sel(mode=nao_mode)
    ace2_pna_score = ace2_pna_metrics["principal_components"].sel(mode=pna_mode)

    # Compute teleconnections to NAO and PNA
    corr_tmp2m_nao = compute_teleconnection(ace2_nao_score, ace2_tmp2m_seasonal)
    corr_precip_nao = compute_teleconnection(ace2_nao_score, ace2_precip_seasonal)
    corr_windspeed_nao = compute_teleconnection(ace2_nao_score, ace2_windspeed_seasonal)
    nao_teleconnections = {
        "TMP2m": corr_tmp2m_nao,
        "PRATEsfc": corr_precip_nao,
        "WINDSPEED": corr_windspeed_nao
    }

    corr_tmp2m_pna = compute_teleconnection(ace2_pna_score, ace2_tmp2m_seasonal)
    corr_precip_pna = compute_teleconnection(ace2_pna_score, ace2_precip_seasonal)
    corr_windspeed_pna = compute_teleconnection(ace2_pna_score, ace2_windspeed_seasonal)
    pna_teleconnections = {
        "TMP2m": corr_tmp2m_pna,
        "PRATEsfc": corr_precip_pna,
        "WINDSPEED": corr_windspeed_pna
    }

    # Visualize teleconnections
    # modes_and_teleconnections(
    #     ace2_pca_metrics=ace2_nao_metrics,
    #     era5_pca_metrics=era5_nao_metrics,
    #     corr_vars=nao_teleconnections,
    #     mode=nao_mode,
    #     climate_mode="NAO",
    #     file="nao_modes_and_teleconnections"
    # )
    modes_and_teleconnections(
        ace2_pca_metrics=ace2_pna_metrics,
        era5_pca_metrics=era5_pna_metrics,
        corr_vars=pna_teleconnections,
        mode=pna_mode,
        climate_mode="PNA",
        file="pna_modes_and_teleconnections",
        cbar_ax_kwargs={"cbar_ax_top": [0.125, 0.55, 0.35, 0.015]}, # [left, bottom, width, height]
        loading_projection=ccrs.EqualEarth(central_longitude=180),
    )

#%% Run
if __name__ == "__main__":
    main()


def nao_pna_relationship():
    """Computes the NAO and PNA indices based on monthly anomalies in 1941-2022. 
    Constructs a 21y running window and computes the correlation between the NAO and PNA index for ERA5 and ACE2.
    """
    #---
    # Load pressure data
    #---
    ace2_pressfc = load_ace2_1940_2022("PRESsfc")["PRESsfc"]
    era5_pressfc = xr.open_dataset("/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ERA5/1D/PRESsfc_day_1941-2022.nc")["sp"]

    # Convert from Pa to hPa
    ace2_pressfc = ace2_pressfc / 100.0
    era5_pressfc = era5_pressfc / 100.0

    # Compute monthly means
    ace2_pressfc_monthly = ace2_pressfc.resample(time="1M").mean()
    era5_pressfc_monthly = era5_pressfc.resample(time="1M").mean()

    # Compute Monthly Anomalies (remove seasonal cycle)
    ace2_pressfc_anom = ace2_pressfc_monthly.groupby("time.month") - ace2_pressfc_monthly.groupby("time.month").mean(dim="time")
    era5_pressfc_anom = era5_pressfc_monthly.groupby("time.month") - era5_pressfc_monthly.groupby("time.month").mean(dim="time")

    #---
    # Compute PNA & NAO Index
    #---
    ace2_nao_metrics = compute_nao_index_monthly(ace2_pressfc_anom)
    era5_nao_metrics = compute_nao_index_monthly(era5_pressfc_anom)

    ace2_pna_metrics = compute_pna_index_monthly(ace2_pressfc_anom)
    era5_pna_metrics = compute_pna_index_monthly(era5_pressfc_anom)
    #ace2_pna_index_old = xr.open_dataset("/work/gg0304/g260230/projects/ACE2_VS_ERA5/output/climate_modes/pna_index_ace2.nc")

    #---
    # Plot Loadings of PNA for first three modes along with explained variance
    #---
    # n_modes = 5
    # projection = ccrs.EqualEarth(central_longitude=180) # ccrs.LambertConformal()
    # fig, axes = plt.subplots(n_modes, 2, figsize=(32, 18), subplot_kw={'projection': projection})
    # for i, mode in enumerate(range(1, n_modes + 1)):
    #     # ACE2
    #     ace2_pna_metrics["loadings"].sel(mode=mode).plot.contourf(
    #         ax=axes[i, 1], 
    #         transform=ccrs.PlateCarree(), 
    #         cmap="coolwarm", 
    #         levels=20,
    #         add_colorbar=True
    #     )
    #     axes[i, 1].coastlines()
    #     axes[i, 1].gridlines(draw_labels=True)
    #     explained_variance = ace2_pna_metrics["explained_variance_ratio"].sel(mode=mode).values * 100
    #     axes[i, 1].set_title(f"ACE2 Mode {mode} | Explained Variance: {explained_variance:.2f}%")

    #     # ERA5
    #     era5_pna_metrics["loadings"].sel(mode=mode).plot.contourf(
    #         ax=axes[i, 0], 
    #         transform=ccrs.PlateCarree(), 
    #         cmap="coolwarm", 
    #         levels=20,
    #         add_colorbar=True
    #     )
    #     axes[i, 0].coastlines()
    #     axes[i, 0].gridlines(draw_labels=True)
    #     explained_variance = era5_pna_metrics["explained_variance_ratio"].sel(mode=mode).values * 100
    #     axes[i, 0].set_title(f"ERA5 PNA Mode {mode} | Explained Variance: {explained_variance:.2f}%")
    # plt.tight_layout()

    #---
    # NAO-PNA Relationship
    #---
    # Select NAO and PNA indices (PC scores) for mode 1
    ace2_nao_index = ace2_nao_metrics["principal_components"].sel(mode=1)
    ace2_pna_index = ace2_pna_metrics["principal_components"].sel(mode=1)
    era5_nao_index = era5_nao_metrics["principal_components"].sel(mode=1)
    era5_pna_index = era5_pna_metrics["principal_components"].sel(mode=1)

    # # Save Indices
    # def clean_attrs_for_netcdf(ds):
    #     """Remove or convert attributes that can't be serialized to NetCDF"""
    #     ds_clean = ds.copy()
    #     for attr in list(ds_clean.attrs.keys()):
    #         val = ds_clean.attrs[attr]
    #         # Remove complex types
    #         if isinstance(val, (dict, list, tuple)) and not isinstance(val, (str, bytes)):
    #             del ds_clean.attrs[attr]
    #     return ds_clean
    
    # output_dir = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed"
    # clean_attrs_for_netcdf(ace2_nao_index).to_netcdf(f"{output_dir}/ace2_nao_index_monthly_anom.nc")
    # clean_attrs_for_netcdf(ace2_pna_index).to_netcdf(f"{output_dir}/ace2_pna_index_monthly_anom.nc")
    # clean_attrs_for_netcdf(era5_nao_index).to_netcdf(f"{output_dir}/era5_nao_index_monthly_anom.nc")
    # clean_attrs_for_netcdf(era5_pna_index).to_netcdf(f"{output_dir}/era5_pna_index_monthly_anom.nc")

    # # Visualize indices
    # fig, ax = plt.subplots(figsize=(10, 5))
    # # ace2_nao_index.plot(ax=ax, label="ACE2 NAO", linewidth=1.5)
    # # ace2_pna_index.plot(ax=ax, label="ACE2 PNA", linewidth=1.5)
    # era5_nao_index.plot(ax=ax, label="ERA5 NAO", linewidth=1.5)
    # era5_pna_index.plot(ax=ax, label="ERA5 PNA", linewidth=1.5)
    # ax.set_xlabel("Months")
    # ax.set_ylabel("PC Score (normalized)")
    # ax.set_title("NAO (Mode 1) and PNA (Mode 3) Indices")
    # ax.legend(loc='upper right')

    # # Visualize the loading of PNA
    # fig, ax = plt.subplots(figsize=(10, 5), subplot_kw={'projection': ccrs.LambertConformal()})
    # ace2_pna_metrics["loadings"].sel(mode=2).plot.contourf(
    #     ax=ax, 
    #     transform=ccrs.PlateCarree(), 
    #     cmap="coolwarm", 
    #     levels=20,
    #     add_colorbar=True
    # )
    # ax.coastlines()
    # ax.gridlines(draw_labels=True)

    # Compute running correlation with a 21y window
    # 1. Turn the rolling windows into a new dimension named 'window'
    window_years = 21
    window = window_years * 12 # Monthly res
    center = True
    
    # 1. Turn rolling windows into a new dimension
    era5_nao_roll = era5_nao_index.rolling(time=window, min_periods=window, center=center).construct("window")
    era5_pna_roll = era5_pna_index.rolling(time=window, min_periods=window, center=center).construct("window")

    ace2_nao_roll = ace2_nao_index.rolling(time=window, min_periods=window, center=center).construct("window")
    ace2_pna_roll = ace2_pna_index.rolling(time=window, min_periods=window, center=center).construct("window")

    # 2. Mask out windows that contain any NaNs (forces full window requirement)
    era5_nao_roll = era5_nao_roll.where(era5_nao_roll.notnull().sum(dim="window") == window)
    era5_pna_roll = era5_pna_roll.where(era5_pna_roll.notnull().sum(dim="window") == window)

    ace2_nao_roll = ace2_nao_roll.where(ace2_nao_roll.notnull().sum(dim="window") == window)
    ace2_pna_roll = ace2_pna_roll.where(ace2_pna_roll.notnull().sum(dim="window") == window)

    # 3. Compute running correlation
    corr_era5 = xr.corr(era5_nao_roll, era5_pna_roll, dim="window")
    corr_ace2 = xr.corr(ace2_nao_roll, ace2_pna_roll, dim="window")

    # Visualizze running correlation
    fig, ax = plt.subplots(figsize=(10, 5))
    corr_ace2.plot(ax=ax, label="ACE2 NAO-PNA Running Corr", linewidth=1.5)
    corr_era5.plot(ax=ax, label="ERA5 NAO-PNA Running Corr", linewidth=1.5)
    ax.set_xlabel("Months")
    ax.set_ylabel("Running Correlation (21y window)")
    ax.set_title("Running Correlation between NAO and PNA Indices")
    ax.legend(loc='upper right')


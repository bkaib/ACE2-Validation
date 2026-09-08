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

def plot_percentiles():
    p = "/work/gg0304/g260230/projects/ACE2_VS_ERA5/output/percentiles/era5_windspeed_95_seas.nc"
    era5_windspeed_percentiles = xr.open_dataset(p)

    p = "/work/gg0304/g260230/projects/ACE2_VS_ERA5/output/percentiles/ace2_windspeed_95_seas.nc"
    ace2_windspeed_percentiles = xr.open_dataset(p)

    seasons = ["DJF", "JJA"]

    vmax = np.ceil(20)  # Auf nächste ganze Zahl aufrunden (z.B. 18.4 -> 19 oder 20)
    vmin = 0

    # Stufen für die Contour-Plot-Farben (z.B. alle 1 m/s)
    levels = np.linspace(vmin, vmax, 21) 

    # Runde Ticks für die Colorbar (z.B. alle 2 oder 5 m/s)
    ticks = np.arange(vmin, vmax + 1, 5) 

    fig, axes = plt.subplots(
        nrows=2, ncols=2, 
        figsize=(14, 8), 
        subplot_kw={'projection': ccrs.PlateCarree()},
        layout="constrained"
    )

    for i, season in enumerate(seasons):
        # --- Column 0 (ERA5) ---
        ax0 = axes[i, 0]
        era5_windspeed_percentiles.sel(season=season).ws.plot.contourf(
            ax=ax0, transform=ccrs.PlateCarree(), cmap="viridis", 
            levels=levels, vmin=vmin, vmax=vmax, add_colorbar=False,
            add_labels=False
        )
        ax0.coastlines()
        
        ax0.text(-0.15, 0.5, season, transform=ax0.transAxes, 
                fontsize=20, va='center', ha='right', rotation='horizontal')
        
        gl0 = ax0.gridlines(draw_labels=True)
        gl0.right_labels = False
        if i == 0:
            ax0.set_title("ERA5", fontsize=20, pad=10)
            gl0.bottom_labels = False
        if i == 1:
            gl0.top_labels = False

        # --- Column 1 (ACE2) ---
        ax1 = axes[i, 1]
        im = ace2_windspeed_percentiles.sel(season=season).WINDSPEED_10m.plot.contourf(
            ax=ax1, transform=ccrs.PlateCarree(), cmap="viridis", 
            levels=levels, vmin=vmin, vmax=vmax, add_colorbar=False,
            add_labels=False
        )
        ax1.coastlines()
        
        gl1 = ax1.gridlines(draw_labels=True)
        gl1.left_labels = False
        if i == 0:
            ax1.set_title("ACE2", fontsize=20, pad=10)
            gl1.bottom_labels = False
        if i == 1:
            gl1.top_labels = False

    # --- 2. Colorbar mit expliziten Ticks ---
    cbar = fig.colorbar(
        im, 
        ax=axes, 
        orientation="horizontal", 
        label="m/s", 
        shrink=0.5,
        aspect=35,
        pad=0.04,
        ticks=ticks,  # 👈 Hier die runden Ticks erzwingen
    )
    cbar.ax.tick_params(which='both', labelsize=12) 
    cbar.ax.minorticks_off()  # 👈 Entfernt alle unbeschrifteten Zwischen-Ticks
    cbar.set_label("m/s", fontsize=12)

    fig.savefig("/work/gg0304/g260230/projects/ACE2-Validation/results/figures/07-percentiles/compare_percentiles.png", dpi=300)


# %% Main
def main():
    pass

# %% Run Main
if __name__ == "__main__":
    main()
# %% Modules
import logging
import sys
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
from libraries.own_libraries import visualisation as vis
import numpy as np
import pandas as pd

#%% Fucntions

#%% Create artificial climate data of dims (time, lat, lon)
time = pd.date_range("2001-01-01", "2010-12-31", freq="D")
lat = np.linspace(-90, 90, 180)
lon = np.linspace(-180, 180, 360)
data = np.random.rand(len(time), len(lat), len(lon)) * 30 + 273.15  # Random temperature data in Kelvin
ensemble = xr.Dataset(
    {
        "TMP2m": (("time", "lat", "lon"), data)
    },
    coords={
        "time": time,
        "lat": lat,
        "lon": lon
    }
)

print(type(ensemble["TMP2m"].name))

# ## Compute grid-weighted monthly mean
# weights = np.cos(np.deg2rad(ensemble.lat))
# time_dim = "time"
# lat_dim = "lat"
# weighted_temp = ensemble["TMP2m"] * xr.DataArray(weights, dims="lat")
# monthly_mean = (
#     weighted_temp
#     .groupby("time.month")
#     .mean(dim="time")
#     .compute()
# )


# %% Load ensemble data

# print("Loading ensemble data...")
# ensemble = xr.open_dataset("data/raw/ace2-ensembles/2000v1940/ensemble_0.nc")
# # print("Computing temporal mean...")
# # data = ensemble["10si"].mean(dim="time").compute()

# # print("Plot temporal mean of 10m wind speed...")
# # fig, ax = vis.world_map(
# #     data=data,
# #     title="Mean 10m Wind Speed (2001-2010) - Ensemble 0",
# #     cbar_label="m/s",
# #     cmap="viridis",
# # )


# # fig.tight_layout()
# # output_path = "results/figures/tmp/mean_10m_wind_speed_ensemble_0.png"
# # fig.savefig(output_path, dpi=300)
# # print(f"Saved figure to {output_path}")

# # Compute Monthly Mean of 10m Wind Speed
# print("Computing monthly mean of 10m wind speed...")
# monthly_mean = ensemble["10si"].groupby("time.month").mean(dim="time").compute()

# ## Plot monthly mean of 10m wind speed for January
# # print("Plotting monthly mean of 10m wind speed for January...")
# # fig, ax = vis.world_map(
# #     data=monthly_mean.sel(month=1),
# #     title="Monthly Mean 10m Wind Speed (January) - Ensemble 0",
# #     cbar_label="m/s",
# #     cmap="viridis",
# # )   

# # ## Save figure to figures/tmp
# # fig.tight_layout()
# # output_path = "results/figures/tmp/monthly_mean_10m_wind_speed_january_ensemble_0.png"
# # fig.savefig(output_path, dpi=300)
# # print(f"Saved figure to {output_path}")

# ## Create a plot with all months in one figure
# print("Plotting monthly mean of 10m wind speed for all months...")
# fig, axes = plt.subplots(3, 4, figsize=(15, 12), subplot_kw={'projection': ccrs.EqualEarth()})
# axes = axes.flatten()
# im = None
# for month in range(1, 13):
#     ax = axes[month-1]
#     monthly_data = monthly_mean.sel(month=month)
#     im = ax.contourf(monthly_data.lon, monthly_data.lat, monthly_data, cmap="viridis", transform=ccrs.PlateCarree())

#     ## Add coastlines and gridlines
#     ax.coastlines()
#     ax.gridlines(draw_labels=True)  
#     ax.set_title(f"Month: {month}")

# ## Add shared colorbar
# cbar_ax = fig.add_axes([0.2, 0.08, 0.6, 0.02])
# plt.colorbar(im, cax=cbar_ax, label="m/s", orientation="horizontal")
# fig.suptitle("Monthly Mean 10m Wind Speed (2001-2010) | Ensemble 0 v1940", fontsize=16)

# ## Save figure to figures/tmp
# fig.tight_layout()
# output_path = "results/figures/tmp/monthly_mean_10m_wind_speed_all_months_ensemble_0.png"
# fig.savefig(output_path, dpi=300)
# print(f"Saved figure to {output_path}")
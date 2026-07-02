"""Regrid the ERA5 data to the ACE2 grid using xESMF.

This script regrids ERA5 data at 0.25° resolution to ACE2's 1° grid using
conservative regridding. This method is essential for precipitation (mass conservation)
and appropriate for temperature extremes.

Input:  data/raw/ERA5/1D/{10si,PRATEsfc,TMP2m}/
Output: data/processed/ERA5/1D/ACE2GRID/{10si,PRATEsfc,TMP2m}/
"""

#%% Modules
import logging
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation")  # Ensure project root is in path
from pathlib import Path
import xarray as xr
import xesmf as xe
from config import project_logging
import warnings


# Setup logging
logger = logging.getLogger(__name__)
filename = Path(__file__).stem

filename = "scratch_log"

logger = project_logging.setup_logger(filename)

# Define paths
PROJECT_ROOT = "/work/gg0304/g260230/projects/ACE2-Validation"
BASE_INPUT = Path(PROJECT_ROOT) / "data/raw/ERA5/1D"
BASE_OUTPUT = Path(PROJECT_ROOT) / "data/processed/ERA5/1D/ACE2GRID"
ACE2_SAMPLE = Path(PROJECT_ROOT) / "data/raw/ace2-ensembles/1D/2000v1979/ensemble_0.nc"


# Load target grid
ace2_grid = xr.open_dataset(ACE2_SAMPLE)
ace2_grid = ace2_grid["tasmax"].isel(time=0)  # Use the first time step to get the grid
logger.info(f"Target grid dimensions: {ace2_grid.dims}")
logger.info(f"""Target grid lon/lat range:
            lon({ace2_grid.lon.min().values}, {ace2_grid.lon.max().values}),
            lat({ace2_grid.lat.min().values}, {ace2_grid.lat.max().values})"""
            )
# Loop over all ERA5 datasets
for variable in ["PRATEsfc", "TMP2m"]: # "10si"
    input_path = BASE_INPUT / variable
    output_path = BASE_OUTPUT / variable
    output_path.mkdir(parents=True, exist_ok=True)

    for file in input_path.glob("*.nc"):
        logger.info(f"Processing {file.name} for variable {variable}")

        # Load ERA5 data
        ds_era5 = xr.open_dataset(file)
        data_var = list(ds_era5.data_vars)[0]  # Assuming the first variable is the one to regrid

        # Create regridder
        logger.info(f"Dimensions of ERA5 data: {ds_era5.dims}")
        logger.info(f"""Lon/lat range of ERA5 data:
                    lon({ds_era5.lon.min().values}, {ds_era5.lon.max().values}),
                    lat({ds_era5.lat.min().values}, {ds_era5.lat.max().values})"""
                    )
        regridder = xe.Regridder(ds_era5, ace2_grid, "conservative", periodic=False)
        
        # Regrid the data
        logger.info(f"Regridding variable: {data_var}")
        ds_regridded = regridder(ds_era5[data_var], keep_attrs=True)
        logger.info(f"Regridding complete for {file.name}.")
        logger.info(ds_regridded)
        
        # Save the regridded dataset
        output_file = output_path / file.name
        ds_regridded.to_netcdf(output_file)
        logger.info(f"Saved regridded data to {output_file}")
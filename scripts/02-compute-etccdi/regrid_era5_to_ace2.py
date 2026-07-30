"""Regrid ERA5 data to ACE2 grid using xESMF with parallel processing.

This script regrids ERA5 data at 0.25° resolution to ACE2's 1° grid
using conservative regridding, parallelized across multiple workers.
Processes multiple variables sequentially, with files within each variable parallelized.

Input:  data/raw/ERA5/1D/{10si,TMP2m,PRATEsfc}/
Output: data/processed/ERA5/1D/ACE2GRID/{10si,TMP2m,PRATEsfc}/
"""

#%% Modules
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation")
from pathlib import Path
import xarray as xr
import xesmf as xe
from dask import delayed, compute, config as dask_config
from config.project_logging import setup_parallel_logger
import warnings

#%% Setup Logger
logger, queue_listener = setup_parallel_logger("regrid-era5-to-ace2-parallel", use_queue_listener=True)

#%% Constants
# Define paths
PROJECT_ROOT = "/work/gg0304/g260230/projects/ACE2-Validation"
BASE_INPUT = Path(PROJECT_ROOT) / "data/raw/ERA5/1D"
BASE_OUTPUT = Path(PROJECT_ROOT) / "data/processed/ERA5/1D/ACE2GRID"
ACE2_SAMPLE = Path(PROJECT_ROOT) / "data/raw/ace2-ensembles/1D/2000v1979/ensemble_0.nc"

#%% Main
def regrid_era5_file(file_path, target_grid, output_dir):
    """Regrid a single ERA5 file to ACE2 grid.
    
    Parameters
    ----------
    file_path : Path
        Path to the ERA5 NetCDF file
    target_grid : xr.DataArray
        Target grid (1D array with lon/lat coords)
    output_dir : Path
        Directory to save regridded output
        
    Returns
    -------
    tuple
        (file_name, success: bool)
    """
    # if not "2004" in file_path.name:
    #     logger.warning(f"Skipping file: {file_path.name}")
        
    #     return file_path.name, False
    
    try:
        logger.info(f"Starting regridding for {file_path.name}")
        
        # Load ERA5 data
        ds_era5 = xr.open_dataset(file_path)
        data_var = list(ds_era5.data_vars)[0]  # Assuming the first variable is the one to regrid
        
        logger.info(f"Loaded {file_path.name}: variable={data_var}, dims={ds_era5.dims}")
        
        # Create regridder
        regridder = xe.Regridder(ds_era5, target_grid, "conservative", periodic=False)
        
        # Regrid the data
        logger.info(f"Regridding variable: {data_var}")
        ds_regridded = regridder(ds_era5[data_var], keep_attrs=True)
        logger.info(f"Regridding complete for {file_path.name}")
        
        # Save the regridded dataset
        output_file = output_dir / file_path.name
        output_dir.mkdir(parents=True, exist_ok=True)
        ds_regridded.to_netcdf(output_file)
        logger.info(f"Saved regridded data to {output_file}")
        
        return file_path.name, True
        
    except Exception as e:
        logger.error(f"Failed regridding {file_path.name}: {e}", exc_info=True)
        return file_path.name, False


def main():
    """Main function to parallelize regridding of ERA5 files for multiple variables."""
    # Variables to process
    variables = [
        #"10si", 
        #"TMP2m", 
        "PRATEsfc",
        ]
    
    # Load target grid
    logger.info(f"Loading target ACE2 grid from {ACE2_SAMPLE}")
    ace2_ds = xr.open_dataset(ACE2_SAMPLE)
    target_grid = ace2_ds["tasmax"].isel(time=0).drop_vars("time", errors="ignore")  # Use the first time step to get the grid
    logger.info(f"Target grid dimensions: {target_grid.dims}")
    logger.info(f"""Target grid lon/lat range:
                lon({target_grid.lon.min().values}, {target_grid.lon.max().values}),
                lat({target_grid.lat.min().values}, {target_grid.lat.max().values})""")
    
    # Configure Dask for HPC environment
    n_workers = 10  # Increase if memory permits; decrease if you hit memory limits
    dask_config.set(scheduler='processes', num_workers=n_workers)
    logger.info(f"Starting parallel regridding with {n_workers} workers")
    
    # Process each variable sequentially
    for variable in variables:
        logger.info(f"\n=== Processing variable: {variable} ===")
        
        input_dir = BASE_INPUT / variable
        output_dir = BASE_OUTPUT / variable
        
        # Find all ERA5 files for this variable
        if not input_dir.exists():
            logger.warning(f"Input directory does not exist: {input_dir}")
            continue
        
        era5_files = sorted(input_dir.glob("*.nc"))
        logger.info(f"Found {len(era5_files)} ERA5 files for {variable}")
        
        if len(era5_files) == 0:
            logger.warning(f"No NetCDF files found in {input_dir}")
            continue
        
        # Create delayed tasks for each file in this variable
        delayed_tasks = [
            delayed(regrid_era5_file)(file_path, target_grid, output_dir)
            for file_path in era5_files
        ]
        
        # Compute all tasks in parallel
        results = compute(*delayed_tasks)
        
        # Report per-variable results
        successful = [file_name for file_name, success in results if success]
        failed = [file_name for file_name, success in results if not success]
        
        logger.info(f"Variable {variable}: {len(successful)} successful, {len(failed)} failed")
        if failed:
            logger.warning(f"Failed files for {variable}: {failed}")
    
    logger.info("\n=== Regridding complete ===")


if __name__ == "__main__":
    main()

# %%

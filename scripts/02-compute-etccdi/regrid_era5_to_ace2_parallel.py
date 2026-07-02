"""Regrid ERA5 10si data to ACE2 grid using xESMF with parallel processing.

This script regrids ERA5 10m wind speed (10si) data at 0.25° resolution to ACE2's 1° grid
using conservative regridding, parallelized across multiple workers.

Input:  data/raw/ERA5/1D/10si/
Output: data/processed/ERA5/1D/ACE2GRID/10si/
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

# Define paths
PROJECT_ROOT = "/work/gg0304/g260230/projects/ACE2-Validation"
BASE_INPUT = Path(PROJECT_ROOT) / "data/raw/ERA5/1D/10si"
BASE_OUTPUT = Path(PROJECT_ROOT) / "data/processed/ERA5/1D/ACE2GRID/10si"
ACE2_SAMPLE = Path(PROJECT_ROOT) / "data/raw/ace2-ensembles/1D/2000v1979/ensemble_0.nc"


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
    """Main function to parallelize regridding of all ERA5 10si files."""
    # Load target grid
    logger.info(f"Loading target ACE2 grid from {ACE2_SAMPLE}")
    ace2_ds = xr.open_dataset(ACE2_SAMPLE)
    target_grid = ace2_ds["tasmax"].isel(time=0)  # Use the first time step to get the grid
    logger.info(f"Target grid dimensions: {target_grid.dims}")
    logger.info(f"""Target grid lon/lat range:
                lon({target_grid.lon.min().values}, {target_grid.lon.max().values}),
                lat({target_grid.lat.min().values}, {target_grid.lat.max().values})""")
    
    # Find all ERA5 files
    if not BASE_INPUT.exists():
        logger.error(f"Input directory does not exist: {BASE_INPUT}")
        return
    
    era5_files = sorted(BASE_INPUT.glob("*.nc"))
    logger.info(f"Found {len(era5_files)} ERA5 files to process")
    
    if len(era5_files) == 0:
        logger.warning(f"No NetCDF files found in {BASE_INPUT}")
        return
    
    # Configure Dask for HPC environment
    n_workers = 10  # Increase if memory permits; decrease if you hit memory limits
    dask_config.set(scheduler='processes', num_workers=n_workers)
    logger.info(f"Starting parallel regridding with {n_workers} workers")
    
    # Create delayed tasks for each file
    delayed_tasks = [
        delayed(regrid_era5_file)(file_path, target_grid, BASE_OUTPUT)
        for file_path in era5_files
    ]
    
    # Compute all tasks in parallel
    results = compute(*delayed_tasks)
    
    # Report results
    successful = [file_name for file_name, success in results if success]
    failed = [file_name for file_name, success in results if not success]
    
    logger.info(f"Regridding complete: {len(successful)} successful, {len(failed)} failed")
    if failed:
        logger.warning(f"Failed files: {failed}")


if __name__ == "__main__":
    main()

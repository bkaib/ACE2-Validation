#%% Modules
import xarray as xr
import logging
import sys
from pathlib import Path
from datetime import datetime
from tqdm import tqdm

#%% Functions
def setup_logging(script_name, project_root):
    """
    Set up logging to both file and console.
    
    Parameters:
    -----------
    script_name : str
        Name of the script (without .py extension)
    project_root : Path
        Root directory of the project
    
    Returns:
    --------
    logger : logging.Logger
        Configured logger instance
    log_file : Path
        Path to the log file
    """
    # Create logs directory
    logs_dir = project_root / "logs" / script_name
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate timestamp for log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = logs_dir / f"{timestamp}.log"
    
    # Create logger
    logger = logging.getLogger(script_name)
    logger.setLevel(logging.DEBUG)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # File handler (DEBUG level - most verbose)
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # Console handler (INFO level - less verbose)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    logger.info(f"Logging initialized. Log file: {log_file}")
    
    return logger, log_file


def aggregate_6h_to_daily(input_path, output_path, logger):
    """
    Aggregate 6-hourly netCDF data to daily values for ETCCDI computation.
    
    Produces standard ETCCDI variable names:
    - tasmax: Daily maximum temperature (for TXx, TX90p, WSDI)
    - tasmin: Daily minimum temperature (for TNn, TN10p, WSDI)
    - pr: Daily total precipitation (for R10, Rx1day, CWD)
    - sfcWind_mean: Daily mean wind speed (for FG95p, WSD)
    - sfcWind_max: Daily maximum wind gust (for FXx)
    
    Parameters:
    -----------
    input_path : str or Path
        Path to input 6-hourly netCDF file
    output_path : str or Path
        Path to output daily netCDF file
    logger : logging.Logger
        Logger instance for recording progress
    """
    try:
        logger.debug(f"Starting aggregation of {input_path}")
        
        # Open the 6-hourly dataset
        ds = xr.open_dataset(input_path)
        logger.debug(f"Successfully loaded {input_path}: shape={dict(ds.dims)}, variables={list(ds.data_vars)}")
        
        # Determine the time dimension name (could be 'time', 'Time', etc.)
        time_dim = None
        for dim in ds.dims:
            if 'time' in dim.lower():
                time_dim = dim
                break
        
        if time_dim is None:
            error_msg = f"Could not find time dimension in {input_path}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.debug(f"Identified time dimension: {time_dim}")
        
        # Initialize empty dataset for daily values
        daily_vars = {}
        
        # Process each variable with appropriate aggregation
        for var_name in ds.data_vars:
            var_lower = var_name.lower()
            
            # Temperature variables: TMP2m → tasmax and tasmin
            if var_name == 'TMP2m' or any(temp_name in var_lower for temp_name in ['tas', 't2m', 'temp', 'temperature']):
                logger.debug(f"Processing temperature variable: {var_name} → tasmax, tasmin")
                # Daily maximum temperature (tasmax)
                daily_vars['tasmax'] = ds[var_name].resample({time_dim: '1D'}).max()
                daily_vars['tasmax'].attrs = ds[var_name].attrs.copy()
                daily_vars['tasmax'].attrs['standard_name'] = 'air_temperature'
                daily_vars['tasmax'].attrs['long_name'] = 'Daily maximum near-surface air temperature'
                daily_vars['tasmax'].attrs['aggregation'] = 'maximum'
                daily_vars['tasmax'].attrs['cell_methods'] = f'{time_dim}: maximum'
                daily_vars['tasmax'].attrs['source_variable'] = var_name
                
                # Daily minimum temperature (tasmin)
                daily_vars['tasmin'] = ds[var_name].resample({time_dim: '1D'}).min()
                daily_vars['tasmin'].attrs = ds[var_name].attrs.copy()
                daily_vars['tasmin'].attrs['standard_name'] = 'air_temperature'
                daily_vars['tasmin'].attrs['long_name'] = 'Daily minimum near-surface air temperature'
                daily_vars['tasmin'].attrs['aggregation'] = 'minimum'
                daily_vars['tasmin'].attrs['cell_methods'] = f'{time_dim}: minimum'
                daily_vars['tasmin'].attrs['source_variable'] = var_name
            
            # Precipitation variables: PRATEsfc → pr (sum of rates)
            elif var_name == 'PRATEsfc' or any(precip_name in var_lower for precip_name in ['pr', 'precip', 'tp', 'rain', 'prate']):
                logger.debug(f"Processing precipitation variable: {var_name} → pr")
                daily_vars['pr'] = ds[var_name].resample({time_dim: '1D'}).sum()
                daily_vars['pr'].attrs = ds[var_name].attrs.copy()
                daily_vars['pr'].attrs['standard_name'] = 'precipitation_amount'
                daily_vars['pr'].attrs['long_name'] = 'Daily total precipitation'
                daily_vars['pr'].attrs['aggregation'] = 'sum'
                daily_vars['pr'].attrs['cell_methods'] = f'{time_dim}: sum'
                daily_vars['pr'].attrs['source_variable'] = var_name
            
            # Wind variables: 10si → sfcWind_mean and sfcWind_max
            elif var_name == '10si' or any(wind_name in var_lower for wind_name in ['wind', 'ws', 'sfcwind', 'uas', 'vas', 'u10', 'v10', 'fg', 'gust']):
                logger.debug(f"Processing wind variable: {var_name} → sfcWind_mean, sfcWind_max")
                # Daily mean wind speed (for FG95p, WSD)
                daily_vars['sfcWind_mean'] = ds[var_name].resample({time_dim: '1D'}).mean()
                daily_vars['sfcWind_mean'].attrs = ds[var_name].attrs.copy()
                daily_vars['sfcWind_mean'].attrs['standard_name'] = 'wind_speed'
                daily_vars['sfcWind_mean'].attrs['long_name'] = 'Daily mean near-surface wind speed'
                daily_vars['sfcWind_mean'].attrs['aggregation'] = 'mean'
                daily_vars['sfcWind_mean'].attrs['cell_methods'] = f'{time_dim}: mean'
                daily_vars['sfcWind_mean'].attrs['source_variable'] = var_name
                
                # Daily maximum wind gust (for FXx)
                daily_vars['sfcWind_max'] = ds[var_name].resample({time_dim: '1D'}).max()
                daily_vars['sfcWind_max'].attrs = ds[var_name].attrs.copy()
                daily_vars['sfcWind_max'].attrs['standard_name'] = 'wind_speed_of_gust'
                daily_vars['sfcWind_max'].attrs['long_name'] = 'Daily maximum near-surface wind gust'
                daily_vars['sfcWind_max'].attrs['aggregation'] = 'maximum'
                daily_vars['sfcWind_max'].attrs['cell_methods'] = f'{time_dim}: maximum'
                daily_vars['sfcWind_max'].attrs['source_variable'] = var_name
        
        logger.debug(f"Generated {len(daily_vars)} daily variables: {list(daily_vars.keys())}")
        
        # Create new dataset with daily variables
        ds_daily = xr.Dataset(daily_vars, coords=ds.coords)
        
        # Copy over dimension coordinates that were resampled
        for coord in ds.coords:
            if coord != time_dim and coord not in ds_daily.coords:
                ds_daily.coords[coord] = ds.coords[coord]
        
        # Add global attributes to track the processing
        ds_daily.attrs = ds.attrs.copy()
        ds_daily.attrs['temporal_resolution'] = 'daily'
        ds_daily.attrs['source_resolution'] = '6-hourly'
        ds_daily.attrs['processing_note'] = 'Aggregated for ETCCDI computation: tasmax, tasmin, pr, sfcWind_mean, sfcWind_max'
        ds_daily.attrs['etccdi_variables'] = 'tasmax (TXx, TX90p, WSDI), tasmin (TNn, TN10p), pr (R10, Rx1day, CWD), sfcWind_mean (FG95p, WSD), sfcWind_max (FXx)'
        
        # Create output directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save to netCDF
        ds_daily = ds_daily.dropna(dim=time_dim, how='all')  # Drop any days with all NaNs
        ds_daily.to_netcdf(output_path)
        logger.debug(f"Successfully saved aggregated data to {output_path}")
        
        ds.close()
        ds_daily.close()
        logger.debug(f"Completed aggregation of {input_path}")
        
        return output_path
    
    except Exception as e:
        logger.error(f"Error aggregating {input_path}: {str(e)}", exc_info=True)
        raise

def process_all_ensembles(input_base_dir, output_base_dir, logger):
    """
    Process all ensemble files from 6H to daily aggregation.
    
    Parameters:
    -----------
    input_base_dir : str or Path
        Base directory containing 6-hourly data (e.g., data/raw/ace2-ensembles/6H)
    output_base_dir : str or Path
        Base directory for daily data output (e.g., data/raw/ace2-ensembles/1D)
    logger : logging.Logger
        Logger instance for recording progress
    """
    input_base = Path(input_base_dir)
    output_base = Path(output_base_dir)
    
    # Find all .nc files in the input directory
    nc_files = list(input_base.rglob('*.nc'))
    
    if not nc_files:
        error_msg = f"No .nc files found in {input_base}"
        logger.error(error_msg)
        return
    
    logger.info(f"Found {len(nc_files)} netCDF files to process")
    logger.info(f"Input directory:  {input_base}")
    logger.info(f"Output directory: {output_base}")
    
    # Track statistics
    successful = 0
    skipped = 0
    failed = 0
    
    # Process each file
    for input_file in tqdm(nc_files, desc="Processing ensembles"):
        # Compute relative path from input base
        rel_path = input_file.relative_to(input_base)
        
        # Create corresponding output path
        output_file = output_base / rel_path
        
        # Skip if output already exists (optional - remove this check to overwrite)
        if output_file.exists():
            logger.info(f"Skipping {rel_path} (already exists)")
            skipped += 1
            continue
        
        try:
            # Aggregate 6H to daily
            aggregate_6h_to_daily(input_file, output_file, logger)
            logger.info(f"✓ Processed: {rel_path}")
            successful += 1
        except Exception as e:
            logger.error(f"✗ Error processing {rel_path}: {str(e)}")
            failed += 1
            continue
    
    # Summary statistics
    logger.info("="*60)
    logger.info("Processing Summary:")
    logger.info(f"  Total files:     {len(nc_files)}")
    logger.info(f"  Successful:      {successful}")
    logger.info(f"  Skipped:         {skipped}")
    logger.info(f"  Failed:          {failed}")
    logger.info("="*60)

#%% Main run
if __name__ == "__main__":
    # Define paths
    project_root = Path(__file__).parent.parent.parent
    script_name = Path(__file__).stem
    
    # Setup logging
    logger, log_file = setup_logging(script_name, project_root)
    
    # Define input/output directories
    input_dir = project_root / "data" / "raw" / "ace2-ensembles" / "6H"
    output_dir = project_root / "data" / "raw" / "ace2-ensembles" / "1D"
    
    logger.info("="*60)
    logger.info("ACE2 Ensemble Data: 6-hourly to Daily Aggregation")
    logger.info("="*60)
    logger.info(f"Input directory:  {input_dir}")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Log file:         {log_file}")
    logger.info("="*60)
    
    # Check if input directory exists
    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        exit(1)
    
    try:
        # Process all ensemble files
        process_all_ensembles(input_dir, output_dir, logger)
        
        logger.info("\n" + "="*60)
        logger.info("Processing complete!")
        logger.info("="*60)
    except Exception as e:
        logger.error(f"Fatal error during processing: {str(e)}", exc_info=True)
        exit(1)
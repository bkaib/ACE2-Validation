#%% Modules
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
from config import constants
from config.project_logging import setup_parallel_logger
from dask import delayed, compute, config as dask_config
import xarray as xr
import xclim.indices as xci
import glob
#%% Setup Logger
logger, queue_listener = setup_parallel_logger("compute_etccdis_non_ai", use_queue_listener=True)


#%% Loading functions

def load_era5():
    ## Load Tasmax
    era5_tasmax_files = glob.glob(
        "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/TMP2m/daily_max_*.nc"
        )
    era5_tasmax = xr.open_mfdataset(era5_tasmax_files, combine="by_coords",)
    era5_tasmax = era5_tasmax["tasmax"]
    logger.info(f"Loaded ERA5 tasmax data with shape: {era5_tasmax.shape} and time range: {era5_tasmax.time.min().values} to {era5_tasmax.time.max().values}")

    ## Load Tasmin
    era5_tasmin_files = glob.glob(
        "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/TMP2m/daily_min_*.nc"
        )
    era5_tasmin = xr.open_mfdataset(era5_tasmin_files, combine="by_coords",)
    era5_tasmin = era5_tasmin["tasmin"]
    logger.info(f"Loaded ERA5 tasmin data with shape: {era5_tasmin.shape} and time range: {era5_tasmin.time.min().values} to {era5_tasmin.time.max().values}")
    
    ## Load Prate
    era5_prate_files = glob.glob(
        "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/PRATEsfc/daily_sum_*.nc"
        )
    era5_prate = xr.open_mfdataset(era5_prate_files, combine="by_coords",)
    era5_prate = era5_prate["prate"] * 1000.0  # Convert from m to mm
    era5_prate.attrs["units"] = "1 mm/d"
    logger.info(f"Loaded ERA5 prate data with shape: {era5_prate.shape} and time range: {era5_prate.time.min().values} to {era5_prate.time.max().values}")
    logger.info(f"ERA5 prate multiplied by 1000 to convert from m to mm. New units: {era5_prate.attrs['units']}")

    ## Load SfcWind_max
    era5_sfcWind_max_files = glob.glob(
        "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/10si/daily_max_*.nc"
        )
    era5_sfcWind_max = xr.open_mfdataset(era5_sfcWind_max_files, combine="by_coords",)
    era5_sfcWind_max = era5_sfcWind_max["10si_max"]
    logger.info(f"Loaded ERA5 sfcWind_max data with shape: {era5_sfcWind_max.shape} and time range: {era5_sfcWind_max.time.min().values} to {era5_sfcWind_max.time.max().values}")

    # ## Load sfcWind_mean for FG95p computation
    # era5_sfcWind_mean_files = glob.glob(
    #     "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/10si/daily_mean_*.nc"
    # )
    # era5_sfcWind_mean = xr.open_mfdataset(era5_sfcWind_mean_files, combine="by_coords",)
    # era5_sfcWind_mean = era5_sfcWind_mean["10si_mean"]
    # logger.info(f"Loaded ERA5 sfcWind_mean data with shape: {era5_sfcWind_mean.shape} and time range: {era5_sfcWind_mean.time.min().values} to {era5_sfcWind_mean.time.max().values}")

    return era5_tasmax, era5_tasmin, era5_prate, era5_sfcWind_max,
#%% Functions for absolute indices
def compute_TXx(tasmax: xr.DataArray):
    TXx = tasmax.resample(time='YE').max(dim='time')
    TXx.name = 'TXx'
    return TXx

def compute_TNn(tasmin: xr.DataArray):
    TNn = tasmin.resample(time='YE').min(dim='time')
    TNn.name = 'TNn'
    return TNn

def compute_ETR(TXx, TNn):
    ETR = TXx - TNn
    ETR.name = 'ETR'
    return ETR

def compute_Rx1day(pr: xr.DataArray):
    Rx1day = pr.resample(time='YE').max(dim='time')
    Rx1day.name = 'Rx1day'
    return Rx1day

def compute_R10(pr: xr.DataArray):
    R10 = (pr >= 10).resample(time='YS').sum(dim='time')
    R10.name = 'R10'
    return R10

def compute_CWD(pr: xr.DataArray):
    cwd = xci.maximum_consecutive_wet_days(pr, thresh="1 mm/d", freq="YS")
    cwd.name = 'CWD'
    return cwd

def compute_FXx(sfcWind_max: xr.DataArray):
    FXx = sfcWind_max.resample(time='YE').max(dim='time')
    FXx.name = 'FXx'
    return FXx

def compute_WSD(sfcWind_max: xr.DataArray, thresh=20):
    # Use the CWD logic to compute the number of consecutive days with 
    # maximum wind speeds above a certain threshold.
    # Rename the variable to match the expected input for xclim's function
    sfcWind_max.attrs["units"] = "1 mm/d" # Needs to be mm/d even though is wind speed because the xclim logic expects it.
    WSD = xci.maximum_consecutive_wet_days(sfcWind_max, thresh=f"{thresh} mm/d", freq="YS") # needs to be mm/d even though is wind speed because the logic expects it.
    WSD.name = 'WSD'

    return WSD

def compute_absolute_indices_era5():
    # Load ERA5 data
    ## Load Tasmax
    era5_tasmax_files = glob.glob(
        "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/TMP2m/daily_max_*.nc"
        )
    era5_tasmax = xr.open_mfdataset(era5_tasmax_files, combine="by_coords",)
    era5_tasmax = era5_tasmax["tasmax"]

    ## Load Tasmin
    era5_tasmin_files = glob.glob(
        "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/TMP2m/daily_min_*.nc"
        )
    era5_tasmin = xr.open_mfdataset(era5_tasmin_files, combine="by_coords",)
    era5_tasmin = era5_tasmin["tasmin"]

    ## Load Prate
    era5_prate_files = glob.glob(
        "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/PRATEsfc/daily_sum_*.nc"
        )
    era5_prate = xr.open_mfdataset(era5_prate_files, combine="by_coords",)
    era5_prate = era5_prate["prate"] * 1000.0  # Convert from m to mm
    era5_prate.attrs["units"] = "1 mm/d"

    ## Load SfcWind_max
    era5_sfcWind_max_files = glob.glob(
        "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/10si/daily_max_*.nc"
        )
    era5_sfcWind_max = xr.open_mfdataset(era5_sfcWind_max_files, combine="by_coords",)
    era5_sfcWind_max = era5_sfcWind_max["10si_max"]

    # Compute absolute indices
    TXx = compute_TXx(era5_tasmax)
    TNn = compute_TNn(era5_tasmin)
    ETR = compute_ETR(TXx, TNn)
    Rx1day = compute_Rx1day(era5_prate)
    R10 = compute_R10(era5_prate)
    CWD = compute_CWD(era5_prate)
    FXx = compute_FXx(era5_sfcWind_max)
    WSD = compute_WSD(era5_sfcWind_max, thresh=20)

    # Save indices
    file = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/TXx_1981-2010.nc"
    TXx.to_netcdf(file)
    logger.info(f"Saved TXx to {file}")

    file = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/TNn_1981-2010.nc"
    TNn.to_netcdf(file)
    logger.info(f"Saved TNn to {file}")

    file = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/ETR_1981-2010.nc"
    ETR.to_netcdf(file)
    logger.info(f"Saved ETR to {file}")

    file = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/Rx1day_1981-2010.nc"
    Rx1day.to_netcdf(file)
    logger.info(f"Saved Rx1day to {file}")

    file = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/R10_1981-2010.nc"
    R10.to_netcdf(file)
    logger.info(f"Saved R10 to {file}")

    file = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/CWD_1981-2010.nc"
    CWD.to_netcdf(file)
    logger.info(f"Saved CWD to {file}")

    file = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/FXx_1981-2010.nc"
    FXx.to_netcdf(file)
    logger.info(f"Saved FXx to {file}")

    file = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/WSD_1981-2010.nc"
    WSD.to_netcdf(file)
    logger.info(f"Saved WSD to {file}")


def process_single_ensemble_member(ensemble_folder, ensemble_num):
    """Process a single ensemble member and compute all absolute indices."""
    import os
    
    base_path = "/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ace2-ensembles/1D"
    output_base_path = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2"
    
    try:
        logger.info(f"Starting processing for {ensemble_folder}/ensemble_{ensemble_num}")
        
        ensemble_path = os.path.join(base_path, ensemble_folder)
        ensemble_file = os.path.join(ensemble_path, f"ensemble_{ensemble_num}.nc")
        
        # Load ACE2 data for this ensemble member
        ds = xr.open_dataset(ensemble_file)
        
        # Extract variables
        ace2_tasmax = ds["tasmax"]
        ace2_tasmin = ds["tasmin"]
        ace2_prate = ds["pr"] * 21600  # Convert to 1 mm/d
        ace2_prate.attrs["units"] = "1 mm/d"
        ace2_sfcWind_max = ds["sfcWind_max"]
        
        # Compute absolute indices
        TXx = compute_TXx(ace2_tasmax)
        TNn = compute_TNn(ace2_tasmin)
        ETR = compute_ETR(TXx, TNn)
        Rx1day = compute_Rx1day(ace2_prate)
        R10 = compute_R10(ace2_prate)
        CWD = compute_CWD(ace2_prate)
        FXx = compute_FXx(ace2_sfcWind_max)
        WSD = compute_WSD(ace2_sfcWind_max, thresh=20)
        
        # Create output directory if it doesn't exist
        output_dir = os.path.join(output_base_path, ensemble_folder)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save indices
        file = os.path.join(output_dir, f"TXx_ensemble_{ensemble_num}.nc")
        TXx.to_netcdf(file)
        logger.info(f"  Saved TXx to {file}")
        
        file = os.path.join(output_dir, f"TNn_ensemble_{ensemble_num}.nc")
        TNn.to_netcdf(file)
        logger.info(f"  Saved TNn to {file}")

        file = os.path.join(output_dir, f"ETR_ensemble_{ensemble_num}.nc")
        ETR.to_netcdf(file)
        logger.info(f"  Saved ETR to {file}")
        
        file = os.path.join(output_dir, f"Rx1day_ensemble_{ensemble_num}.nc")
        Rx1day.to_netcdf(file)
        logger.info(f"  Saved Rx1day to {file}")
        
        file = os.path.join(output_dir, f"R10_ensemble_{ensemble_num}.nc")
        R10.to_netcdf(file)
        logger.info(f"  Saved R10 to {file}")
        
        file = os.path.join(output_dir, f"CWD_ensemble_{ensemble_num}.nc")
        CWD.to_netcdf(file)
        logger.info(f"  Saved CWD to {file}")
        
        file = os.path.join(output_dir, f"FXx_ensemble_{ensemble_num}.nc")
        FXx.to_netcdf(file)
        logger.info(f"  Saved FXx to {file}")

        file = os.path.join(output_dir, f"WSD_ensemble_{ensemble_num}.nc")
        WSD.to_netcdf(file)
        logger.info(f"  Saved WSD to {file}")
        
        # Close the dataset
        ds.close()
        
        logger.info(f"Successfully completed processing for {ensemble_folder}/ensemble_{ensemble_num}")
        return (ensemble_folder, ensemble_num), True
        
    except Exception as e:
        logger.error(f"Failed processing {ensemble_folder}/ensemble_{ensemble_num}: {e}", exc_info=True)
        return (ensemble_folder, ensemble_num), False


def compute_absolute_indices_ace2():
    """Compute absolute indices for all ACE2 ensemble members in parallel."""
    
    # Define ensemble folders
    ensemble_folders = [
        "2000v1940",
        "2000v1950", 
        "2000v1979",
        "2000v2020"
    ]
    
    # Create list of all ensemble member tasks
    tasks = []
    for ensemble_folder in ensemble_folders:
        for ensemble_num in range(12):
            tasks.append((ensemble_folder, ensemble_num))
    
    # Configure Dask for HPC environment
    n_workers = 10  # Adjust based on available memory and CPU cores
    dask_config.set(scheduler='processes', num_workers=n_workers)
    logger.info(f"Starting parallel processing of {len(tasks)} ensemble members with {n_workers} workers")
    
    # Create delayed tasks for parallel execution
    delayed_tasks = [delayed(process_single_ensemble_member)(folder, num) for folder, num in tasks]
    
    # Compute all tasks in parallel
    results = compute(*delayed_tasks)
    
    # Report results
    successful = [(folder, num) for (folder, num), success in results if success]
    failed = [(folder, num) for (folder, num), success in results if not success]
    
    logger.info(f"Processing complete: {len(successful)} successful, {len(failed)} failed")
    if failed:
        logger.warning(f"Failed ensemble members: {failed}")
    
    logger.info("Completed computing absolute indices for all ACE2 ensemble members")

#%% Functions for relative indices

def compute_TN10p(
    _tasmin: xr.DataArray,
    _baseline_data: xr.DataArray,
    per = 10,
    window = 5,
    _bootstrap = True,
    _freq = "YS",
):
    from xclim.core.calendar import percentile_doy
    _baseline_data.time.values.shape
    
    _tasmin_per = percentile_doy(_baseline_data, per=per, window=window) 
    tn10p = (xci
     .indicators
     .atmos
     .tn10p(
         _tasmin=_tasmin,
         _tasmin_per=_tasmin_per,
         _freq=_freq, 
         _bootstrap=_bootstrap,
         )
    )
    return tn10p

def compute_TX90p(
    _tasmax: xr.DataArray,
    _baseline_data: xr.DataArray,
    per = 90,
    window = 5,
    _bootstrap = True,
    _freq = "YS",
):
    from xclim.core.calendar import percentile_doy
    _baseline_data.time.values.shape
    
    _tasmax_per = percentile_doy(_baseline_data, per=per, window=window) 
    tx90p = (xci
     .indicators
     .atmos
     .tx90p(
         _tasmax=_tasmax,
         _tasmax_per=_tasmax_per,
         _freq=_freq, 
         _bootstrap=_bootstrap,
         )
    )
    return tx90p

def compute_WSDI(
   _tasmax: xr.DataArray,
    _baseline_data: xr.DataArray,
    per = 90,
    window = 5,
    _bootstrap = True,
    _freq = "YS",
):
    from xclim.core.calendar import percentile_doy

    _tasmax_per = percentile_doy(_baseline_data, per=per, window=window)

    WSDI = (xci
            .indicators
            .icclim
            .WSDI(
                _tasmax=_tasmax, 
                _tasmax_per=_tasmax_per,
                _freq=_freq, 
                _bootstrap=_bootstrap, 
            )
    )
    return WSDI

# def compute_FG95p(
#     _sfcWind_mean: xr.DataArray,
#     _baseline_data: xr.DataArray,
#     per = 95,
#     window = 5,
#     _bootstrap = True,
#     _freq = "YS",
# ):
# TODO Check if it works
#     from xclim.core.calendar import percentile_doy

#     # Compute the daily thresholds
#     _sfcWind_mean_per = percentile_doy(_baseline_data, per=per, window=window)

#     # Count the number of days exceeding the threshold at each grid point and sum over the year
#     exceedances = (_sfcWind_mean > _sfcWind_mean_per).astype(int)
#     FG95p = exceedances.resample(time=_freq).sum()
    
#     return FG95p


def compute_relative_indices_era5():
    # Load data
    era5_tasmax, era5_tasmin, era5_prate, era5_sfcWind_max = load_era5()

    # Compute relative indices

    ## TN10p
    _baseline_data = era5_tasmin.sel(time=slice("2001-01-01", "2010-12-31")) # For computation of percentiles.
    tn10p = compute_TN10p(
        _tasmin=era5_tasmin,
        _baseline_data=_baseline_data,
        per=10,
        window=5,
        _bootstrap=True,
        _freq = "YS",
        )
    
    file = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/TN10p_1981-2010.nc"
    tn10p.to_netcdf(file)
    logger.info(f"Saved TN10p to {file}")

    ## TX90p
    _baseline_data = era5_tasmax.sel(time=slice("2001-01-01", "2010-12-31")) # For computation of percentiles.
    tx90p = compute_TX90p(
        _tasmax=era5_tasmax,
        _baseline_data=_baseline_data,
        per=90,
        window=5,
        _bootstrap=True,
        _freq = "YS",
        )
    
    file = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/TX90p_1981-2010.nc"
    tx90p.to_netcdf(file)
    logger.info(f"Saved TX90p to {file}")

    ## WSDI (Warm spell duration index)
    _baseline_data = era5_tasmax.sel(time=slice("2001-01-01", "2010-12-31")) # For computation of percentiles.
    wsdi = compute_WSDI(
        _tasmax=era5_tasmax,
        _baseline_data=_baseline_data,
        per=90,
        window=5,
        _bootstrap=True,
        _freq = "YS",
        )
    
    file = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ERA5/WSDI_1981-2010.nc"
    wsdi.to_netcdf(file)
    logger.info(f"Saved WSDI to {file}")

    ## FG95p (Days when daily mean wind speed is above the 95th percentile of the baseline period)

def comp_relative_index_sem(ensemble_folder, ensemble_num):
    """Process a single ensemble member and compute all absolute indices."""
    import os
    
    base_path = "/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ace2-ensembles/1D"
    output_base_path = "/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ETCCDI/ACE2"
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(output_base_path, ensemble_folder)
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        logger.info(f"Starting processing for {ensemble_folder}/ensemble_{ensemble_num}")
        ensemble_path = os.path.join(base_path, ensemble_folder)
        ensemble_file = os.path.join(ensemble_path, f"ensemble_{ensemble_num}.nc")
        
        # Load ACE2 data for this ensemble member
        ds = xr.open_dataset(ensemble_file)
        
        # Extract variables
        ace2_tasmax = ds["tasmax"]
        ace2_tasmin = ds["tasmin"]
        ace2_sfcWind_mean = ds["sfcWind_mean"]
 
        
        # Compute relative indices

        ## TN10p
        TN10p = compute_TN10p(
            _tasmin=ace2_tasmin,
            _baseline_data=ace2_tasmin.sel(time=slice("2001-01-01", "2010-12-31")),
            per=10,
            window=5,
            _bootstrap=True,
            _freq = "YS",
        )
        file = os.path.join(output_dir, f"TN10p_ensemble_{ensemble_num}.nc")
        TN10p.to_netcdf(file)
        logger.info(f"  Saved TN10p to {file}")        

        ## TX90p
        TX90p = compute_TX90p(
            _tasmax=ace2_tasmax,
            _baseline_data=ace2_tasmax.sel(time=slice("2001-01-01", "2010-12-31")),
            per=90,
            window=5,
            _bootstrap=True,
            _freq = "YS",
        )
        file = os.path.join(output_dir, f"TX90p_ensemble_{ensemble_num}.nc")
        TX90p.to_netcdf(file)
        logger.info(f"  Saved TX90p to {file}")


        ## WSDI
        WSDI = compute_WSDI(
            _tasmax=ace2_tasmax,
            _baseline_data=ace2_tasmax.sel(time=slice("2001-01-01", "2010-12-31")),
            per=90,
            window=5,
            _bootstrap=True,
            _freq = "YS",
        )
        file = os.path.join(output_dir, f"WSDI_ensemble_{ensemble_num}.nc")
        WSDI.to_netcdf(file)
        logger.info(f"  Saved WSDI to {file}")


        ## FG95p

        # Close the dataset
        ds.close()
        
        logger.info(f"Successfully completed processing for {ensemble_folder}/ensemble_{ensemble_num}")
        return (ensemble_folder, ensemble_num), True
        
    except Exception as e:
        logger.error(f"Failed processing {ensemble_folder}/ensemble_{ensemble_num}: {e}", exc_info=True)
        return (ensemble_folder, ensemble_num), False

def compute_relative_indices_ace2():
    # Define ensemble folders
    ensemble_folders = [
        "2000v1940",
        "2000v1950", 
        "2000v1979",
        "2000v2020"
    ]
    
    # Create list of all ensemble member tasks
    tasks = []
    for ensemble_folder in ensemble_folders:
        for ensemble_num in range(12):
            tasks.append((ensemble_folder, ensemble_num))
    
    # Configure Dask for HPC environment
    n_workers = 10  # Adjust based on available memory and CPU cores
    dask_config.set(scheduler='processes', num_workers=n_workers)
    logger.info(f"Starting parallel processing of {len(tasks)} ensemble members with {n_workers} workers")
    
    # Create delayed tasks for parallel execution
    delayed_tasks = [delayed(comp_relative_index_sem)(folder, num) for folder, num in tasks]
    
    # Compute all tasks in parallel
    results = compute(*delayed_tasks)
    
    # Report results
    successful = [(folder, num) for (folder, num), success in results if success]
    failed = [(folder, num) for (folder, num), success in results if not success]
    
    logger.info(f"Processing complete: {len(successful)} successful, {len(failed)} failed")
    if failed:
        logger.warning(f"Failed ensemble members: {failed}")
    
    logger.info("Completed computing relative indices for all ACE2 ensemble members")


#%% Main run
def main():
    # # Compute absolute indices for ERA5
    # logger.info("Computing absolute indices for ERA5...")
    # compute_absolute_indices_era5()
    
    # # Compute absolute indices for ACE2 ensembles
    # logger.info("Computing absolute indices for ACE2 ensembles...")
    # compute_absolute_indices_ace2() 

    # Compute relative indices for ERA5
    logger.info("Computing relative indices for ERA5...")
    compute_relative_indices_era5()
    logger.info("Completed computing relative indices for ERA5")

    # # Compute relative indices for ACE2 ensembles
    # logger.info("Computing relative indices for ACE2 ensembles...")
    # compute_relative_indices_ace2()
    # logger.info("Completed computing relative indices for ACE2 ensembles")



if __name__ == "__main__":
    main()

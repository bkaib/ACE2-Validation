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

import importlib
importlib.reload(constants)

#%% Setup Logger
current_filename = __file__.split("/")[-1].replace(".py", "")
logger, queue_listener = setup_parallel_logger(current_filename, use_queue_listener=True)

#%% Functions

#---
# ERA5 Loading
#---
def load_era5_sfcWindmax(start_year, end_year):
    """
    Load ERA5 data for the sfcWindmax variable and time range.
    """
    files = glob.glob(f"/work/gg0304/g260230/projects/ACE2-Validation/data/processed/ERA5/1D/ACE2GRID/10si/daily_max_*.nc")
    files.sort()
    ds = xr.open_mfdataset(files, combine="by_coords").sel(time=slice(f"{start_year}-01-01", f"{end_year}-12-31"))
    return ds

#---
# ACE2 Loading
#---
def load_ace2_ensemble_member(var_name, scenario, ensemble_number):
    """Load a single ACE2 ensemble member."""
    base_path = f"/work/gg0304/g260230/projects/ACE2-Validation/data/raw/ace2-ensembles/1D/{scenario}"
    file = os.path.join(base_path, f"ensemble_{ensemble_number}.nc")
    ds = xr.open_dataset(file)
    da = ds[var_name]
    ds = da.to_dataset(name=var_name)
    return ds

def load_ace2_ensemble(var_name, n_members=12):
    """Loads all ensemble members of the ensemble into one dataset"""
    all_scenarios_ds = []
    for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]:
        _members_ds = xr.concat(
            [load_ace2_ensemble_member(var_name, scenario, ensemble_number=i) for i in range(0, n_members)], dim="ensemble_member"
            )
        all_scenarios_ds.append(_members_ds)
    all_scenarios_ds = xr.concat(all_scenarios_ds, dim="scenario")
    return all_scenarios_ds

#---
# Autocorrelation Functions
#---
def compute_acf_1d(ts, max_lag=15, detrend=True):
    """
    Compute temporal autocorrelation function for a 1D time series.
    
    Parameters:
    -----------
    ts : array-like
        Time series data
    max_lag : int
        Maximum lag in days to compute
    detrend : bool
        Whether to detrend and standardize before computing ACF
        
    Returns:
    --------
    array of autocorrelation values for lags 0 to max_lag
    """
    ts = np.array(ts)
    
    # Remove NaNs
    ts = ts[~np.isnan(ts)]
    
    if len(ts) == 0:
        return np.full(max_lag + 1, np.nan)
    
    # Detrend and standardize
    if detrend:
        ts = ts - np.mean(ts)
        ts = ts / np.std(ts)
    
    # Compute ACF using numpy correlate
    acf = np.correlate(ts, ts, mode='full')
    acf = acf[len(acf)//2:]  # Take only positive lags
    acf = acf / acf[0]  # Normalize by lag-0
    
    return acf[:max_lag + 1]

def compute_regional_acf(ds, var_name, region_bounds, max_lag=15):
    """
    Compute ACF for a spatial region by first averaging spatially.
    
    Parameters:
    -----------
    ds : xr.Dataset
        Dataset with variable
    var_name : str
        Variable name to analyze
    region_bounds : dict
        Dictionary with 'lat' and 'lon' tuples
    max_lag : int
        Maximum lag to compute
        
    Returns:
    --------
    array of ACF values
    """
    # Select region
    lat_slice = slice(region_bounds["lat"][0], region_bounds["lat"][1])
    lon_slice = slice(region_bounds["lon"][0], region_bounds["lon"][1])
    ds_region = ds.sel(lat=lat_slice, lon=lon_slice)
    
    # Spatial average (weighted by latitude)
    weights = np.cos(np.deg2rad(ds_region.lat))
    weighted_ds = ds_region.weighted(xr.DataArray(weights, coords=[ds_region.lat], dims=['lat']))
    ts = weighted_ds.mean(dim=['lat', 'lon'])[var_name].values
    
    # Compute ACF
    acf = compute_acf_1d(ts, max_lag=max_lag)
    
    return acf

def compute_gridpoint_acf(ds, var_name, lat, lon, max_lag=15):
    """
    Compute ACF for a single gridpoint.
    
    Parameters:
    -----------
    ds : xr.Dataset
        Dataset with variable
    var_name : str
        Variable name to analyze
    lat : float
        Latitude of gridpoint
    lon : float
        Longitude of gridpoint
    max_lag : int
        Maximum lag to compute
        
    Returns:
    --------
    array of ACF values
    """
    # Select nearest gridpoint
    ds_point = ds.sel(lat=lat, lon=lon, method='nearest')
    ts = ds_point[var_name].values
    
    # Compute ACF
    acf = compute_acf_1d(ts, max_lag=max_lag)
    
    return acf

def select_representative_gridpoints(region_bounds):
    """
    Select three representative gridpoints (west, center, east) from a region.
    
    Parameters:
    -----------
    region_bounds : dict
        Dictionary with 'lat' and 'lon' tuples
        
    Returns:
    --------
    dict : Dictionary with 'west', 'center', 'east' keys containing (lat, lon) tuples
    """
    lat_min, lat_max = region_bounds["lat"]
    lon_min, lon_max = region_bounds["lon"]
    
    # Center latitude of the region
    lat_center = (lat_min + lat_max) / 2
    
    # Longitude positions: west (25%), center (50%), east (75%)
    lon_west = lon_min + 0.25 * (lon_max - lon_min)
    lon_center = (lon_min + lon_max) / 2
    lon_east = lon_min + 0.75 * (lon_max - lon_min)
    
    gridpoints = {
        'west': (lat_center, lon_west),
        'center': (lat_center, lon_center),
        'east': (lat_center, lon_east)
    }
    
    return gridpoints

def decorrelation_timescale(acf_values, threshold=1/np.e):
    """
    Find the lag where ACF drops below threshold (typically 1/e ≈ 0.37).
    Longer decorrelation time = more persistent.
    
    Parameters:
    -----------
    acf_values : array
        Array of autocorrelation values
    threshold : float
        Threshold value (default: 1/e for e-folding time)
        
    Returns:
    --------
    int : lag where ACF first drops below threshold
    """
    try:
        lag_e_fold = np.where(acf_values < threshold)[0][0]
    except IndexError:
        lag_e_fold = len(acf_values)  # Never decays below threshold
    return lag_e_fold

#---
# Ensemble Analysis
#---
def ensemble_acf_analysis(var_name='sfcWind_max', region_name='storm_track_atlantic', 
                         start_year=2001, end_year=2010, max_lag=15, n_members=12,
                         include_gridpoints=False):
    """
    Compute ACF for all 48 ensemble members and ERA5.
    Returns mean ACF and uncertainty envelope.
    
    Parameters:
    -----------
    var_name : str
        Variable name to analyze
    region_name : str
        Region name from constants.domains
    start_year : int
        Start year for analysis
    end_year : int
        End year for analysis
    max_lag : int
        Maximum lag to compute
    n_members : int
        Number of ensemble members per scenario
    include_gridpoints : bool
        Whether to compute ACF for individual gridpoints (west, center, east)
        
    Returns:
    --------
    tuple : (era5_acf, ace2_acf_mean, ace2_acf_std, all_ace2_acfs, gridpoint_data)
            where gridpoint_data is None if include_gridpoints=False, otherwise a dict
    """
    logger.info(f"Computing ACF analysis for {var_name} in {region_name}")
    logger.info(f"Period: {start_year}-{end_year}, Max lag: {max_lag} days")
    
    # Get region bounds
    region_bounds = constants.domains[region_name]
    
    # Select representative gridpoints if requested
    gridpoints = None
    if include_gridpoints:
        gridpoints = select_representative_gridpoints(region_bounds)
        logger.info(f"Selected gridpoints:")
        for position, (lat, lon) in gridpoints.items():
            logger.info(f"  {position.capitalize()}: lat={lat:.2f}°, lon={lon:.2f}°")
    
    # Load ERA5
    logger.info("Loading ERA5 data...")
    era5_data = load_era5_sfcWindmax(start_year, end_year)
    era5_var = list(era5_data.data_vars)[0]
    
    # Convert longitude to -180 to 180
    era5_data = era5_data.assign_coords(lon=(((era5_data.lon + 180) % 360) - 180)).sortby('lon')
    
    # Compute ERA5 ACF for region
    logger.info("Computing ERA5 ACF...")
    era5_acf = compute_regional_acf(era5_data, era5_var, region_bounds, max_lag)
    era5_decorr = decorrelation_timescale(era5_acf)
    logger.info(f"ERA5 decorrelation timescale (regional): {era5_decorr} days")
    
    # Compute ERA5 ACF for gridpoints if requested
    era5_gridpoint_acfs = None
    if include_gridpoints:
        logger.info("Computing ERA5 ACF for gridpoints...")
        era5_gridpoint_acfs = {}
        for position, (lat, lon) in gridpoints.items():
            acf = compute_gridpoint_acf(era5_data, era5_var, lat, lon, max_lag)
            era5_gridpoint_acfs[position] = acf
            decorr = decorrelation_timescale(acf)
            logger.info(f"  ERA5 {position} decorrelation: {decorr} days")
    
    # Load all 48 ACE2 members
    logger.info(f"Loading ACE2 ensemble ({n_members * 4} members)...")
    ace2_acfs = []
    ace2_gridpoint_acfs = {pos: [] for pos in (gridpoints.keys() if include_gridpoints else [])}
    member_count = 0
    
    for scenario in ["2000v1940", "2000v1950", "2000v1979", "2000v2020"]:
        for ens in range(n_members):
            member_count += 1
            logger.info(f"Processing member {member_count}/48: {scenario} ensemble {ens}")
            
            ace2_data = load_ace2_ensemble_member(var_name, scenario, ens)
            
            # Convert longitude to -180 to 180
            ace2_data = ace2_data.assign_coords(lon=(((ace2_data.lon + 180) % 360) - 180)).sortby('lon')
            
            # Compute ACF for this member (regional)
            ace2_acf = compute_regional_acf(ace2_data, var_name, region_bounds, max_lag)
            ace2_acfs.append(ace2_acf)
            
            # Compute ACF for gridpoints if requested
            if include_gridpoints:
                for position, (lat, lon) in gridpoints.items():
                    gridpoint_acf = compute_gridpoint_acf(ace2_data, var_name, lat, lon, max_lag)
                    ace2_gridpoint_acfs[position].append(gridpoint_acf)
    
    # Convert to array
    ace2_acfs = np.array(ace2_acfs)
    
    # Statistics across ensemble (regional)
    ace2_acf_mean = np.mean(ace2_acfs, axis=0)
    ace2_acf_std = np.std(ace2_acfs, axis=0)
    ace2_decorr_mean = np.mean([decorrelation_timescale(acf) for acf in ace2_acfs])
    ace2_decorr_std = np.std([decorrelation_timescale(acf) for acf in ace2_acfs])
    
    logger.info(f"ACE2 decorrelation timescale (regional): {ace2_decorr_mean:.1f} ± {ace2_decorr_std:.1f} days")
    logger.info(f"Difference (ACE2 - ERA5): {ace2_decorr_mean - era5_decorr:.1f} days")
    
    # Process gridpoint statistics if requested
    gridpoint_data = None
    if include_gridpoints:
        gridpoint_data = {
            'gridpoints': gridpoints,
            'era5': era5_gridpoint_acfs,
            'ace2_all': {},
            'ace2_mean': {},
            'ace2_std': {}
        }
        
        for position in gridpoints.keys():
            ace2_gp_array = np.array(ace2_gridpoint_acfs[position])
            gridpoint_data['ace2_all'][position] = ace2_gp_array
            gridpoint_data['ace2_mean'][position] = np.mean(ace2_gp_array, axis=0)
            gridpoint_data['ace2_std'][position] = np.std(ace2_gp_array, axis=0)
            
            # Log decorrelation statistics
            ace2_gp_decorr_mean = np.mean([decorrelation_timescale(acf) for acf in ace2_gp_array])
            ace2_gp_decorr_std = np.std([decorrelation_timescale(acf) for acf in ace2_gp_array])
            era5_gp_decorr = decorrelation_timescale(era5_gridpoint_acfs[position])
            logger.info(f"ACE2 decorrelation ({position}): {ace2_gp_decorr_mean:.1f} ± {ace2_gp_decorr_std:.1f} days | "
                       f"ERA5: {era5_gp_decorr} days | Diff: {ace2_gp_decorr_mean - era5_gp_decorr:.1f} days")
    
    return era5_acf, ace2_acf_mean, ace2_acf_std, ace2_acfs, gridpoint_data

#---
# Visualization
#---
def plot_acf_comparison(era5_acf, ace2_mean, ace2_std, region_name='storm_track_atlantic', 
                       var_name='sfcWind_max', output_dir=None):
    """
    Plot ACF comparison between ERA5 and ACE2 ensemble.
    
    Parameters:
    -----------
    era5_acf : array
        ERA5 autocorrelation values
    ace2_mean : array
        ACE2 ensemble mean autocorrelation
    ace2_std : array
        ACE2 ensemble standard deviation
    region_name : str
        Region name for title
    var_name : str
        Variable name for title
    output_dir : str or None
        Directory to save figure. If None, displays figure.
    """
    lags = np.arange(len(era5_acf))
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Plot ERA5
    ax.plot(lags, era5_acf, 'o-', label='ERA5', linewidth=2.5, 
            color='black', markersize=6, markerfacecolor='white', 
            markeredgewidth=2, markeredgecolor='black')
    
    # Plot ACE2 ensemble mean with uncertainty
    ax.plot(lags, ace2_mean, 's-', label='ACE2 (ensemble mean)', 
            linewidth=2.5, color='#d62728', markersize=6)
    ax.fill_between(lags, ace2_mean - ace2_std, ace2_mean + ace2_std, 
                     alpha=0.25, color='#d62728', label='ACE2 (±1σ)')
    
    # Add e-folding line
    ax.axhline(1/np.e, ls='--', color='gray', alpha=0.6, linewidth=1.5,
               label=f'e-folding threshold ({1/np.e:.3f})')
    
    # Calculate decorrelation timescales
    era5_decorr = decorrelation_timescale(era5_acf)
    ace2_decorr_mean = decorrelation_timescale(ace2_mean)
    
    # Add decorrelation timescale annotations
    ax.axvline(era5_decorr, ls=':', color='black', alpha=0.5, linewidth=1.5)
    ax.axvline(ace2_decorr_mean, ls=':', color='#d62728', alpha=0.5, linewidth=1.5)
    
    # Add text annotations for decorrelation times
    y_text = 0.15
    ax.text(era5_decorr, y_text, f'ERA5: {era5_decorr}d', 
            rotation=90, va='bottom', ha='right', fontsize=10, color='black')
    ax.text(ace2_decorr_mean, y_text, f'ACE2: {ace2_decorr_mean}d', 
            rotation=90, va='bottom', ha='left', fontsize=10, color='#d62728')
    
    # Formatting
    ax.set_xlabel('Lag (days)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Autocorrelation', fontsize=14, fontweight='bold')
    ax.set_title(f'Wind Maxima Persistence - {region_name.replace("_", " ").title()}\n'
                f'ACE2 decorrelation: {ace2_decorr_mean}d | ERA5 decorrelation: {era5_decorr}d | '
                f'Difference: +{ace2_decorr_mean - era5_decorr}d', 
                fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='upper right', framealpha=0.9)
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xlim(-0.5, len(lags) - 0.5)
    ax.set_ylim(-0.1, 1.05)
    
    # Add zero line
    ax.axhline(0, color='black', linewidth=0.8, alpha=0.3)
    
    plt.tight_layout()
    
    # Save or show
    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"acf_comparison_{var_name}_{region_name}.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        logger.info(f"Saved figure to {filepath}")
    else:
        plt.show()
    
    return fig, ax

def plot_all_members_acf(ace2_acfs, era5_acf, ace2_mean, region_name='storm_track_atlantic',
                        var_name='sfcWind_max', output_dir=None):
    """
    Plot all individual ensemble member ACFs as thin lines with ensemble mean and ERA5.
    
    Parameters:
    -----------
    ace2_acfs : array
        ACF values for all ensemble members (shape: n_members x n_lags)
    era5_acf : array
        ERA5 autocorrelation values
    ace2_mean : array
        ACE2 ensemble mean autocorrelation
    region_name : str
        Region name for title
    var_name : str
        Variable name for title
    output_dir : str or None
        Directory to save figure. If None, displays figure.
    """
    lags = np.arange(ace2_acfs.shape[1])
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    # Plot all individual members as thin gray lines
    for i, acf in enumerate(ace2_acfs):
        ax.plot(lags, acf, '-', linewidth=0.5, color='gray', alpha=0.3)
    
    # Plot ERA5
    ax.plot(lags, era5_acf, 'o-', label='ERA5', linewidth=3, 
            color='black', markersize=7, markerfacecolor='white', 
            markeredgewidth=2, markeredgecolor='black', zorder=10)
    
    # Plot ACE2 ensemble mean
    ax.plot(lags, ace2_mean, 's-', label='ACE2 (ensemble mean)', 
            linewidth=3, color='#d62728', markersize=7, zorder=10)
    
    # Add e-folding line
    ax.axhline(1/np.e, ls='--', color='gray', alpha=0.6, linewidth=1.5,
               label=f'e-folding threshold ({1/np.e:.3f})')
    
    # Formatting
    ax.set_xlabel('Lag (days)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Autocorrelation', fontsize=14, fontweight='bold')
    ax.set_title(f'Wind Maxima Persistence - All 48 Ensemble Members\n{region_name.replace("_", " ").title()}', 
                fontsize=14, fontweight='bold')
    ax.legend(fontsize=11, loc='upper right', framealpha=0.9)
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xlim(-0.5, len(lags) - 0.5)
    ax.set_ylim(-0.1, 1.05)
    
    # Add zero line
    ax.axhline(0, color='black', linewidth=0.8, alpha=0.3)
    
    plt.tight_layout()
    
    # Save or show
    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"acf_all_members_{var_name}_{region_name}.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        logger.info(f"Saved figure to {filepath}")
    else:
        plt.show()
    
    return fig, ax

def plot_acf_with_gridpoints(era5_acf, ace2_mean, ace2_std, gridpoint_data,
                            region_name='storm_track_atlantic', var_name='sfcWind_max',
                            output_dir=None):
    """
    Plot ACF comparison including regional average and three gridpoints.
    
    Parameters:
    -----------
    era5_acf : array
        ERA5 autocorrelation values (regional)
    ace2_mean : array
        ACE2 ensemble mean autocorrelation (regional)
    ace2_std : array
        ACE2 ensemble standard deviation (regional)
    gridpoint_data : dict
        Dictionary containing gridpoint ACF data
    region_name : str
        Region name for title
    var_name : str
        Variable name for title
    output_dir : str or None
        Directory to save figure. If None, displays figure.
    """
    lags = np.arange(len(era5_acf))
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'Wind Maxima Persistence - {region_name.replace("_", " ").title()}', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    # Colors for gridpoints
    gridpoint_colors = {'west': '#1f77b4', 'center': '#ff7f0e', 'east': '#2ca02c'}
    gridpoint_labels = {'west': 'West', 'center': 'Center', 'east': 'East'}
    
    # Panel 1: Regional average (top-left)
    ax = axes[0, 0]
    ax.plot(lags, era5_acf, 'o-', label='ERA5 (regional)', linewidth=2.5, 
            color='black', markersize=6, markerfacecolor='white', 
            markeredgewidth=2, markeredgecolor='black')
    ax.plot(lags, ace2_mean, 's-', label='ACE2 (regional mean)', 
            linewidth=2.5, color='#d62728', markersize=6)
    ax.fill_between(lags, ace2_mean - ace2_std, ace2_mean + ace2_std, 
                     alpha=0.25, color='#d62728', label='ACE2 (±1σ)')
    ax.axhline(1/np.e, ls='--', color='gray', alpha=0.6, linewidth=1.5,
               label=f'e-folding ({1/np.e:.3f})')
    ax.set_xlabel('Lag (days)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Autocorrelation', fontsize=12, fontweight='bold')
    ax.set_title('Regional Average', fontsize=13, fontweight='bold')
    ax.legend(fontsize=9, loc='upper right', framealpha=0.9)
    ax.grid(alpha=0.3, linestyle='--')
    ax.set_xlim(-0.5, len(lags) - 0.5)
    ax.set_ylim(-0.1, 1.05)
    ax.axhline(0, color='black', linewidth=0.8, alpha=0.3)
    
    # Panels 2-4: Individual gridpoints
    positions = ['west', 'center', 'east']
    panel_positions = [(0, 1), (1, 0), (1, 1)]
    
    for position, (row, col) in zip(positions, panel_positions):
        ax = axes[row, col]
        
        lat, lon = gridpoint_data['gridpoints'][position]
        era5_gp_acf = gridpoint_data['era5'][position]
        ace2_gp_mean = gridpoint_data['ace2_mean'][position]
        ace2_gp_std = gridpoint_data['ace2_std'][position]
        
        # Plot ERA5 and ACE2
        ax.plot(lags, era5_gp_acf, 'o-', label='ERA5', linewidth=2.5, 
                color='black', markersize=6, markerfacecolor='white', 
                markeredgewidth=2, markeredgecolor='black')
        ax.plot(lags, ace2_gp_mean, 's-', label='ACE2 (mean)', 
                linewidth=2.5, color=gridpoint_colors[position], markersize=6)
        ax.fill_between(lags, ace2_gp_mean - ace2_gp_std, ace2_gp_mean + ace2_gp_std, 
                         alpha=0.25, color=gridpoint_colors[position], label='ACE2 (±1σ)')
        ax.axhline(1/np.e, ls='--', color='gray', alpha=0.6, linewidth=1.5,
                   label=f'e-folding ({1/np.e:.3f})')
        
        # Calculate and show decorrelation times
        era5_decorr = decorrelation_timescale(era5_gp_acf)
        ace2_decorr = decorrelation_timescale(ace2_gp_mean)
        
        ax.set_xlabel('Lag (days)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Autocorrelation', fontsize=12, fontweight='bold')
        ax.set_title(f'{gridpoint_labels[position]} Gridpoint\n'
                    f'(lat={lat:.1f}°, lon={lon:.1f}°) | '
                    f'ACE2: {ace2_decorr}d, ERA5: {era5_decorr}d',
                    fontsize=12, fontweight='bold')
        ax.legend(fontsize=9, loc='upper right', framealpha=0.9)
        ax.grid(alpha=0.3, linestyle='--')
        ax.set_xlim(-0.5, len(lags) - 0.5)
        ax.set_ylim(-0.1, 1.05)
        ax.axhline(0, color='black', linewidth=0.8, alpha=0.3)
    
    plt.tight_layout()
    
    # Save or show
    if output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"acf_gridpoints_{var_name}_{region_name}.png"
        filepath = os.path.join(output_dir, filename)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        logger.info(f"Saved gridpoint figure to {filepath}")
    else:
        plt.show()
    
    return fig, axes

#%% Main Function
def main():
    """
    Main function to run the autocorrelation analysis.
    Analyzes wind persistence for storm track regions.
    """
    logger.info("="*80)
    logger.info("Starting Wind Persistence Autocorrelation Analysis")
    logger.info("="*80)
    
    # Configuration
    var_name = 'sfcWind_max'
    start_year = 2001
    end_year = 2010
    max_lag = 15
    n_members = 12
    output_dir = "/work/gg0304/g260230/projects/ACE2-Validation/results/figures/03-etccdi-validation"
    
    # Regions to analyze
    storm_track_regions = [
        'storm_track_atlantic',
        # Add more regions if defined in constants.domains:
        # 'NH_Pacific', 'SH_Atlantic', 'SH_Pacific', etc.
    ]
    
    for region_name in storm_track_regions:
        logger.info("")
        logger.info(f"Analyzing region: {region_name}")
        logger.info("-"*80)
        
        # Compute ACF analysis with gridpoints
        era5_acf, ace2_acf_mean, ace2_acf_std, ace2_acfs, gridpoint_data = ensemble_acf_analysis(
            var_name=var_name,
            region_name=region_name,
            start_year=start_year,
            end_year=end_year,
            max_lag=max_lag,
            n_members=n_members,
            include_gridpoints=True
        )
        
        # Plot comparison with uncertainty envelope (regional only)
        logger.info("Creating comparison plot with uncertainty envelope...")
        plot_acf_comparison(
            era5_acf, ace2_acf_mean, ace2_acf_std,
            region_name=region_name,
            var_name=var_name,
            output_dir=output_dir
        )
        
        # Plot all individual members (regional only)
        logger.info("Creating plot with all ensemble members...")
        plot_all_members_acf(
            ace2_acfs, era5_acf, ace2_acf_mean,
            region_name=region_name,
            var_name=var_name,
            output_dir=output_dir
        )
        
        # Plot gridpoint comparison
        if gridpoint_data is not None:
            logger.info("Creating gridpoint comparison plot...")
            plot_acf_with_gridpoints(
                era5_acf, ace2_acf_mean, ace2_acf_std, gridpoint_data,
                region_name=region_name,
                var_name=var_name,
                output_dir=output_dir
            )
        
        logger.info(f"Completed analysis for {region_name}")
        logger.info("")
    
    logger.info("="*80)
    logger.info("Autocorrelation Analysis Complete!")
    logger.info("="*80)
    
    # Close logger
    if queue_listener:
        queue_listener.stop()

#%% Run
if __name__ == "__main__":
    main()

#%% Load Modules
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
import os
import logging
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
from config import paths
import importlib
importlib.reload(paths)
import dask
from dask.diagnostics import ProgressBar
import time
import zarr
import shutil

# Configure logging
log_dir = os.path.join(paths.PROJECT_ROOT, "logs")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "validate-ace2-sim-output.log")
logging.basicConfig(
	level=logging.INFO,
	format='%(asctime)s - %(levelname)s - %(message)s',
	handlers=[
		logging.FileHandler(log_file),
		logging.StreamHandler()
	]
)
logger = logging.getLogger(__name__)

# %% Helper function to analyze dataset structure
def analyze_dataset_structure(experiment_id):
	"""Document the dataset structure for performance tuning."""
	filepath = paths.ACE2_RAW + experiment_id + "/autoregressive_predictions.nc"
	logger.info(f"Analyzing dataset structure: {filepath}")
	
	pred = xr.open_dataset(filepath, chunks="auto")
	
	logger.info(f"\n{'='*80}")
	logger.info("DATASET STRUCTURE ANALYSIS")
	logger.info(f"{'='*80}")
	logger.info(f"Dimensions: {dict(pred.dims)}")
	logger.info(f"Data variables: {list(pred.data_vars)}")
	logger.info(f"\nChunking information:")
	
	for var in pred.data_vars:
		if hasattr(pred[var].data, 'chunks'):
			logger.info(f"  {var}: chunks={pred[var].data.chunks}")
		else:
			logger.info(f"  {var}: not chunked (in-memory)")
	
	# Calculate memory footprint
	total_size_gb = pred.nbytes / (1024**3)
	per_member_size_gb = total_size_gb / pred.sample.size
	
	logger.info(f"\nMemory footprint:")
	logger.info(f"  Total dataset: {total_size_gb:.2f} GB")
	logger.info(f"  Per ensemble member: {per_member_size_gb:.2f} GB")
	logger.info(f"  Number of ensemble members: {pred.sample.size}")
	logger.info(f"{'='*80}\n")
	
	pred.close()
	return {
		'dims': dict(pred.dims),
		'total_size_gb': total_size_gb,
		'per_member_size_gb': per_member_size_gb
	}

# %% Parallelized slice function using Dask delayed
def slice_valid_time_parallel(experiment_id, 
							 start="2001-01-01", 
							 end="2010-12-31",
							 use_parallel=True):
	"""
	Slices the dataset to a given time period with parallel processing option.
	"""
	timing_log = {}

	# Load Raw Data of Simulation
	t0 = time.time()
	filepath = paths.ACE2_RAW + experiment_id + "/autoregressive_predictions.nc"
	logger.info(f"Loading raw dataset from: {filepath}...")
	pred = xr.open_dataset(filepath, chunks="auto")
	logger.info(f"Dataset loaded: {pred}")
	timing_log['load'] = time.time() - t0
	logger.info(f"⏱️  Load time: {timing_log['load']:.2f}s")

	# Slice ensemble members (parallel or sequential)
	t0 = time.time()
	n_members = pred.sample.size

	if use_parallel:
		logger.info(f"Creating delayed tasks for {n_members} ensemble members...")
		sliced_members = [
			slice_ensemble_member_delayed(pred, n, start, end) 
			for n in range(n_members)
		]
		logger.info(f"Created {len(sliced_members)} delayed tasks")
		logger.info(f"Example delayed object: {sliced_members[0]}")
	else:
		logger.info(f"Processing {n_members} ensemble members sequentially...")
		sliced_members = []
		for n_ensemble in range(n_members):
			logger.info(f"Slicing ensemble member {n_ensemble}...")
			ensemble_member = pred.isel(sample=n_ensemble)
			ensemble_member = ensemble_member.set_index(time="valid_time")
			ensemble_member = ensemble_member.sel(time=slice(start, end))
			sliced_members.append(ensemble_member)

	timing_log['slice_setup'] = time.time() - t0
	logger.info(f"⏱️  Slice setup time: {timing_log['slice_setup']:.2f}s")

	# Concatenate sliced members into a single dataset
	t0 = time.time()
	logger.info(f"Concatenating sliced ensemble members into a single dataset...")

	if use_parallel:
		# Compute delayed tasks and concatenate
		with ProgressBar():
			logger.info("Computing delayed tasks...")
			computed_members = dask.compute(*sliced_members)
		selected_period = xr.concat(computed_members, dim="sample")
	else:
		selected_period = xr.concat(sliced_members, dim="sample")

	logger.info(f"Dataset after slicing: {selected_period}")
	timing_log['concat'] = time.time() - t0
	logger.info(f"⏱️  Concat time: {timing_log['concat']:.2f}s")

	# Save new dataset
	t0 = time.time()
	start_year = start.split("-")[0]
	end_year = end.split("-")[0]
	path = paths.ACE2_RAW + experiment_id + f"/predictions_{start_year}-{end_year}.nc"
	os.makedirs(os.path.dirname(path), exist_ok=True)
	logger.info(f"Saving dataset to: {path}...")
	selected_period.to_netcdf(path)
	logger.info(f"Saved sliced dataset to: {path}")
	timing_log['save'] = time.time() - t0
	logger.info(f"⏱️  Save time: {timing_log['save']:.2f}s")

	# Log total time
	total_time = sum(timing_log.values())
	logger.info(f"⏱️  Total time: {total_time:.2f}s")
	logger.info(f"Mode: {'Parallel (Dask delayed)' if use_parallel else 'Sequential'}")

	return timing_log

# %% Helper function for parallel Zarr writes
def write_ensemble_member_zarr(dataset, n_ensemble, start, end, zarr_path, 
							   time_chunk=None, spatial_chunk=None):
	"""
	Slice and write a single ensemble member directly to Zarr store.
	"""
	# Slice the ensemble member
	ensemble_member = dataset.isel(sample=n_ensemble)
	ensemble_member = ensemble_member.set_index(time="valid_time")
	ensemble_member = ensemble_member.sel(time=slice(start, end))

	# Add sample dimension back for concatenation
	ensemble_member = ensemble_member.expand_dims(sample=[n_ensemble])

	# Configure chunking
	if time_chunk or spatial_chunk:
		chunk_dict = {}
		if time_chunk:
			chunk_dict['time'] = time_chunk
		if spatial_chunk and 'lat' in ensemble_member.dims:
			chunk_dict['lat'] = spatial_chunk
			chunk_dict['lon'] = spatial_chunk
		ensemble_member = ensemble_member.chunk(chunk_dict)

	# Write to Zarr with append mode
	mode = 'a' if n_ensemble > 0 else 'w'
	append_dim = 'sample' if n_ensemble > 0 else None

	ensemble_member.to_zarr(
		zarr_path,
		mode=mode,
		append_dim=append_dim,
		consolidated=True
	)

	return n_ensemble


# %% Parallel Zarr write implementation
def slice_valid_time_zarr(experiment_id,
						  start="2001-01-01",
						  end="2010-12-31",
						  time_chunk=30,
						  spatial_chunk=100,
						  n_workers=None):
	"""
	Slice dataset and write directly to Zarr format in parallel.
	"""
	timing_log = {}

	# Load Raw Data of Simulation
	t0 = time.time()
	filepath = paths.ACE2_RAW + experiment_id + "/autoregressive_predictions.nc"
	logger.info(f"Loading raw dataset from: {filepath}...")
	pred = xr.open_dataset(filepath, chunks="auto")
	logger.info(f"Dataset loaded: {pred}")
	timing_log['load'] = time.time() - t0
	logger.info(f"⏱️  Load time: {timing_log['load']:.2f}s")

	# Prepare Zarr output path
	start_year = start.split("-")[0]
	end_year = end.split("-")[0]
	zarr_path = paths.ACE2_RAW + experiment_id + f"/predictions_{start_year}-{end_year}.zarr"

	# Remove existing Zarr store if it exists
	if os.path.exists(zarr_path):
		logger.info(f"Removing existing Zarr store: {zarr_path}")
		shutil.rmtree(zarr_path)

	os.makedirs(os.path.dirname(zarr_path), exist_ok=True)

	# Write members (slice then write)
	t0 = time.time()
	n_members = pred.sample.size
	logger.info(f"Writing {n_members} ensemble members to Zarr...")
	for n in range(n_members):
		logger.info(f"Processing ensemble member {n+1}/{n_members}...")
		write_ensemble_member_zarr(
			pred, n, start, end, zarr_path,
			time_chunk=time_chunk,
			spatial_chunk=spatial_chunk
		)

	timing_log['write_zarr'] = time.time() - t0
	logger.info(f"⏱️  Zarr write time: {timing_log['write_zarr']:.2f}s")

	# Verify the output
	t0 = time.time()
	logger.info(f"Verifying Zarr output...")
	result = xr.open_zarr(zarr_path)
	logger.info(f"Verification complete. Dataset shape: {dict(result.dims)}")
	result.close()
	timing_log['verify'] = time.time() - t0

	total_time = sum(timing_log.values())
	logger.info(f"⏱️  Total time: {total_time:.2f}s")
	logger.info(f"Output format: Zarr")

	return timing_log

# %% Efficient concatenation with rechunking
def concat_with_rechunking(sliced_members, target_chunks=None):
	"""
	Efficiently concatenate ensemble members with optimal chunking.
	"""
	logger.info("Concatenating with efficient rechunking strategy...")

	# Compute delayed tasks if needed
	if sliced_members and hasattr(sliced_members[0], 'compute'):
		logger.info("Computing delayed tasks...")
		with ProgressBar():
			sliced_members = dask.compute(*sliced_members)

	logger.info("Performing concatenation...")
	result = xr.concat(
		sliced_members,
		dim="sample",
		coords='minimal',
		compat='override',
		data_vars='minimal'
	)

	# Rechunk if specified
	if target_chunks:
		logger.info(f"Rechunking to: {target_chunks}")
		result = result.chunk(target_chunks)

	return result


# %% Configuration validation
def validate_config(output_format, time_chunk, spatial_chunk, n_workers, memory_limit):
	"""
	Validate configuration parameters for slicing operation.
	"""
	if output_format not in ['zarr', 'netcdf']:
		raise ValueError(f"Invalid output_format: {output_format}. Must be 'zarr' or 'netcdf'")

	if time_chunk is not None and (time_chunk < 1 or time_chunk > 365):
		raise ValueError(f"Invalid time_chunk: {time_chunk}. Must be between 1 and 365")

	if spatial_chunk is not None and (spatial_chunk < 10 or spatial_chunk > 1000):
		raise ValueError(f"Invalid spatial_chunk: {spatial_chunk}. Must be between 10 and 1000")

	if n_workers is not None and n_workers < 1:
		raise ValueError(f"Invalid n_workers: {n_workers}. Must be >= 1")

	logger.info("✓ Configuration validation passed")
	return True


# %% Dask client setup
def setup_dask_client(n_workers=None, threads_per_worker=2, memory_limit='4GB'):
	"""
	Set up Dask distributed client for parallel processing.
	"""
	try:
		from dask.distributed import Client, LocalCluster
		import multiprocessing

		if n_workers is None:
			n_workers = max(1, multiprocessing.cpu_count() // 2)

		logger.info(f"Setting up Dask LocalCluster with {n_workers} workers...")
		cluster = LocalCluster(
			n_workers=n_workers,
			threads_per_worker=threads_per_worker,
			memory_limit=memory_limit,
			silence_logs=logging.ERROR
		)
		client = Client(cluster)
		logger.info(f"Dask client: {client}")
		logger.info(f"Dashboard: {client.dashboard_link}")
		return client
	except ImportError:
		logger.warning("dask.distributed not available. Falling back to single-threaded execution.")
		return None
	except Exception as e:
		logger.warning(f"Failed to setup Dask client: {e}. Falling back to single-threaded.")
		return None


# %% Complete slice function with NetCDF fallback
def slice_valid_time_complete(experiment_id,
							 start="2001-01-01",
							 end="2010-12-31",
							 output_format='zarr',
							 time_chunk=30,
							 spatial_chunk=100,
							 n_workers=None):
	"""
	Complete slice function supporting both Zarr and NetCDF output.
	"""
	if output_format == 'zarr':
		return slice_valid_time_zarr(
			experiment_id, start, end,
			time_chunk=time_chunk,
			spatial_chunk=spatial_chunk,
			n_workers=n_workers
		)

	# NetCDF path with efficient concat
	timing_log = {}

	# Load data
	t0 = time.time()
	filepath = paths.ACE2_RAW + experiment_id + "/autoregressive_predictions.nc"
	logger.info(f"Loading raw dataset from: {filepath}...")
	pred = xr.open_dataset(filepath, chunks="auto")
	timing_log['load'] = time.time() - t0
	logger.info(f"⏱️  Load time: {timing_log['load']:.2f}s")

	# Create delayed slicing tasks
	t0 = time.time()
	n_members = pred.sample.size
	logger.info(f"Creating delayed tasks for {n_members} ensemble members...")
	sliced_members = [
		slice_ensemble_member_delayed(pred, n, start, end)
		for n in range(n_members)
	]
	timing_log['setup'] = time.time() - t0

	# Efficient concatenation
	t0 = time.time()
	target_chunks = {
		'time': time_chunk,
		'sample': -1  # Don't chunk sample dimension
	}
	if 'lat' in pred.dims:
		target_chunks['lat'] = spatial_chunk
		target_chunks['lon'] = spatial_chunk

	selected_period = concat_with_rechunking(sliced_members, target_chunks)
	timing_log['concat'] = time.time() - t0
	logger.info(f"⏱️  Concat time: {timing_log['concat']:.2f}s")

	# Write to NetCDF with compression
	t0 = time.time()
	start_year = start.split("-")[0]
	end_year = end.split("-")[0]
	path = paths.ACE2_RAW + experiment_id + f"/predictions_{start_year}-{end_year}.nc"
	os.makedirs(os.path.dirname(path), exist_ok=True)

	# Configure encoding for compression
	encoding = {}
	for var in selected_period.data_vars:
		encoding[var] = {
			'zlib': True,
			'complevel': 4,
			'chunksizes': tuple([
				target_chunks.get(dim, selected_period.dims[dim])
				for dim in selected_period[var].dims
			])
		}

	logger.info(f"Saving to NetCDF with compression: {path}...")
	selected_period.to_netcdf(path, encoding=encoding)
	timing_log['save'] = time.time() - t0
	logger.info(f"⏱️  Save time: {timing_log['save']:.2f}s")

	total_time = sum(timing_log.values())
	logger.info(f"⏱️  Total time: {total_time:.2f}s")
	logger.info(f"Output format: NetCDF (optimized)")

	return timing_log

# %% Slice to 2001-2010 and save to new file
def slice_valid_time(experiment_id, 
					 start="2001-01-01", 
					 end="2010-12-31",
					 ):    
	"""Slices the dataset to a given time period based on the `valid_time` coordinate."""
	import time
	timing_log = {}
    
	# Load Raw Data of Simulation
	t0 = time.time()
	filepath = paths.ACE2_RAW + experiment_id + "/autoregressive_predictions.nc"
	logger.info(f"Loading raw dataset from: {filepath}...")
	pred = xr.open_dataset(filepath, chunks="auto")
	logger.info(f"Dataset loaded: {pred}")
	timing_log['load'] = time.time() - t0
	logger.info(f"⏱️  Load time: {timing_log['load']:.2f}s")

	# Select each ensemble member
	t0 = time.time()
	sliced_members = []
	for n_ensemble in range(pred.sample.size):

		# Slice the period
		logger.info(f"Slicing period from {start} to {end} for ensemble member {n_ensemble}...")
		ensemble_member = pred.isel(sample=n_ensemble)
		ensemble_member = ensemble_member.set_index(time="valid_time")
		ensemble_member = ensemble_member.sel(time=slice(start, end))
        
		# Add the sliced member to the list
		sliced_members.append(ensemble_member)
	timing_log['slice'] = time.time() - t0
	logger.info(f"⏱️  Slice time: {timing_log['slice']:.2f}s")

	# Concatenate sliced members into a single dataset
	t0 = time.time()
	logger.info(f"Concatenating sliced ensemble members into a single dataset...")
	selected_period = xr.concat(sliced_members, dim="sample")
	logger.info(f"Dataset after slicing: {selected_period}")
	timing_log['concat'] = time.time() - t0
	logger.info(f"⏱️  Concat time: {timing_log['concat']:.2f}s")

	# Save new dataset
	t0 = time.time()
	start_year = start.split("-")[0]
	end_year = end.split("-")[0]
	path = paths.ACE2_RAW + experiment_id + f"/predictions_{start_year}-{end_year}.nc"
	os.makedirs(os.path.dirname(path), exist_ok=True)
	logger.info(f"Saving dataset to: {path}...")
	selected_period.to_netcdf(path)
	logger.info(f"Saved sliced dataset to: {path}")
	timing_log['save'] = time.time() - t0
	logger.info(f"⏱️  Save time: {timing_log['save']:.2f}s")
    
	# Log total time and write to performance log
	total_time = sum(timing_log.values())
	logger.info(f"⏱️  Total time: {total_time:.2f}s")
    
	perf_log_path = os.path.join(paths.PROJECT_ROOT, "logs", "slice-performance-baseline.log")
	with open(perf_log_path, 'a') as f:
		f.write(f"\n{'='*80}\n")
		f.write(f"Experiment: {experiment_id}\n")
		f.write(f"Period: {start} to {end}\n")
		f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
		f.write(f"Number of ensemble members: {pred.sample.size}\n")
		for phase, duration in timing_log.items():
			f.write(f"  {phase}: {duration:.2f}s ({duration/total_time*100:.1f}%)\n")
		f.write(f"  TOTAL: {total_time:.2f}s\n")
	logger.info(f"Performance log written to: {perf_log_path}")

	return timing_log

# %% Inspect Sliced Dataset
def inspect_dataset(experiment_id):
	"""Loads the sliced dataset and prints its structure and value ranges."""
	
	# Load sliced dataset
	filepath = paths.ACE2_RAW + experiment_id + "/predictions_2001-2010.nc"
	logger.info(f"Loading sliced dataset from: {filepath}...")
	pred = xr.open_dataset(filepath, chunks="auto")
	logger.info(f"Dataset loaded for inspection: {pred}")

	# Inspect Dataset Structure
	logger.info("=" * 80)
	logger.info(f"DATASET INSPECTION: {experiment_id}")
	logger.info("=" * 80)
	logger.info("📊 Dimensions:")
	for dim, size in pred.dims.items():
		logger.info(f"  {dim}: {size}")

	logger.info("📍 Coordinates:")
	for coord in pred.coords:
		logger.info(f"  {coord}: {pred[coord].dims} | dtype: {pred[coord].dtype}")

	logger.info("🌡️  Data Variables:")
	for var in pred.data_vars:
		logger.info(f"  {var}:")
		logger.info(f"    dims: {pred[var].dims}")
		logger.info(f"    shape: {pred[var].shape}")
		logger.info(f"    dtype: {pred[var].dtype}")
		if 'units' in pred[var].attrs:
			logger.info(f"    units: {pred[var].attrs['units']}")
		if 'long_name' in pred[var].attrs:
			logger.info(f"    long_name: {pred[var].attrs['long_name']}")

	logger.info("🕐 Time Range:")
	logger.info(f"  First time step: {pred.time.values[0]}")
	logger.info(f"  Last time step:  {pred.time.values[-1]}")
	logger.info(f"  Total steps:     {len(pred.time)}")

	return None

# %% Validate variable values (e.g., check for NaNs, reasonable ranges)
def validate_physical_consistency(experiment_id):
	"""Checks for NaNs and reasonable value ranges in the dataset."""
	
	# Load predictor data
	filepath = paths.ACE2_RAW + experiment_id + "/predictions_2001-2010.nc"
	pred = xr.open_dataset(filepath, chunks="auto")

	# Declare variables
	issues = []
	logger.info("Validating physical consistency of the dataset...")

	# Check for NaNs
	for var in pred.data_vars:
		has_nan = pred[var].isnull().any().compute().values
		if has_nan:
			nan_count = pred[var].isnull().sum().compute().values
			msg = f"{var} contains {nan_count} NaN values"
			logger.warning(f"  ❌ {msg}")
			issues.append(msg)
		else:
			logger.info(f"  ✓ {var}: no NaNs")

	# Check Temporal Completeness
	
	# Check Physical Boundaries
	## TMP2m: 150 K – 370 K
	if 'TMP2m' in pred.data_vars:
		tmp_min = pred['TMP2m'].min().compute().values
		tmp_max = pred['TMP2m'].max().compute().values
		logger.info(f"  TMP2m range: {tmp_min:.2f} K to {tmp_max:.2f} K")
		if tmp_min < 150 or tmp_max > 370:
			msg = f"TMP2m out of bounds: [{tmp_min:.2f}, {tmp_max:.2f}] K (expected 150-370 K)"
			logger.warning(f"    ❌ {msg}")
			issues.append(msg)
		else:
			logger.info(f"    ✓ Within physical bounds (150-370 K)")

	## PRATEsfc: >= 0
	if 'PRATEsfc' in pred.data_vars:
		prate_min = pred['PRATEsfc'].min().compute().values
		prate_max = pred['PRATEsfc'].max().compute().values
		logger.info(f"  PRATEsfc range: {prate_min:.2e} to {prate_max:.2e} kg m⁻² s⁻¹")
		if prate_min < 0:
			msg = f"PRATEsfc negative: min = {prate_min:.2e} kg m⁻² s⁻¹"
			logger.warning(f"    ❌ {msg}")
			issues.append(msg)
		else:
			logger.info(f"    ✓ Non-negative")

	## UGRD10m, VGRD10m: |value| <= 150 m/s
	for wind_var in ['UGRD10m', 'VGRD10m']:
		if wind_var in pred.data_vars:
			wind_min = pred[wind_var].min().compute().values
			wind_max = pred[wind_var].max().compute().values
			wind_abs_max = max(abs(wind_min), abs(wind_max))
			logger.info(f"  {wind_var} range: {wind_min:.2f} to {wind_max:.2f} m s⁻¹")
			if wind_abs_max > 150:
				msg = f"{wind_var} exceeds physical limit: max |value| = {wind_abs_max:.2f} m s⁻¹ (expected <= 150)"
				logger.warning(f"    ❌ {msg}")
				issues.append(msg)
			else:
				logger.info(f"    ✓ Within physical bounds (|v| <= 150 m s⁻¹)")
	
	# Report Issues
	if not issues:
		logger.info("✅ No issues found")
	else:
		logger.warning(f"⚠️  {len(issues)} issue(s) detected")
    
	return {"exp_id": experiment_id, "issues": issues}
	
# %% Compute Statistics

## For each ensemble compute annual global mean

## Compute Ensemble Spread

## Plot the the annual global mean and spread over time

if __name__ == "__main__":
	experiment_id = "2000v1950"
		import argparse
		parser = argparse.ArgumentParser(description='Parallel slice valid_time for ACE2 predictions')
		parser.add_argument("--experiment", required=False, default='2000v1950')
		parser.add_argument("--start", default='2001-01-01')
		parser.add_argument("--end", default='2010-12-31')
		parser.add_argument("--output", choices=['zarr','netcdf'], default='zarr')
		parser.add_argument("--n-workers", type=int, default=None)
		parser.add_argument("--time-chunk", type=int, default=30)
		parser.add_argument("--spatial-chunk", type=int, default=100)
		parser.add_argument("--memory-limit", default='4GB')
		args = parser.parse_args()

		# Validate config
		validate_config(args.output, args.time_chunk, args.spatial_chunk, args.n_workers, args.memory_limit)

		# Setup Dask client if requested
		client = setup_dask_client(n_workers=args.n_workers, memory_limit=args.memory_limit)

		slice_valid_time_complete(
			args.experiment,
			start=args.start,
			end=args.end,
			output_format=args.output,
			time_chunk=args.time_chunk,
			spatial_chunk=args.spatial_chunk,
			n_workers=args.n_workers
		)

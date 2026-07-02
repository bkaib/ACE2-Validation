#%% Modules
import sys
sys.path.append("/work/gg0304/g260230/projects/ACE2-Validation/")
from config import constants
import importlib
from config.project_logging import setup_parallel_logger
from dask import delayed, compute, config as dask_config

#%% Setup Logger
logger, queue_listener = setup_parallel_logger("parallelization-example", use_queue_listener=True)


def preprocessing_function1(yyyy):
    pass

def remapping(yyyy):
    pass

def looped_main(yyyy):
    """Process a single year - wraps preprocess and remap."""
    try:
        # This is what is actually computed in each process that we loop over
        logger.info(f"Starting processing for year {yyyy}")
        preprocessing_function1(yyyy)
        remapping(yyyy)
        logger.info(f"Successfully completed processing for year {yyyy}")
        return yyyy, True
    except Exception as e:
        logger.error(f"Failed processing year {yyyy}: {e}", exc_info=True)
        return yyyy, False
    
def main():
    # Process over which to parallelize, e.g. years.
    years = range(1981, 2010 + 1)
    
    # Configure Dask for HPC environment
    n_workers = 10  # Increase if memory permits; decrease if you hit memory limits
    dask_config.set(scheduler='processes', num_workers=n_workers)
    logger.info(f"Starting parallel processing of {len(years)} years with {n_workers} workers")

    # Create a list of tasks that will be parallelized
    delayed_tasks = [delayed(looped_main)(yyyy) for yyyy in years]
    
    # Compute all tasks in parallel
    results = compute(*delayed_tasks)
    
    # Reporting results
    successful = [year for year, success in results if success]
    failed = [year for year, success in results if not success]
    
    logger.info(f"Processing complete: {len(successful)} successful, {len(failed)} failed")
    if failed:
        logger.warning(f"Failed years: {failed}")

if __name__ == "__main__":
    main()
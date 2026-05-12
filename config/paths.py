#---
# Purpose: keep track of all paths within this project and use it for
# relative linking in code.
#---

# General project paths
PROJECT_ROOT = "/work/gg0304/g260230/projects/ACE2-Validation/"
WORK_DATA = "/work/gg0304/g260230/data/"
SCRATCH = "/scratch/g/g260230/" # For intermediate files and outputs


# Raw data
ERA5_RAW = PROJECT_ROOT + "raw/ERA5/"
ACE2_RAW = PROJECT_ROOT + "raw/ACE2/"

# ACE2-ERA5 Model
# Use `sbatch start_inference' to run the ACE2-ERA5 model.
# The `inference_config.yaml' file contains the configuration for the model run, 
# including the ICs, forcing, and output paths. Make sure to update the paths in that file as well.
# The model here is symlinked. The original mode is located at /work/gg0304/g260230/model_assets/ACE2-ERA5/. 
# This is done to keep the project organized and to avoid modifying the original model files.

ACE2_MODEL = PROJECT_ROOT + "models/ACE2-ERA5/" # symlink
ACE2_FORCING = PROJECT_ROOT + "models/ACE2-ERA5/FORCING/"
ACE2_INITIAL_CONDITIONS = PROJECT_ROOT + "models/ACE2-ERA5/INITIAL/" # Original and perturbed ICs in subfolders.

# ACE2-Output
ACE2_SIMULATION_OUTPUT = SCRATCH + "ACE2-ERA5/output_directory/"


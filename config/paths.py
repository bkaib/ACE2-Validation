#---
# Purpose: keep track of all paths within this project and use it for
# relative linking in code.
#---

# General project paths
PROJECT_ROOT = "/work/gg0304/g260230/projects/ACE2-Validation/"
WORK_DATA = "/work/gg0304/g260230/data/"
SCRATCH = "/scratch/g/g260230/" # For intermediate files and outputs

#---
# DATA
#---

# Processed ETCCDI indices
ETCCDI_ERA5 = PROJECT_ROOT + "data/processed/ETCCDI/ERA5/"
ETCCDI_ACE2 = PROJECT_ROOT + "data/processed/ETCCDI/ACE2/"
ETCCDI_THRESHOLDS = PROJECT_ROOT + "data/processed/ETCCDI/THRESHOLDS/"
ACE2_ENSEMBLES_PROCESSED = PROJECT_ROOT + "data/processed/ace2-ensembles/"

# Raw data
ERA5_RAW = PROJECT_ROOT + "data/raw/ERA5/"
ACE2_RAW = PROJECT_ROOT + "data/raw/ACE2-ERA5/output_directory/"
ACE2_ENSEMBLES = PROJECT_ROOT + "data/raw/ace2-ensembles/"
# ERA5
ERA5_PARAMS = {
    49 : "10fg", # 10m wind gust
    131 : "u", # zonal wind component
    134 : "sp", # surface pressure
    165 : "10u", # 10m zonal wind speed
    166 : "10v", # 10m meridional wind speed
    167 : "2t", # 2m temperature, required for ETCCDI computation
    207 : "10si", # 10m wind speed, required for ETCCDI computation
    228 : "tp", # total precipitation, required for ETCCDI computation
    235 : "skt", # skin temperature
}

#---
# MODELS
#---

# ACE2-ERA5 Model
#---
# Use `sbatch start_inference' to run the ACE2-ERA5 model.
# The `inference_config.yaml' file contains the configuration for the model run, 
# including the ICs, forcing, and output paths. Make sure to update the paths in that file as well.
# The model here is symlinked. The original mode is located at /work/gg0304/g260230/model_assets/ACE2-ERA5/. 
# This is done to keep the project organized and to avoid modifying the original model files.

ACE2_MODEL = PROJECT_ROOT + "models/ACE2-ERA5/" # symlink
ACE2_FORCING = PROJECT_ROOT + "models/ACE2-ERA5/FORCING/"
ACE2_INITIAL_CONDITIONS = PROJECT_ROOT + "models/ACE2-ERA5/INITIAL/" # Original and perturbed ICs in subfolders.

## ACE2-Output
ACE2_SIMULATION_OUTPUT = SCRATCH + "ACE2-ERA5/output_directory/"

#---
# FIGURES
#---
FIGURES = PROJECT_ROOT + "results/figures/"
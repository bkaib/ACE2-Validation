# %% Modules
import xarray as xr

# %% Validate if the preprocessing of ICs did work.
yyyy = 2020
ic_orig = xr.open_dataset(f"models/ACE2-ERA5/INITIAL/original/ic_{yyyy}.nc")
ic_copied = xr.open_dataset(f"models/ACE2-ERA5/INITIAL/ACE2-Validation/ic_2000v{yyyy}.nc")

# Check if they are the same
print("Original IC:")
print(ic_orig)    
print("\nCopied IC:")
print(ic_copied)

# Compare data variables (excluding time coordinate)
print("\n--- Comparison ---")
for var in ic_orig.data_vars:
    if var in ic_copied.data_vars:
        orig_data = ic_orig[var].values
        copied_data = ic_copied[var].values
        is_equal = (orig_data == copied_data).all()
        print(f"{var}: {'✓ Match' if is_equal else '✗ Mismatch'}")
    else:
        print(f"{var}: ✗ Missing in copied dataset")

for var in ic_copied.data_vars:
    if var not in ic_orig.data_vars:
        print(f"{var}: ✗ Extra in copied dataset")

# %% Load ensemble data

ensemble = xr.open_dataset("/scratch/g/g260230/ACE2-ERA5/output_directory/2000v1940/autoregressive_predictions.nc")
ensemble.valid_time.values
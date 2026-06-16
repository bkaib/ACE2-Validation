import numpy as np

#-------------
# General constants
#-------------
ace2_units = {
    "TMP2m": "K",
    "PRATEsfc": "kg/m**2/s",
    "UGRD10m": "m/s",
    "VGRD10m": "m/s",
    "10si": "m/s",
}

colormaps = {
    "TMP2m": "coolwarm",
    "PRATEsfc": "Blues",
    "UGRD10m": "viridis",
    "VGRD10m": "viridis",
    "10si": "viridis",
}

era5_params = {
    "TMP2m": 167,
    "PRATEsfc": 228,
    "10si": 207,
}

#-------------
# ETCCDI related
#-------------
etccdi_baseline = np.arange(1981, 2010 + 1) # 1981-2010 is the baseline period for ETCCDI indices as defined by WMO. See https://etccdi.pacificclimate.org/list_27_indices.shtml for more details.
absolute_indices = ["TXx", "TNn", "Rx1day", "FXx",]
relative_indices = ["R10mm", "TX90p", "TN10p", "FG95p", "WSDI", "CWD"]
etccdi_indices = {
    "temperature": ["TXx", "TNn", "TX90p", "TN10p", "WSDI"],
    "precipitation": ["Rx1day", "R10mm", "CWD"],
    "wind": ["FXx", "FG95p"],
}
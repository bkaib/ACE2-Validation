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
    "TMP2m": {
        "PARAM": 167, 
        "1H": "/pool/data/ERA5/E5/sf/an/1H/167/E5sf00_1H_", 
        "filetype": "grb",
        "unit": "K",
        },
    "PRATEsfc": {
        "PARAM": 228, 
        "1H": "/pool/data/ERA5/E5/sf/fc/1H/228/E5sf12_1H_", 
        "filetype": "grb",
        "unit": "m",
        },
    "10si": {
        "PARAM": 207, 
        "1D": "/work/gg0304/g260230/data/ERA5/E5/sf/an/1D/207/E5sf00_1D_", 
        "filetype": "nc",
        "unit": "m/s",
        },
    "U10": {
        "PARAM": 165,
        "1H": "/pool/data/ERA5/E5/sf/an/1H/165/E5sf00_1H_",
    },
    "V10": {
        "PARAM": 166,
        "1H": "/pool/data/ERA5/E5/sf/an/1H/166/E5sf00_1H_"
    },
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

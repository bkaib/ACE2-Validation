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

domains = {
	"Northern Hemisphere": {"lat": (20, 90),   "lon": (-180, 180)}, 
	"North America": {"lat": (20, 80),   "lon": (-170, -50)},
	"Europe":        {"lat": (30, 75),   "lon": (-30,   40)},
	"Asia":          {"lat": (20, 75),   "lon": ( 40,  160)},
    "Southern Hemisphere": {"lat": (-90, -20), "lon": (-180, 180)},
    "storm_track_atlantic": {"lat": (40, 60), "lon": (-50, -15)},
}
#-------------
# ETCCDI related
#-------------
etccdi_baseline = np.arange(1981, 2010 + 1) # 1981-2010 is the baseline period for ETCCDI indices as defined by WMO. See https://etccdi.pacificclimate.org/list_27_indices.shtml for more details.
absolute_indices = ["TXx", "TNn", "Rx1day", "FXx",]
relative_indices = ["R10mm", "TX90p", "TN10p", "FG95p", "WSDI", "CWD"]
etccdi_indices = {
    "temperature": ["TXx", "TNn", "ETR", "TX90p", "TN10p", "WSDI"],
    "precipitation": ["Rx1day", "R10", "CWD"],
    "wind": ["FXx", "FG95p", "WSD"],
}
etccdi_cmaps = {
    "TXx": "Reds",
    "TNn": "Blues",
    "TX90p": "Reds",
    "TN10p": "Blues",
    "WSDI": "Purples",
    "Rx1day": "Blues",
    "R10": "Blues",
    "CWD": "Greens",
    "FXx": "Reds",
    "FG95p": "Purples",
}
etccdi_units = {
    "ETR": "K",
    "TXx": "K",
    "TNn": "K",
    "TX90p": "days",
    "TN10p": "days",
    "WSDI": "days",
    "Rx1day": "mm/day",
    "R10": "days",
    "CWD": "days",
    "FXx": "m/s",
    "FG95p": "days",
    "WSD": "days",
}
    
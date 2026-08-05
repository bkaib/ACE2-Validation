#!/usr/bin/env python3
"""
Visualize all domains defined in config.constants on an EqualEarth projection map.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import sys
from pathlib import Path

# Add parent directories to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.constants import domains


def plot_domains(domains, save_path=None):
    """
    Plot domains as rectangles on an EqualEarth projection.
    
    Parameters
    ----------
    domains : dict
        Dictionary of domains with lat/lon boundaries
    save_path : str, optional
        Path to save the figure
    """
    # Create figure with EqualEarth projection
    fig = plt.figure(figsize=(16, 10))
    ax = plt.axes(projection=ccrs.EqualEarth())
    
    # Add map features
    ax.add_feature(cfeature.LAND, facecolor='lightgray', alpha=0.5)
    ax.add_feature(cfeature.OCEAN, facecolor='lightblue', alpha=0.3)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
    ax.add_feature(cfeature.BORDERS, linewidth=0.3, alpha=0.5)
    ax.gridlines(draw_labels=False, linewidth=0.5, alpha=0.5, linestyle='--')
    
    # Define colors for each domain
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta', 'yellow']
    
    # Plot each domain
    legend_handles = []
    for (domain_name, bounds), color in zip(domains.items(), colors):
        lat_min, lat_max = bounds['lat']
        lon_min, lon_max = bounds['lon']
        
        # Create rectangle in PlateCarree (lat/lon) coordinates
        width = lon_max - lon_min
        height = lat_max - lat_min
        
        rect = mpatches.Rectangle(
            xy=(lon_min, lat_min),
            width=width,
            height=height,
            facecolor=color,
            edgecolor=color,
            alpha=0.3,
            linewidth=2,
            transform=ccrs.PlateCarree()
        )
        ax.add_patch(rect)
        
        # Add border for emphasis
        border = mpatches.Rectangle(
            xy=(lon_min, lat_min),
            width=width,
            height=height,
            facecolor='none',
            edgecolor=color,
            linewidth=2.5,
            transform=ccrs.PlateCarree()
        )
        ax.add_patch(border)
        
        # Create legend handle
        legend_handle = mpatches.Patch(
            facecolor=color, 
            edgecolor=color, 
            alpha=0.5, 
            label=domain_name
        )
        legend_handles.append(legend_handle)
    
    # Add legend
    ax.legend(
        handles=legend_handles, 
        loc='lower left', 
        frameon=True, 
        framealpha=0.9,
        fontsize=10
    )
    
    # Set title
    ax.set_title('ACE2 Validation Study Domains', fontsize=16, fontweight='bold', pad=20)
    
    # Set global extent
    ax.set_global()
    
    plt.tight_layout()
    
    # Save or show
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"Figure saved to {save_path}")
    else:
        plt.show()
    
    return fig, ax


if __name__ == "__main__":
    # Print domains info
    print("Visualizing the following domains:")
    print("-" * 60)
    for name, bounds in domains.items():
        lat_range = f"{bounds['lat'][0]}°N to {bounds['lat'][1]}°N"
        lon_range = f"{bounds['lon'][0]}°E to {bounds['lon'][1]}°E"
        print(f"{name:25s}: {lat_range:20s}, {lon_range}")
    print("-" * 60)
    
    # Create output directory
    output_dir = Path(__file__).parent.parent.parent / "results" / "figures" / "00-general"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Plot and save
    output_path = output_dir / "domain_visualization.png"
    plot_domains(domains, save_path=output_path)

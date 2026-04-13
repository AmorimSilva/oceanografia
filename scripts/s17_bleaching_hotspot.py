"""Script 17: Coral Bleaching Hotspot (Heat Stress)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
from config import DADOS_DIR, OUTPUT_DIR, SHAPEFILES_DIR, FIG_DPI, FIG_SIZE, add_branding
from utilities_ocean import download_OCEAN

# Download Bleaching Hotspot
date = input('Digite a data (AAAAMMDD): ')
file_name = download_OCEAN('BHS', date, DADOS_DIR)

# Region extent [lon_min, lon_max, lat_min, lat_max]
extent = [-93.0, -25.0, -60.0, 18.0]

# Open NetCDF
file_path = os.path.join(DADOS_DIR, file_name)
ds = Dataset(file_path)

data = ds.variables['hotspot'][:]
lats = ds.variables['lat'][:]
lons = ds.variables['lon'][:]

# Read time (seconds since 1981-01-01)
time_val = ds.variables['time'][0]
date_formatted = (datetime(1981, 1, 1) + timedelta(seconds=int(time_val))).strftime('%d/%m/%Y')

# Calculate lat/lon indices
latli = np.argmin(np.abs(lats - extent[2]))
latui = np.argmin(np.abs(lats - extent[3]))
lonli = np.argmin(np.abs(lons - extent[0]))
lonui = np.argmin(np.abs(lons - extent[1]))

# Extract subset (latui:latli — data stored top-to-bottom)
data_subset = data[0, latui:latli, lonli:lonui].astype(float)

# Apply ocean mask: values <= 0 become NaN
data_subset[data_subset <= 0] = np.nan

img_extent = [lons[lonli], lons[lonui], lats[latli], lats[latui]]

# Custom palette
colors = ["#ffffff", "#ffffcc", "#f7ff02", "#ff8e01", "#ef0004", "#960004"]
cmap = mcolors.LinearSegmentedColormap.from_list('hotspot', colors)

# Create figure
fig, ax = plt.subplots(figsize=FIG_SIZE,
                        subplot_kw={'projection': ccrs.PlateCarree()})

img = ax.imshow(data_subset, vmin=0, vmax=5, cmap=cmap,
                origin='upper', extent=img_extent, transform=ccrs.PlateCarree())

# Land feature
ax.add_feature(cfeature.LAND, facecolor='gray')

# Shapefile
shapefile_path = os.path.join(SHAPEFILES_DIR, 'ne_10m_admin_1_states_provinces.shp')
if os.path.exists(shapefile_path):
    reader = shpreader.Reader(shapefile_path)
    ax.add_geometries(reader.geometries(), ccrs.PlateCarree(),
                       edgecolor='gray', facecolor='none', linewidth=0.3)

ax.coastlines(resolution='50m', color='black', linewidth=0.8)
ax.add_feature(cfeature.BORDERS, edgecolor='black', linewidth=0.5)

gl = ax.gridlines(crs=ccrs.PlateCarree(), color='white', alpha=0.0,
                   linestyle='--', linewidth=0,
                   xlocs=np.arange(-180, 181, 20),
                   ylocs=np.arange(-90, 91, 10),
                   draw_labels=True)
gl.top_labels = False
gl.right_labels = False

ax.set_extent(extent, ccrs.PlateCarree())

# Vertical colorbar
plt.colorbar(img, label='Hotspot de Branqueamento (°C)', extend='max',
             orientation='horizontal', pad=0.06, fraction=0.046, aspect=35)

add_branding(fig, f'Hotspot de Branqueamento \nNOAA CRW - {date_formatted}', ax)

save_dir = os.path.join(OUTPUT_DIR, 'Branqueamento_Hotspot')
os.makedirs(save_dir, exist_ok=True)
plt.savefig(os.path.join(save_dir, f'Branqueamento_Hotspot_{date}.png'), bbox_inches='tight', dpi=FIG_DPI)
plt.show()

ds.close()
print(f'Branqueamento_Hotspot_{date}.png saved.')

"""Script 16: Coral Bleaching Alert Area"""
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

# Download Bleaching Alert Area
date = input('Digite a data (AAAAMMDD): ')
file_name = download_OCEAN('BAA', date, DADOS_DIR)

# Region extent [lon_min, lon_max, lat_min, lat_max]
extent = [-93.0, -25.0, -60.0, 18.0]

# Open NetCDF
file_path = os.path.join(DADOS_DIR, file_name)
ds = Dataset(file_path)

data = ds.variables['bleaching_alert_area'][:]
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
data_subset = data[0, latui:latli, lonli:lonui]
img_extent = [lons[lonli], lons[lonui], lats[latli], lats[latui]]

# Discrete palette
colors = ["#e5e5e5", "#feff00", "#ffaa00", "#ff0000", "#7d0000"]
bounds = [0, 1, 2, 3, 4, 5]
cmap = mcolors.ListedColormap(colors)
norm = mcolors.BoundaryNorm(bounds, cmap.N)

# Create figure
fig, ax = plt.subplots(figsize=FIG_SIZE,
                        subplot_kw={'projection': ccrs.PlateCarree()})

img = ax.imshow(data_subset, cmap=cmap, norm=norm,
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

# Colorbar with custom labels
cbar = plt.colorbar(img, orientation='horizontal', pad=0.06, fraction=0.046, aspect=35)
cbar.set_ticks([0.5, 1.5, 2.5, 3.5, 4.5])
cbar.set_ticklabels(['Sem Estresse', 'Vigilância', 'Alerta', 'Alerta Nv.1', 'Alerta Nv.2'])
cbar.ax.tick_params(labelrotation=20)

add_branding(fig, f'Alerta de Branqueamento - NOAA CRW - {date_formatted}', ax)

save_dir = os.path.join(OUTPUT_DIR, 'Branqueamento_Alerta')
os.makedirs(save_dir, exist_ok=True)
plt.savefig(os.path.join(save_dir, f'Branqueamento_Alerta_{date}.png'), bbox_inches='tight', dpi=FIG_DPI)
plt.show()

ds.close()
print(f'Branqueamento_Alerta_{date}.png saved.')

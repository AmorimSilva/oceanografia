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
import cartopy.io.img_tiles as cimgt
import cartopy.io.shapereader as shpreader
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import matplotlib.patheffects as PathEffects
from config import DADOS_DIR, OUTPUT_DIR, SHAPEFILES_DIR, FIG_DPI, add_branding
from utilities_ocean import download_OCEAN

def get_extent_for_figure(base_extent, fig_size):
    lon_min, lon_max, lat_min, lat_max = base_extent
    target_ratio = fig_size[0] / fig_size[1]
    lon_span = lon_max - lon_min
    new_lat_span = lon_span / target_ratio
    lat_center = (lat_min + lat_max) / 2
    lat_min = lat_center - (new_lat_span / 2)
    lat_max = lat_center + (new_lat_span / 2)
    return [lon_min, lon_max, lat_min, lat_max]

def add_satellite_background(ax, zoom=6):
    try:
        tiler = cimgt.GoogleTiles(style='satellite')
        ax.add_image(tiler, zoom)
    except Exception as e:
        print(f'Falha ao carregar fundo de satélite: {e}')
        ax.add_feature(cfeature.LAND, facecolor='whitesmoke')
        ax.add_feature(cfeature.OCEAN, facecolor='lightblue')

# Download Bleaching Hotspot
date = input('Digite a data (AAAAMMDD): ')
file_name = download_OCEAN('BHS', date, DADOS_DIR)

# Region extent [lon_min, lon_max, lat_min, lat_max]
base_extent = [-93.0, -25.0, -60.0, 18.0]
FIG_SIZE_INSTAGRAM = (10.8, 13.5)
extent = get_extent_for_figure(base_extent, FIG_SIZE_INSTAGRAM)

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
fig = plt.figure(figsize=FIG_SIZE_INSTAGRAM, facecolor='black')
ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], projection=ccrs.PlateCarree())
ax.set_aspect('auto')
ax.set_extent(extent, ccrs.PlateCarree())
add_satellite_background(ax, zoom=6)
ax.spines['geo'].set_visible(False)

img = ax.imshow(data_subset, vmin=0, vmax=5, cmap=cmap, zorder=3,
                origin='upper', extent=img_extent, transform=ccrs.PlateCarree())

# Shapefile
shapefile_path = os.path.join(SHAPEFILES_DIR, 'ne_10m_admin_1_states_provinces.shp')
if os.path.exists(shapefile_path):
    reader = shpreader.Reader(shapefile_path)
    ax.add_geometries(reader.geometries(), ccrs.PlateCarree(),
                       edgecolor='white', facecolor='none', linewidth=0.6, zorder=4)

ax.coastlines(resolution='50m', color='black', linewidth=0.8, zorder=4)
ax.add_feature(cfeature.BORDERS, edgecolor='black', linewidth=0.5, zorder=4)

gl = ax.gridlines(crs=ccrs.PlateCarree(), color='gray', alpha=0.5,
                   linestyle='--', linewidth=0.25,
                   xlocs=np.arange(-180, 181, 20),
                   ylocs=np.arange(-90, 91, 10),
                   draw_labels=True)
gl.top_labels = False
gl.right_labels = False
gl.left_labels = False
gl.bottom_labels = False

# Colorbar with custom labels
cax = inset_axes(ax, width='35%', height='3%', loc='lower left', bbox_to_anchor=(0.05, 0.06, 1, 1), bbox_transform=ax.transAxes, borderpad=0)
cbar = plt.colorbar(img, cax=cax, orientation='horizontal', extend='max')
cbar.set_label('Hotspot de Branqueamento (°C)', fontsize=18, color='white', fontweight='bold')
cbar.ax.xaxis.label.set_path_effects([PathEffects.withStroke(linewidth=2, foreground='black')])

cbar.ax.tick_params(labelsize=16, pad=1, colors='white')
for label in cbar.ax.xaxis.get_ticklabels():
    label.set_fontweight('bold')
    label.set_path_effects([PathEffects.withStroke(linewidth=2, foreground='black')])

cbar.outline.set_edgecolor('none')

# Título customizado
titulo = f'Hotspot de Branqueamento\nPara o dia {date_formatted}\n@samuel.meteorologia'
ax.set_title(titulo, fontsize=16, fontweight='bold', color='white', y=0.945, pad=2)

save_dir = os.path.join(OUTPUT_DIR, 'Branqueamento_Hotspot')
os.makedirs(save_dir, exist_ok=True)
output_file = os.path.join(save_dir, f'Branqueamento_Hotspot_{date}.png')
plt.savefig(output_file, dpi=FIG_DPI, facecolor=fig.get_facecolor(), edgecolor='none')
plt.close(fig)

ds.close()
print(f'Salvo: {output_file}')

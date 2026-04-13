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
import cartopy.io.img_tiles as cimgt
import cartopy.io.shapereader as shpreader
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import matplotlib.patheffects as PathEffects
from config import DADOS_DIR, OUTPUT_DIR, SHAPEFILES_DIR, FIG_DPI, add_branding
from utilities_ocean import download_OCEAN

def get_extent_for_figure(base_extent, fig_size):
    """Ajusta o recorte para preencher a figura no aspecto desejado."""
    lon_min, lon_max, lat_min, lat_max = base_extent
    target_ratio = fig_size[0] / fig_size[1]
    lon_span = lon_max - lon_min
    new_lat_span = lon_span / target_ratio
    lat_center = (lat_min + lat_max) / 2
    lat_min = lat_center - (new_lat_span / 2)
    lat_max = lat_center + (new_lat_span / 2)
    return [lon_min, lon_max, lat_min, lat_max]

def add_satellite_background(ax, zoom=6):
    """Adiciona fundo de satélite; se falhar, usa fundo simples."""
    try:
        tiler = cimgt.GoogleTiles(style='satellite')
        ax.add_image(tiler, zoom)
    except Exception as e:
        print(f'Falha ao carregar fundo de satélite: {e}')
        ax.add_feature(cfeature.LAND, facecolor='whitesmoke')
        ax.add_feature(cfeature.OCEAN, facecolor='lightblue')

# Download Bleaching Alert Area
date = input('Digite a data (AAAAMMDD): ')
file_name = download_OCEAN('BAA', date, DADOS_DIR)

# Region extent [lon_min, lon_max, lat_min, lat_max]
base_extent = [-93.0, -25.0, -60.0, 18.0]
FIG_SIZE_INSTAGRAM = (10.8, 13.5)
extent = get_extent_for_figure(base_extent, FIG_SIZE_INSTAGRAM)

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
colors = [(1, 1, 1, 0), "#feff00", "#ffaa00", "#ff0000", "#7d0000"]
bounds = [0, 1, 2, 3, 4, 5]
cmap = mcolors.ListedColormap(colors)
norm = mcolors.BoundaryNorm(bounds, cmap.N)

# Create figure
fig = plt.figure(figsize=FIG_SIZE_INSTAGRAM, facecolor='black')
ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], projection=ccrs.PlateCarree())
ax.set_aspect('auto')
ax.set_extent(extent, ccrs.PlateCarree())
add_satellite_background(ax, zoom=6)
ax.spines['geo'].set_visible(False)

# Land feature - optional, keep it semi-transparent so satellite shows through or just drop it?
# In ocean data, if we want the satellite background on land, we don't draw LAND over it!
# Wait, s16 has: ax.add_feature(cfeature.LAND, facecolor='gray')
# If we add satellite, we don't need grey LAND.
# We just draw the image.

img = ax.imshow(data_subset, cmap=cmap, norm=norm, zorder=3,
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
cax = inset_axes(ax, width='35%', height='3%', loc='upper right', borderpad=3.0)
cbar = plt.colorbar(img, cax=cax, orientation='horizontal')
cbar.set_ticks([0.5, 1.5, 2.5, 3.5, 4.5])
cbar.set_ticklabels(['Sem Estresse', 'Vigilância', 'Alerta', 'Alerta 1', 'Alerta 2'])
cbar.ax.tick_params(labelsize=16, pad=1, colors='white', labelrotation=45)
for label in cbar.ax.xaxis.get_ticklabels():
    label.set_fontweight('bold')
    label.set_path_effects([PathEffects.withStroke(linewidth=2, foreground='black')])
cbar.outline.set_edgecolor('none')

# Título customizado
titulo = f'Alerta de Branqueamento\nPara o dia {date_formatted}\n@samuel.meteorologia'
title_obj = ax.text(0.04, 0.94, titulo, fontsize=22, fontweight='bold', color='black',
                    transform=ax.transAxes, ha='left', va='top', zorder=10)
title_obj.set_path_effects([PathEffects.withStroke(linewidth=3, foreground='white')])

save_dir = os.path.join(OUTPUT_DIR, 'Branqueamento_Alerta')
os.makedirs(save_dir, exist_ok=True)
output_file = os.path.join(save_dir, f'Branqueamento_Alerta_{date}.png')
plt.savefig(output_file, dpi=FIG_DPI, facecolor=fig.get_facecolor(), edgecolor='none')
plt.close(fig)

ds.close()
print(f'Salvo: {output_file}')

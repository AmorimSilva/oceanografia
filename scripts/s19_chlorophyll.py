"""Script 19: Surface Chlorophyll"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from netCDF4 import Dataset
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt
import cartopy.io.shapereader as shpreader
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
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

# Download Chlorophyll
date = input('Digite a data (AAAAMMDD): ')
file_name = download_OCEAN('CLO', date, DADOS_DIR)

# Region extent [lon_min, lon_max, lat_min, lat_max]
base_extent = [-93.0, -25.0, -40.0, 20.0]
FIG_SIZE_INSTAGRAM = (10.8, 13.5)
extent = get_extent_for_figure(base_extent, FIG_SIZE_INSTAGRAM)

# Open NetCDF
file_path = os.path.join(DADOS_DIR, file_name)
ds = Dataset(file_path)

data = ds.variables['chlor_a'][:]
lats = ds.variables['lat'][:]
lons = ds.variables['lon'][:]

# Read time for title
time_var = ds.variables['time']
time_units = time_var.units if hasattr(time_var, 'units') else ''
from netCDF4 import num2date
date_obj = num2date(time_var[0], units=time_units)
date_formatted = date_obj.strftime('%d/%m/%Y')

# Calculate lat/lon indices
latli = np.argmin(np.abs(lats - extent[2]))
latui = np.argmin(np.abs(lats - extent[3]))
lonli = np.argmin(np.abs(lons - extent[0]))
lonui = np.argmin(np.abs(lons - extent[1]))

# Ensure correct order
if latli > latui:
    latli, latui = latui, latli

# Extract subset (latitude south-to-north: latli:latui)
data_subset = data[0, 0, latli:latui, lonli:lonui]

# Debug info
print(f"Data shape: {data_subset.shape}")
print(f"Data min: {np.nanmin(data_subset)}, max: {np.nanmax(data_subset)}")
print(f"Valid values count: {np.sum(~np.isnan(data_subset))}")

# Apply mask: invalid values or <= 0 become NaN (LogNorm requires positive values)
data_subset = np.ma.masked_where((data_subset <= 0) | (data_subset > 1000) | np.isnan(data_subset), data_subset)

# Check if we have valid data
if data_subset.mask.all() or not np.any(~data_subset.mask):
    print("AVISO: Nenhum dado válido de clorofila encontrado na região especificada.")
    print("Verifique se a data está correta ou se há cobertura de dados para esta área.")
    ds.close()
    sys.exit(1)

img_extent = [lons[lonli], lons[lonui], lats[latli], lats[latui]]

# Create figure
fig = plt.figure(figsize=FIG_SIZE_INSTAGRAM, facecolor='black')
ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], projection=ccrs.PlateCarree())
ax.set_aspect('auto')
ax.set_extent(extent, ccrs.PlateCarree())
add_satellite_background(ax, zoom=6)
ax.spines['geo'].set_visible(False)

img = ax.imshow(data_subset, norm=LogNorm(vmin=0.01, vmax=10.0), cmap='viridis', zorder=3,
                origin='lower', extent=img_extent, transform=ccrs.PlateCarree())

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
cax = inset_axes(ax, width='35%', height='3%', loc='lower right', borderpad=3.0)
cbar = plt.colorbar(img, cax=cax, orientation='horizontal')
cbar.set_label('Clorofila-a (mg/m³)', fontsize=14, color='white')
cbar.ax.tick_params(labelsize=13, pad=1, colors='white')
cbar.outline.set_edgecolor('none')

# Título customizado
titulo = f'Clorofila-a - NOAA CoastWatch\nPara o dia {date_formatted}\n@samuel.meteorologia'
ax.set_title(titulo, fontsize=16, fontweight='bold', color='white', y=0.945, pad=2)

save_dir = os.path.join(OUTPUT_DIR, 'Clorofila')
os.makedirs(save_dir, exist_ok=True)
output_file = os.path.join(save_dir, f'Clorofila_{date}.png')
plt.savefig(output_file, dpi=FIG_DPI, facecolor=fig.get_facecolor(), edgecolor='none')
plt.close(fig)

ds.close()
print(f'Salvo: {output_file}')

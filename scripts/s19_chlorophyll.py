"""Script 19: Surface Chlorophyll"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from netCDF4 import Dataset
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
from config import DADOS_DIR, OUTPUT_DIR, SHAPEFILES_DIR, FIG_DPI, FIG_SIZE, add_branding
from utilities_ocean import download_OCEAN

# Download Chlorophyll
date = input('Digite a data (AAAAMMDD): ')
file_name = download_OCEAN('CLO', date, DADOS_DIR)

# Region extent [lon_min, lon_max, lat_min, lat_max]
extent = [-93.0, -25.0, -60.0, 18.0]

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
fig, ax = plt.subplots(figsize=FIG_SIZE,
                        subplot_kw={'projection': ccrs.PlateCarree()})

img = ax.imshow(data_subset, norm=LogNorm(vmin=0.01, vmax=10.0), cmap='viridis',
                origin='lower', extent=img_extent, transform=ccrs.PlateCarree())

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
plt.colorbar(img, label='Clorofila-a (mg/m³)',
             orientation='horizontal', pad=0.06, fraction=0.046, aspect=35)

add_branding(fig, f'Clorofila-a - NOAA CoastWatch - {date_formatted}', ax)

save_dir = os.path.join(OUTPUT_DIR, 'Clorofila')
os.makedirs(save_dir, exist_ok=True)
plt.savefig(os.path.join(save_dir, f'Clorofila_{date}.png'), bbox_inches='tight', dpi=FIG_DPI)
plt.show()

ds.close()
print(f'Clorofila_{date}.png saved.')

"""Script: splot_tsm_serie_tendencia.py
Gera uma figura com a série temporal de TSM para um ponto e o mapa de tendência de TSM (7 dias), lado a lado.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
import numpy as np
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
from config import DADOS_DIR, OUTPUT_DIR, SHAPEFILES_DIR, FIG_DPI, FIG_SIZE_WIDE, add_branding
from utilities_ocean import download_OCEAN

# --- INPUTS ---
target_lat = float(input('Digite a latitude (ex: -24.0): '))
target_lon = float(input('Digite a longitude (ex: -44.0): '))
date_ini = input('Digite a data inicial (AAAAMMDD): ')
date_end = input('Digite a data final (AAAAMMDD): ')
date_trend = input('Digite a data para tendência (AAAAMMDD): ')

# --- SÉRIE TEMPORAL ---
date_loop = datetime.strptime(date_ini, '%Y%m%d')
date_end_dt = datetime.strptime(date_end, '%Y%m%d')
dates = []
sst_values = []

while date_loop <= date_end_dt:
    date_str = date_loop.strftime('%Y%m%d')
    file_name = download_OCEAN('SST', date_str, DADOS_DIR)
    file_path = os.path.join(DADOS_DIR, file_name)
    ds = Dataset(file_path)
    sst = ds.variables['analysed_sst'][:]
    lats = ds.variables['lat'][:]
    lons = ds.variables['lon'][:]
    lat_idx = np.argmin(np.abs(lats - target_lat))
    lon_idx = np.argmin(np.abs(lons - target_lon))
    sst_val = float(sst[0, lat_idx, lon_idx])
    if not np.isnan(sst_val) and sst_val > -10:
        dates.append(date_loop)
        sst_values.append(sst_val)
    ds.close()
    date_loop += timedelta(days=1)

if len(dates) == 0:
    print('Nenhum dado válido encontrado. Verifique se o ponto está no oceano.')
    sys.exit(1)

date_ini_fmt = datetime.strptime(date_ini, '%Y%m%d').strftime('%d/%m/%Y')
date_end_fmt = datetime.strptime(date_end, '%Y%m%d').strftime('%d/%m/%Y')

# --- TENDÊNCIA DE TSM (MAPA) ---
file_name_trend = download_OCEAN('SST-T', date_trend, DADOS_DIR)
file_path_trend = os.path.join(DADOS_DIR, file_name_trend)
ds_trend = Dataset(file_path_trend)
data_trend = ds_trend.variables['trend'][:]
lats_trend = ds_trend.variables['lat'][:]
lons_trend = ds_trend.variables['lon'][:]
time_val = ds_trend.variables['time'][0]
date_trend_fmt = (datetime(1981, 1, 1) + timedelta(seconds=int(time_val))).strftime('%d/%m/%Y')

# Região de interesse
extent = [-93.0, -25.0, -60.0, 18.0]
latli = np.argmin(np.abs(lats_trend - extent[2]))
latui = np.argmin(np.abs(lats_trend - extent[3]))
lonli = np.argmin(np.abs(lons_trend - extent[0]))
lonui = np.argmin(np.abs(lons_trend - extent[1]))
data_subset = data_trend[0, latui:latli, lonli:lonui]
img_extent = [lons_trend[lonli], lons_trend[lonui], lats_trend[latli], lats_trend[latui]]

# Paleta de cores para tendência
colors_trend = [
    "#640064","#6300f9","#2259d3","#0078ff","#00bdfe","#00ffff",
    "#0ba062","#ffff00","#ffbe00","#ff5000","#db0000","#950000","#640000"
]
cmap_trend = mcolors.LinearSegmentedColormap.from_list('sst_trend', colors_trend)

# --- FIGURA UNIFICADA ---
fig = plt.figure(figsize=(14, 7))

# --- Subplot 1: Série Temporal ---
ax1 = fig.add_subplot(1, 2, 1)
ax1.plot(dates, sst_values, marker='o', color='blue', linewidth=2, markersize=6)
ax1.set_xlabel('Data')
ax1.set_ylabel('TSM (°C)')
ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
ax1.set_title(f'Série Temporal de TSM\nLat {target_lat}°, Lon {target_lon}°\n({date_ini_fmt} a {date_end_fmt})')
ax1.grid(True, alpha=0.3)
fig.autofmt_xdate()

# --- Subplot 2: Tendência de TSM ---
ax2 = fig.add_subplot(1, 2, 2, projection=ccrs.PlateCarree())
img = ax2.imshow(data_subset, vmin=-3.0, vmax=3.0, cmap=cmap_trend,
                origin='upper', extent=img_extent, transform=ccrs.PlateCarree())
ax2.add_feature(cfeature.LAND, facecolor='gray')
shapefile_path = os.path.join(SHAPEFILES_DIR, 'ne_10m_admin_1_states_provinces.shp')
if os.path.exists(shapefile_path):
    reader = shpreader.Reader(shapefile_path)
    ax2.add_geometries(reader.geometries(), ccrs.PlateCarree(),
                       edgecolor='gray', facecolor='none', linewidth=0.3)
ax2.coastlines(resolution='50m', color='black', linewidth=0.8)
ax2.add_feature(cfeature.BORDERS, edgecolor='black', linewidth=0.5)
gl = ax2.gridlines(crs=ccrs.PlateCarree(), color='white', alpha=0.0,
                   linestyle='--', linewidth=0,
                   xlocs=np.arange(-180, 181, 20),
                   ylocs=np.arange(-90, 91, 10),
                   draw_labels=True)
gl.top_labels = False
gl.right_labels = False
ax2.set_extent(extent, ccrs.PlateCarree())
cbar = plt.colorbar(img, ax=ax2, label='Tendência da TSM 7 dias (°C)', extend='both',
             orientation='horizontal', pad=0.06, fraction=0.046, aspect=35)
ax2.set_title(f'Tendência da TSM (7 dias)\nNOAA CRW - {date_trend_fmt}')

# --- Branding e Salvamento ---
add_branding(fig, f'Série Temporal e Tendência de TSM', ax1)
save_dir = os.path.join(OUTPUT_DIR, 'TSM_Serie_Tendencia')
os.makedirs(save_dir, exist_ok=True)
plt.savefig(os.path.join(save_dir, f'TSM_Serie_Tendencia_{date_ini}_{date_end}_{date_trend}.png'), bbox_inches='tight', dpi=FIG_DPI)
plt.show()

ds_trend.close()
print(f'TSM_Serie_Tendencia_{date_ini}_{date_end}_{date_trend}.png saved.')

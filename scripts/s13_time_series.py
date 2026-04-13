"""Script 13: Time Series."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timedelta
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from config import DADOS_DIR, OUTPUT_DIR, FIG_DPI, FIG_SIZE_WIDE, add_branding
from utilities_ocean import download_OCEAN

# Target coordinate (user input)
target_lat = float(input('Digite a latitude (ex: -24.0): '))
target_lon = float(input('Digite a longitude (ex: -44.0): '))

# Date range
date_ini = input('Digite a data inicial (AAAAMMDD): ')
date_end = input('Digite a data final (AAAAMMDD): ')
date_loop = datetime.strptime(date_ini, '%Y%m%d')
date_end_dt = datetime.strptime(date_end, '%Y%m%d')

dates = []
sst_values = []

while date_loop <= date_end_dt:
    date_str = date_loop.strftime('%Y%m%d')

    # Download SST
    file_name = download_OCEAN('SST', date_str, DADOS_DIR)

    # Open file and read SST at the target coordinate
    file_path = os.path.join(DADOS_DIR, file_name)
    ds = Dataset(file_path)

    sst = ds.variables['analysed_sst'][:]
    lats = ds.variables['lat'][:]
    lons = ds.variables['lon'][:]

    lat_idx = np.argmin(np.abs(lats - target_lat))
    lon_idx = np.argmin(np.abs(lons - target_lon))
    sst_val = float(sst[0, lat_idx, lon_idx])

    # Only append valid ocean values
    if not np.isnan(sst_val) and sst_val > -10:
        dates.append(date_loop)
        sst_values.append(sst_val)
    else:
        print(f'  {date_str}: sem dado válido neste ponto')

    ds.close()
    date_loop += timedelta(days=1)

if len(dates) == 0:
    print('Nenhum dado válido encontrado. Verifique se o ponto está no oceano.')
    sys.exit(1)

# Format dates for title
date_ini_fmt = datetime.strptime(date_ini, '%Y%m%d').strftime('%d/%m/%Y')
date_end_fmt = datetime.strptime(date_end, '%Y%m%d').strftime('%d/%m/%Y')

# Plot time series
fig, ax = plt.subplots(figsize=FIG_SIZE_WIDE)

ax.plot(dates, sst_values, marker='o', color='blue', linewidth=2, markersize=6)

ax.set_xlabel('Data')
ax.set_ylabel('TSM (°C)')
ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
add_branding(fig, f'Série Temporal de TSM - NOAA CRW\nLat {target_lat}°, Lon {target_lon}° ({date_ini_fmt} a {date_end_fmt})', ax)
ax.grid(True, alpha=0.3)

fig.autofmt_xdate()

save_dir = os.path.join(OUTPUT_DIR, 'TSM_Serie_Temporal')
os.makedirs(save_dir, exist_ok=True)
plt.savefig(os.path.join(save_dir, f'TSM_Serie_{date_ini}_{date_end}.png'), bbox_inches='tight', dpi=FIG_DPI)
plt.show()

print(f'TSM_Serie_{date_ini}_{date_end}.png saved.')

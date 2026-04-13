"""Script 28: Satellite vs Buoy Comparison (Function)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from netCDF4 import Dataset
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.shapereader as shpreader
from config import (DADOS_DIR, OUTPUT_DIR, SHAPEFILES_DIR,
                    SST_CMAP, SST_VMIN, SST_VMAX, FIG_DPI, FIG_SIZE, add_branding)
from utilities_ocean import download_OCEAN


def compare_satellite_buoy(date_str, buoy_list):
    """Compare satellite SST with PIRATA buoy observations.

    Args:
        date_str: Date in 'YYYYMMDD' format.
        buoy_list: List of PIRATA buoy names (e.g., ['B20n38w', 'B0n35w']).

    Returns:
        List of dicts with keys: name, lat, lon, buoy_sst, sat_sst.
    """
    # --- Download satellite SST ---
    file_name = download_OCEAN('SST', date_str, DADOS_DIR)
    file_path = os.path.join(DADOS_DIR, file_name)
    ds = Dataset(file_path)

    sst = ds.variables['analysed_sst'][:]
    lats = ds.variables['lat'][:]
    lons = ds.variables['lon'][:]

    # --- Read buoy data ---
    base_url = 'http://goosbrasil.org:8080/pirata/'
    ref_date = datetime(1, 1, 1)
    year = int(date_str[0:4])
    month = int(date_str[4:6])
    day = int(date_str[6:8])
    target_date = datetime(year, month, day, 12, 0)
    delta_days = (target_date - ref_date).days + (target_date - ref_date).seconds / 86400.0

    pairs = []

    for buoy_name in buoy_list:
        url = f'{base_url}{buoy_name}.nc'
        try:
            bds = Dataset(url)
            time_var = bds.variables['time'][:]
            idx = np.argmin(np.abs(time_var - delta_days))
            buoy_temp = float(bds.variables['temperature'][idx, 0])
            blat = float(bds.variables['latitude'][0])
            blon = float(bds.variables['longitude'][0])
            bds.close()

            if np.isnan(buoy_temp) or buoy_temp < -100:
                continue

            # Extract satellite SST at buoy location
            lat_idx = np.argmin(np.abs(lats - blat))
            lon_idx = np.argmin(np.abs(lons - blon))
            sat_temp = float(sst[0, lat_idx, lon_idx])

            if np.isnan(sat_temp) or sat_temp < -10:
                continue

            pairs.append({
                'name': buoy_name,
                'lat': blat,
                'lon': blon,
                'buoy_sst': buoy_temp,
                'sat_sst': sat_temp,
            })
            print(f'{buoy_name}: buoy={buoy_temp:.2f} °C, sat={sat_temp:.2f} °C')

        except Exception as e:
            print(f'{buoy_name}: error - {e}')

    ds.close()

    # --- Plot ---
    extent = [-60.0, 15.0, -45.0, 25.0]

    latli = np.argmin(np.abs(lats - extent[2]))
    latui = np.argmin(np.abs(lats - extent[3]))
    lonli = np.argmin(np.abs(lons - extent[0]))
    lonui = np.argmin(np.abs(lons - extent[1]))

    # Re-open for subset (variables released above)
    ds2 = Dataset(file_path)
    sst2 = ds2.variables['analysed_sst'][:]
    sst_subset = sst2[0, latli:latui, lonli:lonui]
    img_extent = [lons[lonli], lons[lonui], lats[latli], lats[latui]]
    ds2.close()

    fig, ax = plt.subplots(figsize=FIG_SIZE,
                            subplot_kw={'projection': ccrs.PlateCarree()})

    img = ax.imshow(sst_subset, vmin=SST_VMIN, vmax=SST_VMAX, cmap=SST_CMAP,
                    origin='lower', extent=img_extent, transform=ccrs.PlateCarree())

    for p in pairs:
        ax.scatter(p['lon'], p['lat'], c=p['buoy_sst'], cmap=SST_CMAP,
                   vmin=SST_VMIN, vmax=SST_VMAX,
                   s=120, edgecolors='black', linewidths=1.5, zorder=5,
                   transform=ccrs.PlateCarree())
        ax.text(p['lon'] + 3.5, p['lat'],
                f"Bóia: {p['name']}\nBóia: {p['buoy_sst']:.1f}°C\nSatélite: {p['sat_sst']:.1f}°C",
                fontsize=6, color='black', transform=ccrs.PlateCarree(),
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9),
                verticalalignment='center')

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

    plt.colorbar(img, label='Temperatura da Superfície do Mar (°C)',
                 extend='both', orientation='horizontal',
                 pad=0.06, fraction=0.046, aspect=35)

    date_fmt = datetime.strptime(date_str, '%Y%m%d').strftime('%d/%m/%Y')
    add_branding(fig, f'TSM Satélite vs Bóias PIRATA - NOAA CRW - {date_fmt}', ax)

    save_dir = os.path.join(OUTPUT_DIR, 'Satelite_vs_Boia')
    os.makedirs(save_dir, exist_ok=True)
    plt.savefig(os.path.join(save_dir, f'Satelite_vs_Boia_Func_{date_str}.png'), bbox_inches='tight', dpi=FIG_DPI)
    plt.show()

    return pairs


# --- Example usage ---
if __name__ == '__main__':
    buoys = [
        'B20n38w', 'B15n38w', 'B12n38w', 'B8n38w', 'B4n38w',
        'B0n35w', 'B0n23w', 'B2s10e', 'B6s10e', 'B6s8e',
        'B10s10w', 'B14s32w', 'B19s34w'
    ]
    date_str = input('Digite a data (AAAAMMDD): ')
    results = compare_satellite_buoy(date_str, buoys)

    print('\n--- Satellite vs Buoy Pairs ---')
    for r in results:
        diff = r['sat_sst'] - r['buoy_sst']
        print(f"{r['name']}: Buoy={r['buoy_sst']:.2f}, Sat={r['sat_sst']:.2f}, Diff={diff:.2f}")

    print(f'Satelite_vs_Boia_Func_{date_str}.png saved.')

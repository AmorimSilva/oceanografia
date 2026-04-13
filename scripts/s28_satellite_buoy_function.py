"""Script 28: Satellite vs Buoy Comparison (Function)"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from netCDF4 import Dataset
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt
import cartopy.io.shapereader as shpreader
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
import matplotlib.patheffects as PathEffects
from config import (DADOS_DIR, OUTPUT_DIR, SHAPEFILES_DIR,
                    SST_CMAP, SST_VMIN, SST_VMAX, FIG_DPI, add_branding)
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
    base_extent = [-180.0, -60.0, -50.0, 30.0]
    FIG_SIZE_INSTAGRAM = (10.8, 13.5)
    extent = get_extent_for_figure(base_extent, FIG_SIZE_INSTAGRAM)

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

    fig = plt.figure(figsize=FIG_SIZE_INSTAGRAM, facecolor='black')
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], projection=ccrs.PlateCarree())
    ax.set_aspect('auto')
    ax.set_extent(extent, ccrs.PlateCarree())
    add_satellite_background(ax, zoom=6)
    ax.spines['geo'].set_visible(False)

    img = ax.imshow(sst_subset, vmin=SST_VMIN, vmax=SST_VMAX, cmap=SST_CMAP, zorder=3,
                    origin='lower', extent=img_extent, transform=ccrs.PlateCarree())

    # Add islands
    islands = [
        {'name': 'Tahiti', 'lat': -17.65, 'lon': -149.46},
        {'name': 'Ilha de Darwin', 'lat': 1.67, 'lon': -92.00}
    ]
    for isle in islands:
        ax.scatter(isle['lon'], isle['lat'], c='red',
                   s=100, edgecolors='white', linewidths=1.5,
                   transform=ccrs.PlateCarree(), zorder=6)
        txt = ax.text(isle['lon'] + 2.0, isle['lat'], isle['name'],
                      fontsize=14, fontweight='bold', color='white',
                      transform=ccrs.PlateCarree(), zorder=7,
                      verticalalignment='center')
        txt.set_path_effects([PathEffects.withStroke(linewidth=3, foreground='black')])

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

    cax = inset_axes(ax, width='35%', height='3%', loc='lower right', bbox_to_anchor=(-0.12, 0.05, 1, 1), bbox_transform=ax.transAxes, borderpad=0)
    cbar = plt.colorbar(img, cax=cax, orientation='horizontal', extend='both')
    cbar.set_label('Temperatura da Superfície do Mar (°C)', fontsize=18, color='white', fontweight='bold')
    cbar.ax.xaxis.label.set_path_effects([PathEffects.withStroke(linewidth=2, foreground='black')])

    cbar.ax.tick_params(labelsize=16, pad=1, colors='white')
    for label in cbar.ax.xaxis.get_ticklabels():
        label.set_fontweight('bold')
        label.set_path_effects([PathEffects.withStroke(linewidth=2, foreground='black')])
    cbar.outline.set_edgecolor('none')

    date_fmt = datetime.strptime(date_str, '%Y%m%d').strftime('%d/%m/%Y')
    titulo = f'Temperatura da Superfície do Mar (TSM) - Satélite\nPara o dia {date_fmt}\n@samuel.meteorologia'
    title_obj = ax.text(0.5, 0.94, titulo, fontsize=20, fontweight='bold', color='white',
                        transform=ax.transAxes, ha='center', va='top', zorder=10)
    title_obj.set_path_effects([PathEffects.withStroke(linewidth=3, foreground='black')])

    save_dir = os.path.join(OUTPUT_DIR, 'Satelite_vs_Boia')
    os.makedirs(save_dir, exist_ok=True)
    output_file = os.path.join(save_dir, f'Satelite_vs_Boia_Func_{date_str}.png')
    plt.savefig(output_file, dpi=FIG_DPI, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)

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

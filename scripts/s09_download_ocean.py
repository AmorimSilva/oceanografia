"""Script 9: Downloading Data Using Functions."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import matplotlib
matplotlib.use('Agg')

from datetime import datetime, timedelta
from netCDF4 import Dataset
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
import numpy as np
import imageio.v2 as imageio
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import cartopy.io.img_tiles as cimgt
import cartopy.io.shapereader as shpreader
from mpl_toolkits.axes_grid1.inset_locator import inset_axes
from config import (DADOS_DIR, OUTPUT_DIR, SHAPEFILES_DIR,
                    SST_CMAP, SST_VMIN, SST_VMAX,
                    FIG_DPI)
from utilities_ocean import download_OCEAN


BASE_EXTENT = [-93.0, -10.0, -60.0, 18.0]
FIG_SIZE_INSTAGRAM = (10.8, 13.5)
SATELLITE_ZOOM = 6


def add_satellite_background(ax, zoom=6):
    """Adiciona fundo satélite com fallback simples."""
    try:
        tiler = cimgt.GoogleTiles(style='satellite')
        ax.add_image(tiler, zoom)
    except Exception as e:
        print(f'Falha ao carregar fundo de satélite: {e}')
        ax.add_feature(cfeature.LAND, facecolor='whitesmoke')
        ax.add_feature(cfeature.OCEAN, facecolor='lightblue')


def get_extent_for_figure(base_extent, fig_size):
    """Ajusta o recorte para preencher a figura no aspecto desejado."""
    lon_min, lon_max, lat_min, lat_max = base_extent
    target_ratio = fig_size[0] / fig_size[1]

    lon_max += 0.6

    lon_span = lon_max - lon_min
    new_lat_span = lon_span / target_ratio
    lat_center = (lat_min + lat_max) / 2
    lat_min = lat_center - (new_lat_span / 2)
    lat_max = lat_center + (new_lat_span / 2)

    return [lon_min, lon_max, lat_min, lat_max]


def get_uf_shapefile_path():
    """Retorna o caminho do shapefile de UFs disponível."""
    base_dir = os.path.dirname(__file__)
    candidates = [
        os.path.join(base_dir, '..', '..', 'shapefiles', 'BR_UF_2024', 'BR_UF_2024.shp'),
        os.path.join(base_dir, '..', 'shapefiles', 'BR_UF_2022.shp'),
        os.path.join(SHAPEFILES_DIR, 'BR_UF_2024', 'BR_UF_2024.shp'),
        os.path.join(SHAPEFILES_DIR, 'BR_UF_2022.shp'),
        os.path.join(SHAPEFILES_DIR, 'ne_10m_admin_1_states_provinces.shp'),
    ]
    for path in candidates:
        full_path = os.path.abspath(path)
        if os.path.exists(full_path):
            return full_path
    return None


PLOT_EXTENT = get_extent_for_figure(BASE_EXTENT, FIG_SIZE_INSTAGRAM)
UF_SHAPEFILE = get_uf_shapefile_path()
GIF_DURATION_MS = 700
LOOKBACK_DAYS = 30


def resolve_sst_file(date_str):
    """Baixa/localiza arquivo SST válido para a data informada."""
    for attempt in range(2):
        file_name = download_OCEAN('SST', date_str, DADOS_DIR)
        if not file_name or file_name == -1:
            continue

        file_path = os.path.join(DADOS_DIR, file_name)
        if not os.path.exists(file_path):
            continue

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            print(f'Arquivo vazio detectado ({file_path}). Removendo e tentando novamente...')
            try:
                os.remove(file_path)
            except OSError:
                pass
            continue

        return file_path

    return None

# Intervalo automático: últimos 30 dias até hoje
date_end_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
date_loop = date_end_dt - timedelta(days=LOOKBACK_DAYS - 1)
date_ini = date_loop.strftime('%Y%m%d')
date_end = date_end_dt.strftime('%Y%m%d')
print(f'Processando período automático: {date_ini} até {date_end}')

save_dir = os.path.join(OUTPUT_DIR, 'TSM')
os.makedirs(save_dir, exist_ok=True)
frame_files = []

uf_geometries = None
if UF_SHAPEFILE:
    uf_geometries = list(shpreader.Reader(UF_SHAPEFILE).geometries())

tick_step = 2 if (SST_VMAX - SST_VMIN) <= 16 else 5
colorbar_ticks = np.arange(np.floor(SST_VMIN), np.ceil(SST_VMAX) + 0.1, tick_step)

while date_loop <= date_end_dt:
    date_str = date_loop.strftime('%Y%m%d')
    print(f'\nProcessando {date_str}...')

    file_path = resolve_sst_file(date_str)
    if not file_path:
        print(f'Falha ao obter arquivo SST válido para {date_str}. Pulando...')
        date_loop += timedelta(days=1)
        continue

    loaded = False
    for open_attempt in range(2):
        try:
            with Dataset(file_path) as ds:
                sst = ds.variables['analysed_sst'][:]
                lats = ds.variables['lat'][:]
                lons = ds.variables['lon'][:]

                latli = np.argmin(np.abs(lats - PLOT_EXTENT[2]))
                latui = np.argmin(np.abs(lats - PLOT_EXTENT[3]))
                lonli = np.argmin(np.abs(lons - PLOT_EXTENT[0]))
                lonui = np.argmin(np.abs(lons - PLOT_EXTENT[1]))

                lat_start, lat_end = sorted([latli, latui])
                lon_start, lon_end = sorted([lonli, lonui])

                sst_subset = sst[0, lat_start:lat_end + 1, lon_start:lon_end + 1]
                lats_subset = lats[lat_start:lat_end + 1]
                lons_subset = lons[lon_start:lon_end + 1]
                img_extent = (
                    float(np.min(lons_subset)),
                    float(np.max(lons_subset)),
                    float(np.min(lats_subset)),
                    float(np.max(lats_subset)),
                )
            loaded = True
            break
        except Exception as e:
            print(f'Arquivo inválido para {date_str} ({file_path}): {e}.')
            if open_attempt == 0:
                try:
                    os.remove(file_path)
                except OSError:
                    pass
                file_path = resolve_sst_file(date_str)
                if file_path:
                    print('Novo download obtido, tentando abrir novamente...')
                    continue
            break

    if not loaded:
        print(f'Não foi possível ler SST para {date_str}. Pulando...')
        date_loop += timedelta(days=1)
        continue

    date_fmt = datetime.strptime(date_str, '%Y%m%d').strftime('%d/%m/%Y')

    fig = plt.figure(figsize=FIG_SIZE_INSTAGRAM, facecolor='black')
    ax = fig.add_axes([0.0, 0.0, 1.0, 1.0], projection=ccrs.PlateCarree())
    ax.set_aspect('auto')
    ax.set_extent(PLOT_EXTENT, ccrs.PlateCarree())
    add_satellite_background(ax, zoom=SATELLITE_ZOOM)
    ax.spines['geo'].set_visible(False)

    img = ax.imshow(
        sst_subset,
        vmin=SST_VMIN,
        vmax=SST_VMAX,
        cmap=SST_CMAP,
        origin='lower',
        extent=img_extent,
        transform=ccrs.PlateCarree(),
        alpha=0.9,
        zorder=1,
    )

    ax.coastlines(resolution='10m', color='black', linewidth=0.8, zorder=3)
    ax.add_feature(cfeature.BORDERS, edgecolor='black', linewidth=0.5, zorder=3)

    if uf_geometries:
        ax.add_geometries(
            uf_geometries,
            ccrs.PlateCarree(),
            edgecolor='white',
            facecolor='none',
            linewidth=0.6,
            zorder=4,
        )

    gl = ax.gridlines(
        crs=ccrs.PlateCarree(),
        color='gray',
        alpha=0.5,
        linestyle='--',
        linewidth=0.25,
        xlocs=np.arange(-180, 180.1, 2.5),
        ylocs=np.arange(-90, 90.1, 2.5),
        draw_labels=True,
    )
    gl.top_labels = False
    gl.right_labels = False
    gl.left_labels = False
    gl.bottom_labels = False

    cax = inset_axes(ax, width='35%', height='3%', loc='lower right', borderpad=3.0)
    cbar = plt.colorbar(img, cax=cax, ticks=colorbar_ticks, orientation='horizontal', extend='both')
    cbar.set_label('Temperatura da Superfície do Mar (°C)', fontsize=14, color='white')
    cbar.ax.tick_params(labelsize=13, pad=1, colors='white')
    cbar.outline.set_edgecolor('none')
    cbar.ax.xaxis.label.set_path_effects([pe.withStroke(linewidth=2, foreground='black')])
    for tick_label in cbar.ax.get_xticklabels():
        tick_label.set_path_effects([pe.withStroke(linewidth=2, foreground='black')])

    title_text = f'TSM - NOAA CRW\n{date_fmt}\n@samuel.meteorologia'
    title = ax.set_title(title_text, fontsize=12, fontweight='bold', color='white', y=0.945, pad=2)
    title.set_path_effects([pe.withStroke(linewidth=3, foreground='black')])

    output_file = os.path.join(save_dir, f'TSM_{date_str}.png')
    plt.savefig(output_file, dpi=FIG_DPI, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close(fig)
    print(f'Salvo: {output_file}')
    frame_files.append(output_file)

    date_loop += timedelta(days=1)

# Criar GIF da sequência temporal
if frame_files:
    output_gif = os.path.join(save_dir, f'TSM_anim_{date_ini}_{date_end}.gif')
    images = [imageio.imread(frame) for frame in frame_files if os.path.exists(frame)]
    if images:
        imageio.mimsave(output_gif, images, duration=GIF_DURATION_MS / 1000, loop=0)
        print(f'GIF criado: {output_gif}')
else:
    print('Nenhum frame foi gerado. GIF não criado.')

"""Configuracoes compartilhadas para todos os scripts oceanograficos."""
import os
import matplotlib
import matplotlib.colors
import matplotlib.pyplot as plt
import numpy as np

# --- Instagram / Figuras ---
INSTAGRAM_HANDLE = '@samuel.meteorologia'
INSTAGRAM_TAG = '@samuel.meteorologia'
FIG_DPI = 600
FIG_SIZE = (5.4, 6.75)        # 4:5 ratio (Instagram portrait)
FIG_SIZE_WIDE = (5.4, 5.4)    # 1:1 para séries temporais / scatter
FONTSIZE = 13

# Aplicar fontsize global
matplotlib.rcParams.update({
    'font.size': FONTSIZE,
    'axes.titlesize': FONTSIZE + 1,
    'axes.labelsize': FONTSIZE,
    'xtick.labelsize': FONTSIZE - 1,
    'ytick.labelsize': FONTSIZE - 1,
    'legend.fontsize': FONTSIZE - 1,
    'font.family': ['DejaVu Sans', 'Segoe UI Emoji'],
})

# --- Diretorios ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DADOS_DIR = os.path.join(BASE_DIR, 'dados')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
SHAPEFILES_DIR = os.path.join(BASE_DIR, 'shapefiles')

os.makedirs(DADOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SHAPEFILES_DIR, exist_ok=True)

# --- Extensoes padrao ---
EXTENT_SOUTH_AMERICA = [-93.0, -60.00, -10.00, 18.00]
EXTENT_BRAZIL_SE = [-70.0, -50.00, -30.00, -20.00]
EXTENT_GOES = [-93.0, -60.00, -25.00, 18.00]

# --- Paleta continua SST (baseada NASA Worldview) ---
SST_COLORS = [
    "#2d001c", "#5b0351", "#780777", "#480a5e", "#1e1552",
    "#1f337d", "#214c9f", "#2776c6", "#2fa5f1", "#1bad1d",
    "#8ad900", "#ffec00", "#ffab00", "#f46300", "#de3b00",
    "#ab1900", "#6b0200", "#3c0000"
]
SST_CMAP = matplotlib.colors.LinearSegmentedColormap.from_list("sst_nasa", SST_COLORS)
SST_CMAP.set_over('#3c0000')
SST_CMAP.set_under('#28000a')
SST_VMIN = -2.0
SST_VMAX = 35.0

# --- Paleta discreta SST (baseada NOAA) ---
SST_NOAA_COLORS = [
    "#2d001c", "#5b0351", "#780777", "#480a5e", "#1e1552",
    "#1f337d", "#214c9f", "#2776c6", "#2fa5f1", "#1bad1d",
    "#8ad900", "#ffec00", "#ffab00", "#f46300", "#de3b00",
    "#ab1900", "#6b0200", "#3c0000"
]
SST_NOAA_BOUNDS = np.arange(-2, 36, 2)
SST_NOAA_CMAP = matplotlib.colors.ListedColormap(SST_NOAA_COLORS)

# --- Paleta ventos ---
WIND_COLORS = [
    "#747474", "#00befe", "#0048ff", "#00c300", "#fedb12",
    "#f25505", "#ff1526", "#87422a", "#d100e1", "#7f00ad"
]
WIND_BOUNDS = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

# --- Funcao auxiliar de plot ---
def setup_map(ax, extent, resolution='50m', grid_step=10):
    """Configura mapa Cartopy com costas, bordas e grade."""
    import cartopy
    import cartopy.crs as ccrs
    ax.set_extent([extent[0], extent[2], extent[1], extent[3]], ccrs.PlateCarree())
    ax.coastlines(resolution=resolution, color='black', linewidth=0.8)
    ax.add_feature(cartopy.feature.BORDERS, edgecolor='black', linewidth=0.5)
    gl = ax.gridlines(
        crs=ccrs.PlateCarree(), color='white', alpha=0.0,
        linestyle='--', linewidth=0,
        xlocs=np.arange(-180, 181, 20),
        ylocs=np.arange(-90, 91, grid_step),
        draw_labels=True
    )
    gl.top_labels = False
    gl.right_labels = False
    return gl


def add_branding(fig, title_text, ax=None):
    """Adiciona 3 anotações Instagram à figura.

    1. Título + handle no topo
    2. Marca d'água central transparente
    3. Crédito junto à barra de cores / rodapé
    """
    tag = INSTAGRAM_TAG

    # 1 – Título com Instagram
    if ax is not None:
        ax.set_title(f'{title_text}\n{tag}',
                     fontsize=FONTSIZE + 1, fontweight='bold', pad=10)
    else:
        fig.suptitle(f'{title_text}\n{tag}',
                     fontsize=FONTSIZE + 1, fontweight='bold', y=0.97)

    # 2 – Marca d'água central (transparente)
    import matplotlib.patheffects as pe
    fig.text(0.5, 0.45, tag,
             fontsize=FONTSIZE + 12, color='black', alpha=0.12,
             ha='center', va='center', rotation=30,
             fontweight='bold', zorder=1000,
             transform=fig.transFigure,
             path_effects=[pe.withStroke(linewidth=3, foreground='white', alpha=0.12)])

    # 3 – Rodapé / crédito junto à legenda
    fig.text(0.5, 0.01, tag,
             fontsize=FONTSIZE - 3, color='gray', alpha=0.8,
             ha='center', va='bottom',
             transform=fig.transFigure)

"""Script para baixar dados auxiliares (shapefiles, paletas CPT)."""
import os
import urllib.request
import zipfile

from config import DADOS_DIR, SHAPEFILES_DIR

# --- Shapefiles ---
SHAPEFILES = {
    'ne_10m_admin_1_states_provinces': (
        'https://naciscdn.org/naturalearth/10m/cultural/ne_10m_admin_1_states_provinces.zip'
    ),
    'br_unidades_da_federacao': (
        'https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/'
        'malhas_municipais/municipio_2022/Brasil/BR/BR_UF_2022.zip'
    ),
    'Metareas': (
        'https://github.com/diegormsouza/Oceanography_Python_May_2022/raw/main/Metareas.zip'
    ),
}

# --- CPT color palettes ---
CPTS = {
    'IR4AVHRR6.cpt': (
        'https://raw.githubusercontent.com/diegormsouza/SHOWCast-2.3.0_b/'
        'main/Cloud/IR4AVHRR6.cpt'
    ),
    'SVGAWVX_TEMP.cpt': (
        'https://raw.githubusercontent.com/diegormsouza/SHOWCast-2.3.0_b/'
        'main/Cloud/SVGAWVX_TEMP.cpt'
    ),
}


def download_file(url, dest):
    """Baixa um arquivo se ainda nao existe."""
    if os.path.exists(dest):
        print(f'  Ja existe: {dest}')
        return
    print(f'  Baixando: {url}')
    urllib.request.urlretrieve(url, dest)
    print(f'  Salvo em: {dest}')


def extract_zip(zip_path, dest_dir):
    """Extrai um zip no diretorio de destino."""
    print(f'  Extraindo: {zip_path}')
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(dest_dir)


def setup_shapefiles():
    """Baixa e extrai shapefiles."""
    print('\n=== Shapefiles ===')
    for name, url in SHAPEFILES.items():
        zip_dest = os.path.join(SHAPEFILES_DIR, f'{name}.zip')
        download_file(url, zip_dest)
        # Verifica se ja foi extraido (procura .shp)
        shp = os.path.join(SHAPEFILES_DIR, f'{name}.shp')
        if not os.path.exists(shp):
            extract_zip(zip_dest, SHAPEFILES_DIR)


def setup_cpts():
    """Baixa paletas CPT."""
    print('\n=== Paletas CPT ===')
    for name, url in CPTS.items():
        dest = os.path.join(DADOS_DIR, name)
        download_file(url, dest)


if __name__ == '__main__':
    print('Configurando dados auxiliares...\n')
    setup_shapefiles()
    setup_cpts()
    print('\n=== Pronto! ===')

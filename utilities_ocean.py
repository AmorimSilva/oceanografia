"""Funcao de download de dados oceanograficos via FTP (NOAA)."""

from datetime import datetime, timedelta
import os
import time as t
from ftplib import FTP


def download_OCEAN(product, date, path_dest):
    """Baixa produto oceanografico da NOAA via FTP.

    Args:
        product: codigo do produto (ex: 'SST', 'SST-A', 'BAA', 'CLO', etc.)
        date: data no formato 'YYYYMMDD'
        path_dest: diretorio de destino
    Returns:
        Nome do arquivo baixado.
    """
    print('-----------------------------------')
    print('NOAA FTP Download - Script started.')
    print('-----------------------------------')

    start_time = t.time()
    os.makedirs(path_dest, exist_ok=True)

    year = date[0:4]
    month = date[4:6]
    day = date[6:8]

    # Seleciona servidor FTP
    STAR_PRODUCTS = {
        'SST', 'SST-A', 'SST-T', 'BAA', 'BHS', 'DHW', 'CLO',
        'SST-Monthly-Min', 'SST-Monthly-Mean', 'SST-Monthly-Max',
        'SST-Annual-Min', 'SST-Annual-Mean', 'SST-Annual-Max',
        'SST-A-Monthly-Min', 'SST-A-Monthly-Mean', 'SST-A-Monthly-Max',
        'SST-A-Annual-Min', 'SST-A-Annual-Mean', 'SST-A-Annual-Max',
        'BAA-Monthly-Max', 'BAA-Annual-Max',
        'BHS-Monthly-Max', 'BHS-Annual-Max',
        'DHW-Monthly-Max', 'DHW-Annual-Max',
    }
    COASTWATCH_PRODUCTS = {
        'ASC-A-a-hdf', 'ASC-A-d-hdf', 'ASC-B-a-hdf', 'ASC-B-d-hdf',
        'ASC-C-a-hdf', 'ASC-C-d-hdf', 'SLA', 'JAS', 'SST-LEO',
    }

    if product in STAR_PRODUCTS:
        ftp = FTP('ftp.star.nesdis.noaa.gov')
    elif product in COASTWATCH_PRODUCTS:
        ftp = FTP('ftpcoastwatch.noaa.gov')
    else:
        raise ValueError(f'Produto desconhecido: {product}')

    ftp.login('', '')

    # Monta caminho e nome do arquivo
    path, file_name = _build_ftp_path(product, year, month, day)

    print(f'\nProduct: {product}')
    print(f'Date: {year}{month}{day}')
    print(f'File Name: {file_name}')

    try:
        ftp.cwd(path)
        dest = os.path.join(path_dest, file_name)
        if os.path.exists(dest):
            print(f'O arquivo {dest} ja existe.')
        else:
            print('Downloading the file...')
            with open(dest, 'wb') as f:
                ftp.retrbinary('RETR ' + file_name, f.write)
            print('Download Finished.')
            print(f'Total Download Time: {round(t.time() - start_time, 2)} seconds.')
    except Exception as e:
        # Special handling for SLA: try latest file if year directory doesn't exist
        if product == 'SLA' and f'{year}/' in path:
            print(f'\nDiretório {year}/ não encontrado. Tentando arquivo mais recente...')
            try:
                parent_path = 'pub/socd/lsa/rads/sla/daily/nrt/sla/'
                latest_file = 'rads_global_nrt_sla_latest.nc'
                ftp.cwd('/')
                ftp.cwd(parent_path)
                dest = os.path.join(path_dest, latest_file)
                print(f'File Name: {latest_file}')
                if os.path.exists(dest):
                    print(f'O arquivo {dest} ja existe.')
                else:
                    print('Downloading the file...')
                    with open(dest, 'wb') as f:
                        ftp.retrbinary('RETR ' + latest_file, f.write)
                    print('Download Finished.')
                    print(f'Total Download Time: {round(t.time() - start_time, 2)} seconds.')
                ftp.quit()
                return latest_file
            except Exception:
                print('\nFile not available!')
        else:
            print('\nFile not available!')

    ftp.quit()
    return file_name


def _julian_day(year, month, day):
    """Retorna o dia Juliano formatado com 3 digitos."""
    from datetime import datetime as dt
    return dt.strptime(f'{year}{month}{day}', '%Y%m%d').strftime('%j')


def _build_ftp_path(product, year, month, day):
    """Retorna (ftp_path, file_name) para o produto."""

    CRW = 'pub/socd/mecb/crw/data/5km/v3.1_op/nc/v1.0'

    # --- SST ---
    if product == 'SST':
        return f'{CRW}/daily/sst/{year}/', f'coraltemp_v3.1_{year}{month}{day}.nc'
    if product == 'SST-Monthly-Max':
        return f'{CRW}/monthly/{year}/', f'ct5km_sst-max_v3.1_{year}{month}.nc'
    if product == 'SST-Monthly-Mean':
        return f'{CRW}/monthly/{year}/', f'ct5km_sst-mean_v3.1_{year}{month}.nc'
    if product == 'SST-Monthly-Min':
        return f'{CRW}/monthly/{year}/', f'ct5km_sst-min_v3.1_{year}{month}.nc'
    if product == 'SST-Annual-Max':
        return f'{CRW}/annual/', f'ct5km_sst-max_v3.1_{year}.nc'
    if product == 'SST-Annual-Mean':
        return f'{CRW}/annual/', f'ct5km_sst-mean_v3.1_{year}.nc'
    if product == 'SST-Annual-Min':
        return f'{CRW}/annual/', f'ct5km_sst-min_v3.1_{year}.nc'

    # --- SST Anomaly ---
    if product == 'SST-A':
        return f'{CRW}/daily/ssta/{year}/', f'ct5km_ssta_v3.1_{year}{month}{day}.nc'
    if product == 'SST-A-Monthly-Max':
        return f'{CRW}/monthly/{year}/', f'ct5km_ssta-max_v3.1_{year}{month}.nc'
    if product == 'SST-A-Monthly-Mean':
        return f'{CRW}/monthly/{year}/', f'ct5km_ssta-mean_v3.1_{year}{month}.nc'
    if product == 'SST-A-Monthly-Min':
        return f'{CRW}/monthly/{year}/', f'ct5km_ssta-min_v3.1_{year}{month}.nc'
    if product == 'SST-A-Annual-Max':
        return f'{CRW}/annual/', f'ct5km_ssta-max_v3.1_{year}.nc'
    if product == 'SST-A-Annual-Mean':
        return f'{CRW}/annual/', f'ct5km_ssta-mean_v3.1_{year}.nc'
    if product == 'SST-A-Annual-Min':
        return f'{CRW}/annual/', f'ct5km_ssta-min_v3.1_{year}.nc'

    # --- SST Trend ---
    if product == 'SST-T':
        return f'{CRW}/daily/sst-trend-7d/{year}/', f'ct5km_sst-trend-7d_v3.1_{year}{month}{day}.nc'

    # --- Bleaching Alert Area ---
    if product == 'BAA':
        return f'{CRW}/daily/baa/{year}/', f'ct5km_baa_v3.1_{year}{month}{day}.nc'
    if product == 'BAA-Monthly-Max':
        return f'{CRW}/monthly/{year}/', f'ct5km_baa-max_v3.1_{year}{month}.nc'
    if product == 'BAA-Annual-Max':
        return f'{CRW}/annual/', f'ct5km_baa-max_v3.1_{year}.nc'

    # --- Bleaching Hotspot ---
    if product == 'BHS':
        return f'{CRW}/daily/hs/{year}/', f'ct5km_hs_v3.1_{year}{month}{day}.nc'
    if product == 'BHS-Monthly-Max':
        return f'{CRW}/monthly/{year}/', f'ct5km_hs-max_v3.1_{year}{month}.nc'
    if product == 'BHS-Annual-Max':
        return f'{CRW}/annual/', f'ct5km_hs-max_v3.1_{year}.nc'

    # --- Degree Heating Week ---
    if product == 'DHW':
        return f'{CRW}/daily/dhw/{year}/', f'ct5km_dhw_v3.1_{year}{month}{day}.nc'
    if product == 'DHW-Monthly-Max':
        return f'{CRW}/monthly/{year}/', f'ct5km_dhw-max_v3.1_{year}{month}.nc'
    if product == 'DHW-Annual-Max':
        return f'{CRW}/annual/', f'ct5km_dhw-max_v3.1_{year}.nc'

    # --- Chlorophyll ---
    if product == 'CLO':
        jday = _julian_day(year, month, day)
        return (f'pub/socd1/mecb/coastwatch/viirs/nrt/L3/global/chlora/dineof/{year}/',
                f'V{year}{jday}_a1_WW00_chlora.nc')

    # --- Sea Level Anomaly ---
    if product == 'SLA':
        date_1 = f'{year}{month}{day}'
        date_2 = (datetime(int(year), int(month), int(day)) + timedelta(days=1)).strftime('%Y%m%d')
        return (f'pub/socd/lsa/rads/sla/daily/nrt/sla/{year}/',
                f'rads_global_nrt_sla_{date_1}_{date_2}_001.nc')

    # --- ASCAT Winds ---
    if product.startswith('ASC-'):
        jday = _julian_day(year, month, day)
        # ex: ASC-B-d-hdf -> Bds
        parts = product.replace('-hdf', '').split('-')
        sat = parts[1]  # A, B ou C
        orb = parts[2]  # a ou d
        suffix = f'{sat}{orb}s_WW'
        return 'pub/socd1/coastwatch/products/ascat/4hr/hdf/', f'AS{year}{jday}{suffix}.hdf'

    # --- JASON-3 ---
    if product == 'JAS':
        return 'pub/socd/lsa/johnk/coastwatch/j3/', f'j3_{year}{month}{day}.nc'

    # --- SST LEO ---
    if product == 'SST-LEO':
        jday = _julian_day(year, month, day)
        conv = '120000-STAR-L3S_GHRSST-SSTsubskin-LEO_PM_D-ACSPO_V2.81-v02.0-fv01.0'
        return (f'pub/socd2/coastwatch/sst/nrt/l3s/leo/pm/{year}/{jday}',
                f'{year}{month}{day}{conv}.nc')

    raise ValueError(f'Produto desconhecido: {product}')

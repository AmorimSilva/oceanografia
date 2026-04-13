import os
import numpy as np
import colorsys
import boto3
from botocore import UNSIGNED
from botocore.config import Config
import math
from datetime import datetime
import rasterio
from rasterio.transform import Affine
from rasterio.warp import reproject as rio_reproject, Resampling
from rasterio.crs import CRS


def loadCPT(path):
    """Load a CPT color palette file and return a colorDict for matplotlib LinearSegmentedColormap."""
    try:
        f = open(path)
    except FileNotFoundError:
        print("File ", path, "not found")
        return None

    lines = f.readlines()
    f.close()

    x = np.array([])
    r = np.array([])
    g = np.array([])
    b = np.array([])

    colorModel = 'RGB'

    for l in lines:
        ls = l.split()
        if l[0] == '#':
            if ls[-1] == 'HSV':
                colorModel = 'HSV'
                continue
            else:
                continue
        if ls[0] == 'B' or ls[0] == 'F' or ls[0] == 'N':
            pass
        else:
            x = np.append(x, float(ls[0]))
            r = np.append(r, float(ls[1]))
            g = np.append(g, float(ls[2]))
            b = np.append(b, float(ls[3]))
            xtemp = float(ls[4])
            rtemp = float(ls[5])
            gtemp = float(ls[6])
            btemp = float(ls[7])
            x = np.append(x, xtemp)
            r = np.append(r, rtemp)
            g = np.append(g, gtemp)
            b = np.append(b, btemp)

    if colorModel == 'HSV':
        for i in range(r.shape[0]):
            rr, gg, bb = colorsys.hsv_to_rgb(r[i] / 360., g[i], b[i])
            r[i] = rr
            g[i] = gg
            b[i] = bb

    if colorModel == 'RGB':
        r = r / 255.0
        g = g / 255.0
        b = b / 255.0

    xNorm = (x - x[0]) / (x[-1] - x[0])

    red = []
    blue = []
    green = []

    for i in range(len(x)):
        red.append([xNorm[i], r[i], r[i]])
        green.append([xNorm[i], g[i], g[i]])
        blue.append([xNorm[i], b[i], b[i]])

    colorDict = {'red': red, 'green': green, 'blue': blue}

    return colorDict


def download_CMI(yyyymmddhhmn, band, path_dest):
    """Download GOES-19 ABI CMI (Cloud and Moisture Imagery) data from AWS S3."""
    os.makedirs(path_dest, exist_ok=True)

    year = datetime.strptime(yyyymmddhhmn, '%Y%m%d%H%M').strftime('%Y')
    day_of_year = datetime.strptime(yyyymmddhhmn, '%Y%m%d%H%M').strftime('%j')
    hour = datetime.strptime(yyyymmddhhmn, '%Y%m%d%H%M').strftime('%H')
    min = datetime.strptime(yyyymmddhhmn, '%Y%m%d%H%M').strftime('%M')

    bucket_name = 'noaa-goes19'
    product_name = 'ABI-L2-CMIPF'

    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))

    prefix = f'{product_name}/{year}/{day_of_year}/{hour}/OR_{product_name}-M6C{int(band):02.0f}_G19_s{year}{day_of_year}{hour}{min}'

    s3_result = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, Delimiter="/")

    if 'Contents' not in s3_result:
        print(f'No files found for the date: {yyyymmddhhmn}, Band-{band}')
        return -1
    else:
        for obj in s3_result['Contents']:
            key = obj['Key']
            file_name = key.split('/')[-1].split('.')[0]

            if os.path.exists(f'{path_dest}/{file_name}.nc'):
                print(f'File {path_dest}/{file_name}.nc exists')
            else:
                print(f'Downloading file {path_dest}/{file_name}.nc')
                s3_client.download_file(bucket_name, key, f'{path_dest}/{file_name}.nc')
        return f'{file_name}'


def download_PROD(yyyymmddhhmn, product_name, path_dest):
    """Download GOES-19 L2 products from AWS S3."""
    os.makedirs(path_dest, exist_ok=True)

    year = datetime.strptime(yyyymmddhhmn, '%Y%m%d%H%M').strftime('%Y')
    day_of_year = datetime.strptime(yyyymmddhhmn, '%Y%m%d%H%M').strftime('%j')
    hour = datetime.strptime(yyyymmddhhmn, '%Y%m%d%H%M').strftime('%H')
    min = datetime.strptime(yyyymmddhhmn, '%Y%m%d%H%M').strftime('%M')

    bucket_name = 'noaa-goes19'

    s3_client = boto3.client('s3', config=Config(signature_version=UNSIGNED))

    prefix = f'{product_name}/{year}/{day_of_year}/{hour}/OR_{product_name}-M6_G19_s{year}{day_of_year}{hour}{min}'

    s3_result = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix, Delimiter="/")

    if 'Contents' not in s3_result:
        print(f'No files found for the date: {yyyymmddhhmn}, Product-{product_name}')
        return -1
    else:
        for obj in s3_result['Contents']:
            key = obj['Key']
            file_name = key.split('/')[-1].split('.')[0]

            if os.path.exists(f'{path_dest}/{file_name}.nc'):
                print(f'File {path_dest}/{file_name}.nc exists')
            else:
                print(f'Downloading file {path_dest}/{file_name}.nc')
                s3_client.download_file(bucket_name, key, f'{path_dest}/{file_name}.nc')
        return f'{file_name}'


def geo2grid(lat, lon, nc):
    """Convert lat/lon to GOES grid row/column indices."""
    xscale, xoffset = nc.variables['x'].scale_factor, nc.variables['x'].add_offset
    yscale, yoffset = nc.variables['y'].scale_factor, nc.variables['y'].add_offset

    x, y = latlon2xy(lat, lon)
    col = (x - xoffset) / xscale
    lin = (y - yoffset) / yscale
    return int(lin), int(col)


def latlon2xy(lat, lon):
    """Convert lat/lon to GOES-19 geostationary projection x/y coordinates."""
    req = 6378137  # semi_major_axis (meters)
    invf = 298.257222096  # inverse_flattening
    rpol = 6356752.31414  # semi_minor_axis (meters)
    e = 0.0818191910435
    H = 42164160  # perspective_point_height + semi_major_axis (meters)
    lambda0 = -75.2 * (math.pi / 180)  # GOES-19 longitude_of_projection_origin (radians)

    latRad = lat * (math.pi / 180)
    lonRad = lon * (math.pi / 180)

    Phi_c = math.atan(((rpol * rpol) / (req * req)) * math.tan(latRad))
    rc = rpol / (math.sqrt(1 - ((e * e) * (math.cos(Phi_c) * math.cos(Phi_c)))))
    sx = H - (rc * math.cos(Phi_c) * math.cos(lonRad - lambda0))
    sy = -rc * math.cos(Phi_c) * math.sin(lonRad - lambda0)
    sz = rc * math.sin(Phi_c)

    x = math.asin((-sy) / math.sqrt((sx * sx) + (sy * sy) + (sz * sz)))
    y = math.atan(sz / sx)

    return x, y


def convertExtent2GOESProjection(extent):
    """Convert geographic extent [min_lon, min_lat, max_lon, max_lat] to GOES-19 projection extent."""
    GOES19_HEIGHT = 35786023.0
    GOES19_LONGITUDE = -75.2

    a, b = latlon2xy(extent[1], extent[0])
    c, d = latlon2xy(extent[3], extent[2])
    return (a * GOES19_HEIGHT, c * GOES19_HEIGHT, b * GOES19_HEIGHT, d * GOES19_HEIGHT)


def reproject(file_name, nc_path, array, extent, undef):
    """Reproject GOES data from geostationary projection to lat/lon using rasterio.

    Args:
        file_name: Output file path (GeoTIFF).
        nc_path: Path to original GOES NetCDF file (to read projection info).
        array: 2D numpy array with the data to reproject.
        extent: [min_lon, min_lat, max_lon, max_lat].
        undef: Fill/undefined value.
    """
    from netCDF4 import Dataset as NCDataset

    nc = NCDataset(nc_path)
    proj_info = nc.variables['goes_imager_projection']

    h = float(proj_info.perspective_point_height)
    lon_0 = float(proj_info.longitude_of_projection_origin)
    sweep = str(proj_info.sweep_angle_axis)
    semi_major = float(proj_info.semi_major_axis)
    semi_minor = float(proj_info.semi_minor_axis)

    x = nc.variables['x'][:].astype(float) * h
    y = nc.variables['y'][:].astype(float) * h
    nc.close()

    src_crs = CRS.from_proj4(
        f'+proj=geos +h={h} +lon_0={lon_0} +sweep={sweep} '
        f'+a={semi_major} +b={semi_minor} +units=m +no_defs'
    )

    dx = abs(float(x[1] - x[0]))
    dy = abs(float(y[0] - y[1]))
    src_transform = Affine(dx, 0, float(x[0]) - dx / 2, 0, -dy, float(y[0]) + dy / 2)

    dst_crs = CRS.from_epsg(4326)
    dst_width = 1000
    dst_height = 1000
    dst_transform = rasterio.transform.from_bounds(
        extent[0], extent[1], extent[2], extent[3], dst_width, dst_height
    )

    dst_array = np.full((dst_height, dst_width), np.nan, dtype=np.float32)

    rio_reproject(
        source=array.astype(np.float32),
        destination=dst_array,
        src_transform=src_transform,
        src_crs=src_crs,
        dst_transform=dst_transform,
        dst_crs=dst_crs,
        src_nodata=undef,
        dst_nodata=np.nan,
        resampling=Resampling.nearest,
    )

    out_path = file_name if file_name.endswith('.tif') else file_name.replace('.nc', '.tif')
    with rasterio.open(
        out_path, 'w',
        driver='GTiff',
        height=dst_height,
        width=dst_width,
        count=1,
        dtype='float32',
        crs=dst_crs,
        transform=dst_transform,
    ) as dst:
        dst.write(dst_array, 1)

    return dst_array

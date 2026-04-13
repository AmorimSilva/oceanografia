# Script: s17_bleaching_hotspot.py

## Arquivo-fonte
- oceanografia/scripts/s17_bleaching_hotspot.py

## O que faz
- Calcula hotspot de estresse termico para corais.

## Requisitos
- Python 3.11+
- numpy
- matplotlib
- cartopy
- netCDF4
- rasterio
- boto3
- scikit-image
- Pillow

## Variaveis a serem alteradas
- date
- extent
- shapefile_path

## Passo a passo para execucao
1. Ative o ambiente do projeto (venv ou conda).
2. Ajuste as variaveis listadas acima conforme sua area e periodo.
3. Rode o comando abaixo na raiz do repositorio.
4. Confira os arquivos gerados no diretorio de output do modulo.

## Comando pronto
```powershell
python "oceanografia/scripts/s17_bleaching_hotspot.py"
```

## Exemplos de resultado
- oceanografia/output/TSM/TSM_anim_20260301_20260330.gif
- oceanografia/output/TSM/TSM_20260329.png
- oceanografia/output/TSM/TSM_20260328.png

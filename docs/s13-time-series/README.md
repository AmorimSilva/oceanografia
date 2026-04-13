# Script: s13_time_series.py

## Arquivo-fonte
- oceanografia/scripts/s13_time_series.py

## O que faz
- Gera serie temporal da TSM para janela de datas definida.

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
- date_ini
- date_end
- lat
- lon

## Passo a passo para execucao
1. Ative o ambiente do projeto (venv ou conda).
2. Ajuste as variaveis listadas acima conforme sua area e periodo.
3. Rode o comando abaixo na raiz do repositorio.
4. Confira os arquivos gerados no diretorio de output do modulo.

## Comando pronto
```powershell
python "oceanografia/scripts/s13_time_series.py"
```

## Exemplos de resultado
- oceanografia/output/TSM/TSM_anim_20260301_20260330.gif
- oceanografia/output/TSM/TSM_20260329.png
- oceanografia/output/TSM/TSM_20260328.png

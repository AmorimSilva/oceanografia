# Modulo oceanografia

## Objetivo
- Centraliza rotinas oceanograficas operacionais para gerar produtos de publicacao (TSM, tendencia, clorofila e alertas de branqueamento).

## Requisitos
- Python 3.11+
- numpy
- matplotlib
- cartopy
- netCDF4
- imageio
- rasterio
- boto3
- Pillow

## Variaveis principais para editar
- INSTAGRAM_HANDLE e INSTAGRAM_TAG em config.py
- EXTENT_SOUTH_AMERICA e EXTENT_BRAZIL_SE em config.py
- Datas iniciais/finais no bloco principal de cada script
- Caminhos de dados e shapefiles em setup_dados.py

## Passo a passo
1. Ative o ambiente Python do projeto.
2. Revise config.py e, se necessario, rode setup_dados.py para preparar dados auxiliares.
3. Ajuste data, area e parametros dos scripts desejados.
4. Execute os scripts abaixo a partir da raiz do repositorio.
5. Verifique os resultados em oceanografia/output/.

## Scripts e comandos
- s09_download_ocean.py: `python "oceanografia/scripts/s09_download_ocean.py"`
- s13_time_series.py: `python "oceanografia/scripts/s13_time_series.py"`
- s15_sst_trend.py: `python "oceanografia/scripts/s15_sst_trend.py"`
- s16_coral_bleaching_alert.py: `python "oceanografia/scripts/s16_coral_bleaching_alert.py"`
- s17_bleaching_hotspot.py: `python "oceanografia/scripts/s17_bleaching_hotspot.py"`
- s19_chlorophyll.py: `python "oceanografia/scripts/s19_chlorophyll.py"`
- s28_satellite_buoy_function.py: `python "oceanografia/scripts/s28_satellite_buoy_function.py"`
- splot_tsm_serie_tendencia.py: `python "oceanografia/scripts/splot_tsm_serie_tendencia.py"`

## Pasta de saida principal
- oceanografia/output/TSM/

## Documentacao detalhada por script
- oceanografia/docs/

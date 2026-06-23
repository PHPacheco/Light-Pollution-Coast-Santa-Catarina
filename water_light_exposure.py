from pathlib import Path
import urllib.request

import ee

from water_land_separation import (
    CIDADES,
    COR_TERRA,
    DIMENSOES_PNG,
    MAX_VIIRS,
    construir_camadas,
    inicializar_earth_engine,
)

# Continuous gradient: solid gray land and increasing light intensity over water.
PALETA_EXPOSICAO = [
    '#000000',
    '#0000ff',
    '#800080',
    '#ffff00',
    '#ffffff',
]

OUTPUT_DIR = Path('Images/exposure-gradient')


def mapa_exposicao(cidade):
    camadas = construir_camadas(cidade)
    region = camadas['region']
    region_geom = camadas['region_geom']
    mascara_agua = camadas['mascara_agua']
    viirs_agua = camadas['viirs_agua']

    fundo_cinza = ee.Image.constant(COR_TERRA).clip(region_geom).visualize(min=0, max=255)
    mapa_luz = viirs_agua.visualize(min=0, max=MAX_VIIRS, palette=PALETA_EXPOSICAO)
    mapa_tematico = fundo_cinza.blend(mapa_luz)
    return mapa_tematico.getThumbURL({'region': region, 'dimensions': DIMENSOES_PNG})


def output_filename(cidade):
    return f"{cidade['arquivo'].replace('_', '-')}-exposure-gradient.png"


def baixar_imagem(url, caminho):
    urllib.request.urlretrieve(url, caminho)
    print(f"Saved image: {caminho}")


if __name__ == '__main__':
    inicializar_earth_engine()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for cidade in CIDADES:
        print(f"\n{cidade['nome']}")
        url = mapa_exposicao(cidade)
        caminho_png = OUTPUT_DIR / output_filename(cidade)
        baixar_imagem(url, caminho_png)

    print("\nWater-light exposure maps generated.")

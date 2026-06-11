import os
import urllib.request

import ee

from etapa4_separacao_agua_terra import (
    CIDADES,
    COR_TERRA,
    DIMENSOES_PNG,
    construir_camadas,
    inicializar_earth_engine,
)

CLASSES = [1.0, 3, 10]
PALETA_EXPOSICAO = ['#08081f', '#1f6feb', '#f5d020', '#e8000b']

PASTA_SAIDA = 'saida_etapa6'


def mapa_exposicao(cidade):
    camadas = construir_camadas(cidade)
    region = camadas['region']
    region_geom = camadas['region_geom']
    mascara_agua = camadas['mascara_agua']
    viirs_agua = camadas['viirs_agua']

    classe = (
        viirs_agua.gte(CLASSES[0])
        .add(viirs_agua.gte(CLASSES[1]))
        .add(viirs_agua.gte(CLASSES[2]))
        .updateMask(mascara_agua)
    )

    fundo_cinza = ee.Image.constant(COR_TERRA).clip(region_geom).visualize(min=0, max=255)
    mapa_classe = classe.visualize(min=0, max=3, palette=PALETA_EXPOSICAO)
    mapa_tematico = fundo_cinza.blend(mapa_classe)
    return mapa_tematico.getThumbURL({'region': region, 'dimensions': DIMENSOES_PNG})


def baixar_imagem(url, caminho):
    urllib.request.urlretrieve(url, caminho)
    print(f"Imagem salva em: {caminho}")


if __name__ == '__main__':
    inicializar_earth_engine()
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    for cidade in CIDADES:
        print(f"\n{cidade['nome']}")
        url = mapa_exposicao(cidade)
        caminho_png = os.path.join(PASTA_SAIDA, f"mapa_exposicao_{cidade['arquivo']}.png")
        baixar_imagem(url, caminho_png)

    print("\nAnalise da Etapa 6 concluida.")

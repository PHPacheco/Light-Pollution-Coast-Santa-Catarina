import ee

# ID do seu projeto do Google Cloud
PROJECT_ID = 'processamento-de-imagem-496515'


def inicializar_earth_engine():
    try:
        ee.Initialize(project=PROJECT_ID)
        print("Google Earth Engine inicializado com sucesso!")
    except Exception as e:
        print(f"Nao foi possivel inicializar diretamente: {e}")
        print("Iniciando fluxo de autenticacao...")
        ee.Authenticate()
        ee.Initialize(project=PROJECT_ID)
        print("Google Earth Engine autenticado e inicializado com sucesso!")


def criar_imagem_cidade(cidade):
    lon = cidade['longitude']
    lat = cidade['latitude']
    roi = ee.Geometry.Point([lon, lat]).buffer(cidade['buffer_m']).bounds()
    region = roi.bounds().getInfo()

    # Carregar e filtrar a colecao de imagens usando o ID completo correto.
    dataset = (
        ee.ImageCollection('NASA/VIIRS/002/VNP46A2')
        .filterBounds(roi)
        .filterDate(DATA_INICIO, DATA_FIM)
    )

    # Selecionar a banda de radiancia noturna corrigida.
    imagem_luzes = dataset.select('DNB_BRDF_Corrected_NTL')

    # Reduzir a colecao diaria para uma unica imagem, usando a mediana para limpar ruidos.
    imagem_final = imagem_luzes.median().clip(roi)

    # Parametros corrigidos para VISUALIZACAO em alta qualidade (PNG).
    parametros_visao = {
        'min': 0,
        'max': 60,  # Mantido o max original que voce validou
        'palette': ['black', 'blue', 'purple', 'yellow', 'white'],
        'region': region,
        'dimensions': 1024,  # PNG com 1024px de largura
    }

    parametros_download = {
        'name': f"{cidade['arquivo']}_viirs_luzes_noturnas",
        'scale': 500,
        'crs': 'EPSG:4326',
        'region': region['coordinates'],
    }

    return {
        'visualizacao': imagem_final.getThumbURL(parametros_visao),
        'download': imagem_final.getDownloadURL(parametros_download),
    }


DATA_INICIO = '2026-01-01'
DATA_FIM = '2026-01-31'

CIDADES = [
    {
        'nome': 'Florianopolis',
        'latitude': -27.5969,
        'longitude': -48.5468,
        'arquivo': 'florianopolis',
        'buffer_m': 27500,
    },
    {
        'nome': 'Balneario Camboriu',
        'latitude': -26.9980,
        'longitude': -48.6326,
        'arquivo': 'balneario_camboriu',
        'buffer_m': 27500,
    },
    {
        'nome': 'Itajai',
        'latitude': -26.9083,
        'longitude': -48.6775,
        'arquivo': 'itajai',
        'buffer_m': 27500,
    },
]


inicializar_earth_engine()

for cidade in CIDADES:
    urls = criar_imagem_cidade(cidade)

    print(f"\n{cidade['nome']}")
    print(f"Coordenadas: {cidade['latitude']}, {cidade['longitude']}")
    print(f"Imagem VIIRS de luzes noturnas (PNG):\n{urls['visualizacao']}\n")
    print(f"Download VIIRS em alta resolucao (ZIP/GeoTIFF):\n{urls['download']}")

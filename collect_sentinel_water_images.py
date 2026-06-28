import ee

from earth_engine_config import obter_project_id


def inicializar_earth_engine():
    project_id = obter_project_id()
    try:
        ee.Initialize(project=project_id)
        print("Google Earth Engine inicializado com sucesso!")
    except Exception as e:
        print(f"Nao foi possivel inicializar diretamente: {e}")
        print("Iniciando fluxo de autenticacao...")
        ee.Authenticate()
        ee.Initialize(project=project_id)
        print("Google Earth Engine autenticado e inicializado com sucesso!")


def criar_imagem_cidade(cidade):
    lon = cidade['longitude']
    lat = cidade['latitude']
    region_geom = ee.Geometry.Point([lon, lat]).buffer(cidade['buffer_m']).bounds()
    region = region_geom.getInfo()

    dataset = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(region_geom)
        .filterDate(DATA_INICIO, DATA_FIM)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', MAX_NUVENS))
        .select(['B2', 'B3', 'B4', 'B11'])
    )

    imagem = dataset.median().clip(region_geom)

    # MNDWI: valores mais altos tendem a ser agua; valores baixos tendem a ser terra.
    mndwi = imagem.normalizedDifference(['B3', 'B11']).rename('MNDWI')

    parametros_rgb = {
        'bands': ['B4', 'B3', 'B2'],
        'min': 0,
        'max': 3000,
        'region': region,
        'dimensions': DIMENSOES_PNG,
    }

    parametros_mndwi = {
        'min': -0.5,
        'max': 0.5,
        'palette': ['8c510a', 'f6e8c3', 'c7eae5', '01665e'],
        'region': region,
        'dimensions': DIMENSOES_PNG,
    }

    parametros_download = {
        'name': f"{cidade['arquivo']}_sentinel2_mndwi",
        'scale': 30,
        'crs': 'EPSG:4326',
        'region': region['coordinates'],
    }

    return {
        'rgb': imagem.getThumbURL(parametros_rgb),
        'mndwi': mndwi.getThumbURL(parametros_mndwi),
        'download': mndwi.getDownloadURL(parametros_download),
    }


DATA_INICIO = '2026-01-01'
DATA_FIM = '2026-01-31'
MAX_NUVENS = 20
DIMENSOES_PNG = 1024

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
    print(f"Imagem RGB Sentinel-2 (PNG):\n{urls['rgb']}\n")
    print(f"Imagem MNDWI para distinguir agua/terra (PNG):\n{urls['mndwi']}\n")
    print(f"Download MNDWI em alta resolucao (ZIP/GeoTIFF):\n{urls['download']}")

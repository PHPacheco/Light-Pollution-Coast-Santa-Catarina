import ee

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


def criar_separacao_cidade(cidade):
    lon = cidade['longitude']
    lat = cidade['latitude']
    region_geom = ee.Geometry.Point([lon, lat]).buffer(cidade['buffer_m']).bounds()
    region = region_geom.getInfo()

    s2 = (
        ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
        .filterBounds(region_geom)
        .filterDate(DATA_INICIO, DATA_FIM)
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', MAX_NUVENS))
        .select(['B3', 'B11'])
        .median()
        .clip(region_geom)
    )
    mndwi = s2.normalizedDifference(['B3', 'B11']).rename('MNDWI')

    mascara_agua = mndwi.gt(LIMIAR_AGUA)

    viirs = (
        ee.ImageCollection('NASA/VIIRS/002/VNP46A2')
        .filterBounds(region_geom)
        .filterDate(DATA_INICIO, DATA_FIM)
        .select('DNB_BRDF_Corrected_NTL')
        .median()
        .clip(region_geom)
    )
    viirs_agua = viirs.updateMask(mascara_agua)

    fundo_cinza = ee.Image.constant(COR_TERRA).clip(region_geom)
    viirs_rgb = viirs_agua.visualize(
        min=0,
        max=MAX_VIIRS,
        palette=['black', 'blue', 'purple', 'yellow', 'white'],
    )
    viirs_sobre_terra = fundo_cinza.visualize(min=0, max=255).blend(viirs_rgb)

    parametros_mndwi = {
        'min': -0.5,
        'max': 0.5,
        'palette': ['8c510a', 'f6e8c3', 'c7eae5', '01665e'],
        'region': region,
        'dimensions': DIMENSOES_PNG,
    }

    parametros_mascara = {
        'min': 0,
        'max': 1,
        'palette': ['black', 'cyan'],
        'region': region,
        'dimensions': DIMENSOES_PNG,
    }

    parametros_viirs = {
        'region': region,
        'dimensions': DIMENSOES_PNG,
    }

    return {
        'mndwi': mndwi.getThumbURL(parametros_mndwi),
        'mascara': mascara_agua.getThumbURL(parametros_mascara),
        'viirs_agua': viirs_sobre_terra.getThumbURL(parametros_viirs),
    }


DATA_INICIO = '2026-01-01'
DATA_FIM = '2026-01-31'
MAX_NUVENS = 20
DIMENSOES_PNG = 1024
LIMIAR_AGUA = 0.0  # MNDWI > 0 tende a ser agua (padrao da literatura)
MAX_VIIRS = 60
COR_TERRA = [128, 128, 128]  # cinza solido para a terra, como no artigo

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
    urls = criar_separacao_cidade(cidade)

    print(f"\n{cidade['nome']}")
    print(f"Coordenadas: {cidade['latitude']}, {cidade['longitude']}")
    print(f"MNDWI continuo (PNG):\n{urls['mndwi']}\n")
    print(f"Mascara binaria de agua (PNG):\n{urls['mascara']}\n")
    print(f"VIIRS noturno apenas sobre agua (PNG):\n{urls['viirs_agua']}")

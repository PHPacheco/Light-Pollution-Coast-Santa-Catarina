import ee

# ID do seu projeto do Google Cloud
PROJECT_ID = 'processamento-de-imagem-496515'

try:
    ee.Initialize(project=PROJECT_ID)
    print("Google Earth Engine inicializado com sucesso!")
except Exception as e:
    print(f"Não foi possível inicializar diretamente: {e}")
    print("Iniciando fluxo de autenticação...")
    ee.Authenticate()
    ee.Initialize(project=PROJECT_ID)
    print("Google Earth Engine autenticado e inicializado com sucesso!")

lon, lat = -48.6356, -26.9926 # Balneário Camboriú (Longitude, Latitude)
roi = ee.Geometry.Point([lon, lat]).buffer(150000) # Buffer de 15km para cobrir a cidade e arredores

data_inicio = '2026-01-01'
data_fim = '2026-01-31'

# Carregar e filtrar a coleção de imagens usando o ID completo correto
dataset = (ee.ImageCollection('NASA/VIIRS/002/VNP46A2')
           .filterBounds(roi)
           .filterDate(data_inicio, data_fim))

# Selecionar a banda de radiância noturna corrigida
imagem_luzes = dataset.select('DNB_BRDF_Corrected_NTL')

# Reduzir a coleção diária para uma única imagem (usando a mediana para limpar nuvens)
imagem_final = imagem_luzes.median().clip(roi)

# Parâmetros corrigidos para VISUALIZAÇÃO em alta qualidade (PNG)
parametros_visao = {
    'min': 0,
    'max': 60, # Mantido o max original que você validou
    'palette': ['black', 'blue', 'purple', 'yellow', 'white'],
    'region': roi.bounds().getInfo(),
    'dimensions': 1024 # PNG com 1024px de largura
}

url_thumbnail = imagem_final.getThumbURL(parametros_visao)

parametros_download = {
    'name': 'luzes_noturnas_bc_alta_resolucao',
    'scale': 500,
    'crs': 'EPSG:4326',
    'region': roi.bounds().getInfo()['coordinates']
}

url_download = imagem_final.getDownloadURL(parametros_download)

print(f"Link para visualizar a imagem nítida (PNG):\n{url_thumbnail}\n")
print(f"Link para baixar o arquivo original de alta resolução (ZIP/GeoTIFF):\n{url_download}")
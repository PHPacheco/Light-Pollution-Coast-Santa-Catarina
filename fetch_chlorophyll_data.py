"""Prioridade 3 - Clorofila-a como proxy de produtividade/area de alimentacao.

Consulta servidores ERDDAP (NOAA CoastWatch) por clorofila-a mensal sobre a
caixa delimitadora de cada cidade, interpola para o tamanho da imagem do projeto
e salva um array normalizado em [0,1] que o `ecological_risk_analysis.py` usa
para substituir o `productivity_proxy` calculado por distancia da costa.

Se nenhum dataset ERDDAP responder, o pipeline principal mantem o proxy atual.
So usa biblioteca padrao (urllib + csv) mais NumPy, que ja e dependencia do projeto.
"""

from io import StringIO
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen
import csv
import math

import numpy as np

ROOT = Path(__file__).resolve().parent
IMAGES_DIR = ROOT / "Images"
DATA_DIR = ROOT / "Data" / "ecological-risk"
CHL_DIR = DATA_DIR / "chlorophyll"

HTTP_TIMEOUT = 20

# Datasets griddap a tentar em ordem; (id, variavel, data) cobrem clorofila mensal.
# A data alvo aproxima janeiro/2026; se indisponivel, o servidor recusa e tentamos
# o proximo dataset (que pode ter periodo de cobertura diferente).
ERDDAP_BASE = "https://coastwatch.pfeg.noaa.gov/erddap/griddap"
ERDDAP_DATASETS = [
    {"id": "erdVHNchlamday", "var": "chla", "time": "2026-01-16T12:00:00Z"},
    {"id": "erdMBchla1mday", "var": "chlorophyll", "time": "2026-01-16T12:00:00Z"},
    {"id": "erdVH2018chla1mday", "var": "chla", "time": "2022-01-16T12:00:00Z"},
]

CITIES = [
    {"name": "Florianopolis", "slug": "florianopolis", "buffer_m": 27500,
     "lat": -27.5954, "lon": -48.5480},
    {"name": "Balneario Camboriu", "slug": "balneario-camboriu", "buffer_m": 27500,
     "lat": -26.9904, "lon": -48.6345},
    {"name": "Itajai", "slug": "itajai", "buffer_m": 27500,
     "lat": -26.9081, "lon": -48.6617},
]


def bounding_box(city):
    radius_m = city["buffer_m"]
    dlat = radius_m / 111_320.0
    dlon = radius_m / (111_320.0 * math.cos(math.radians(city["lat"])))
    return {
        "lat_min": city["lat"] - dlat,
        "lat_max": city["lat"] + dlat,
        "lon_min": city["lon"] - dlon,
        "lon_max": city["lon"] + dlon,
    }


def image_shape(city):
    """Altura, largura da imagem de exposicao da cidade (para interpolar a grade)."""
    from PIL import Image

    path = IMAGES_DIR / "exposure-gradient" / f"{city['slug']}-exposure-gradient.png"
    with Image.open(path) as image:
        return image.height, image.width


def build_url(dataset, box):
    """Monta a URL griddap .csv. ERDDAP ordena lat conforme o dataset; pedimos a
    faixa nos dois sentidos via min:max e tratamos a ordem ao parsear."""
    var = dataset["var"]
    sel = (
        f"{var}[({dataset['time']})]"
        f"[({box['lat_min']}):({box['lat_max']})]"
        f"[({box['lon_min']}):({box['lon_max']})]"
    )
    return f"{ERDDAP_BASE}/{dataset['id']}.csv?{quote(sel, safe='()[]:.,-')}"


def parse_griddap_csv(text, var):
    """Le o CSV do ERDDAP em uma grade 2D (lat x lon) de valores do var.

    O CSV tem cabecalho + linha de unidades, depois linhas
    time,latitude,longitude,<var>. Reconstroi a grade pelos eixos unicos.
    """
    reader = csv.reader(StringIO(text))
    rows = list(reader)
    if len(rows) < 3:
        raise ValueError("CSV do ERDDAP sem linhas de dados")

    header = rows[0]
    lat_idx = header.index("latitude")
    lon_idx = header.index("longitude")
    var_idx = header.index(var)

    lats, lons, points = [], [], {}
    for row in rows[2:]:  # pula cabecalho e linha de unidades
        if not row or not row[var_idx].strip():
            continue
        try:
            lat = float(row[lat_idx])
            lon = float(row[lon_idx])
            value = float(row[var_idx])
        except ValueError:
            continue
        if math.isnan(value):
            continue
        lats.append(lat)
        lons.append(lon)
        points[(lat, lon)] = value

    if not points:
        raise ValueError("Nenhum ponto valido de clorofila no CSV")

    unique_lats = sorted(set(lats))
    unique_lons = sorted(set(lons))
    grid = np.full((len(unique_lats), len(unique_lons)), np.nan, dtype=np.float32)
    lat_pos = {lat: i for i, lat in enumerate(unique_lats)}
    lon_pos = {lon: j for j, lon in enumerate(unique_lons)}
    for (lat, lon), value in points.items():
        grid[lat_pos[lat], lon_pos[lon]] = value

    # grade indexada por lat crescente (sul->norte) e lon crescente (oeste->leste)
    return grid


def fill_nan(grid):
    """Substitui NaN (nuvem/terra) pela media valida, para nao furar a interpolacao."""
    if np.isnan(grid).all():
        raise ValueError("Grade de clorofila totalmente vazia")
    mean_value = float(np.nanmean(grid))
    return np.where(np.isnan(grid), mean_value, grid)


def resize_bilinear(grid, shape):
    """Interpola a grade (lat x lon) para (altura, largura) da imagem.

    A grade vem com lat crescente (sul no topo do array); a imagem tem norte no
    topo, entao invertemos o eixo de latitude ao reamostrar.
    """
    from PIL import Image

    grid = grid[::-1, :]  # norte no topo
    pil = Image.fromarray(grid.astype(np.float32), mode="F")
    resized = pil.resize((shape[1], shape[0]), Image.Resampling.BILINEAR)
    return np.asarray(resized, dtype=np.float32)


def normalize_log(array):
    """Escala log relativa ao maximo -> [0,1]."""
    array = np.clip(array, 0.0, None)
    max_value = float(array.max())
    if max_value <= 0:
        return np.zeros_like(array)
    return np.clip(np.log1p(array) / math.log1p(max_value), 0.0, 1.0)


def fetch_city_chlorophyll(city):
    box = bounding_box(city)
    shape = image_shape(city)
    last_error = None
    for dataset in ERDDAP_DATASETS:
        url = build_url(dataset, box)
        try:
            request = Request(url, headers={"User-Agent": "light-pollution-sc/1.0"})
            with urlopen(request, timeout=HTTP_TIMEOUT) as response:
                text = response.read().decode("utf-8")
            grid = parse_griddap_csv(text, dataset["var"])
            grid = fill_nan(grid)
            resized = resize_bilinear(grid, shape)
            normalized = normalize_log(resized)
            print(f"Clorofila {city['slug']:>20} via {dataset['id']} "
                  f"(grade {grid.shape} -> imagem {normalized.shape})")
            return normalized, dataset["id"]
        except Exception as error:
            last_error = error
            continue
    print(f"Clorofila {city['slug']:>20} indisponivel ({last_error})")
    return None, None


def main():
    CHL_DIR.mkdir(parents=True, exist_ok=True)
    used = {}
    for city in CITIES:
        array, dataset_id = fetch_city_chlorophyll(city)
        if array is None:
            continue
        output = CHL_DIR / f"{city['slug']}_chlorophyll.npy"
        np.save(output, array)
        used[city["slug"]] = dataset_id

    if used:
        print(f"\nSaved chlorophyll arrays for: {', '.join(used)}")
    else:
        print("\nNenhum dado de clorofila salvo; o pipeline usara o proxy por distancia.")


if __name__ == "__main__":
    main()

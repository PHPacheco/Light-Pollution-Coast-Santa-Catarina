"""Prioridade 3 - Sobreposicao de unidades de conservacao (CNUC/MMA).

Projeta poligonos de unidades de conservacao costeiras/marinhas sobre as
coordenadas de pixel de cada cidade e desenha o contorno sobre o mapa de indice
ecologico. Permite "defender" os resultados mostrando onde a luz/risco coincide
com areas legalmente protegidas.

A projecao e local e equiretangular: cada imagem cobre um quadrado de
`buffer_m * 2` metros centrado em (lat, lon) da cidade, com norte no topo. Isso e
coerente com o recorte circular usado no restante do projeto.

So usa NumPy + Pillow (ja dependencias) - sem geopandas/shapely.
"""

from pathlib import Path
import csv
import json
import math

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "Data" / "ecological-risk"
OUTPUT_DIR = ROOT / "EcologicalRiskImages"
PROTECTED_DIR = OUTPUT_DIR / "06-protected-areas"
PROTECTED_DATA_DIR = DATA_DIR / "protected_areas"
PROTECTED_CSV = PROTECTED_DATA_DIR / "protected_areas_catalog.csv"
PROTECTED_GEOJSON_CANDIDATES = [
    PROTECTED_DATA_DIR / "protected_areas.geojson",
    PROTECTED_DATA_DIR / "cnuc_sc.geojson",
    PROTECTED_DATA_DIR / "cnuc_mma.geojson",
]

EARTH_M_PER_DEG_LAT = 111_320.0


def _circle_polygon(center, radius_m, sides=24):
    """Aproxima um circulo (centro lat/lon, raio em metros) por um poligono."""
    lat0, lon0 = center
    m_per_deg_lon = EARTH_M_PER_DEG_LAT * math.cos(math.radians(lat0))
    verts = []
    for i in range(sides):
        angle = 2.0 * math.pi * i / sides
        dlat = (radius_m * math.cos(angle)) / EARTH_M_PER_DEG_LAT
        dlon = (radius_m * math.sin(angle)) / m_per_deg_lon
        verts.append((lat0 + dlat, lon0 + dlon))
    return verts


PROTECTED_AREAS = [
    {
        "name": "APA de Anhatomirim",
        "code": "APA-ANHATOMIRIM",
        "color": "#00dd88",
        # Baia Norte de Florianopolis, em torno da Ilha de Anhatomirim.
        "polygon": [
            (-27.48, -48.66), (-27.38, -48.60), (-27.30, -48.54),
            (-27.31, -48.47), (-27.43, -48.46), (-27.50, -48.56),
        ],
    },
    {
        "name": "REBIO Marinha do Arvoredo",
        "code": "REBIO-ARVOREDO",
        "color": "#ff4444",
        # Arquipelago do Arvoredo, ~50 km ao norte do centro de Florianopolis.
        "polygon": _circle_polygon((-27.18, -48.37), 8000),
    },
    {
        "name": "APA da Baleia Franca",
        "code": "APA-BALEIA-FRANCA",
        "color": "#4488ff",
        # Faixa costeira do sul de SC; limite norte ~28S, fora dos buffers atuais.
        "polygon": [
            (-28.00, -49.20), (-28.00, -47.80),
            (-29.20, -47.80), (-29.20, -49.20),
        ],
    },
    {
        "name": "APA Costa Brava",
        "code": "APA-COSTA-BRAVA",
        "color": "#00e5ff",
        # APA municipal de Balneario Camboriu (Lei 1985/2000): faixa costeira das
        # Interpraias, de Ponta das Laranjeiras a Estaleirinho/Ponta do Malta,
        # incluindo o mar adjacente. Praia do Estaleiro ~-27.03,-48.58.
        "polygon": [
            (-26.992, -48.605), (-27.022, -48.598), (-27.045, -48.595),
            (-27.078, -48.593),
            (-27.078, -48.562), (-27.045, -48.560), (-27.022, -48.563),
            (-26.992, -48.576),
        ],
    },
    {
        "name": "Parque Natural Municipal do Atalaia",
        "code": "PNM-ATALAIA",
        "color": "#ff33cc",
        # UC municipal de Itajai (Decreto, 2007), bairro Fazenda/Cabecudas, junto
        # a foz do Itajai-Acu. Poligono aproximado (~19 ha na realidade).
        "polygon": [
            (-26.915, -48.650), (-26.915, -48.636),
            (-26.932, -48.636), (-26.932, -48.650),
        ],
    },
]


def _color_for_index(idx):
    palette = ["#00dd88", "#ff4444", "#4488ff", "#00e5ff", "#ff33cc", "#ffaa00", "#7c3aed"]
    return palette[idx % len(palette)]


def _normalise_area(area, idx=0):
    polygons = area.get("polygons")
    if polygons is None and "polygon" in area:
        polygons = [area["polygon"]]
    return {
        "name": area.get("name", f"UC {idx + 1}"),
        "code": area.get("code", ""),
        "color": area.get("color") or _color_for_index(idx),
        "source": area.get("source", "catalogo interno"),
        "boundary_type": area.get("boundary_type", "poligono aproximado"),
        "polygons": polygons or [],
    }


def _parse_polygon_json(text):
    data = json.loads(text)
    if not data:
        return []
    # Aceita tanto [[lat, lon], ...] quanto [[[lat, lon], ...], ...].
    first = data[0]
    if first and isinstance(first[0], (int, float)):
        return [data]
    return data


def load_csv_catalog(path):
    areas = []
    with path.open("r", encoding="utf-8", newline="") as file:
        for idx, row in enumerate(csv.DictReader(file)):
            polygon_text = row.get("polygon_json", "").strip()
            if not polygon_text:
                continue
            area = {
                "name": row.get("name", "").strip(),
                "code": row.get("code", "").strip(),
                "color": row.get("color", "").strip(),
                "source": row.get("source", "").strip() or "catalogo CSV local",
                "boundary_type": row.get("boundary_type", "").strip() or "poligono aproximado",
                "polygons": _parse_polygon_json(polygon_text),
            }
            areas.append(_normalise_area(area, idx))
    return areas


def _property_value(properties, candidates, fallback=""):
    for key in candidates:
        value = properties.get(key)
        if value not in (None, ""):
            return str(value)
    return fallback


def _geojson_polygons(geometry):
    if not geometry:
        return []
    gtype = geometry.get("type")
    coordinates = geometry.get("coordinates") or []
    polygons = []
    if gtype == "Polygon":
        if coordinates:
            polygons.append([(lat, lon) for lon, lat, *_ in coordinates[0]])
    elif gtype == "MultiPolygon":
        for polygon in coordinates:
            if polygon:
                polygons.append([(lat, lon) for lon, lat, *_ in polygon[0]])
    return polygons


def load_geojson_catalog(path):
    payload = json.loads(path.read_text(encoding="utf-8"))
    features = payload.get("features", [])
    areas = []
    for idx, feature in enumerate(features):
        properties = feature.get("properties") or {}
        polygons = _geojson_polygons(feature.get("geometry"))
        if not polygons:
            continue
        name = _property_value(
            properties,
            ["name", "nome", "nome_uc", "NOME_UC", "nm_uc", "NOME", "unidade", "UC"],
            f"UC {idx + 1}",
        )
        code = _property_value(
            properties,
            ["code", "codigo", "cod_uc", "CNUC", "cnuc", "id", "ID"],
            "",
        )
        area = {
            "name": name,
            "code": code,
            "color": _color_for_index(idx),
            "source": str(path),
            "boundary_type": "limite vetorial externo (GeoJSON)",
            "polygons": polygons,
        }
        areas.append(_normalise_area(area, idx))
    return areas


def load_protected_areas():
    for path in PROTECTED_GEOJSON_CANDIDATES:
        if path.exists():
            areas = load_geojson_catalog(path)
            if areas:
                return areas, {
                    "catalog_source": "GeoJSON externo (preferencial para CNUC/MMA)",
                    "catalog_paths": [str(path)],
                }
    if PROTECTED_CSV.exists():
        areas = load_csv_catalog(PROTECTED_CSV)
        if areas:
            return areas, {
                "catalog_source": "CSV local de UCs costeiras",
                "catalog_paths": [str(PROTECTED_CSV)],
            }

    areas = [_normalise_area(area, idx) for idx, area in enumerate(PROTECTED_AREAS)]
    return areas, {
        "catalog_source": "catalogo interno aproximado",
        "catalog_paths": [],
    }


def load_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def latlon_to_pixel(lat, lon, city, pixel_m, img_shape):
    """Converte (lat, lon) em coordenadas de pixel (x, y) da imagem da cidade."""
    height, width = img_shape
    m_per_deg_lon = EARTH_M_PER_DEG_LAT * math.cos(math.radians(city["lat"]))
    dx_m = (lon - city["lon"]) * m_per_deg_lon  # leste positivo
    dy_m = (lat - city["lat"]) * EARTH_M_PER_DEG_LAT  # norte positivo
    px = width / 2.0 + dx_m / pixel_m
    py = height / 2.0 - dy_m / pixel_m  # norte no topo
    return px, py


def polygon_pixels(area, city, pixel_m, img_shape):
    """Lista de aneis em pixels para a UC."""
    return [
        [latlon_to_pixel(lat, lon, city, pixel_m, img_shape) for lat, lon in polygon]
        for polygon in area["polygons"]
    ]


# Numero minimo de pixels de interseccao para uma UC ser desenhavel (evita
# slivers de 1-2 pixels). O criterio principal de "dentro do buffer" e o
# centroide da UC, nao a area: assim UCs pequenas mas internas (ex.: PNM Atalaia,
# ~19 ha) entram, e UCs grandes mas externas que so roçam a borda (ex.: REBIO
# Arvoredo) ficam de fora.
MIN_OVERLAP_PX = 50


def centroid_latlon(area):
    """Centroide aproximado (media dos vertices) do poligono da UC."""
    verts = [vertex for polygon in area["polygons"] for vertex in polygon]
    if not verts:
        return 0.0, 0.0
    lat = sum(v[0] for v in verts) / len(verts)
    lon = sum(v[1] for v in verts) / len(verts)
    return lat, lon


def distance_m(lat1, lon1, lat2, lon2):
    """Distancia equiretangular aproximada em metros entre dois pontos."""
    m_per_deg_lon = EARTH_M_PER_DEG_LAT * math.cos(math.radians((lat1 + lat2) / 2.0))
    dy = (lat1 - lat2) * EARTH_M_PER_DEG_LAT
    dx = (lon1 - lon2) * m_per_deg_lon
    return math.hypot(dx, dy)


def polygon_to_mask(pixel_rings, img_shape):
    """Mascara binaria do poligono (em pixels) com o tamanho da imagem."""
    height, width = img_shape
    layer = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(layer)
    for pixels in pixel_rings:
        if len(pixels) >= 3:
            draw.polygon(pixels, fill=255)
    return np.asarray(layer, dtype=np.uint8) > 127


def circular_roi_mask(city, pixel_m, img_shape):
    """Recorte circular de raio `buffer_m` (a regiao real analisada no projeto).

    A imagem e quadrada (lado 2*buffer_m), mas a analise usa um circulo inscrito.
    UCs que so aparecem nos cantos do quadrado estao fora do buffer real."""
    height, width = img_shape
    cy, cx = height / 2.0, width / 2.0
    radius_px = city["buffer_m"] / pixel_m
    yy, xx = np.ogrid[:height, :width]
    return ((yy - cy) ** 2 + (xx - cx) ** 2) <= radius_px ** 2


def polygon_outline_mask(pixel_rings, img_shape, line_width=3):
    """Mascara do contorno (fechado) do poligono, em pixels."""
    height, width = img_shape
    layer = Image.new("L", (width, height), 0)
    draw = ImageDraw.Draw(layer)
    for pixels in pixel_rings:
        if len(pixels) >= 2:
            draw.line(list(pixels) + [pixels[0]], fill=255, width=line_width)
    return np.asarray(layer, dtype=np.uint8) > 127


def draw_overlay(base_image, intersecting, city_name, roi):
    """Desenha os contornos das UCs (recortados ao buffer circular) e a legenda.

    `intersecting` e uma lista de (area, pixels); `roi` e a mascara do recorte
    circular, usada para nunca desenhar linhas fora da regiao analisada."""
    # Pinta os contornos no plano da imagem (mesmas coordenadas dos pixels).
    base_arr = np.asarray(base_image.convert("RGB"), dtype=np.uint8).copy()
    img_shape = base_arr.shape[:2]
    for area, pixels in intersecting:
        outline = polygon_outline_mask(pixels, img_shape) & roi
        base_arr[outline] = ImageColor.getrgb(area["color"])
    painted = Image.fromarray(base_arr, mode="RGB")

    legend_h = 30 + 26 * max(1, len(intersecting))
    title_h = 46
    canvas = Image.new("RGB", (painted.width, painted.height + title_h + legend_h), "white")
    draw = ImageDraw.Draw(canvas)
    font_title = load_font(24, bold=True)
    font = load_font(17)

    title = f"{city_name} - risco x unidades de conservacao"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    draw.text(((painted.width - (bbox[2] - bbox[0])) / 2, 11), title,
              font=font_title, fill="#111111")
    canvas.paste(painted, (0, title_h))

    y = title_h + painted.height + 12
    for area, _ in intersecting:
        draw.rectangle([20, y, 48, y + 18], outline=area["color"], width=3)
        draw.text((58, y - 1), area["name"], font=font, fill="#111111")
        y += 26
    if not intersecting:
        draw.text((20, y), "Nenhuma UC catalogada dentro do buffer desta cidade.",
                  font=font, fill="#555555")
    return canvas


def _risk_base_image(result):
    """Imagem crua do indice de risco (sem titulo/legenda), alinhada aos pixels.

    Prefere a imagem ja renderizada em memoria (`result['risk_image']`); como
    alternativa, le a imagem salva da etapa 04 (que inclui titulo/legenda e por
    isso desalinha levemente os poligonos)."""
    base = result.get("risk_image")
    if base is not None:
        return base.convert("RGB")
    slug = result["city"]["slug"]
    path = OUTPUT_DIR / "04-ecological-risk-index" / f"{slug}-ecological-risk-index.png"
    if path.exists():
        return Image.open(path).convert("RGB")
    return None


def generate_all_overlays(results):
    """Gera um mapa de sobreposicao por cidade. `results` vem de analyze_city().

    Cada result precisa de: result['city'] (com lat/lon), result['mask'] (shape da
    imagem analisada) e result['pixel_m']. Retorna info por cidade para o relatorio.
    """
    PROTECTED_DIR.mkdir(parents=True, exist_ok=True)
    areas, catalog_info = load_protected_areas()
    report = {
        "by_city": {},
        "catalog_source": catalog_info["catalog_source"],
        "catalog_paths": catalog_info["catalog_paths"],
        "catalog_areas": [
            {
                "name": area["name"],
                "code": area.get("code", ""),
                "source": area.get("source", ""),
                "boundary_type": area.get("boundary_type", ""),
            }
            for area in areas
        ],
    }

    for result in results:
        city = result["city"]
        img_shape = result["mask"].shape
        pixel_m = result["pixel_m"]
        roi = circular_roi_mask(city, pixel_m, img_shape)

        intersecting = []
        for area in areas:
            pixels = polygon_pixels(area, city, pixel_m, img_shape)
            mask = polygon_to_mask(pixels, img_shape)
            overlap = int((mask & roi).sum())
            clat, clon = centroid_latlon(area)
            inside_buffer = distance_m(clat, clon, city["lat"], city["lon"]) <= city["buffer_m"]
            if inside_buffer and overlap >= MIN_OVERLAP_PX:
                intersecting.append((area, pixels))

        base = _risk_base_image(result)
        if base is None:
            # fundo cinza neutro caso a etapa 04 ainda nao tenha rodado
            base = Image.new("RGB", (img_shape[1], img_shape[0]), (128, 128, 128))

        overlay = draw_overlay(base, intersecting, city["name"], roi)
        output = PROTECTED_DIR / f"{city['slug']}-risk-protected-areas.png"
        overlay.save(output)

        report["by_city"][city["slug"]] = [area["name"] for area, _ in intersecting]
        names = ", ".join(report["by_city"][city["slug"]]) or "nenhuma"
        print(f"UCs em {city['name']:>20}: {names}")

    return report


if __name__ == "__main__":
    print("Este modulo e chamado por ecological_risk_analysis.py com os resultados.")
    areas, catalog_info = load_protected_areas()
    print(f"Fonte: {catalog_info['catalog_source']}")
    print("UCs catalogadas:")
    for area in areas:
        print(f"  - {area['name']} ({area['code']})")

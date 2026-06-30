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
import math

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = ROOT / "EcologicalRiskImages"
PROTECTED_DIR = OUTPUT_DIR / "06-protected-areas"

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
]


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
    """Lista de vertices (x, y) em pixel para o poligono da UC."""
    return [
        latlon_to_pixel(lat, lon, city, pixel_m, img_shape)
        for lat, lon in area["polygon"]
    ]


# Fracao minima do buffer circular que uma UC precisa cobrir para ser mapeada.
# Evita que uma UC apenas "roce" a borda do recorte (artefato de canto da imagem
# quadrada) seja rotulada como dentro do buffer.
MIN_OVERLAP_FRACTION = 0.01


def polygon_to_mask(pixels, img_shape):
    """Mascara binaria do poligono (em pixels) com o tamanho da imagem."""
    height, width = img_shape
    layer = Image.new("L", (width, height), 0)
    ImageDraw.Draw(layer).polygon(pixels, fill=255)
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


def polygon_outline_mask(pixels, img_shape, line_width=3):
    """Mascara do contorno (fechado) do poligono, em pixels."""
    height, width = img_shape
    layer = Image.new("L", (width, height), 0)
    ImageDraw.Draw(layer).line(list(pixels) + [pixels[0]], fill=255, width=line_width)
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
    report = {}

    for result in results:
        city = result["city"]
        img_shape = result["mask"].shape
        pixel_m = result["pixel_m"]
        roi = circular_roi_mask(city, pixel_m, img_shape)
        min_overlap = MIN_OVERLAP_FRACTION * float(roi.sum())

        intersecting = []
        for area in PROTECTED_AREAS:
            pixels = polygon_pixels(area, city, pixel_m, img_shape)
            mask = polygon_to_mask(pixels, img_shape)
            overlap = float((mask & roi).sum())  # interseccao com o buffer circular
            if overlap >= min_overlap:
                intersecting.append((area, pixels))

        base = _risk_base_image(result)
        if base is None:
            # fundo cinza neutro caso a etapa 04 ainda nao tenha rodado
            base = Image.new("RGB", (img_shape[1], img_shape[0]), (128, 128, 128))

        overlay = draw_overlay(base, intersecting, city["name"], roi)
        output = PROTECTED_DIR / f"{city['slug']}-risk-protected-areas.png"
        overlay.save(output)

        report[city["slug"]] = [area["name"] for area, _ in intersecting]
        names = ", ".join(report[city["slug"]]) or "nenhuma"
        print(f"UCs em {city['name']:>20}: {names}")

    return report


if __name__ == "__main__":
    print("Este modulo e chamado por ecological_risk_analysis.py com os resultados.")
    print("UCs catalogadas:")
    for area in PROTECTED_AREAS:
        print(f"  - {area['name']} ({area['code']})")

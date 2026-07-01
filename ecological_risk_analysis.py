from csv import DictReader, DictWriter
from pathlib import Path
import math

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parent
IMAGES_DIR = ROOT / "Images"
OUTPUT_DIR = ROOT / "EcologicalRiskImages"
DATA_DIR = ROOT / "Data" / "ecological-risk"
REPORTS_DIR = ROOT / "Reports"

STEP_DIRS = {
    "light": OUTPUT_DIR / "01-light-exposure",
    "buffers": OUTPUT_DIR / "02-marine-buffers",
    "habitat": OUTPUT_DIR / "03-habitat-and-bottom-light",
    "risk": OUTPUT_DIR / "04-ecological-risk-index",
    "comparison": OUTPUT_DIR / "05-comparisons",
    "protected": OUTPUT_DIR / "06-protected-areas",
}

MAX_VIIRS = 60.0
BUFFER_LABELS = {
    1: "0-1 km",
    2: "1-5 km",
    3: "5-10 km",
    4: "10-30 km",
}

BUFFER_COLORS = {
    1: "#ffcc66",
    2: "#66c2a5",
    3: "#3288bd",
    4: "#5e4fa2",
}

RISK_PALETTE = [
    "#07101f",
    "#155e75",
    "#22c55e",
    "#facc15",
    "#f97316",
    "#ffffff",
]

LIGHT_PALETTE = [
    "#000000",
    "#0000ff",
    "#800080",
    "#ffff00",
    "#ffffff",
]

HABITAT_PALETTE = [
    "#172554",
    "#0f766e",
    "#84cc16",
    "#facc15",
]

CITIES = [
    {
        "name": "Florianopolis",
        "slug": "florianopolis",
        "buffer_m": 27500,
        "lat": -27.5954,
        "lon": -48.5480,
    },
    {
        "name": "Balneario Camboriu",
        "slug": "balneario-camboriu",
        "buffer_m": 27500,
        "lat": -26.9904,
        "lon": -48.6345,
    },
    {
        "name": "Itajai",
        "slug": "itajai",
        "buffer_m": 27500,
        "lat": -26.9081,
        "lon": -48.6617,
    },
]


def load_font(size, bold=False):
    candidates = [
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()


def ensure_dirs():
    for directory in STEP_DIRS.values():
        directory.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def water_mask(city):
    path = IMAGES_DIR / "water-masks" / f"{city['slug']}-water-mask.png"
    image = Image.open(path).convert("RGB")
    arr = np.asarray(image, dtype=np.uint8)
    return (arr[:, :, 1] > 80) & (arr[:, :, 2] > 80) & (arr[:, :, 0] < 100)


def decode_light(city):
    path = IMAGES_DIR / "exposure-gradient" / f"{city['slug']}-exposure-gradient.png"
    image = Image.open(path).convert("RGB")
    rgb = np.asarray(image, dtype=np.float32) / 255.0
    palette = np.array([ImageColor.getrgb(c) for c in LIGHT_PALETTE], dtype=np.float32) / 255.0

    best_distance = np.full(rgb.shape[:2], np.inf, dtype=np.float32)
    best_value = np.zeros(rgb.shape[:2], dtype=np.float32)

    for idx in range(len(palette) - 1):
        start = palette[idx]
        end = palette[idx + 1]
        segment = end - start
        denom = float(np.dot(segment, segment))
        projected = ((rgb - start) * segment).sum(axis=2) / denom
        projected = np.clip(projected, 0.0, 1.0)
        nearest = start + projected[..., None] * segment
        distance = ((rgb - nearest) ** 2).sum(axis=2)
        value = (idx + projected) / (len(palette) - 1)

        choose = distance < best_distance
        best_distance[choose] = distance[choose]
        best_value[choose] = value[choose]

    return np.clip(best_value, 0.0, 1.0)


def distance_from_land_px(mask, max_px):
    remaining = mask.copy()
    distances = np.zeros(mask.shape, dtype=np.int16)
    image = Image.fromarray((remaining.astype(np.uint8) * 255), mode="L")

    for step in range(1, max_px + 1):
        eroded = np.asarray(image.filter(ImageFilter.MinFilter(3))) > 127
        edge = remaining & ~eroded
        distances[edge] = step
        remaining = eroded
        if not remaining.any():
            break
        image = Image.fromarray((remaining.astype(np.uint8) * 255), mode="L")

    distances[remaining] = max_px + 1
    return distances


def buffer_classes(distances_px, pixel_m):
    thresholds = {
        1: max(1, round(1000 / pixel_m)),
        2: max(2, round(5000 / pixel_m)),
        3: max(3, round(10000 / pixel_m)),
    }

    classes = np.zeros(distances_px.shape, dtype=np.uint8)
    water = distances_px > 0
    classes[water & (distances_px <= thresholds[1])] = 1
    classes[water & (distances_px > thresholds[1]) & (distances_px <= thresholds[2])] = 2
    classes[water & (distances_px > thresholds[2]) & (distances_px <= thresholds[3])] = 3
    classes[water & (distances_px > thresholds[3])] = 4
    return classes, thresholds


def read_fauna_weights():
    """Pesos medios de fauna por cidade.

    Prioridade 3: prefere `obis_fauna_weights.csv` (derivado de ocorrencias reais
    do OBIS, com fallback AquaMaps por grupo). Se ausente, usa o proxy original
    `fauna_sensitivity_weights.csv` das Prioridades 1 e 2.
    """
    obis_path = DATA_DIR / "obis_fauna_weights.csv"
    proxy_path = DATA_DIR / "fauna_sensitivity_weights.csv"
    path = obis_path if obis_path.exists() else proxy_path
    source = "obis" if path is obis_path else "proxy"

    weights = {}
    with path.open("r", encoding="utf-8", newline="") as file:
        for row in DictReader(file):
            slug = row["city_slug"]
            weights.setdefault(slug, []).append(
                float(row["sensitivity_weight"]) * float(row["habitat_weight"])
            )
    factors = {slug: float(np.mean(values)) for slug, values in weights.items()}
    return factors, source


def gradient(values, palette, mask=None):
    values = np.clip(values, 0.0, 1.0)
    colors = np.array([ImageColor.getrgb(c) for c in palette], dtype=np.float32)
    scaled = values * (len(colors) - 1)
    idx = np.floor(scaled).astype(np.int16)
    idx = np.clip(idx, 0, len(colors) - 2)
    local = scaled - idx
    rgb = colors[idx] * (1.0 - local[..., None]) + colors[idx + 1] * local[..., None]
    rgb = rgb.astype(np.uint8)
    if mask is not None:
        background = np.full(rgb.shape, 128, dtype=np.uint8)
        rgb = np.where(mask[..., None], rgb, background)
    return Image.fromarray(rgb, mode="RGB")


def draw_title_and_legend(image, title, palette, labels):
    title_h = 48
    legend_h = 82
    margin = 18
    font_title = load_font(26, bold=True)
    font = load_font(18, bold=False)
    canvas = Image.new("RGB", (image.width, image.height + title_h + legend_h), "white")
    draw = ImageDraw.Draw(canvas)

    bbox = draw.textbbox((0, 0), title, font=font_title)
    draw.text(((image.width - (bbox[2] - bbox[0])) / 2, 11), title, font=font_title, fill="#111111")
    canvas.paste(image, (0, title_h))

    bar_w = min(760, image.width - 2 * margin)
    bar_h = 20
    x0 = (image.width - bar_w) // 2
    y0 = title_h + image.height + 18
    pal = [ImageColor.getrgb(c) for c in palette]
    for x in range(bar_w):
        value = x / max(1, bar_w - 1)
        color = gradient(np.array([[value]], dtype=np.float32), palette).getpixel((0, 0))
        draw.line([(x0 + x, y0), (x0 + x, y0 + bar_h)], fill=color)
    draw.rectangle([x0, y0, x0 + bar_w, y0 + bar_h], outline="#666666")

    for text, value in labels:
        x = x0 + bar_w * value
        draw.line([(x, y0 + bar_h), (x, y0 + bar_h + 6)], fill="#555555")
        bbox = draw.textbbox((0, 0), text, font=font)
        draw.text((x - (bbox[2] - bbox[0]) / 2, y0 + bar_h + 10), text, font=font, fill="#111111")

    return canvas


def draw_buffer_map(classes):
    rgb = np.full((*classes.shape, 3), 128, dtype=np.uint8)
    for klass, color in BUFFER_COLORS.items():
        rgb[classes == klass] = ImageColor.getrgb(color)
    return Image.fromarray(rgb, mode="RGB")


def draw_buffer_legend(image, title):
    title_h = 48
    legend_h = 92
    font_title = load_font(26, bold=True)
    font = load_font(18)
    canvas = Image.new("RGB", (image.width, image.height + title_h + legend_h), "white")
    draw = ImageDraw.Draw(canvas)

    bbox = draw.textbbox((0, 0), title, font=font_title)
    draw.text(((image.width - (bbox[2] - bbox[0])) / 2, 11), title, font=font_title, fill="#111111")
    canvas.paste(image, (0, title_h))

    item_w = image.width / 4
    y = title_h + image.height + 26
    for idx, klass in enumerate([1, 2, 3, 4]):
        x = idx * item_w + 26
        draw.rectangle([x, y, x + 28, y + 20], fill=BUFFER_COLORS[klass], outline="#555555")
        draw.text((x + 38, y - 1), BUFFER_LABELS[klass], font=font, fill="#111111")
    return canvas


def save_comparison(images, output_path, title):
    font_title = load_font(28, bold=True)
    font_city = load_font(23, bold=True)
    target_h = 620
    margin = 20
    title_h = 54
    panels = []
    for city_name, image in images:
        resized_w = round(image.width * target_h / image.height)
        resized = image.resize((resized_w, target_h), Image.Resampling.LANCZOS)
        panel = Image.new("RGB", (resized_w, target_h + 40), "white")
        draw = ImageDraw.Draw(panel)
        bbox = draw.textbbox((0, 0), city_name, font=font_city)
        draw.text(((resized_w - (bbox[2] - bbox[0])) / 2, 7), city_name, font=font_city, fill="#111111")
        panel.paste(resized, (0, 40))
        panels.append(panel)

    width = sum(p.width for p in panels) + margin * (len(panels) + 1)
    height = title_h + max(p.height for p in panels) + margin
    canvas = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(canvas)
    bbox = draw.textbbox((0, 0), title, font=font_title)
    draw.text(((width - (bbox[2] - bbox[0])) / 2, 12), title, font=font_title, fill="#111111")
    x = margin
    for panel in panels:
        canvas.paste(panel, (x, title_h))
        x += panel.width + margin
    canvas.save(output_path)


def summarize_metrics(city, classes, light, bottom_light, productivity, habitat, fauna, risk, pixel_m):
    rows = []
    pixel_area_km2 = (pixel_m * pixel_m) / 1_000_000
    for klass, label in BUFFER_LABELS.items():
        mask = classes == klass
        if not mask.any():
            continue
        water_area = float(mask.sum() * pixel_area_km2)
        rows.append(
            {
                "city": city["name"],
                "buffer": label,
                "water_area_km2": water_area,
                "radiance_mean_relative": float(light[mask].mean()),
                "radiance_p90_relative": float(np.percentile(light[mask], 90)),
                "bottom_light_mean_relative": float(bottom_light[mask].mean()),
                "productivity_proxy_mean": float(productivity[mask].mean()),
                "habitat_proxy_mean": float(habitat[mask].mean()),
                "fauna_proxy_mean": float(fauna[mask].mean()),
                "risk_index_mean": float(risk[mask].mean()),
                "high_risk_area_km2": float((mask & (risk >= 0.55)).sum() * pixel_area_km2),
            }
        )
    return rows


def write_metrics(rows):
    output = DATA_DIR / "ecological_risk_metrics.csv"
    fields = [
        "city",
        "buffer",
        "water_area_km2",
        "radiance_mean_relative",
        "radiance_p90_relative",
        "bottom_light_mean_relative",
        "productivity_proxy_mean",
        "habitat_proxy_mean",
        "fauna_proxy_mean",
        "risk_index_mean",
        "high_risk_area_km2",
    ]
    with output.open("w", encoding="utf-8", newline="") as file:
        writer = DictWriter(file, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: f"{value:.6f}" if isinstance(value, float) else value
                    for key, value in row.items()
                }
            )
    return output


def write_result_report(rows):
    by_city = {}
    for row in rows:
        by_city.setdefault(row["city"], []).append(row)

    lines = [
        "# Resultados do Indice Ecologico Relativo",
        "",
        "Este relatorio e gerado pelo script `ecological_risk_analysis.py`.",
        "Os valores sao relativos e usam as imagens atuais do projeto mais proxies espaciais de habitat.",
        "",
        "## Leitura correta",
        "",
        "- `radiance_mean_relative` representa a intensidade visual normalizada da camada de luz.",
        "- `bottom_light_mean_relative` estima a luz que permanece relevante em agua rasa/profunda usando um proxy de atenuacao.",
        "- `productivity_proxy_mean` resume a camada de clorofila/produtividade usada como proxy de area de alimentacao.",
        "- `risk_index_mean` combina luz, habitat e sensibilidade de fauna em escala relativa de 0 a 1.",
        "- `high_risk_area_km2` e a area estimada com indice maior ou igual a 0,55.",
        "",
    ]

    for city, city_rows in by_city.items():
        lines.append(f"## {city}")
        lines.append("")
        lines.append("| Buffer | Area agua km2 | Luz media | Luz fundo | Produtividade | Habitat | Fauna | Risco | Area alto risco km2 |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for row in city_rows:
            lines.append(
                "| {buffer} | {water_area_km2:.2f} | {radiance_mean_relative:.3f} | "
                "{bottom_light_mean_relative:.3f} | {productivity_proxy_mean:.3f} | "
                "{habitat_proxy_mean:.3f} | "
                "{fauna_proxy_mean:.3f} | {risk_index_mean:.3f} | {high_risk_area_km2:.2f} |".format(**row)
            )
        lines.append("")

    output = REPORTS_DIR / "relatorio_resultados_indice_ecologico.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def read_chlorophyll_metadata():
    metadata_path = DATA_DIR / "chlorophyll" / "chlorophyll_sources.csv"
    if not metadata_path.exists():
        return {}
    with metadata_path.open("r", encoding="utf-8", newline="") as file:
        return {row["city_slug"]: row for row in DictReader(file)}


def load_productivity_layer(city, mask):
    """Array de clorofila/produtividade [0,1] da Prioridade 3.

    O arquivo e gerado por `fetch_chlorophyll_data.py`. Quando presente, substitui
    o proxy de produtividade por distancia da costa; senao, o pipeline mantem o
    calculo original.
    """
    path = DATA_DIR / "chlorophyll" / f"{city['slug']}_chlorophyll.npy"
    if not path.exists():
        return None, "proxy-distancia", "sem camada externa/local salva"
    array = np.load(path)
    if array.shape != mask.shape:
        chl_image = Image.fromarray(array.astype(np.float32), mode="F")
        chl_image = chl_image.resize((mask.shape[1], mask.shape[0]), Image.Resampling.BILINEAR)
        array = np.asarray(chl_image, dtype=np.float32)
    metadata = read_chlorophyll_metadata().get(city["slug"], {})
    source = metadata.get("source", "camada-salva")
    source_key = {
        "erddap": "clorofila-erddap",
        "local_proxy": "produtividade-local",
    }.get(source, source)
    detail = metadata.get("dataset", "camada salva em Data/ecological-risk/chlorophyll")
    return np.clip(array, 0.0, 1.0), source_key, detail


def analyze_city(city, fauna_factors):
    mask = water_mask(city)
    light = decode_light(city)
    light = np.where(mask, light, 0.0)

    width = light.shape[1]
    pixel_m = (city["buffer_m"] * 2) / width
    max_px = max(3, math.ceil(10000 / pixel_m))
    distances = distance_from_land_px(mask, max_px)
    classes, thresholds = buffer_classes(distances, pixel_m)

    max_distance = thresholds[3]
    depth_proxy = np.clip(distances.astype(np.float32) / max_distance, 0.0, 1.0)
    depth_proxy = np.where(mask, depth_proxy, 0.0)
    shallow_factor = 1.0 - depth_proxy

    kd_proxy = np.where(mask, 0.35 + 0.55 * shallow_factor + 0.10 * (1.0 - light), 0.0)
    bottom_light = np.where(mask, light * np.exp(-1.65 * kd_proxy * depth_proxy), 0.0)

    productivity_layer, productivity_source, productivity_detail = load_productivity_layer(city, mask)
    if productivity_layer is not None:
        # Camada de clorofila/produtividade substitui o proxy interno por distancia.
        productivity_proxy = np.where(mask, 0.30 + 0.70 * productivity_layer, 0.0)
    else:
        productivity_proxy = np.where(mask, 0.35 + 0.65 * shallow_factor, 0.0)
        productivity_detail = "calculado internamente pela distancia da costa"
    habitat = np.where(mask, 0.52 * shallow_factor + 0.30 * productivity_proxy + 0.18 * bottom_light, 0.0)
    habitat = np.clip(habitat, 0.0, 1.0)

    city_fauna = fauna_factors[city["slug"]]
    fauna = np.where(mask, np.clip(city_fauna * (0.45 + 0.55 * habitat), 0.0, 1.0), 0.0)
    raw_risk = np.where(mask, bottom_light * habitat * fauna, 0.0)

    return {
        "city": city,
        "mask": mask,
        "light": light,
        "classes": classes,
        "depth_proxy": depth_proxy,
        "bottom_light": bottom_light,
        "productivity": productivity_proxy,
        "habitat": habitat,
        "fauna": fauna,
        "raw_risk": raw_risk,
        "pixel_m": pixel_m,
        "productivity_source": productivity_source,
        "productivity_detail": productivity_detail,
    }


def save_city_outputs(result, risk):
    city = result["city"]
    slug = city["slug"]

    light_image = gradient(result["light"], LIGHT_PALETTE, result["mask"])
    light_panel = draw_title_and_legend(
        light_image,
        f"{city['name']} - exposicao luminosa normalizada",
        LIGHT_PALETTE,
        [("baixa", 0.0), ("media", 0.5), ("alta", 1.0)],
    )
    light_panel.save(STEP_DIRS["light"] / f"{slug}-light-exposure-normalized.png")

    buffer_image = draw_buffer_map(result["classes"])
    buffer_panel = draw_buffer_legend(buffer_image, f"{city['name']} - buffers marinhos estimados")
    buffer_panel.save(STEP_DIRS["buffers"] / f"{slug}-marine-buffers.png")

    habitat_image = gradient(result["habitat"], HABITAT_PALETTE, result["mask"])
    habitat_panel = draw_title_and_legend(
        habitat_image,
        f"{city['name']} - proxy de habitat sensivel",
        HABITAT_PALETTE,
        [("baixo", 0.0), ("medio", 0.5), ("alto", 1.0)],
    )
    habitat_panel.save(STEP_DIRS["habitat"] / f"{slug}-habitat-proxy.png")

    bottom_image = gradient(result["bottom_light"], LIGHT_PALETTE, result["mask"])
    bottom_panel = draw_title_and_legend(
        bottom_image,
        f"{city['name']} - luz relativa no fundo",
        LIGHT_PALETTE,
        [("baixa", 0.0), ("media", 0.5), ("alta", 1.0)],
    )
    bottom_panel.save(STEP_DIRS["habitat"] / f"{slug}-bottom-light-proxy.png")

    productivity_image = gradient(result["productivity"], HABITAT_PALETTE, result["mask"])
    productivity_panel = draw_title_and_legend(
        productivity_image,
        f"{city['name']} - produtividade primaria relativa",
        HABITAT_PALETTE,
        [("baixa", 0.0), ("media", 0.5), ("alta", 1.0)],
    )
    productivity_panel.save(STEP_DIRS["habitat"] / f"{slug}-productivity-proxy.png")

    risk_image = gradient(risk, RISK_PALETTE, result["mask"])
    risk_panel = draw_title_and_legend(
        risk_image,
        f"{city['name']} - indice ecologico relativo",
        RISK_PALETTE,
        [("baixo", 0.0), ("medio", 0.5), ("alto", 1.0)],
    )
    risk_panel.save(STEP_DIRS["risk"] / f"{slug}-ecological-risk-index.png")

    return {
        "light": light_image,
        "buffers": buffer_image,
        "habitat": habitat_image,
        "bottom": bottom_image,
        "productivity": productivity_image,
        "risk": risk_image,
    }


def write_priority3_report_v2(results, fauna_source, protected_info):
    """Relatorio da Prioridade 3 com fontes de produtividade e UCs auditaveis."""
    fauna_label = {
        "obis": "OBIS (ocorrencias reais; fallback AquaMaps por grupo)",
        "proxy": "proxy local (Prioridades 1 e 2; OBIS ainda nao importado)",
    }.get(fauna_source, fauna_source)

    if isinstance(protected_info, dict) and "by_city" in protected_info:
        protected_by_city = protected_info["by_city"]
        catalog_source = protected_info.get("catalog_source", "catalogo nao informado")
        catalog_paths = ", ".join(protected_info.get("catalog_paths", [])) or "sem arquivo externo"
        catalog_areas = protected_info.get("catalog_areas", [])
    else:
        protected_by_city = protected_info
        catalog_source = "catalogo legado no codigo"
        catalog_paths = "sem arquivo externo"
        catalog_areas = []

    source_label = {
        "clorofila-erddap": "clorofila-a real (ERDDAP/NOAA)",
        "produtividade-local": "produtividade primaria local (fallback reprodutivel)",
        "proxy-distancia": "proxy interno por distancia da costa",
    }

    lines = [
        "# Prioridade 3 - Enriquecimento Ambiental e Defesa",
        "",
        "Relatorio gerado por `ecological_risk_analysis.py`. Documenta quais fontes",
        "ambientais foram integradas e onde o risco coincide com unidades de",
        "conservacao.",
        "",
        "## Fonte de fauna marinha",
        "",
        f"- Pesos de fauna usados: **{fauna_label}**.",
        "- `fetch_obis_data.py` atualiza o CSV de fauna com ocorrencias OBIS e",
        "  fallback AquaMaps quando ha poucos registros locais.",
        "",
        "## Fonte de produtividade (area de alimentacao)",
        "",
        "| Cidade | Produtividade |",
        "|---|---|",
    ]
    for result in results:
        label = source_label.get(result["productivity_source"], result["productivity_source"])
        detail = result.get("productivity_detail", "")
        lines.append(f"| {result['city']['name']} | {label}; {detail} |")

    lines.extend([
        "",
        "Execute `python fetch_chlorophyll_data.py` para tentar baixar clorofila-a",
        "mensal. Se ERDDAP/NOAA nao responder, o script gera uma camada local",
        "de produtividade primaria a partir da mascara de agua e proximidade da costa.",
        "",
        "## Unidades de conservacao por cidade",
        "",
        "Mapas em `EcologicalRiskImages/06-protected-areas/`.",
        "",
        f"Fonte dos limites: **{catalog_source}**.",
        f"Arquivos de entrada: `{catalog_paths}`.",
        "",
        "Lista de UCs cujo poligono intersecta o recorte de cada cidade:",
        "",
        "| Cidade | Unidades de conservacao no buffer |",
        "|---|---|",
    ])
    for result in results:
        slug = result["city"]["slug"]
        ucs = ", ".join(protected_by_city.get(slug, [])) or "nenhuma catalogada no buffer"
        lines.append(f"| {result['city']['name']} | {ucs} |")

    lines.extend([
        "",
        "### UCs catalogadas",
        "",
    ])
    if catalog_areas:
        for area in catalog_areas:
            name = area.get("name", "UC sem nome")
            code = area.get("code", "")
            boundary_type = area.get("boundary_type", "limite nao informado")
            source = area.get("source", "fonte nao informada")
            code_label = f" ({code})" if code else ""
            lines.append(f"- **{name}**{code_label} - {boundary_type}; fonte: {source}.")
    else:
        lines.append("- Catalogo de UCs nao detalhado.")

    lines.extend([
        "",
        "### Observacoes",
        "",
        "- Uma UC e mapeada quando seu centroide esta dentro do recorte circular",
        "  de 27,5 km da cidade e ha interseccao minima desenhavel com o buffer.",
        "- O script aceita GeoJSON externo em `Data/ecological-risk/protected_areas/`.",
        "  Quando esse arquivo for exportado do CNUC/MMA ou de outro orgao oficial,",
        "  ele substitui automaticamente o catalogo CSV aproximado.",
        "",
    ])

    output = REPORTS_DIR / "relatorio_prioridade_3.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def write_priority3_report(results, fauna_source, protected_info):
    """Relatorio da Prioridade 3: fontes reais (OBIS, clorofila) e UCs por cidade."""
    return write_priority3_report_v2(results, fauna_source, protected_info)

    fauna_label = {
        "obis": "OBIS (ocorrencias reais; fallback AquaMaps por grupo)",
        "proxy": "proxy local (Prioridades 1 e 2; OBIS ainda nao importado)",
    }.get(fauna_source, fauna_source)

    lines = [
        "# Prioridade 3 - Enriquecimento Ambiental e Defesa",
        "",
        "Relatorio gerado por `ecological_risk_analysis.py`. Documenta quais fontes",
        "ambientais reais foram integradas e onde o risco coincide com unidades de",
        "conservacao (CNUC/MMA).",
        "",
        "## Fonte de fauna marinha",
        "",
        f"- Pesos de fauna usados: **{fauna_label}**.",
        "- Execute `python fetch_obis_data.py` para substituir o proxy por ocorrencias",
        "  reais do OBIS (com fallback AquaMaps quando ha poucos registros locais).",
        "",
        "## Fonte de produtividade (area de alimentacao)",
        "",
        "| Cidade | Produtividade |",
        "|---|---|",
    ]
    source_label = {
        "clorofila": "clorofila-a real (ERDDAP/NASA)",
        "proxy-distancia": "proxy por distancia da costa",
    }
    for result in results:
        label = source_label.get(result["productivity_source"], result["productivity_source"])
        lines.append(f"| {result['city']['name']} | {label} |")
    lines.extend([
        "",
        "Execute `python fetch_chlorophyll_data.py` para baixar clorofila-a mensal",
        "e substituir o proxy de produtividade por distancia da costa.",
        "",
        "## Unidades de conservacao por cidade",
        "",
        "Mapas em `EcologicalRiskImages/06-protected-areas/`. Lista de UCs cujo",
        "poligono intersecta o recorte de cada cidade:",
        "",
        "| Cidade | Unidades de conservacao no buffer |",
        "|---|---|",
    ])
    for result in results:
        slug = result["city"]["slug"]
        ucs = ", ".join(protected_info.get(slug, [])) or "nenhuma catalogada no buffer"
        lines.append(f"| {result['city']['name']} | {ucs} |")
    lines.extend([
        "",
        "### UCs catalogadas",
        "",
        "- **APA de Anhatomirim** (federal) - Baia Norte de Florianopolis.",
        "- **APA Costa Brava** (municipal, Lei 1985/2000) - faixa costeira das",
        "  Interpraias de Balneario Camboriu; dentro dos buffers de BC e Itajai.",
        "- **Parque Natural Municipal do Atalaia** (municipal, Decreto 2007) -",
        "  bairro Fazenda/Cabecudas, junto a foz do Itajai-Acu.",
        "- **REBIO Marinha do Arvoredo** e **APA da Baleia Franca** permanecem",
        "  catalogadas, mas seus centros ficam fora dos buffers de 27,5 km das tres",
        "  cidades, entao nao sao mapeadas como internas.",
        "",
        "### Observacoes",
        "",
        "- Uma UC e mapeada quando seu **centroide** esta dentro do recorte",
        "  **circular** de 27,5 km da cidade (nao a imagem quadrada). Assim, UCs",
        "  pequenas mas internas (ex.: PNM Atalaia, ~19 ha) entram, e UCs externas",
        "  que so roçam a borda (ex.: REBIO Arvoredo, centro a ~34 km de BC) ficam",
        "  de fora.",
        "- Os poligonos sao aproximacoes para visualizacao; para uso oficial,",
        "  importar os limites vetoriais do CNUC/MMA.",
        "",
    ])
    output = REPORTS_DIR / "relatorio_prioridade_3.md"
    output.write_text("\n".join(lines), encoding="utf-8")
    return output


def main():
    ensure_dirs()
    fauna_factors, fauna_source = read_fauna_weights()

    results = [analyze_city(city, fauna_factors) for city in CITIES]
    max_risk = max(float(result["raw_risk"].max()) for result in results) or 1.0

    all_rows = []
    comparison_images = []
    for result in results:
        risk = np.where(result["mask"], np.clip(result["raw_risk"] / max_risk, 0.0, 1.0), 0.0)
        result["risk"] = risk
        images = save_city_outputs(result, risk)
        result["risk_image"] = images["risk"]  # imagem crua p/ sobreposicao de UCs
        comparison_images.append((result["city"]["name"], images["risk"]))
        all_rows.extend(
            summarize_metrics(
                result["city"],
                result["classes"],
                result["light"],
                result["bottom_light"],
                result["productivity"],
                result["habitat"],
                result["fauna"],
                risk,
                result["pixel_m"],
            )
        )

    metrics_path = write_metrics(all_rows)
    report_path = write_result_report(all_rows)
    save_comparison(
        comparison_images,
        STEP_DIRS["comparison"] / "comparison-cities-ecological-risk-index.png",
        "Comparacao do indice ecologico relativo",
    )

    # Prioridade 3: sobreposicao de unidades de conservacao (CNUC/MMA).
    from protected_areas_overlay import generate_all_overlays

    protected_info = generate_all_overlays(results)
    priority3_path = write_priority3_report(results, fauna_source, protected_info)

    print(f"Saved metrics: {metrics_path}")
    print(f"Saved report: {report_path}")
    print(f"Saved priority-3 report: {priority3_path}")
    print(f"Saved images: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()

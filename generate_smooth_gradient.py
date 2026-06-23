import os
from pathlib import Path
import tempfile

from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont


PASTA_ENTRADA = Path("Images/exposure-gradient")
PASTA_SAIDA = Path("Images/smooth-gradient")
PASTA_COMPARACOES = Path("Images/comparisons")

MAPAS = [
    ("Florianopolis", "florianopolis-exposure-gradient.png", "florianopolis-smooth-gradient.png"),
    ("Balneario Camboriu", "balneario-camboriu-exposure-gradient.png", "balneario-camboriu-smooth-gradient.png"),
    ("Itajai", "itajai-exposure-gradient.png", "itajai-smooth-gradient.png"),
]

PALETA_GRADIENTE = [
    "#000000",
    "#0000ff",
    "#800080",
    "#ffff00",
    "#ffffff",
]

COR_TERRA = (128, 128, 128)
TOLERANCIA_TERRA = 5
FUNDO = "#ffffff"
TEXTO = "#111111"
ALTURA_MAPA_COMPARACAO = 700
MARGEM = 20
ALTURA_TITULO = 44
ALTURA_LEGENDA = 92


def carregar_fonte(tamanho, negrito=False):
    candidatos = [
        "C:/Windows/Fonts/arialbd.ttf" if negrito else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if negrito else "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if negrito
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for caminho in candidatos:
        if os.path.exists(caminho):
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


def texto_centralizado(draw, caixa, texto, fonte, cor=TEXTO):
    x0, y0, x1, y1 = caixa
    bbox = draw.textbbox((0, 0), texto, font=fonte)
    larg = bbox[2] - bbox[0]
    alt = bbox[3] - bbox[1]
    draw.text(((x0 + x1 - larg) / 2, (y0 + y1 - alt) / 2), texto, font=fonte, fill=cor)


def mascara_terra(imagem):
    pixels = imagem.load()
    mask = Image.new("L", imagem.size, 0)
    mask_px = mask.load()
    for y in range(imagem.height):
        for x in range(imagem.width):
            r, g, b = pixels[x, y][:3]
            if (
                abs(r - COR_TERRA[0]) <= TOLERANCIA_TERRA
                and abs(g - COR_TERRA[1]) <= TOLERANCIA_TERRA
                and abs(b - COR_TERRA[2]) <= TOLERANCIA_TERRA
            ):
                mask_px[x, y] = 255
    return mask


def suavizar_degrade(caminho):
    original = Image.open(caminho).convert("RGB")
    terra = mascara_terra(original)

    # Wide blur to reduce the visible satellite-cell blocks in illuminated water areas.
    blur_1 = original.filter(ImageFilter.GaussianBlur(radius=4.2))
    blur_2 = blur_1.filter(ImageFilter.GaussianBlur(radius=1.4))
    suavizado = Image.blend(original, blur_2, 0.88)

    resultado = Image.composite(original, suavizado, terra)
    return resultado


def interpolar_cor(cor_a, cor_b, fator):
    return tuple(round(a + (b - a) * fator) for a, b in zip(cor_a, cor_b))


def cor_no_gradiente(paleta, fator):
    fator = max(0, min(1, fator))
    pos = fator * (len(paleta) - 1)
    idx = int(pos)
    if idx >= len(paleta) - 1:
        return paleta[-1]
    return interpolar_cor(paleta[idx], paleta[idx + 1], pos - idx)


def desenhar_legenda(draw, largura, topo, fonte):
    paleta = [ImageColor.getrgb(cor) for cor in PALETA_GRADIENTE]
    barra_largura = min(900, largura - 2 * MARGEM)
    barra_altura = 24
    x0 = (largura - barra_largura) / 2
    y0 = topo + 34

    titulo = "Radiancia VIIRS sobre agua - degrade suave (baixa -> alta)"
    texto_centralizado(draw, (0, topo + 2, largura, topo + 30), titulo, fonte)

    for x in range(barra_largura):
        fator = x / max(1, barra_largura - 1)
        cor = cor_no_gradiente(paleta, fator)
        draw.line([(x0 + x, y0), (x0 + x, y0 + barra_altura)], fill=cor)

    draw.rectangle([x0, y0, x0 + barra_largura, y0 + barra_altura], outline="#777777")

    for rotulo, fator in [("baixa", 0), ("media", 0.5), ("alta", 1)]:
        x = x0 + barra_largura * fator
        draw.line([(x, y0 + barra_altura), (x, y0 + barra_altura + 7)], fill="#555555")
        bbox = draw.textbbox((0, 0), rotulo, font=fonte)
        larg = bbox[2] - bbox[0]
        draw.text((x - larg / 2, y0 + barra_altura + 10), rotulo, font=fonte, fill=TEXTO)


def montar_individual(titulo, mapa):
    fonte_titulo = carregar_fonte(30, negrito=True)
    fonte_legenda = carregar_fonte(18, negrito=True)

    largura = mapa.width
    altura = ALTURA_TITULO + mapa.height + ALTURA_LEGENDA + MARGEM
    painel = Image.new("RGB", (largura, altura), FUNDO)
    draw = ImageDraw.Draw(painel)
    texto_centralizado(draw, (0, 0, largura, ALTURA_TITULO), titulo, fonte_titulo)
    painel.paste(mapa, (0, ALTURA_TITULO))
    desenhar_legenda(draw, largura, ALTURA_TITULO + mapa.height, fonte_legenda)
    return painel


def preparar_mapa_comparacao(mapa, titulo, fonte_titulo):
    largura = round(mapa.width * ALTURA_MAPA_COMPARACAO / mapa.height)
    redimensionado = mapa.resize((largura, ALTURA_MAPA_COMPARACAO), Image.Resampling.LANCZOS)

    painel = Image.new("RGB", (largura, ALTURA_TITULO + ALTURA_MAPA_COMPARACAO), FUNDO)
    draw = ImageDraw.Draw(painel)
    texto_centralizado(draw, (0, 0, largura, ALTURA_TITULO), titulo, fonte_titulo)
    painel.paste(redimensionado, (0, ALTURA_TITULO))
    return painel


def montar_comparacao(mapas):
    fonte_titulo = carregar_fonte(28, negrito=True)
    fonte_legenda = carregar_fonte(22, negrito=True)

    paineis = [preparar_mapa_comparacao(mapa, titulo, fonte_titulo) for titulo, mapa in mapas]
    altura_paineis = max(p.height for p in paineis)
    largura_total = sum(p.width for p in paineis) + MARGEM * (len(paineis) + 1)
    altura_total = MARGEM + altura_paineis + ALTURA_LEGENDA + MARGEM

    canvas = Image.new("RGB", (largura_total, altura_total), FUNDO)
    x = MARGEM
    for painel in paineis:
        canvas.paste(painel, (x, MARGEM))
        x += painel.width + MARGEM

    draw = ImageDraw.Draw(canvas)
    desenhar_legenda(draw, largura_total, MARGEM + altura_paineis, fonte_legenda)
    return canvas


def salvar_imagem(imagem, caminho):
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        suffix=caminho.suffix,
        dir=caminho.parent,
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)
    try:
        imagem.save(temp_path)
        temp_path.replace(caminho)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def gerar():
    PASTA_SAIDA.mkdir(exist_ok=True)
    PASTA_COMPARACOES.mkdir(exist_ok=True)

    mapas_suavizados = []
    for titulo, entrada, saida in MAPAS:
        caminho_entrada = PASTA_ENTRADA / entrada
        if not caminho_entrada.exists():
            raise FileNotFoundError(f"Map not found: {caminho_entrada}")

        mapa = suavizar_degrade(caminho_entrada)
        painel = montar_individual(titulo, mapa)
        caminho_saida = PASTA_SAIDA / saida
        salvar_imagem(painel, caminho_saida)
        mapas_suavizados.append((titulo, mapa))
        print(f"Saved individual image: {caminho_saida}")

    comparacao = montar_comparacao(mapas_suavizados)
    caminho_comparacao = PASTA_COMPARACOES / "comparison-cities-smooth-gradient.png"
    salvar_imagem(comparacao, caminho_comparacao)
    print(f"Saved comparison image: {caminho_comparacao}")


if __name__ == "__main__":
    gerar()

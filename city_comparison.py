import os

from PIL import Image, ImageColor, ImageDraw, ImageFont

PASTA_ENTRADA = 'Images/exposure-gradient'
PASTA_SAIDA = 'Images/comparisons'

MAPAS = [
    ('Florianopolis', 'florianopolis-exposure-gradient.png'),
    ('Balneario Camboriu', 'balneario-camboriu-exposure-gradient.png'),
    ('Itajai', 'itajai-exposure-gradient.png'),
]

PALETA_GRADIENTE = [
    '#000000',
    '#0000ff',
    '#800080',
    '#ffff00',
    '#ffffff',
]

ALTURA_MAPA = 700
MARGEM = 20
ALTURA_TITULO = 44
ALTURA_LEGENDA = 92
FUNDO = '#ffffff'
TEXTO = '#111111'


def carregar_fonte(tamanho):
    candidatos = [
        'C:/Windows/Fonts/arialbd.ttf',
        'C:/Windows/Fonts/arial.ttf',
        'C:/Windows/Fonts/calibrib.ttf',
        'C:/Windows/Fonts/calibri.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]
    for caminho in candidatos:
        if os.path.exists(caminho):
            return ImageFont.truetype(caminho, tamanho)
    return ImageFont.load_default()


def texto_centralizado(draw, caixa, texto, fonte, cor):
    x0, y0, x1, y1 = caixa
    larg = draw.textlength(texto, font=fonte)
    asc, desc = fonte.getmetrics()
    alt = asc + desc
    draw.text(((x0 + x1 - larg) / 2, (y0 + y1 - alt) / 2), texto, font=fonte, fill=cor)


def preparar_mapa(caminho, titulo, fonte_titulo):
    img = Image.open(caminho).convert('RGB')
    larg = round(img.width * ALTURA_MAPA / img.height)
    img = img.resize((larg, ALTURA_MAPA))

    painel = Image.new('RGB', (larg, ALTURA_TITULO + ALTURA_MAPA), FUNDO)
    draw = ImageDraw.Draw(painel)
    texto_centralizado(draw, (0, 0, larg, ALTURA_TITULO), titulo, fonte_titulo, TEXTO)
    painel.paste(img, (0, ALTURA_TITULO))
    return painel


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

    titulo = 'Radiancia VIIRS sobre agua - gradiente continuo (baixa -> alta)'
    titulo_larg = draw.textlength(titulo, font=fonte)
    draw.text((largura / 2 - titulo_larg / 2, topo + 6), titulo, font=fonte, fill=TEXTO)

    for x in range(barra_largura):
        fator = x / max(1, barra_largura - 1)
        cor = cor_no_gradiente(paleta, fator)
        draw.line([(x0 + x, y0), (x0 + x, y0 + barra_altura)], fill=cor)

    draw.rectangle([x0, y0, x0 + barra_largura, y0 + barra_altura], outline='#777777')

    rotulos = [('baixa', 0), ('media', 0.5), ('alta', 1)]
    for rotulo, fator in rotulos:
        x = x0 + barra_largura * fator
        draw.line([(x, y0 + barra_altura), (x, y0 + barra_altura + 7)], fill='#555555')
        larg_rotulo = draw.textlength(rotulo, font=fonte)
        draw.text((x - larg_rotulo / 2, y0 + barra_altura + 10), rotulo, font=fonte, fill=TEXTO)


def montar():
    fonte_titulo = carregar_fonte(28)
    fonte_legenda = carregar_fonte(22)

    paineis = []
    for titulo, arquivo in MAPAS:
        caminho = os.path.join(PASTA_ENTRADA, arquivo)
        if not os.path.exists(caminho):
            raise FileNotFoundError(
                f"Map not found: {caminho}. Run water_light_exposure.py first."
            )
        paineis.append(preparar_mapa(caminho, titulo, fonte_titulo))

    altura_paineis = max(p.height for p in paineis)
    largura_total = sum(p.width for p in paineis) + MARGEM * (len(paineis) + 1)
    altura_total = MARGEM + altura_paineis + ALTURA_LEGENDA + MARGEM

    canvas = Image.new('RGB', (largura_total, altura_total), FUNDO)
    x = MARGEM
    for painel in paineis:
        canvas.paste(painel, (x, MARGEM))
        x += painel.width + MARGEM

    draw = ImageDraw.Draw(canvas)
    desenhar_legenda(draw, largura_total, MARGEM + altura_paineis, fonte_legenda)

    os.makedirs(PASTA_SAIDA, exist_ok=True)
    saida = os.path.join(PASTA_SAIDA, 'comparison-cities-gradient.png')
    canvas.save(saida)
    print(f"Saved figure: {saida}")


if __name__ == '__main__':
    montar()

import os

from PIL import Image, ImageColor, ImageDraw, ImageFont

PASTA_ENTRADA = 'saida_etapa6'
PASTA_SAIDA = 'saida_etapa7'

MAPAS = [
    ('Florianopolis', 'mapa_exposicao_florianopolis.png'),
    ('Balneario Camboriu', 'mapa_exposicao_balneario_camboriu.png'),
    ('Itajai', 'mapa_exposicao_itajai.png'),
]

LEGENDA = [
    ('Nao exposta', '#08081f'),
    ('Baixa', '#1f6feb'),
    ('Moderada', '#f5d020'),
    ('Alta', '#e8000b'),
]

ALTURA_MAPA = 700
MARGEM = 20
ALTURA_TITULO = 44
ALTURA_LEGENDA = 60
FUNDO = '#ffffff'
TEXTO = '#111111'


def carregar_fonte(tamanho):
    candidatos = [
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


def desenhar_legenda(draw, largura, topo, fonte):
    amostra = 26
    espaco = 18
    itens = []
    for rotulo, cor in LEGENDA:
        itens.append((rotulo, cor, amostra + 8 + draw.textlength(rotulo, font=fonte)))
    largura_total = sum(l for _, _, l in itens) + espaco * (len(itens) - 1)

    x = (largura - largura_total) / 2
    meio = topo + ALTURA_LEGENDA / 2
    for rotulo, cor, larg_item in itens:
        draw.rectangle(
            [x, meio - amostra / 2, x + amostra, meio + amostra / 2],
            fill=ImageColor.getrgb(cor),
            outline='#888888',
        )
        asc, desc = fonte.getmetrics()
        draw.text((x + amostra + 8, meio - (asc + desc) / 2), rotulo, font=fonte, fill=TEXTO)
        x += larg_item + espaco


def montar():
    fonte_titulo = carregar_fonte(28)
    fonte_legenda = carregar_fonte(22)

    paineis = []
    for titulo, arquivo in MAPAS:
        caminho = os.path.join(PASTA_ENTRADA, arquivo)
        if not os.path.exists(caminho):
            raise FileNotFoundError(
                f"Mapa nao encontrado: {caminho}. Rode etapa6_cruzamento_luz_agua.py antes."
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
    saida = os.path.join(PASTA_SAIDA, 'comparacao_cidades.png')
    canvas.save(saida)
    print(f"Figura salva em: {saida}")


if __name__ == '__main__':
    montar()

# Etapas do artigo adaptadas ao trabalho

Artigo base: *Biologically important artificial light at night on the seafloor*.

Objetivo do trabalho: relacionar a poluicao luminosa noturna costeira com areas de agua proximas a centros urbanos em Florianopolis, Balneario Camboriu e Itajai.

## 1. Definicao do problema

O artigo investiga se a luz artificial noturna de areas urbanas costeiras alcanca ambientes marinhos em intensidade suficiente para gerar impacto ecologico.

No trabalho, a pergunta pode ser adaptada para:

> As cidades costeiras analisadas apresentam emissao de luz noturna proxima a areas de agua, indicando potencial exposicao de ambientes aquaticos a poluicao luminosa?

## 2. Escolha das areas de estudo

As areas escolhidas foram tres cidades costeiras de Santa Catarina:

- Florianopolis: latitude -27.5969, longitude -48.5468
- Balneario Camboriu: latitude -26.9980, longitude -48.6326
- Itajai: latitude -26.9083, longitude -48.6775

Cada cidade deve manter o mesmo formato, borda e posicao de recorte entre as imagens diurnas e noturnas, para permitir comparacao visual direta.

## 3. Coleta das imagens

Etapa ja realizada.

Foram coletadas imagens para cada cidade:

- imagem diurna ou de superficie, usada para distinguir agua e terra
- imagem noturna, usada para observar a distribuicao espacial da luz artificial

Arquivos atuais em `Imagens/`:

- `Florianopolis.png`
- `FlorianopolisNoite.png`
- `Balneario Camboriu.png`
- `Balneario CamboriuNoite.png`
- `Itajai.png`
- `ItajaiNoite.png`

## 4. Separacao entre agua e terra

No artigo, a area de terra aparece como regiao solida cinza e a analise de luz e feita sobre a area aquatica.

No trabalho, esta etapa pode ser feita usando as imagens diurnas:

1. Identificar visualmente as areas de agua e terra.
2. Usar a imagem Sentinel-2/MNDWI como apoio para destacar corpos d'agua.
3. Criar uma mascara simples de agua, quando necessario.
4. Usar essa mascara para interpretar apenas as regioes aquaticas na imagem noturna.

Resultado esperado: uma delimitacao clara das areas de agua em cada cidade.

## 5. Mapeamento da luz artificial noturna

No artigo, os autores mapearam a luz artificial noturna em diferentes bandas espectrais.

No trabalho, esta etapa sera simplificada com imagens VIIRS:

1. Usar a colecao `NASA/VIIRS/002/VNP46A2`.
2. Selecionar a banda `DNB_BRDF_Corrected_NTL`.
3. Aplicar mediana no periodo escolhido para reduzir ruidos.
4. Visualizar com a paleta:

```python
['black', 'blue', 'purple', 'yellow', 'white']
```

Interpretação da escala:

- preto: baixa ou nenhuma emissao luminosa
- azul/roxo: emissao baixa a moderada
- amarelo/branco: emissao mais intensa

## 6. Cruzamento entre agua e luz noturna

Esta e a etapa central da analise.

Para cada cidade:

1. Comparar a imagem diurna com a imagem noturna.
2. Observar onde a luz urbana aparece proxima ou sobre areas de agua.
3. Marcar regioes de maior interesse, como baías, rios, canais, praias e areas portuarias.
4. Registrar exemplos visuais em figuras comparativas.

Resultado esperado: identificar visualmente areas aquaticas mais expostas a luz artificial noturna.

## 7. Comparacao entre cidades

Depois de analisar cada cidade separadamente, comparar:

- intensidade visual da luz noturna
- proximidade entre luz urbana e agua
- extensao aparente das areas aquaticas expostas
- diferencas entre regioes urbanas, portuarias e turisticas

Possivel organizacao:

| Cidade | Presenca de agua | Intensidade de luz noturna | Observacao principal |
| --- | --- | --- | --- |
| Florianopolis | Alta | A preencher | A preencher |
| Balneario Camboriu | Alta | A preencher | A preencher |
| Itajai | Alta | A preencher | A preencher |

## 8. Discussao dos resultados

Relacionar as observacoes com a ideia central do artigo:

- cidades costeiras podem gerar poluicao luminosa sobre ambientes aquaticos
- a proximidade entre iluminacao urbana e agua aumenta o potencial de impacto
- areas com portos, orlas verticalizadas e alta urbanizacao tendem a concentrar emissoes luminosas
- a analise por imagem de satelite permite uma avaliacao espacial inicial do problema

Tambem deixar claro o limite do trabalho:

- o artigo original usa medicoes em campo, propriedades opticas da agua, batimetria e modelagem de transferencia radiativa
- este trabalho usa uma abordagem simplificada por sensoriamento remoto, adequada para analise visual e comparativa

## 9. Conclusao

A conclusao deve responder se as imagens indicam proximidade relevante entre luz artificial noturna e ambientes aquaticos.

Estrutura sugerida:

1. Retomar o objetivo.
2. Resumir o que foi observado nas tres cidades.
3. Indicar qual cidade aparenta maior exposicao de agua a luz noturna.
4. Relacionar o resultado com os riscos ecologicos discutidos no artigo.
5. Sugerir que estudos futuros incluam batimetria, dados de mare, qualidade da agua e medicoes de campo.

## 10. Produtos finais

Entregaveis recomendados:

- mapa/imagem diurna de cada cidade
- mapa/imagem noturna de cada cidade
- comparacao lado a lado entre agua/terra e luz noturna
- tabela comparativa entre cidades
- texto final com introducao, metodologia, resultados, discussao e conclusao

## Etapas opcionais avancadas

Estas etapas aproximariam mais o trabalho do artigo, mas exigem dados adicionais:

- obter batimetria das regioes costeiras
- separar condicoes de ceu claro e nublado
- estimar profundidade da coluna d'agua
- modelar penetracao da luz na agua
- aplicar limiares biologicos de sensibilidade luminosa
- calcular area aquatica exposta acima de um limiar

# Prioridade 3 - Enriquecimento Ambiental e Defesa

Relatorio gerado por `ecological_risk_analysis.py`. Documenta quais fontes
ambientais reais foram integradas e onde o risco coincide com unidades de
conservacao (CNUC/MMA).

## Fonte de fauna marinha

- Pesos de fauna usados: **OBIS (ocorrencias reais; fallback AquaMaps por grupo)**.
- Execute `python fetch_obis_data.py` para substituir o proxy por ocorrencias
  reais do OBIS (com fallback AquaMaps quando ha poucos registros locais).

## Fonte de produtividade (area de alimentacao)

| Cidade | Produtividade |
|---|---|
| Florianopolis | proxy por distancia da costa |
| Balneario Camboriu | proxy por distancia da costa |
| Itajai | proxy por distancia da costa |

Execute `python fetch_chlorophyll_data.py` para baixar clorofila-a mensal
e substituir o proxy de produtividade por distancia da costa.

## Unidades de conservacao por cidade

Mapas em `EcologicalRiskImages/06-protected-areas/`. Lista de UCs cujo
poligono intersecta o recorte de cada cidade:

| Cidade | Unidades de conservacao no buffer |
|---|---|
| Florianopolis | APA de Anhatomirim |
| Balneario Camboriu | nenhuma catalogada no buffer |
| Itajai | nenhuma catalogada no buffer |

### Observacoes

- A interseccao usa o recorte **circular** de 27,5 km (nao a imagem
  quadrada), e exige cobertura minima do buffer para evitar que uma UC
  apenas "roce" a borda seja mapeada.
- A REBIO Marinha do Arvoredo tem centro a ~34 km (Balneario Camboriu) e
  ~42 km (Itajai) dos centros urbanos: fica fora dos buffers circulares das
  tres cidades, por isso nao e mapeada como interna.
- A APA da Baleia Franca tem limite norte proximo de 28S, fora dos buffers
  das tres cidades analisadas.
- Os poligonos sao aproximacoes para visualizacao; para uso oficial,
  importar os limites vetoriais do CNUC/MMA.

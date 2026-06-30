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
| Balneario Camboriu | REBIO Marinha do Arvoredo |
| Itajai | REBIO Marinha do Arvoredo |

### Observacoes

- A REBIO Marinha do Arvoredo fica a ~50 km do centro de Florianopolis;
  pode cair fora do buffer de 27,5 km dependendo do recorte.
- A APA da Baleia Franca tem limite norte proximo de 28S, geralmente fora
  dos buffers das tres cidades analisadas.
- Os poligonos sao aproximacoes para visualizacao; para uso oficial,
  importar os limites vetoriais do CNUC/MMA.

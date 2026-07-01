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
| Balneario Camboriu | APA Costa Brava, Parque Natural Municipal do Atalaia |
| Itajai | APA Costa Brava, Parque Natural Municipal do Atalaia |

### UCs catalogadas

- **APA de Anhatomirim** (federal) - Baia Norte de Florianopolis.
- **APA Costa Brava** (municipal, Lei 1985/2000) - faixa costeira das
  Interpraias de Balneario Camboriu; dentro dos buffers de BC e Itajai.
- **Parque Natural Municipal do Atalaia** (municipal, Decreto 2007) -
  bairro Fazenda/Cabecudas, junto a foz do Itajai-Acu.
- **REBIO Marinha do Arvoredo** e **APA da Baleia Franca** permanecem
  catalogadas, mas seus centros ficam fora dos buffers de 27,5 km das tres
  cidades, entao nao sao mapeadas como internas.

### Observacoes

- Uma UC e mapeada quando seu **centroide** esta dentro do recorte
  **circular** de 27,5 km da cidade (nao a imagem quadrada). Assim, UCs
  pequenas mas internas (ex.: PNM Atalaia, ~19 ha) entram, e UCs externas
  que so roçam a borda (ex.: REBIO Arvoredo, centro a ~34 km de BC) ficam
  de fora.
- Os poligonos sao aproximacoes para visualizacao; para uso oficial,
  importar os limites vetoriais do CNUC/MMA.

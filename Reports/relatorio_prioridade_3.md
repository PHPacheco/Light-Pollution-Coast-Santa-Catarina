# Prioridade 3 - Enriquecimento Ambiental e Defesa

Relatorio gerado por `ecological_risk_analysis.py`. Documenta quais fontes
ambientais foram integradas e onde o risco coincide com unidades de
conservacao.

## Fonte de fauna marinha

- Pesos de fauna usados: **OBIS (ocorrencias reais; fallback AquaMaps por grupo)**.
- `fetch_obis_data.py` atualiza o CSV de fauna com ocorrencias OBIS e
  fallback AquaMaps quando ha poucos registros locais.

## Fonte de produtividade (area de alimentacao)

| Cidade | Produtividade |
|---|---|
| Florianopolis | produtividade primaria local (fallback reprodutivel); local-primary-productivity-proxy |
| Balneario Camboriu | produtividade primaria local (fallback reprodutivel); local-primary-productivity-proxy |
| Itajai | produtividade primaria local (fallback reprodutivel); local-primary-productivity-proxy |

Execute `python fetch_chlorophyll_data.py` para tentar baixar clorofila-a
mensal. Se ERDDAP/NOAA nao responder, o script gera uma camada local
de produtividade primaria a partir da mascara de agua e proximidade da costa.

## Unidades de conservacao por cidade

Mapas em `EcologicalRiskImages/06-protected-areas/`.

Fonte dos limites: **CSV local de UCs costeiras**.
Arquivos de entrada: `C:\FURB\Processamento de imagem\Trabalho final\Light-Pollution-Coast-Santa-Catarina-ecological-risk\Data\ecological-risk\protected_areas\protected_areas_catalog.csv`.

Lista de UCs cujo poligono intersecta o recorte de cada cidade:

| Cidade | Unidades de conservacao no buffer |
|---|---|
| Florianopolis | APA de Anhatomirim |
| Balneario Camboriu | APA Costa Brava, Parque Natural Municipal do Atalaia |
| Itajai | APA Costa Brava, Parque Natural Municipal do Atalaia |

### UCs catalogadas

- **APA de Anhatomirim** (APA-ANHATOMIRIM) - poligono aproximado local; fonte: CNUC/MMA e descricao geografica publica; aproximado para visualizacao didatica.
- **REBIO Marinha do Arvoredo** (REBIO-ARVOREDO) - poligono aproximado local; fonte: CNUC/MMA e descricao geografica publica; aproximado para visualizacao didatica.
- **APA da Baleia Franca** (APA-BALEIA-FRANCA) - poligono aproximado local; fonte: CNUC/MMA e descricao geografica publica; aproximado para visualizacao didatica.
- **APA Costa Brava** (APA-COSTA-BRAVA) - poligono aproximado local; fonte: Prefeitura de Balneario Camboriu e cadastro ambiental; aproximado para visualizacao didatica.
- **Parque Natural Municipal do Atalaia** (PNM-ATALAIA) - poligono aproximado local; fonte: Prefeitura de Itajai e cadastro ambiental; aproximado para visualizacao didatica.

### Observacoes

- Uma UC e mapeada quando seu centroide esta dentro do recorte circular
  de 27,5 km da cidade e ha interseccao minima desenhavel com o buffer.
- O script aceita GeoJSON externo em `Data/ecological-risk/protected_areas/`.
  Quando esse arquivo for exportado do CNUC/MMA ou de outro orgao oficial,
  ele substitui automaticamente o catalogo CSV aproximado.

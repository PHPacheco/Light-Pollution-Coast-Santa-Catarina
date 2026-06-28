# Relatorio de validacao e instrucoes

## Como executar

Na pasta do projeto, rode:

```bash
python ecological_risk_analysis.py
```

Se o Python padrao nao tiver `Pillow` e `numpy`, use um ambiente que tenha essas bibliotecas instaladas. O projeto ja usa Pillow em scripts anteriores, entao a dependencia e coerente com a base atual.

## O que validar visualmente

1. Abra `EcologicalRiskImages/01-light-exposure` e confirme se a luz aparece apenas sobre regioes aquaticas.
2. Abra `EcologicalRiskImages/02-marine-buffers` e confirme se os buffers formam faixas a partir das margens/costa.
3. Abra `EcologicalRiskImages/03-habitat-and-bottom-light` e confira se o habitat sensivel privilegia aguas rasas e regioes proximas da costa.
4. Abra `EcologicalRiskImages/04-ecological-risk-index` e verifique se o risco aparece onde luz, agua rasa e sensibilidade de fauna coincidem.
5. Abra `EcologicalRiskImages/05-comparisons/comparison-cities-ecological-risk-index.png` para comparar as tres cidades.

## O que validar numericamente

Abra `Data/ecological-risk/ecological_risk_metrics.csv` e confira:

- se existem linhas para as tres cidades;
- se cada cidade possui buffers `0-1 km`, `1-5 km`, `5-10 km` e `10-30 km`, quando houver pixels de agua suficientes;
- se `radiance_mean_relative`, `bottom_light_mean_relative`, `habitat_proxy_mean`, `fauna_proxy_mean` e `risk_index_mean` ficam entre `0` e `1`;
- se `water_area_km2` e `high_risk_area_km2` nao sao negativos.

## Como interpretar os resultados

Os resultados sao relativos. Um valor maior de risco significa maior coincidencia entre luz artificial, agua rasa/proxima da costa, habitat presumidamente sensivel e pesos iniciais de fauna.

Nao interprete o indice como impacto biologico comprovado. Ele e uma ferramenta de triagem espacial para indicar onde o projeto deve investigar melhor.

## Como evoluir com datasets reais

- Substituir `fauna_sensitivity_weights.csv` por ocorrencias OBIS agregadas por grupo e buffer.
- Substituir `depth_proxy` por batimetria GEBCO.
- Substituir `kd_proxy` por atenuacao Bio-ORACLE ou NASA OceanColor.
- Adicionar areas protegidas CNUC/MMA como multiplicador ou camada de destaque no mapa final.

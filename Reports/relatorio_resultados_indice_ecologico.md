# Resultados do Indice Ecologico Relativo

Este relatorio e gerado pelo script `ecological_risk_analysis.py`.
Os valores sao relativos e usam as imagens atuais do projeto mais proxies espaciais de habitat.

## Leitura correta

- `radiance_mean_relative` representa a intensidade visual normalizada da camada de luz.
- `bottom_light_mean_relative` estima a luz que permanece relevante em agua rasa/profunda usando um proxy de atenuacao.
- `productivity_proxy_mean` resume a camada de clorofila/produtividade usada como proxy de area de alimentacao.
- `risk_index_mean` combina luz, habitat e sensibilidade de fauna em escala relativa de 0 a 1.
- `high_risk_area_km2` e a area estimada com indice maior ou igual a 0,55.

## Florianopolis

| Buffer | Area agua km2 | Luz media | Luz fundo | Produtividade | Habitat | Fauna | Risco | Area alto risco km2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0-1 km | 542.25 | 0.062 | 0.060 | 0.943 | 0.787 | 0.465 | 0.048 | 9.10 |
| 1-5 km | 709.36 | 0.014 | 0.010 | 0.859 | 0.656 | 0.427 | 0.006 | 0.00 |
| 5-10 km | 65.04 | 0.007 | 0.004 | 0.620 | 0.401 | 0.353 | 0.001 | 0.00 |

## Balneario Camboriu

| Buffer | Area agua km2 | Luz media | Luz fundo | Produtividade | Habitat | Fauna | Risco | Area alto risco km2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0-1 km | 357.67 | 0.087 | 0.085 | 0.917 | 0.788 | 0.454 | 0.066 | 12.94 |
| 1-5 km | 653.59 | 0.014 | 0.010 | 0.837 | 0.633 | 0.410 | 0.006 | 0.00 |
| 5-10 km | 201.16 | 0.006 | 0.003 | 0.571 | 0.343 | 0.328 | 0.001 | 0.00 |
| 10-30 km | 10.59 | 0.005 | 0.002 | 0.474 | 0.142 | 0.271 | 0.000 | 0.00 |

## Itajai

| Buffer | Area agua km2 | Luz media | Luz fundo | Produtividade | Habitat | Fauna | Risco | Area alto risco km2 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 0-1 km | 481.98 | 0.062 | 0.060 | 0.932 | 0.791 | 0.365 | 0.038 | 10.48 |
| 1-5 km | 478.09 | 0.015 | 0.011 | 0.841 | 0.638 | 0.330 | 0.005 | 0.00 |
| 5-10 km | 147.11 | 0.007 | 0.003 | 0.580 | 0.354 | 0.266 | 0.001 | 0.00 |

# Resultados do Indice Ecologico Relativo

Este relatorio e gerado pelo script `ecological_risk_analysis.py`.
Os valores sao relativos e usam as imagens atuais do projeto mais proxies espaciais de habitat.

## Leitura correta

- `radiance_mean_relative` representa a intensidade visual normalizada da camada de luz.
- `bottom_light_mean_relative` estima a luz que permanece relevante em agua rasa/profunda usando um proxy de atenuacao.
- `risk_index_mean` combina luz, habitat e sensibilidade de fauna em escala relativa de 0 a 1.
- `high_risk_area_km2` e a area estimada com indice maior ou igual a 0,55.

## Florianopolis

| Buffer | Area agua km2 | Luz media | Luz fundo | Habitat | Fauna | Risco | Area alto risco km2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0-1 km | 542.25 | 0.062 | 0.060 | 0.795 | 0.559 | 0.049 | 9.64 |
| 1-5 km | 709.36 | 0.014 | 0.010 | 0.653 | 0.510 | 0.006 | 0.00 |
| 5-10 km | 65.04 | 0.007 | 0.004 | 0.400 | 0.422 | 0.001 | 0.00 |

## Balneario Camboriu

| Buffer | Area agua km2 | Luz media | Luz fundo | Habitat | Fauna | Risco | Area alto risco km2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0-1 km | 357.67 | 0.087 | 0.085 | 0.804 | 0.466 | 0.061 | 12.54 |
| 1-5 km | 653.59 | 0.014 | 0.010 | 0.630 | 0.416 | 0.004 | 0.00 |
| 5-10 km | 201.16 | 0.006 | 0.003 | 0.341 | 0.333 | 0.001 | 0.00 |
| 10-30 km | 10.59 | 0.005 | 0.002 | 0.105 | 0.265 | 0.000 | 0.00 |

## Itajai

| Buffer | Area agua km2 | Luz media | Luz fundo | Habitat | Fauna | Risco | Area alto risco km2 |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0-1 km | 481.98 | 0.062 | 0.060 | 0.804 | 0.450 | 0.041 | 11.26 |
| 1-5 km | 478.09 | 0.015 | 0.011 | 0.634 | 0.403 | 0.005 | 0.00 |
| 5-10 km | 147.11 | 0.007 | 0.003 | 0.353 | 0.325 | 0.001 | 0.00 |

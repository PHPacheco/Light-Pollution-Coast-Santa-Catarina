# Relatorio de prioridades: luz artificial e fauna marinha

## Resumo

O projeto deve evoluir de mapas de luz artificial sobre agua para uma analise de risco ecologico costeiro. A estrategia recomendada e manter VIIRS/Black Marble como base quantitativa sempre que possivel, mas tambem permitir uma versao executavel com as imagens atuais do projeto como proxy visual normalizado.

O indice adotado para a primeira implementacao e:

```text
risco_ecologico = exposicao_luminosa * presenca_fauna * sensibilidade * fator_habitat
```

Nesta versao, `presenca_fauna`, `sensibilidade` e `fator_habitat` sao proxies relativos. Eles devem ser substituidos ou calibrados com OBIS, GEBCO e Bio-ORACLE/OceanColor quando esses dados forem baixados.

## Prioridade 1: nucleo essencial

- Gerar metricas por cidade e por buffer marinho: `0-1 km`, `1-5 km`, `5-10 km` e `10-30 km`.
- Calcular exposicao luminosa relativa a partir da imagem `Images/exposure-gradient`.
- Usar a mascara de agua existente para separar pixels aquaticos.
- Criar tabela comparativa com area de agua, radiancia media, radiancia P90 e indice de risco.
- Representar fauna como proxy inicial de grupos sensiveis: zooplancton/copepodes, invertebrados bentonicos, peixes costeiros, tartarugas e aves marinhas.

## Prioridade 2: relacao ecologica mais forte

- Estimar buffers marinhos a partir da distancia dos pixels de agua em relacao a terra.
- Criar proxy de profundidade relativa: pixels mais proximos da margem/costa sao tratados como mais rasos.
- Criar proxy de atenuacao da luz na agua, combinando profundidade relativa, proximidade da costa e exposicao luminosa.
- Calcular uma camada de luz relativa no fundo:

```text
exposicao_fundo_relativa = luz_normalizada * exp(-kd_proxy * profundidade_relativa)
```

- Combinar luz no fundo, habitat raso/produtivo e sensibilidade de fauna em um indice ecologico relativo.
- Gerar mapas por etapa para facilitar auditoria visual do processo.

## Prioridade 3: enriquecimento futuro

- Importar OBIS para substituir proxies de fauna por ocorrencias reais georreferenciadas.
- Importar GEBCO para substituir a profundidade relativa por batimetria real.
- Importar Bio-ORACLE ou NASA OceanColor para substituir o `kd_proxy` por atenuacao da luz ou dados de qualidade optica da agua.
- Cruzar os resultados com CNUC/MMA para destacar unidades de conservacao e habitats sensiveis.
- Usar AquaMaps como complemento quando OBIS tiver poucos registros locais.
- Avaliar ERA5/nuvens e World Atlas sky brightness apenas depois da versao principal estar validada.

## Uso das imagens atuais

As imagens atuais podem ser usadas como fonte operacional para esta versao do indice, desde que o texto do projeto deixe claro que os valores sao relativos. Elas sao especialmente uteis para processamento de imagem, demonstracao visual, validacao qualitativa e composicao do relatorio.

Para medicao fisica de intensidade luminosa, VIIRS/Black Marble continuam sendo mais defensaveis por terem radiancia calibrada e comparabilidade espacial/temporal.

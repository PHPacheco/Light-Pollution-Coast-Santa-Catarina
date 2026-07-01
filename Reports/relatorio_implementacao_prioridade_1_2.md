# Relatorio de implementacao: Prioridades 1 e 2

## O que foi implementado

Foi adicionado um pipeline local em `ecological_risk_analysis.py` para relacionar luz artificial, agua costeira e risco ecologico relativo para Florianopolis, Balneario Camboriu e Itajai.

O script usa as imagens existentes do projeto e gera saidas organizadas por etapa em `EcologicalRiskImages/`:

- `01-light-exposure`: exposicao luminosa normalizada.
- `02-marine-buffers`: buffers marinhos estimados a partir da mascara de agua.
- `03-habitat-and-bottom-light`: proxy de habitat sensivel e luz relativa no fundo.
- `04-ecological-risk-index`: indice ecologico relativo por cidade.
- `05-comparisons`: comparacao visual entre as tres cidades.

Tambem foi criado `Data/ecological-risk/fauna_sensitivity_weights.csv`, com pesos iniciais por cidade e grupo biologico. Esses pesos sao proxies documentados e podem ser substituidos por dados OBIS no futuro.

## Como o indice funciona

O pipeline calcula a luz normalizada a partir das imagens de gradiente existentes, restringe a analise aos pixels classificados como agua e estima buffers a partir da distancia desses pixels ate a terra.

Para aproximar a Prioridade 2 sem baixar novos datasets, o script cria:

- `depth_proxy`: profundidade relativa estimada pela distancia da costa/margem.
- `kd_proxy`: atenuacao relativa da luz na agua.
- `bottom_light`: luz relativa que permanece ecologicamente relevante no fundo.
- `habitat_proxy`: combinacao de agua rasa, produtividade costeira presumida e luz no fundo.
- `fauna_proxy`: sensibilidade relativa por cidade e grupos biologicos.

O indice final e normalizado entre as cidades para permitir comparacao relativa:

```text
risco_ecologico = bottom_light * habitat_proxy * fauna_proxy
```

## Arquivos gerados

- `Data/ecological-risk/ecological_risk_metrics.csv`
- `Reports/relatorio_resultados_indice_ecologico.md`
- `EcologicalRiskImages/01-light-exposure/*.png`
- `EcologicalRiskImages/02-marine-buffers/*.png`
- `EcologicalRiskImages/03-habitat-and-bottom-light/*.png`
- `EcologicalRiskImages/04-ecological-risk-index/*.png`
- `EcologicalRiskImages/05-comparisons/comparison-cities-ecological-risk-index.png`

## Limitacoes assumidas

Esta implementacao nao afirma causalidade biologica nem substitui dados ambientais reais. Ela cria uma versao funcional e auditavel do indice usando as imagens atuais do projeto. A proxima melhoria cientifica e trocar os proxies por OBIS, GEBCO e Bio-ORACLE/OceanColor.

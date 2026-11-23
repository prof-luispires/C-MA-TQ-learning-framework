E3-R73 — Auditoria de estabilidade e recompensas (exploratória)

Objetivo: diagnosticar políticas, não otimizar métricas nem afirmar ganhos cooperativos.

1. Executar 00_INSTALL_ALL.bat (todas as dependências numa única execução).
2. Executar 15_R73_STABILITY_SMOKE.bat.
3. Enviar results/r73_stability_audit.json.
4. Apenas após revisão executar 16_R73_STABILITY_MULTISEED.bat (3 sementes).

A E3-R73 usa apenas a partição de desenvolvimento/validação do ficheiro train.csv.gz.
Não utiliza test.csv.gz para seleção ou auditoria de desempenho; não é confirmação externa.
Não altera a função de recompensa ou o motor E3-R72; primeiro mede FPR, MCC,
seleção de checkpoints, contagem de ações e cobertura Q pós-inspeção.
As arquiteturas ainda não têm capacidade e informação rigorosamente equiparadas.
Os testes contrafactuais E3-R72 permanecem disponíveis separadamente.

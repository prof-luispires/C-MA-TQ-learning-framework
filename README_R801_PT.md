# E3-R80.1 — Correção da classificação dos episódios

Correção: um alerta num episódio normal é FP; num episódio de ataque, um alerta a partir do onset é TP. Alertas prematuros em ataques não contam como TP, conforme a métrica agregada original.

Incluídas asserções por semente e arquitetura que comparam TP/TN/FP/FN individuais com as métricas agregadas. Nenhuma alteração de treino, política, reward ou dados.

Executar primeiro `28_R801_DIAGNOSTIC_SMOKE.bat`; depois `29_R801_DIAGNOSTIC_FULL.bat`. Os ficheiros `results/r80_*` são reescritos pela execução. A execução SMOKE não substitui FULL.

Limitações: validação reutilizada, não confirmatória; o motor ainda lê dados históricos de teste na inicialização; contrafactuais sem retreino.

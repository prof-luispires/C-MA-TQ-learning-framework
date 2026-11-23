# E3-R80 — Diagnóstico estrutural (desenvolvimento)

Estado: PASS; configurações: 8; episódios: 320

## Ficheiros
- r80_metrics.csv: MCC, FPR, recall e matriz de confusão por semente
- r80_episode_errors.csv: classificação TP/TN/FP/FN por episódio e cobertura de Q nas decisões
- r80_q_coverage.csv: cobertura observada dos pares estado-ação
- r80_specialist_buckets.csv: distribuição marginal de sinais dos especialistas
- r80_inference_counterfactual.csv: neutralização **apenas na inferência**, sem retreino

## Avisos
- Dados de validação de desenvolvimento já explorados. Sem inferência confirmatória.
- Neutralização pós-treino não prova importância causal; comparar com ablação retreinada.
- O motor carrega historicamente test.csv.gz no arranque; a R80 não o avalia, mas esta dependência deve ser removida antes do protocolo independente.
- O estudo de redundância entre sinais e a equivalência de capacidade ainda exigem uma fase adicional.

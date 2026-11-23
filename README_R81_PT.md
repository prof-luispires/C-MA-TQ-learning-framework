# E3-R81 — Diagnóstico final de especialistas (desenvolvimento)

Executar `30_R81_DIAGNOSTIC_SMOKE.bat` e depois `31_R81_DIAGNOSTIC_FULL.bat`.

Seis variantes, com coordenador **retreinado**: central, four_q, no_phy, no_protocol, no_radio e no_temporal. As ablações neutralizam o sinal do especialista mas preservam as mesmas dimensões de estado; as políticas locais são treinadas em comum, não se remove o custo de treino local. Cinco sementes no modo FULL.

Resultados em `results`: r80_metrics.csv, r80_episode_errors.csv, r80_q_coverage.csv, r80_specialist_buckets.csv, r80_inference_counterfactual.csv, r81_joint_buckets.csv, r81_pairwise_mutual_information.csv, r81_structural_audit.json e R81_RELATORIO_PT.md. Os nomes r80_* mantêm compatibilidade e são sobrescritos pela execução R81.

**Limitações:** treino e validação são de desenvolvimento; calibração dos especialistas usa dados de validação não rotulados; motor original carrega o test histórico; comparação não é de capacidade equivalente; MI empírica é descritiva e não prova causalidade; este ensaio não constitui teste confirmatório.

**Critério de decisão:** se four_q não superar ablações em MCC e compromisso FPR/recall, congelar ambas como hipóteses concorrentes, sem selecionar retrospectivamente no teste final. R82 deve isolar o test e deslocar calibração para partição de treino antes de qualquer avaliação independente.

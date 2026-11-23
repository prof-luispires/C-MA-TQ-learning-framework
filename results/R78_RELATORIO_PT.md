# E3-R78 — Auditoria de capacidade e comparabilidade

**Âmbito:** desenvolvimento, sem treino adicional nem acesso ao conjunto de teste.

## Verificações

- matched_seeds: SIM
- same_training_step_budget: SIM
- same_validation_episodes: SIM
- same_reward: SIM
- matched_parameter_capacity: NÃO
- matched_state_space: NÃO
- independent_checkpoint_selection_and_evaluation: NÃO
- independent_external_attack_labels: NÃO
- full_training_runtime_measured: NÃO
- end_to_end_inference_runtime_measured: NÃO
- memory_usage_model_measured: NÃO

## Interpretação

A ocupação observada da tabela Q não equivale à capacidade teórica. O microbenchmark mede exclusivamente a codificação de estado, com Q locais vazias; não mede o tempo de inferência nem o custo de treino.

## Decisão

Não congelar conclusões científicas: faltam equivalência de capacidade, benchmark completo e avaliação independente.

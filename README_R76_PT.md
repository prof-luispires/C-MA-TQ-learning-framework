# E3-R76 — Instrumentação e estabilidade multi-semente

## Finalidade
Auditar as ações reais de treino e a estabilidade de cinco sementes no conjunto de desenvolvimento. NÃO é validação confirmatória.

## Execução Windows
1. Executar `00_INSTALL_ALL.bat` (instalação única de dependências).
2. Executar `20_R76_INSTRUMENTED_SMOKE.bat`.
3. Enviar `results/r76_stability_audit.json` e `results/r76_training_td_trace.csv`.
4. Apenas após revisão, executar `21_R76_MULTISEED.bat` (5 sementes; treino mais prolongado).

## O que mudou
- `known_before` registado ANTES de aplicar a atualização Q, em todas as transições instrumentadas.
- `selection_type` diferencia escolha greedy, exploração epsilon e exploração forçada de inspeção.
- Ações disponíveis, número de ações Q conhecidas e epsilon registados.
- Traços de treino reais dos três primeiros episódios e de episódios espaçados.
- Comparação das mesmas 3 condições estruturais e 5 arquiteturas da R75, sem alterar recompensas.

## Limitações
Resultados de validação em dados sintéticos já explorados; não usar para afirmações confirmatórias. Baseline centralizado não equiparado em capacidade; não há ataques externos com rótulos independentes.

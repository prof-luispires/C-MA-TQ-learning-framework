# E3-R80 — Diagnóstico Estrutural da Cooperação

Execute `26_R80_DIAGNOSTIC_SMOKE.bat` para teste rápido ou `27_R80_DIAGNOSTIC_FULL.bat` para cinco sementes.

O script não modifica os algoritmos, a recompensa, a seleção de ações ou os dados. Reproduz o treino com checkpoint final fixo e regista previsões por episódio, cobertura de Q, distribuição dos sinais e neutralização de cada especialista somente na inferência.

Os ficheiros são produzidos em `results/r80_*` e `results/R80_RELATORIO_PT.md`.

**Limitação importante:** o motor original carrega `test.csv.gz` na inicialização, embora o script R80 use apenas os episódios de treino e validação. Não é uma avaliação independente. A neutralização sem retreino não equivale a uma ablação causal. Não existe equivalência de capacidade nem ataques externos rotulados.

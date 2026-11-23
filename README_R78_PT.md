# E3-R78 — Auditoria de capacidade e comparabilidade

Execute `23_R78_CAPACITY_COST_AUDIT.bat` depois de `00_INSTALL_ALL.bat`.

Esta fase **não altera o algoritmo**, não treina modelos nem utiliza `test.csv.gz`. Usa os ficheiros de entrada `inputs/r76_multiseed_audit.json` e `inputs/r76_multiseed_td_trace.csv` herdados da R77.

Resultados: `results/r78_capacity_cost_audit.json`, `results/r78_capacity_observed.csv` e `results/R78_RELATORIO_PT.md`.

O microbenchmark mede apenas a codificação de estado (sem Q locais aprendidas), não o custo de inferência completa. A análise de capacidade reporta entradas Q ocupadas, não uma equivalência de parâmetros. Por isso, esta R78 é uma **auditoria preliminar**, não um congelamento confirmatório.

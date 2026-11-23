# E3-R79 — Benchmark end-to-end de desenvolvimento

Executar `24_R79_BENCHMARK_SMOKE.bat` para verificação rápida ou `25_R79_BENCHMARK_FULL.bat` para cinco sementes.

Saídas: `results/r79_benchmark_audit.json`, `results/r79_end_to_end.csv`, `results/R79_RELATORIO_PT.md`.

O algoritmo e as recompensas não são alterados. A execução usa exclusivamente treino e validação de desenvolvimento; não acede ao conjunto de teste. A comparação usa o último checkpoint, não seleciona pelo conjunto de validação.

Atenção: os tempos de treino local são partilhados entre arquiteturas; não há capacidade nem computação equiparada. A memória é o pico de alocações Python (tracemalloc), não RSS. Não se pode declarar superioridade científica ou generalização externa a partir desta campanha.

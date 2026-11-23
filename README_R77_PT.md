# E3-R77 — Consolidação multi-semente e auditoria de comparabilidade

Executar `00_INSTALL_ALL.bat` se necessário e depois `22_R77_CONSOLIDATE.bat`.

O pacote contém a framework E3-R76 completa e os resultados multi-semente recebidos. O script R77 NÃO treina modelos novos nem acede ao conjunto de teste. Produz `results/r77_consolidated_audit.json`, `results/r77_summary.csv`, `results/r77_paired_differences.csv`, `results/R77_RELATORIO_PT.md`.

As comparações são descritivas e emparelhadas por semente. A seleção de checkpoints reutiliza validação; os episódios de avaliação são partilhados pelas sementes. Não existe equivalência de capacidade entre centralizado e multiagente nem medição rigorosa de latência/energia. Estas tarefas continuam pendentes antes do congelamento da framework.

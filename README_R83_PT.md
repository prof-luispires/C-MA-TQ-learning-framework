# E3-R83 — Grandes simulações de desenvolvimento

Artigo: Cooperative Multi-Agent Q-Learning with Interaction-Aware Coordination for Anomaly Detection in Heterogeneous LoRaWAN Traffic.

Dataset **exclusivo**: `data/train.csv.gz` original sintético. `test.csv.gz` não é lido. Motor limpo R82, calibração exclusivamente no treino.

## Execução Windows
- `33_R83_SMOKE.bat`: 2 sementes, 80/150 passos
- `34_R83_PILOT_5_SEEDS.bat`: 5 sementes, 600/1000 passos
- `35_R83_FULL_20_SEEDS.bat`: 20 sementes, 600/1000 passos (demorado)

**Execute primeiro o piloto de cinco sementes e envie resultados antes de lançar 20 sementes.**

Ficheiros: `results/r83_campaign_manifest.json`, `r83_metrics.csv`, `r83_episode_predictions.csv`, `r83_summary.csv`, `R83_RELATORIO_PT.md`.

## Restrições científicas
- Esta campanha **não é confirmatória**: validação sintética original previamente explorada.
- Comparação com mesmo número de transições mas sem igualdade de capacidade ou de tempo total.
- Tempo de treino dos especialistas é comum e reportado separadamente; não confundir tempo do coordenador com custo total.
- Não modificar hiperparâmetros após examinar resultados para alegar validação independente.

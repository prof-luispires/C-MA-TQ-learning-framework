# E3-R77 — Análise consolidada (desenvolvimento)

Execuções: 75; sementes: [42, 123, 2026, 31415, 27182]; linhas TD verificadas: 13347.

## MCC médio ± desvio-padrão por condição

### baseline
- central: MCC 0.162 ± 0.119; FPR 58.0%; recall 72.7%; unseen 5.5%
- four_q: MCC 0.231 ± 0.065; FPR 32.0%; recall 58.0%; unseen 4.5%
- no_phy: MCC 0.282 ± 0.165; FPR 28.0%; recall 58.7%; unseen 8.5%
- no_protocol: MCC 0.192 ± 0.082; FPR 30.0%; recall 50.7%; unseen 2.1%
- permuted_q: MCC 0.213 ± 0.115; FPR 34.0%; recall 52.7%; unseen 10.5%
### persist_inspection
- central: MCC 0.038 ± 0.083; FPR 68.0%; recall 71.3%; unseen 8.2%
- four_q: MCC 0.161 ± 0.085; FPR 44.0%; recall 61.3%; unseen 19.9%
- no_phy: MCC 0.328 ± 0.047; FPR 8.0%; recall 43.3%; unseen 3.5%
- no_protocol: MCC 0.098 ± 0.076; FPR 26.0%; recall 34.0%; unseen 32.9%
- permuted_q: MCC 0.186 ± 0.166; FPR 50.0%; recall 66.7%; unseen 18.5%
### persist_known_first
- central: MCC 0.215 ± 0.103; FPR 34.0%; recall 54.7%; unseen 22.2%
- four_q: MCC 0.273 ± 0.124; FPR 44.0%; recall 72.0%; unseen 9.6%
- no_phy: MCC 0.320 ± 0.087; FPR 12.0%; recall 48.0%; unseen 2.9%
- no_protocol: MCC 0.114 ± 0.108; FPR 40.0%; recall 52.0%; unseen 17.2%
- permuted_q: MCC 0.277 ± 0.140; FPR 56.0%; recall 80.7%; unseen 11.2%

## Comparações emparelhadas: four_q − alternativa

- baseline / four_q minus central: ΔMCC=+0.069; four_q superior em 4/5 sementes; ΔFPR=-26.0%
- baseline / four_q minus no_phy: ΔMCC=-0.052; four_q superior em 3/5 sementes; ΔFPR=+4.0%
- baseline / four_q minus no_protocol: ΔMCC=+0.038; four_q superior em 3/5 sementes; ΔFPR=+2.0%
- baseline / four_q minus permuted_q: ΔMCC=+0.018; four_q superior em 3/5 sementes; ΔFPR=-2.0%
- persist_inspection / four_q minus central: ΔMCC=+0.123; four_q superior em 4/5 sementes; ΔFPR=-24.0%
- persist_inspection / four_q minus no_phy: ΔMCC=-0.167; four_q superior em 0/5 sementes; ΔFPR=+36.0%
- persist_inspection / four_q minus no_protocol: ΔMCC=+0.063; four_q superior em 3/5 sementes; ΔFPR=+18.0%
- persist_inspection / four_q minus permuted_q: ΔMCC=-0.025; four_q superior em 2/5 sementes; ΔFPR=-6.0%
- persist_known_first / four_q minus central: ΔMCC=+0.058; four_q superior em 3/5 sementes; ΔFPR=+10.0%
- persist_known_first / four_q minus no_phy: ΔMCC=-0.046; four_q superior em 2/5 sementes; ΔFPR=+32.0%
- persist_known_first / four_q minus no_protocol: ΔMCC=+0.159; four_q superior em 5/5 sementes; ΔFPR=+4.0%
- persist_known_first / four_q minus permuted_q: ΔMCC=-0.004; four_q superior em 2/5 sementes; ΔFPR=-12.0%

## Limitações

- Validation set is reused for checkpoint selection; descriptive results only
- 40 validation episodes per seed (30 attacks, 10 normal); seeds share evaluation episodes
- No independently labeled external attack dataset
- No capacity-matched centralized baseline; policy_entries is not model capacity
- No measured runtime or memory cost; do not interpret decision counts as wall-clock costs
- Five seeds are insufficient for robust inferential claims
- Reward and training logic unchanged from R76

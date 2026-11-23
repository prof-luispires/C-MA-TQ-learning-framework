# E3-R82 — Preparação do congelamento experimental

Esta versão **não é ainda uma campanha confirmatória**. Inclui o motor isolado `core/r82_clean_engine.py`, que **não carrega** `test.csv.gz` e calcula a calibração exclusivamente sobre `tr` (treino), e uma auditoria executável de integridade.

## Windows
Executar `32_R82_FREEZE_READINESS.bat`. Enviar `results/r82_freeze_readiness.json`.

## Limites importantes
- Os scripts R81 e anteriores são preservados por compatibilidade e continuam a usar o motor antigo. **Não os utilizar para resultados confirmatórios.**
- A execução R82 é um piloto técnico curto, não reavalia as seis arquiteturas nem produz os resultados finais.
- O congelamento é **provisório** até existir conjunto de avaliação externo, com rótulos e proveniência verificados.
- `r82_protocol_manifest.json` fixa as decisões de desenvolvimento; a campanha R83 exige implementação específica e orçamento/recursos definidos.
- A validação histórica foi explorada e não é um holdout independente.

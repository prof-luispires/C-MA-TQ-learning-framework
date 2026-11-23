# E3-R72 — Correção estrutural exploratória

1. Executar `00_INSTALL_ALL.bat` (instala todas as dependências numa só execução).
2. Executar `14_R72_STRUCTURAL_SMOKE.bat`.
3. Enviar `results/r72_structural_audit.json`.

**Não executar a campanha confirmatória.** O treino R72 gera checkpoints novos em `models_r72/` sem sobrescrever os anteriores.

## Alterações
- Sinais dos especialistas disponíveis antes da inspeção (2 sinais), 4 após inspeção.
- Comparador centralizado recebe o mesmo número de sinais agregados.
- Ablações substituem o sinal por um valor neutro, sem alterar a dimensão do estado.
- Contadores de ações reais e cobertura de estados visitados.
- Auditoria contrafactual em decisões finais e teste de equivalência entre execução instrumentada e motor.
- Checkpoint roundtrip e persistência do mapa permutado.

## Limitações
- Os sinais centrais são agregações de atributos brutos; os sinais multi são Q-vantagens calibradas: cardinalidade igual, mas não capacidade funcional nem informação equivalente.
- Dados sintéticos previamente explorados; resultados apenas diagnósticos.
- Inspeção com sinais prévios poderá ser redundante; esta é uma hipótese arquitetural a verificar, não uma validação.
- `PASS` significa que o programa executou e verificou invariantes, não que a cooperação produziu ganho.
- Checkpoints pickle apenas de origem local fiável.

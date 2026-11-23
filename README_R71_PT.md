# E3-R71 — Auditoria contrafactual, apenas diagnostico

Este pacote preserva o motor E3-R70 e inclui checkpoints gerados num teste exploratorio curto (semente 42, 80 passos locais e 80 passos do coordenador). A auditoria nao executa novo treino. Os 175 episodios de teste sao complementados por 25 controlos normais sinteticos, perfazendo 200 episodios.

## Windows
1. Executar `00_INSTALL_ALL.bat` uma unica vez (instala todas as dependencias).
2. Executar `13_R71_COUNTERFACTUAL_AUDIT.bat`.
3. Enviar `results/r71_counterfactual_audit.json`.

## O que mede
- Cobertura das acoes Q efetivamente visitadas depois da inspecao (nao apenas entradas existentes na tabela).
- Sensibilidade das decisoes finais a substituicao isolada dos sinais dos agentes por valores extremos 0 e 3, **apenas depois da inspecao**.
- Variacoes de previsao, tempo e numero de inspecoes, por episodio.
- Persistencia do mapeamento de permutacao; se faltar, o teste dessa variante e explicitamente omitido.

## Limitacoes
- Dados sinteticos previamente explorados; nao sao avaliacao confirmatoria.
- Alteracoes contrafactuais de buckets nao equivalem a intervencoes fisicas nos sinais radio.
- Nao prova causalidade da cooperacao nem melhoria estatistica.
- Nao altera checkpoints, datasets ou resultados anteriores (exceto criar o novo JSON).
- Antes de congelar a framework, verificar paridade de informacao/capacidade, ataque externo rotulado e protocolo de validacao.

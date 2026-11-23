# E3-R68 — Auditoria de integridade e persistência (DESENVOLVIMENTO)

## Estado científico
O E3-R67 passou a verificação local de persistência em 175 episódios. Os quatro modelos produziram métricas idênticas (MCC 0.1255, FPR 72%). Isto não demonstra vantagem cooperativa. Os resultados são de campanhas sintéticas anteriormente exploradas.

## Execução Windows
1. Descompactar o ZIP numa pasta própria.
2. Executar `00_INSTALL_ALL.bat` **uma única vez** para instalar todas as dependências na `.venv`.
3. Executar `08_AUDIT_FRAMEWORK.bat` — auditoria sem treino; produz `results/framework_audit.json`.
4. **Enviar esse JSON antes de treinos prolongados**. Não executar `09_DEVELOPMENT_RETRAIN.bat` ainda.

## Correção de permutação
O motor E3-R68 passa a guardar o mapa de permutações no checkpoint `permuted_q` durante NOVO treino. O verificador `07_VERIFY_CHECKPOINTS.bat` passa a incluir esta variante, mas o checkpoint legado não tem o mapa e não pode ser verificado. A correção só é efetiva após regenerar os checkpoints com `09_DEVELOPMENT_RETRAIN.bat` (não executar ainda).

## O que a auditoria verifica
- Hashes dos dados, dimensões, distribuição por cenário, duplicados e consistência de episódios;
- Contagem de entradas Q por arquitetura e especialista;
- Acordo de decisões (classe, instante e inspeções) entre políticas, por semente;
- Presença/ausência do mapa de permutação.

## Limitações / bloqueios antes da campanha do artigo
- Os dados de treino/teste incluídos são sintéticos e previamente explorados; não confirmatórios.
- A discrepância entre a avaliação de 200 episódios no PC e o conjunto de 175 episódios neste pacote não está reconciliada.
- Os controlos de custo e capacidade entre modelos não estão totalmente equiparados.
- Falta integrar um dataset externo independente com ataques rotulados e esquema compatível.
- A persistência corrigida do permuted_q ainda precisa de validação após treino.
- `pickle` só deve ser usado com checkpoints locais de confiança.

## Protocolo futuro
Congelar datasets/splits, código, hiperparâmetros, métricas e sementes antes de abrir o teste externo; reportar MCC, FPR, balanced accuracy, recall, atraso de deteção, inspeções, custo computacional, intervalos de confiança e comparação pareada. Resultados negativos também serão reportados.


## E3-R69 - Diagnostico da aprendizagem (sem treino)
Execute 00_INSTALL_ALL.bat e 10_DIAGNOSE_LEARNING.bat. Envie results/learning_diagnostic.json. Este diagnostico mede cobertura dos estados Q, empates, distribuicao de acoes e sensibilidade dos sinais dos agentes apos inspecao. Nao altera checkpoints nem utiliza resultados de teste para treino. Os resultados continuam exploratorios. O checkpoint permuted_q legado e excluido da avaliacao ate regeneracao com mapeamento persistido.


## E3-R70 — prototipo de correcao (exploratorio)
A E3-R69 confirmou ausencia de cobertura Q em estados pos-inspecao. Esta versao conserva `core/legacy_engine.py` e acrescenta `core/r70_engine.py` com: (a) compressao de estado pos-inspecao para quatro sinais agrupados, (b) exploracao de inspecao durante treino, (c) contagem de entradas Q pos-inspecao. A versao R70 NAO esta cientificamente congelada, nao demonstra melhor desempenho nem paridade de capacidade.

**Windows**: executar `00_INSTALL_ALL.bat`, depois `11_R70_SMOKE_TEST.bat`. Enviar `results/r70_learning_audit.json`. O smoke substitui checkpoints e resultados da pasta descompactada: usar uma pasta nova e conservar os ZIPs anteriores. Nao executar `12_R70_DEVELOPMENT_TRAIN.bat` ainda.

**Limites**: os modelos central e multi usam sinais de tipos diferentes, apesar de quatro componentes em cada estado pos-inspecao. A equidade de informacao, complexidade e custo ainda requer estudo. `permuted_q` tem mapeamento guardado apenas nos novos checkpoints; verificacao pos-treino pendente.


E3-R74: ver README_R74_PT.md e executar 17_R74_TRANSITION_AUDIT.bat.

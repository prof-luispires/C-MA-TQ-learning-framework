E3-R75 — Experiência estrutural controlada (desenvolvimento, NÃO confirmatória)

Objetivo: comparar (A) implementação R72, (B) persistência da inspeção, (C) persistência + política de seleção conhecida-primeiro. Mesmos episódios, sementes e orçamentos por variante. Recompensas inalteradas. A regra conhecida-primeiro é uma hipótese experimental, não uma correção universal.

1. Executar 00_INSTALL_ALL.bat (instalação única de todas as dependências).
2. Executar 18_R75_CONTROLLED_SMOKE.bat.
3. Enviar results/r75_structural_audit.json e results/r75_training_td_trace.csv.
4. Não executar 19_R75_MULTISEED.bat até revisão do diagnóstico curto.

O CSV contém TD reais do treino dos primeiros três episódios de cada configuração, incluindo Q anterior, bootstrap, alvo, erro e Q atualizado. O relatório usa apenas validação. Nenhum resultado de teste foi usado para seleção.

Limitações: dados sintéticos já explorados, capacidades dos modelos não equiparadas, ataques externos rotulados ainda não integrados. O congelamento para publicação está pendente.

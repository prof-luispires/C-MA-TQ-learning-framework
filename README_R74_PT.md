E3-R74 | Auditoria de transicoes e recompensas | 2026-11-20

Instalar: 00_INSTALL_ALL.bat (todas as dependencias de uma vez).
Executar: 17_R74_TRANSITION_AUDIT.bat.
Enviar: results/r74_transition_audit.json e results/r74_transition_trace.csv (ou ZIP dos dois).
Nao executar ainda 18_R74_DEVELOPMENT_AUDIT.bat.

Os cinco objetivos:
1) Reconstruir por decisao: estado, acao, recompensa, proximo estado, acoes validas, Q e alvo TD. CSV.
2) Testar recompensas terminais com casos de calculo manual e contar resultados por classe.
3) Quantificar Q conhecido/desconhecido, empates e escolhas por valores nao aprendidos.
4) Validar atualizacao TD(0), gamma, alpha e bootstrap terminal em casos manuais; confirmar trajetorias com o motor.
5) Executar testes automaticos e falhar em caso de discrepancia.

LIMITACAO IMPORTANTE: o CSV reconstitui os alvos TD a partir da politica selecionada, nao regista
historicamente as atualizacoes do treino. Os testes manuais verificam a formula TD e as recompensas,
mas nao sao ainda uma prova de cada atualizacao interna durante o treino. A E3-R75 podera
instrumentar o treino em tempo real caso os resultados justifiquem.

Apenas treino e validacao sinteticos ja explorados. Nenhuma conclusao confirmatoria.
A implementacao do motor e os pesos de recompensa NAO foram alterados.

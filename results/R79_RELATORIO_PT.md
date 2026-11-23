# E3-R79 — Benchmark end-to-end (desenvolvimento)

Executa treino local e do coordenador, com tempos medidos, e inferência de episódios completos. Não utiliza test.csv.gz.

## Limites metodológicos

- Os custos de treino local são partilhados e **não** devem ser atribuídos ao modelo centralizado como custo intrínseco.
- Não existe equivalência de capacidade nem de orçamento de CPU entre arquiteturas.
- Os MCC são apenas diagnósticos no conjunto de desenvolvimento, com checkpoint final fixo.
- A memória tracemalloc não é a memória residente do processo.
- A avaliação confirmatória exige dados independentes nunca explorados e rótulos externos.

## Resultados

- Semente 42 / central: treino coordenador 693.8 ms; inferência 1.404 ms/episódio; Q=314; MCC desenvolvimento=-0.218
- Semente 42 / four_q: treino coordenador 931.4 ms; inferência 1.800 ms/episódio; Q=176; MCC desenvolvimento=-0.173
- Semente 42 / no_phy: treino coordenador 1017.6 ms; inferência 2.220 ms/episódio; Q=109; MCC desenvolvimento=0.252
- Semente 42 / no_protocol: treino coordenador 947.9 ms; inferência 2.034 ms/episódio; Q=174; MCC desenvolvimento=0.030
- Semente 123 / central: treino coordenador 741.2 ms; inferência 1.441 ms/episódio; Q=320; MCC desenvolvimento=-0.092
- Semente 123 / four_q: treino coordenador 1016.8 ms; inferência 1.360 ms/episódio; Q=162; MCC desenvolvimento=-0.164
- Semente 123 / no_phy: treino coordenador 1059.4 ms; inferência 1.791 ms/episódio; Q=107; MCC desenvolvimento=0.058
- Semente 123 / no_protocol: treino coordenador 1133.9 ms; inferência 2.061 ms/episódio; Q=151; MCC desenvolvimento=0.038

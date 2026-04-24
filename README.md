# burst-sort — comparação entre métodos de ordenação de strings

Repositório de testes comparativos entre **Burstsort**, **MSD Radix Sort** e
**Multikey Quicksort**, conforme a discussão de Sinha & Zobel em
*Cache-Conscious Sorting of Large Sets of Strings with Dynamic Tries*
(ACM JEA, 2004).

Usa o harness [`rantala/string-sorting`](https://github.com/rantala/string-sorting)
(MIT) como upstream — mesmo binário, mesmo compilador, mesmas flags para
todos os algoritmos → comparação justa.

## Estrutura

```
burst-sort/
├── upstream/            # clone de rantala/string-sorting (código dos algoritmos)
├── build/               # saída do CMake (gerado; ignorado pelo git)
├── datasets/            # entradas .txt (gerado; ignorado pelo git)
├── results/             # CSVs e tabelas dos experimentos (ignorado pelo git)
├── scripts/
│   ├── build.sh            # configure + compile em Release
│   ├── fetch_datasets.sh   # gera url.txt, genome.txt, random.txt
│   ├── algorithms.txt      # lista de algoritmos a serem comparados
│   ├── run_benchmark.sh    # bateria com perf stat (cache misses, TLB, IPC)
│   └── summarize.py        # agrega CSV em tabela média ± desvio
└── docs/
    ├── plano-experimentos.md  # metodologia completa
    └── algoritmos.md          # mapeamento de variantes do upstream
```

## Fluxo rápido

```bash
# 1. clonar o upstream (uma vez)
git clone https://github.com/rantala/string-sorting.git upstream

# 2. compilar
scripts/build.sh

# 3. preparar dados
scripts/fetch_datasets.sh                 # 1M strings por arquivo

# 4. rodar a bateria
scripts/run_benchmark.sh                  # REPS=5 default

# 5. resumir e plotar
scripts/summarize.py results/bench_*.csv
scripts/plot.py                           # gera results/plots/*.png
```

Requisitos: `cmake ≥ 3.1`, `g++` com C++11, `python3`. Para contadores de
hardware (cache/TLB): `perf`
(`apt install linux-tools-common linux-tools-generic`) **e**
`sudo sysctl kernel.perf_event_paranoid=1` para habilitar leitura sem root.
Sem privilégios, rode `NOPERF=1 scripts/run_benchmark.sh` — coleta só
wall-clock.

## Algoritmos comparados (default)

| id              | algoritmo                      | origem                        |
|-----------------|--------------------------------|-------------------------------|
| `burstsortL`    | Burstsort list-based           | Sinha & Zobel (original)      |
| `msd_A`         | MSD Radix Sort                 | Rantala                       |
| `mkqsort_bs`    | Multikey Quicksort             | Bentley & Sedgewick (original)|

Editar `scripts/algorithms.txt` para incluir/remover variantes.

## Métricas coletadas

Por execução, via `perf stat`: tempo wall, instructions, cycles,
cache-references/misses, L1 e LLC misses, dTLB misses. A motivação é
verificar o argumento central do trabalho original — que Burstsort ganha
por ter **localidade de referência** superior, não por fazer menos
instruções.

Ver `docs/plano-experimentos.md` para metodologia detalhada,
controles de variância e ameaças à validade. Resultados consolidados
(1M, 10M, 50M com contadores de hardware) em `docs/resultados.md`.

## Licença

Este repositório: MIT. Upstream (`upstream/`) mantém sua própria licença MIT.
Arquivos em `upstream/external/` são código de referência de terceiros e
podem ter licenças próprias.
# burstsort

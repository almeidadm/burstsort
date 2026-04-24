# Resultados

Saída dos experimentos. Ignorado pelo git exceto este README.

- `bench_YYYYMMDD-HHMMSS.csv` — dados brutos (uma linha por repetição).
- `bench_YYYYMMDD-HHMMSS.log` — stdout/stderr dos runs que falharam.
- `bench_YYYYMMDD-HHMMSS.md`  — tabela-resumo gerada por `scripts/summarize.py`.

## Fluxo

```bash
scripts/build.sh
scripts/fetch_datasets.sh
scripts/run_benchmark.sh          # pode levar alguns minutos
scripts/summarize.py results/bench_*.csv
```

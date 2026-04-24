#!/usr/bin/env bash
# Executa a bateria comparativa: cada algoritmo × cada dataset × N repetições,
# capturando tempo e contadores de hardware via `perf stat`.
#
# Saída: results/bench_<timestamp>.csv  com as colunas:
#   algorithm,dataset,run,wall_ms,task_clock_ms,
#   instructions,cycles,cache_references,cache_misses,
#   L1_dcache_loads,L1_dcache_load_misses,LLC_loads,LLC_load_misses,
#   dTLB_loads,dTLB_load_misses
#
# Uso:
#   scripts/run_benchmark.sh                              # defaults
#   REPS=5 DATASETS="url genome" scripts/run_benchmark.sh
#   ALGS="burstsortA" scripts/run_benchmark.sh            # só este algoritmo
#                                                         # (ignora algorithms.txt)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BIN="$REPO_ROOT/build/sortstring"
DATASETS_DIR="$REPO_ROOT/datasets"
RESULTS_DIR="$REPO_ROOT/results"
ALG_FILE="$REPO_ROOT/scripts/algorithms.txt"

REPS="${REPS:-5}"
DATASETS="${DATASETS:-url genome random}"

[ -x "$BIN" ] || { echo "Binário não encontrado: $BIN — rode scripts/build.sh" >&2; exit 1; }

# perf é opcional: se NOPERF=1, mede só wall-clock.
USE_PERF=1
if [ "${NOPERF:-0}" = "1" ]; then
    USE_PERF=0
elif ! command -v perf >/dev/null; then
    echo "AVISO: perf não instalado. Usando modo wall-clock apenas." >&2
    echo "       Para medir cache/TLB: apt install linux-tools-common linux-tools-generic" >&2
    USE_PERF=0
else
    # Preflight: tenta um evento simples para verificar permissão.
    if ! perf stat -e task-clock -- true >/dev/null 2>&1; then
        paranoid="$(cat /proc/sys/kernel/perf_event_paranoid 2>/dev/null || echo '?')"
        echo "AVISO: perf_event_paranoid=$paranoid bloqueia contadores sem root." >&2
        echo "       Para liberar (até próximo boot):" >&2
        echo "         sudo sysctl kernel.perf_event_paranoid=1" >&2
        echo "       Permanente: adicione em /etc/sysctl.conf" >&2
        echo "       Prosseguindo em modo wall-clock apenas (NOPERF=1)." >&2
        USE_PERF=0
    fi
fi

# Lê lista de algoritmos. Se ALGS=... for passado via env, usa essa lista;
# caso contrário, lê de scripts/algorithms.txt (ignora comentários/linhas vazias).
if [ -n "${ALGS:-}" ]; then
    read -r -a ALGS <<< "$ALGS"
else
    ALGS=()
    while IFS= read -r line; do
        line="${line%%#*}"
        line="$(echo "$line" | xargs)"
        [ -n "$line" ] && ALGS+=("$line")
    done < "$ALG_FILE"
fi

mkdir -p "$RESULTS_DIR"
TS="$(date +%Y%m%d-%H%M%S)"
OUT="$RESULTS_DIR/bench_${TS}.csv"
LOG="$RESULTS_DIR/bench_${TS}.log"

PERF_EVENTS="task-clock,instructions,cycles,cache-references,cache-misses,\
L1-dcache-loads,L1-dcache-load-misses,LLC-loads,LLC-load-misses,\
dTLB-loads,dTLB-load-misses"

echo "algorithm,dataset,run,wall_ms,task_clock_ms,instructions,cycles,cache_references,cache_misses,L1_dcache_loads,L1_dcache_load_misses,LLC_loads,LLC_load_misses,dTLB_loads,dTLB_load_misses" > "$OUT"

run_one() {
    local alg="$1" dataset="$2" input="$3" rep="$4"
    local t0 t1 wall_ms

    if [ "$USE_PERF" = "1" ]; then
        local perf_out; perf_out="$(mktemp)"
        t0="$(date +%s%N)"
        perf stat -x, -e "$PERF_EVENTS" -o "$perf_out" -- \
            "$BIN" "$alg" "$input" >/dev/null 2>>"$LOG" || {
                echo "FALHA: $alg em $dataset (run $rep) — ver $LOG" >&2
                rm -f "$perf_out"
                return 1
            }
        t1="$(date +%s%N)"
        wall_ms=$(( (t1 - t0) / 1000000 ))
        awk -v alg="$alg" -v ds="$dataset" -v rep="$rep" -v wall="$wall_ms" '
            BEGIN { FS=","; OFS="," }
            !/^#/ && NF >= 3 {
                ev = $3
                val = $1
                if (val == "<not counted>" || val == "<not supported>") val = ""
                data[ev] = val
            }
            END {
                print alg, ds, rep, wall,
                      data["task-clock"], data["instructions"], data["cycles"],
                      data["cache-references"], data["cache-misses"],
                      data["L1-dcache-loads"], data["L1-dcache-load-misses"],
                      data["LLC-loads"], data["LLC-load-misses"],
                      data["dTLB-loads"], data["dTLB-load-misses"]
            }' "$perf_out" >> "$OUT"
        rm -f "$perf_out"
    else
        t0="$(date +%s%N)"
        "$BIN" "$alg" "$input" >/dev/null 2>>"$LOG" || {
            echo "FALHA: $alg em $dataset (run $rep) — ver $LOG" >&2
            return 1
        }
        t1="$(date +%s%N)"
        wall_ms=$(( (t1 - t0) / 1000000 ))
        echo "$alg,$dataset,$rep,$wall_ms,,,,,,,,,,," >> "$OUT"
    fi
}

echo "== Bateria comparativa =="
echo "Algoritmos: ${ALGS[*]}"
echo "Datasets:   $DATASETS"
echo "Repetições: $REPS"
echo "Saída:      $OUT"
echo

for ds in $DATASETS; do
    input="$DATASETS_DIR/${ds}.txt"
    [ -f "$input" ] || { echo "AVISO: dataset ausente $input — pulando" >&2; continue; }
    for alg in "${ALGS[@]}"; do
        for r in $(seq 1 "$REPS"); do
            printf "  %-22s  %-8s  run %d/%d ... " "$alg" "$ds" "$r" "$REPS"
            if run_one "$alg" "$ds" "$input" "$r"; then
                echo "ok"
            else
                echo "falhou"
            fi
        done
    done
done

echo
echo "Concluído. Resultados: $OUT"

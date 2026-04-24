#!/usr/bin/env python3
"""Sumariza um CSV produzido por run_benchmark.sh em médias ± desvio por
(algoritmo, dataset), e imprime uma tabela também salva como markdown.

Uso:
    scripts/summarize.py results/bench_YYYYMMDD-HHMMSS.csv
"""
import csv, statistics, sys
from pathlib import Path
from collections import defaultdict

if len(sys.argv) != 2:
    sys.exit("uso: summarize.py <results/bench_*.csv>")

csv_path = Path(sys.argv[1])
rows = list(csv.DictReader(csv_path.open()))
if not rows:
    sys.exit("CSV vazio")

metrics = ["wall_ms", "instructions", "cycles", "cache_misses",
           "L1_dcache_load_misses", "LLC_load_misses", "dTLB_load_misses"]

groups = defaultdict(list)
for r in rows:
    groups[(r["algorithm"], r["dataset"])].append(r)

def fnum(s):
    try: return float(s) if s not in ("", None) else None
    except ValueError: return None

lines = ["# Resumo — " + csv_path.name, ""]
header = "| algoritmo | dataset | wall_ms (média±dp) | cache_misses | L1_miss | LLC_miss | dTLB_miss |"
sep    = "|---|---|---|---|---|---|---|"
lines += [header, sep]

def fmt(xs):
    xs = [x for x in xs if x is not None]
    if not xs: return "—"
    m = statistics.mean(xs)
    s = statistics.stdev(xs) if len(xs) > 1 else 0.0
    return f"{m:,.0f}±{s:,.0f}"

for (alg, ds), runs in sorted(groups.items()):
    vals = {m: [fnum(r[m]) for r in runs] for m in metrics}
    lines.append("| {alg} | {ds} | {w} | {cm} | {l1} | {llc} | {tlb} |".format(
        alg=alg, ds=ds,
        w=fmt(vals["wall_ms"]),
        cm=fmt(vals["cache_misses"]),
        l1=fmt(vals["L1_dcache_load_misses"]),
        llc=fmt(vals["LLC_load_misses"]),
        tlb=fmt(vals["dTLB_load_misses"]),
    ))

out_md = csv_path.with_suffix(".md")
out_md.write_text("\n".join(lines) + "\n")
print("\n".join(lines))
print(f"\n(salvo em {out_md})")

#!/usr/bin/env python3
"""Gera gráficos a partir dos CSVs de results/.

Uso:
    scripts/plot.py                       # usa todos bench_*.csv
    scripts/plot.py results/bench_X.csv   # um arquivo específico

Saída: results/plots/*.png
"""
import sys
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"
OUT = RESULTS / "plots"
OUT.mkdir(exist_ok=True)

# Paleta estável: cada algoritmo com a mesma cor em todos os gráficos.
COLORS = {
    "burstsortA":  "#d62728",  # vermelho
    "burstsortL":  "#ff9896",  # vermelho claro
    "msd_A":       "#1f77b4",  # azul
    "mkqsort_bs":  "#2ca02c",  # verde
}
ORDER = ["burstsortA", "burstsortL", "msd_A", "mkqsort_bs"]

# N de strings por arquivo de bench (inferido da nossa convenção).
# Se você variar os CSVs, ajuste aqui.
N_BY_TIMESTAMP = {
    "20260424-083850": 1_000_000,
    "20260424-084714": 10_000_000,
    "20260424-090853": 50_000_000,
}

plt.rcParams.update({
    "font.size": 10,
    "axes.grid": True,
    "grid.alpha": 0.3,
    "figure.autolayout": True,
})

# -----------------------------------------------------------------------------
def load_all():
    """Carrega todos bench_*.csv e adiciona coluna N (tamanho do dataset)."""
    args = [Path(p) for p in sys.argv[1:]] or sorted(RESULTS.glob("bench_*.csv"))
    frames = []
    for path in args:
        df = pd.read_csv(path)
        ts = path.stem.replace("bench_", "")
        df["N"] = N_BY_TIMESTAMP.get(ts, pd.NA)
        df["source"] = ts
        frames.append(df)
    return pd.concat(frames, ignore_index=True)

df = load_all()
# tipos
for col in df.columns:
    if col in ("algorithm", "dataset", "source"): continue
    df[col] = pd.to_numeric(df[col], errors="coerce")

DATASETS = ["url", "genome", "random"]

# -----------------------------------------------------------------------------
def algos_present(sub):
    return [a for a in ORDER if a in sub["algorithm"].unique()]

def fmt_si(x, _pos=None):
    if x >= 1e9: return f"{x/1e9:.1f}G"
    if x >= 1e6: return f"{x/1e6:.1f}M"
    if x >= 1e3: return f"{x/1e3:.0f}k"
    return f"{x:.0f}"

# -----------------------------------------------------------------------------
# 1) Barras — wall-clock médio em 50M, um subplot por dataset.
# -----------------------------------------------------------------------------
def plot_bars_50M():
    sub = df[df["N"] == 50_000_000]
    if sub.empty:
        print("sem dados 50M, pulando bars_50M")
        return
    fig, axes = plt.subplots(1, 3, figsize=(11, 4), sharey=False)
    for ax, ds in zip(axes, DATASETS):
        g = sub[sub["dataset"] == ds].groupby("algorithm")["wall_ms"]
        means = g.mean().reindex(algos_present(sub))
        stds = g.std().reindex(means.index)
        colors = [COLORS[a] for a in means.index]
        bars = ax.bar(means.index, means.values, yerr=stds.values,
                      color=colors, edgecolor="black", linewidth=0.5,
                      capsize=3)
        ax.set_title(f"{ds}  (50M strings)")
        ax.set_ylabel("wall-clock (ms)")
        ax.tick_params(axis="x", rotation=30)
        for bar, v in zip(bars, means.values):
            ax.text(bar.get_x() + bar.get_width()/2, v, f"{v:,.0f}",
                    ha="center", va="bottom", fontsize=8)
    fig.suptitle("Tempo de ordenação — 50M strings", fontsize=12, y=1.02)
    out = OUT / "01_wall_50M.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out}")

# -----------------------------------------------------------------------------
# 2) Escalabilidade — wall_ms vs N (log-log), um subplot por dataset.
# -----------------------------------------------------------------------------
def plot_scaling():
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=False)
    for ax, ds in zip(axes, DATASETS):
        sub = df[df["dataset"] == ds].dropna(subset=["N"])
        for alg in algos_present(sub):
            g = (sub[sub["algorithm"] == alg]
                 .groupby("N")["wall_ms"].mean().sort_index())
            if g.empty: continue
            ax.plot(g.index, g.values, marker="o", linewidth=1.5,
                    label=alg, color=COLORS[alg])
        # referência linear e n log n a partir do primeiro ponto de msd_A
        msd = (sub[sub["algorithm"] == "msd_A"]
               .groupby("N")["wall_ms"].mean().sort_index())
        if not msd.empty:
            n0, t0 = msd.index[0], msd.values[0]
            ns = msd.index.values
            import numpy as np
            ax.plot(ns, t0 * ns / n0, "--", color="gray", alpha=0.5,
                    linewidth=0.8, label="O(n) ref")
            ax.plot(ns, t0 * (ns*np.log2(ns)) / (n0*np.log2(n0)),
                    ":", color="gray", alpha=0.5, linewidth=0.8,
                    label="O(n·log n) ref")
        ax.set_xscale("log"); ax.set_yscale("log")
        ax.set_xlabel("N (strings)"); ax.set_ylabel("wall-clock (ms)")
        ax.set_title(ds)
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(fmt_si))
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(fmt_si))
        ax.legend(fontsize=8, loc="upper left")
    fig.suptitle("Escalabilidade: wall-clock vs N (log-log)", fontsize=12, y=1.02)
    out = OUT / "02_scaling.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out}")

# -----------------------------------------------------------------------------
# 3) Cache misses/string em 50M — grouped bar por dataset.
# -----------------------------------------------------------------------------
def plot_cache_misses():
    sub = df[df["N"] == 50_000_000].copy()
    if sub.empty or sub["cache_misses"].isna().all():
        print("sem dados de perf em 50M, pulando cache_misses")
        return
    # misses por string
    for col in ("cache_misses", "L1_dcache_load_misses",
                "LLC_load_misses", "dTLB_load_misses"):
        sub[col + "_per_str"] = sub[col] / sub["N"]

    metrics = [
        ("cache_misses_per_str",          "cache-miss / string"),
        ("L1_dcache_load_misses_per_str", "L1d-miss / string"),
        ("LLC_load_misses_per_str",       "LLC-miss / string"),
        ("dTLB_load_misses_per_str",      "dTLB-miss / string"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(11, 8))
    import numpy as np
    for ax, (col, label) in zip(axes.flat, metrics):
        algs = algos_present(sub)
        x = np.arange(len(DATASETS))
        width = 0.8 / len(algs)
        for i, alg in enumerate(algs):
            vals = []
            for ds in DATASETS:
                v = sub[(sub["algorithm"] == alg) & (sub["dataset"] == ds)][col].mean()
                vals.append(v)
            ax.bar(x + i*width - 0.4 + width/2, vals, width,
                   label=alg, color=COLORS[alg], edgecolor="black",
                   linewidth=0.3)
        ax.set_xticks(x); ax.set_xticklabels(DATASETS)
        ax.set_ylabel(label)
        ax.set_title(label)
        ax.legend(fontsize=8)
    fig.suptitle("Contadores de hardware por string ordenada (50M strings)",
                 fontsize=12, y=1.00)
    out = OUT / "03_cache_misses_per_string.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out}")

# -----------------------------------------------------------------------------
# 4) Correlação tempo × cache-miss total (50M) — scatter.
# -----------------------------------------------------------------------------
def plot_time_vs_misses():
    sub = df[df["N"] == 50_000_000].copy()
    if sub.empty or sub["cache_misses"].isna().all():
        print("sem dados de perf em 50M, pulando time_vs_misses")
        return
    fig, ax = plt.subplots(figsize=(7, 5))
    markers = {"url": "o", "genome": "s", "random": "^"}
    for alg in algos_present(sub):
        for ds in DATASETS:
            s = sub[(sub["algorithm"] == alg) & (sub["dataset"] == ds)]
            if s.empty: continue
            ax.scatter(s["cache_misses"].mean()/1e6, s["wall_ms"].mean(),
                       color=COLORS[alg], marker=markers[ds], s=80,
                       edgecolor="black", linewidth=0.5,
                       label=f"{alg} / {ds}")
    # legendas separadas: alg por cor, dataset por símbolo
    from matplotlib.lines import Line2D
    alg_legend = [Line2D([0],[0], marker="o", color="w",
                          markerfacecolor=COLORS[a], markersize=9,
                          label=a) for a in algos_present(sub)]
    ds_legend = [Line2D([0],[0], marker=m, color="k", linestyle="",
                         markersize=8, label=ds)
                  for ds, m in markers.items()]
    l1 = ax.legend(handles=alg_legend, loc="upper left", title="algoritmo",
                   fontsize=8, title_fontsize=9)
    ax.add_artist(l1)
    ax.legend(handles=ds_legend, loc="lower right", title="dataset",
              fontsize=8, title_fontsize=9)
    ax.set_xlabel("cache-misses totais (milhões)")
    ax.set_ylabel("wall-clock (ms)")
    ax.set_title("Tempo × cache-misses — 50M strings")
    out = OUT / "04_time_vs_cachemisses.png"
    fig.savefig(out, dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"  -> {out}")

# -----------------------------------------------------------------------------
if __name__ == "__main__":
    print("Gerando gráficos em", OUT)
    plot_bars_50M()
    plot_scaling()
    plot_cache_misses()
    plot_time_vs_misses()
    print("Concluído.")

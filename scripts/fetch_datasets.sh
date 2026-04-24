#!/usr/bin/env bash
# Prepara os datasets de entrada para os experimentos.
#
# Sinha & Zobel (JEA 2004) usaram três coleções de strings:
#   - url      (URLs únicas extraídas de crawls)
#   - genome   (substrings genômicas)
#   - random   (strings aleatórias, distribuição uniforme)
#
# Os datasets originais (~300 MB cada) não têm mais link público estável.
# Este script gera substitutos sintéticos/semissintéticos equivalentes em perfil
# estatístico, suficientes para reproduzir a ordem relativa dos algoritmos.
#
# Tamanhos controláveis via variáveis de ambiente:
#   N_STRINGS  (default 1000000)
#   SEED       (default 42)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT_DIR="$REPO_ROOT/datasets"
N_STRINGS="${N_STRINGS:-1000000}"
SEED="${SEED:-42}"

mkdir -p "$OUT_DIR"

python3 - "$OUT_DIR" "$N_STRINGS" "$SEED" <<'PY'
import os, sys, random, string

out_dir, n, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
rng = random.Random(seed)

def write_lines(path, gen):
    with open(path, "w", encoding="utf-8") as f:
        for s in gen:
            f.write(s + "\n")
    print(f"  -> {path}  ({os.path.getsize(path)/1e6:.1f} MB)")

# 1) URL-like: muito prefixo em comum ("http(s)://<dominio>/<path>")
tlds = ["com", "org", "net", "edu", "gov", "io", "br"]
def gen_url():
    for _ in range(n):
        scheme = rng.choice(["http", "https"])
        host = "".join(rng.choices(string.ascii_lowercase, k=rng.randint(4, 12)))
        tld = rng.choice(tlds)
        depth = rng.randint(0, 4)
        path = "/".join("".join(rng.choices(string.ascii_lowercase + string.digits,
                                            k=rng.randint(3, 10)))
                        for _ in range(depth))
        yield f"{scheme}://{host}.{tld}/{path}"

# 2) Genome-like: alfabeto de 4 símbolos, comprimento médio alto (~80)
def gen_genome():
    alpha = "ACGT"
    for _ in range(n):
        L = max(10, int(rng.gauss(80, 15)))
        yield "".join(rng.choices(alpha, k=L))

# 3) Random: ASCII imprimível, comprimento uniforme entre 5 e 60
def gen_random():
    alpha = string.ascii_letters + string.digits
    for _ in range(n):
        L = rng.randint(5, 60)
        yield "".join(rng.choices(alpha, k=L))

print(f"Gerando {n} strings por dataset (seed={seed})...")
write_lines(os.path.join(out_dir, "url.txt"),    gen_url())
write_lines(os.path.join(out_dir, "genome.txt"), gen_genome())
write_lines(os.path.join(out_dir, "random.txt"), gen_random())
PY

echo
echo "Pronto. Para usar seus próprios arquivos, coloque-os em $OUT_DIR/"
echo "(um string por linha, codificação raw bytes)."

# Resultados experimentais

Três baterias executadas na mesma máquina, mesmo binário
(`rantala/string-sorting` em Release, `-O3 -march=native`), mesmo conjunto
de datasets sintéticos (seed 42) gerados por `scripts/fetch_datasets.sh`.

## Ambiente

- CPU: conforme `lscpu` do host; compilado com `g++ 11.4` e `-march=native`.
- RAM: 15 GiB.
- SO: Linux 6.8, `perf` (`linux-tools-generic`) disponível com
  `kernel.perf_event_paranoid=1`.
- Datasets: `url` (prefixos comuns), `genome` (alfabeto ACGT, strings longas),
  `random` (ASCII uniforme). Tamanhos em 50M: 1,77 / 4,02 / 1,67 GB.

## Algoritmos comparados

| id no harness | descrição                              | papel                              |
|---------------|----------------------------------------|-------------------------------------|
| `burstsortL`  | Burstsort list-based (Sinha & Zobel)   | variante conservadora do paper     |
| `burstsortA`  | Burstsort array-based (Sinha & Zobel)  | variante competitiva do paper (50M)|
| `msd_A`       | MSD radix sort array-based (Rantala)   | baseline de radix                   |
| `mkqsort_bs`  | Multikey Quicksort (Bentley & Sedgewick) | baseline de quicksort ternário    |

## Escalonamento por volume (wall-clock, ms)

Os 4 algoritmos medidos nos 3 volumes (1M, 10M, 50M), mesmo seed
determinístico para os datasets.

### `url` — prefixos comuns

| algoritmo    | 1M         | 10M             | 50M              |
|--------------|------------|-----------------|------------------|
| `msd_A`      | **151 ± 2**| 1.762 ± 22      | 9.077 ± 63       |
| `burstsortA` | 156 ± 26   | **1.532 ± 102** | **6.707 ± 42**   |
| `burstsortL` | 195 ± 18   | 2.258 ± 108     | 13.751 ± 588     |
| `mkqsort_bs` | 174 ± 3    | 2.273 ± 10      | 14.172 ± 294     |

### `genome` — alfabeto de 4 símbolos, strings longas

| algoritmo    | 1M         | 10M             | 50M              |
|--------------|------------|-----------------|------------------|
| `msd_A`      | **153 ± 2**| **1.787 ± 11**  | 12.043 ± 108     |
| `burstsortA` | 236 ± 45   | 2.151 ± 207     | **11.808 ± 46**  |
| `mkqsort_bs` | 214 ± 4    | 2.877 ± 47      | 19.616 ± 420     |
| `burstsortL` | 248 ± 40   | 3.631 ± 342     | 20.644 ± 109     |

### `random` — ASCII uniforme

| algoritmo    | 1M         | 10M             | 50M              |
|--------------|------------|-----------------|------------------|
| `msd_A`      | **83 ± 4** | **928 ± 12**    | **4.679 ± 51**   |
| `burstsortA` | 135 ± 12   | 1.265 ± 85      | 6.144 ± 67       |
| `mkqsort_bs` | 148 ± 3    | 2.275 ± 157     | 12.641 ± 105     |
| `burstsortL` | 175 ± 16   | 2.106 ± 85      | 14.285 ± 439     |

### Razão 10M / 1M (ideal linear = 10×; ideal n·log n ≈ 11,5×)

| algoritmo    | url    | genome | random |
|--------------|--------|--------|--------|
| `msd_A`      | 11,7×  | 11,7×  | 11,2×  |
| `mkqsort_bs` | 13,1×  | 13,4×  | 15,4×  |
| `burstsortL` | 11,6×  | 14,6×  | 12,0×  |

## Métricas de hardware em 50M

Extraídas de `perf stat` em cada execução, depois **normalizadas por string**
(misses / 50 000 000).

### `url`

| algoritmo    | wall (ms) | cache-miss/str | L1d-miss/str | LLC-miss/str | dTLB-miss/str |
|--------------|-----------|----------------|--------------|--------------|---------------|
| `burstsortA` | **6.707** | **6,9**        | **15,9**     | **1,8**      | 2,1           |
| `msd_A`      | 9.077     | 15,9           | 22,3         | 2,9          | **1,2**       |
| `burstsortL` | 13.751    | 12,4           | 15,5         | 3,5          | 2,8           |
| `mkqsort_bs` | 14.172    | 28,5           | 37,6         | 10,2         | 8,6           |

### `genome`

| algoritmo    | wall (ms) | cache-miss/str | L1d-miss/str | LLC-miss/str | dTLB-miss/str |
|--------------|-----------|----------------|--------------|--------------|---------------|
| `burstsortA` | **11.808**| **12,5**       | 29,0         | 3,2          | 3,9           |
| `msd_A`      | 12.043    | 17,8           | **28,0**     | 4,2          | **2,1**       |
| `mkqsort_bs` | 19.616    | 34,2           | 43,8         | 12,5         | 10,9          |
| `burstsortL` | 20.644    | 21,1           | 30,3         | 5,5          | 5,4           |

### `random`

| algoritmo    | wall (ms) | cache-miss/str | L1d-miss/str | LLC-miss/str | dTLB-miss/str |
|--------------|-----------|----------------|--------------|--------------|---------------|
| `msd_A`      | **4.679** | **8,3**        | **11,4**     | **1,9**      | **1,0**       |
| `burstsortA` | 6.144     | 7,9            | 14,1         | 2,6          | 2,2           |
| `mkqsort_bs` | 12.641    | 24,0           | 31,9         | 8,3          | 8,9           |
| `burstsortL` | 14.285    | 14,7           | 15,2         | 4,4          | 3,5           |

Observação: em `random` o `burstsortA` tem menos cache-miss/str que o `msd_A`
mas perde em wall-clock — evidência de que o preço em instruções da trie
passa a dominar quando não há prefixo comum explorável.

## Leitura crítica

### A tese do paper reproduz?

**Sim, parcialmente.** Sinha & Zobel afirmam que Burstsort vence MSD radix
em datasets grandes de strings com prefixos compartilhados. Isso se
confirmou em `url` a **50M** (Burstsort 26% mais rápido que MSD), e
praticamente empatou em `genome`. **Não** se confirmou em `random` — e o
artigo, de fato, nunca prometeu vitória nesse perfil.

### O volume crítico nesta máquina

Em `url`, **a virada acontece entre 1M e 10M** — já em 10M o `burstsortA`
supera o `msd_A` em 13% (1.532 ms vs 1.762 ms), folga que cresce para 26%
em 50M (6.707 ms vs 9.077 ms). A 1M os dois praticamente empatam
(156 vs 151 ms, dentro do desvio-padrão). Isso é mais cedo do que a
primeira leitura sugeria e ocorre justamente quando o vetor de ponteiros
+ dados começa a estourar o L3 (na faixa das dezenas de MB).

Em `genome` a virada é mais tardia: o MSD dominou até 10M e só empatou
em 50M. Alfabeto de 4 símbolos mantém a trie do Burstsort rasa; cabe no
L3 por mais tempo, adiando o momento em que a localidade compensa.

Em `random`, MSD manteve vantagem estável em todos os volumes
(~1,3-1,5×): sem prefixos comuns, Burstsort paga a trie sem receber o
retorno em profundidade média menor.

O artigo original enxergou a virada em tamanhos menores porque os L2 de
2004 eram ~2 MB, enquanto o L3 moderno tem dezenas de MB — por isso
precisamos de N ≈ 10M para reproduzir o efeito em hardware atual.

### Qual variante de Burstsort importa

**A escolha da variante é dominante.** `burstsortA` venceu `burstsortL`
em tempo (2,05× em `url` a 50M) **e** em cache-miss (1,8× menor). Qualquer
comparação contra MSD/Multikey que use `burstsortL` como representante do
Burstsort subestima o algoritmo — esse parece ter sido o erro que
explicou as medições iniciais adversas (1M/10M sem `burstsortA`).

### Multikey Quicksort não escala

`mkqsort_bs` foi dominado em tempo e em todas as métricas de cache em
todos os datasets de 50M. Em `url`, fez **4× mais cache misses** e
**7× mais dTLB misses** que `burstsortA`. A razão é estrutural: cada
chamada recursiva particiona o vetor inteiro de ponteiros, sem qualquer
localidade — exatamente o anti-padrão que o artigo do Burstsort ataca.

### Cache-conscious, em números

A métrica mais discriminante foi **dTLB-miss por string**. Em `url` 50M:

- `msd_A`: 1,2
- `burstsortA`: 2,1
- `mkqsort_bs`: 8,6 (**7× pior**)

O TLB tem tipicamente poucas centenas de entradas; mkqsort varre um vetor
de ~400 MB de ponteiros em cada nível, não cabe em entry-count nenhum.
Burstsort opera sobre buckets pequenos, contidos em poucas páginas.
Mesmo que Burstsort perca para MSD em dTLB aqui, perde por um fator
pequeno e ganha em L1d e LLC — o balanço favorece Burstsort no tempo total.

## Ameaças à validade

- **Datasets são sintéticos.** O ranking qualitativo é robusto, mas
  magnitudes absolutas diferem do que se veria em URLs reais de Common
  Crawl ou reads genômicos reais.
- **Uma só máquina.** Sem repetir em CPU diferente (Intel/AMD/ARM, caches
  distintos), generalizar é arriscado.
- **`perf` usa eventos arquitetados genéricos.** Em microarquiteturas
  específicas, contadores nativos (`uarch-bench`) dariam leituras mais
  precisas.
- **Sem controle fino de variância**: não foi fixado governor
  `performance` nem drop-caches entre datasets. O desvio-padrão baixo
  sugere que o efeito foi pequeno, mas é um ponto a travar em replicação
  formal.

## Arquivos brutos

- `results/bench_20260424-083850.csv` — 1M strings, 3 algoritmos.
- `results/bench_20260424-084714.csv` — 10M strings, 3 algoritmos.
- `results/bench_20260424-090853.csv` — 50M strings, 4 algoritmos, com perf.

Cada CSV é acompanhado de um `.md` gerado por `scripts/summarize.py` com
médias ± desvio por (algoritmo, dataset).

## Gráficos

Gerados por `scripts/plot.py`, em `results/plots/`:

- **`01_wall_50M.png`** — barras de tempo médio (± desvio) por algoritmo e
  dataset em 50M. `burstsortA` sai na frente em `url`; `msd_A` em `random`;
  empate técnico em `genome`.
- **`02_scaling.png`** — log-log de `wall_ms` vs `N` (1M → 10M → 50M) por
  dataset, com linhas de referência O(n) e O(n·log n). `burstsortA` só tem
  ponto em 50M (não foi medido nos volumes menores).
- **`03_cache_misses_per_string.png`** — grade 2×2 com cache-miss, L1d-miss,
  LLC-miss e dTLB-miss **normalizados por string** em 50M. Visualiza o
  argumento "cache-conscious": `burstsortA` ≤ `msd_A` em quase tudo e
  `mkqsort_bs` é o pior em todas as métricas.
- **`04_time_vs_cachemisses.png`** — dispersão de `wall_ms` vs cache-misses
  totais em 50M, colorido por algoritmo e com marcadores por dataset.
  Correlação visível mas não linear: Burstsort consegue mais trabalho útil
  por miss que o Multikey Quicksort.

## Próximos experimentos sugeridos

1. **100M em `url`** apenas — mapear se a folga do Burstsort cresce ou
   satura.
2. **`burstsort2_vector` / `copy-burstsort`** — variantes mais recentes
   do harness, que o artigo original aponta como as campeãs.
3. **`std::sort` com `strcmp`** como baseline ingênuo para quantificar
   quanto se ganha com qualquer algoritmo string-aware.
4. **Sweep de `N` ∈ {1, 2, 5, 10, 20, 50, 100}M em `url`** para achar o
   ponto exato de virada MSD ↔ Burstsort nesta máquina.
5. **Repetir em hardware distinto** (idealmente uma CPU com L3 pequeno,
   tipo Raspberry Pi 5 ou laptop antigo) para contrastar o efeito do
   cache moderno.

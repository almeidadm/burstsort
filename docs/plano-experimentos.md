# Plano de Experimentos

Este documento descreve a metodologia usada para comparar implementações dos
três métodos de ordenação de strings estudados no trabalho de Sinha & Zobel
(*Cache-Conscious Sorting of Large Sets of Strings with Dynamic Tries*,
ACM JEA, 2004).

## 1. Objetivo

Reproduzir, em hardware atual, o núcleo da comparação experimental do artigo:
verificar se **Burstsort** mantém vantagem sobre **MSD Radix Sort** e
**Multikey Quicksort** quando o fator limitante é a hierarquia de memória.

## 2. Algoritmos avaliados

Todos saem do harness `rantala/string-sorting` (C/C++, mesmo binário, mesmo
compilador, mesmas flags → comparação justa). Seleção canônica em
`scripts/algorithms.txt`:

| id no harness | algoritmo                      | origem                                |
|---------------|--------------------------------|---------------------------------------|
| `burstsortL`  | Burstsort list-based           | Sinha & Zobel (referência do artigo)  |
| `msd_A`       | MSD Radix Sort array-based     | Rantala, 2007 (reimplementação limpa) |
| `mkqsort_bs`  | Multikey Quicksort             | Bentley & Sedgewick, 1997 (original)  |

Variantes adicionais (Burstsort com amostragem, MSD adaptativo, Multikey com
cache de chave) estão comentadas no mesmo arquivo para experimentos de
sensibilidade.

## 3. Datasets

Gerados por `scripts/fetch_datasets.sh`. Três perfis reproduzem o espectro
testado no artigo:

- **url** — grande compartilhamento de prefixos; favorece estruturas trie.
- **genome** — alfabeto pequeno (4 símbolos) e strings longas; profundidade alta.
- **random** — ASCII uniforme; caso médio, poucos prefixos comuns.

Parâmetro default: **1 000 000 strings/arquivo** (ajustável via
`N_STRINGS`). Em máquinas com RAM sobrando, subir para 5–10 M aproxima do
regime "cache-stressed" original (300 MB).

## 4. Métricas

Coletadas com `perf stat` por execução:

- **wall_ms**, **task-clock** — tempo de CPU.
- **instructions**, **cycles**, **IPC** (derivado).
- **cache-references / cache-misses** — visão agregada.
- **L1-dcache-load-misses**, **LLC-load-misses** — hierarquia de cache.
- **dTLB-load-misses** — pressão em TLB (chave do argumento "cache-conscious").

## 5. Protocolo

1. `scripts/build.sh` — compila em Release (`-O3 -march=native`, OpenMP, libc rt).
2. `scripts/fetch_datasets.sh` — gera/recupera entradas em `datasets/`.
3. `scripts/run_benchmark.sh` — executa `REPS=5` repetições por (algoritmo,
   dataset), embrulhando cada invocação em `perf stat` com os eventos acima.
4. `scripts/summarize.py results/bench_*.csv` — agrega por média ± desvio e
   emite tabela markdown.

### Controles para reduzir variância

- Build único por bateria (mesmo binário para todos os algoritmos).
- `sortstring --check` pode ser ativado pontualmente para validar que a saída
  está ordenada, mas é desabilitado no benchmark para não contaminar o tempo.
- Recomendado antes da bateria final:
  ```bash
  sudo cpupower frequency-set -g performance
  echo 3 | sudo tee /proc/sys/vm/drop_caches      # antes de cada dataset novo
  ```
- `--hugetlb-text --hugetlb-ptrs` do `sortstring` permite isolar o efeito de
  TLB: rodar uma bateria com e outra sem para medir o ganho de páginas grandes.

## 6. Análise

Para cada dataset, olhar:

1. **Tempo relativo** (ms) — ranking bruto.
2. **Cache-miss por string ordenada** (`cache_misses / N`) — normaliza por
   tamanho do dataset; deve separar Burstsort dos demais.
3. **IPC** — IPC baixo com muitas misses confirma que o gargalo é memória.
4. **dTLB misses** — justificativa teórica de Burstsort: buckets cabem em
   poucas páginas; MSD radix e Multikey fazem acesso aleatório ao vetor de
   ponteiros inteiro.

## 7. Ameaças à validade

- Datasets sintéticos ≠ os originais do artigo; o ranking pode ser estável
  mas as magnitudes absolutas diferem.
- `perf` em contadores de cache depende da arquitetura — validar com
  `perf list` que os eventos escolhidos existem no host.
- CPUs modernas têm caches maiores e prefetchers mais agressivos que as de
  2004; a vantagem de Burstsort deve encolher em números absolutos.
- Uma única máquina: cuidado ao generalizar. Idealmente repetir em hardware
  distinto (Intel/AMD, ARM).

## 8. Próximos passos sugeridos

- [ ] Adicionar um dataset real (ex.: subset de URLs do Common Crawl).
- [ ] Varredura de tamanho: N ∈ {10^5, 10^6, 10^7} para curva de escalabilidade.
- [ ] Incluir `std::sort` com comparação lexicográfica como baseline "ingênuo".
- [ ] Reproduzir com `bingmann/parallel-string-sorting` para confronto cruzado
      das mesmas variantes.

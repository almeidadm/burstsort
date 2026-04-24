# Algoritmos no harness `rantala/string-sorting`

O binário `sortstring` registra **128 variantes**. Abaixo, as famílias
relevantes para este trabalho e por que escolhemos as três representantes.

## Burstsort

Em `src/burstsort.cpp`, `src/burstsort2.cpp`, `src/burstsort_mkq.cpp` (Rantala)
e `external/burstsortL.c`, `external/burstsortA.c` (Sinha & Zobel, originais).

- **`burstsortL`** — versão *list-based* original. **Escolhida** porque é
  exatamente o código usado no artigo.
- `burstsortA` — variante *array-based* do mesmo par de autores.
- `burstsort_vector`, `burstsort_brodnik`, `burstsort_bagwell`,
  `burstsort_vector_block` — reimplementações de Rantala variando a estrutura
  do bucket.
- `burstsort_sampling_*` — Burstsort com amostragem (Sinha & Zobel, 2005).
- `burstsort_superalphabet_*` — alfabeto estendido (processa mais de 1 byte
  por nível da trie).
- `burstsort2_*` — segunda geração de Rantala.
- `burstsort_mkq_*` — burst + multikey quicksort para ordenar buckets
  pequenos.

## MSD Radix Sort

Em `src/msd_a.cpp`, `msd_ce.cpp`, `msd_ci.cpp`, `msd_dyn_*.cpp`, `msd_lsd.cpp`
e `external/msd.c` (McIlroy, Bostic, McIlroy).

- **`msd_A`** — implementação *array-based* de Rantala. **Escolhida**
  como baseline MSD "bem-implementado sem viés pró-cache".
- `msd_A_adaptive` — troca para insertion sort em subarrays pequenos.
- `msd_CE0..CE8` — variantes *cache-efficient* (nível crescente de otimização).
- `msd_ci` — *cache-inefficient* proposital; útil como baseline ruim.
- `msd_DB` — *dynamic block* (layout orientado a bloco).
- `msd_A_lsd4..12` — híbrido MSD→LSD em determinado nível.
- `msd_nilsson` — MSD adaptativo de Nilsson.

## Multikey Quicksort

Em `src/multikey_block.cpp`, `multikey_cache.cpp`, `multikey_dynamic.cpp`,
`multikey_multipivot.cpp`, `multikey_simd.cpp` e `external/multikey.c`,
`external/mkqsort.c` (Bentley & Sedgewick).

- **`mkqsort_bs`** — Bentley & Sedgewick original (1997). **Escolhida** por
  ser o código de referência reproduzido em livros.
- `multikey_block1/2/4` — versão "em bloco" de Rantala.
- `multikey_cache4/8` — caches de 4 ou 8 bytes da chave de pivô.
- `multikey_dynamic_*` — estruturas dinâmicas para pivôs.
- `multikey_multipivot` — múltiplos pivôs por particionamento.
- `multikey_simd` — paralelização SIMD do laço de comparação.

## Listar tudo no host

```bash
build/sortstring -A           # nome + descrição
build/sortstring -L           # só nomes (1 por linha)
```

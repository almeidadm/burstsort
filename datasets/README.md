# Datasets

Formato esperado pelo `sortstring`: arquivo de texto puro com uma string por
linha (delimitador `\n`; byte `NUL` também é aceito via `--raw`).

## Gerando dados sintéticos

```bash
scripts/fetch_datasets.sh                 # 1.000.000 strings por arquivo
N_STRINGS=5000000 scripts/fetch_datasets.sh
```

Gera três arquivos cujo perfil estatístico espelha os datasets usados por
Sinha & Zobel (2004):

| arquivo       | perfil                                                             |
|---------------|--------------------------------------------------------------------|
| `url.txt`     | URLs sintéticas — prefixos muito repetidos, bom para trie/burst    |
| `genome.txt`  | alfabeto ACGT, strings longas — estressa profundidade de radix     |
| `random.txt`  | ASCII aleatório — distribuição uniforme, caso médio                |

## Usando dados reais

Basta soltar arquivos `.txt` neste diretório. Os datasets clássicos de
Sinha & Zobel (`url`, `genome`, `random`, `set5_large`, `set6_large`) não têm
mais hospedagem pública estável; alternativas:

- **URLs**: Common Crawl (cc-index) ou corpus OpenWebText.
- **Genoma**: reads do SRA (NCBI) ou coleções k-mer do Jellyfish.
- **Palavras naturais**: Project Gutenberg, Wikipedia dumps.

Este diretório é ignorado pelo git (ver `.gitignore`).

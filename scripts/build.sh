#!/usr/bin/env bash
# Configura e compila o harness do rantala/string-sorting em modo Release.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD_DIR="$REPO_ROOT/build"
SRC_DIR="$REPO_ROOT/upstream"

if [ ! -d "$SRC_DIR" ]; then
    echo "upstream/ não encontrado — rode: git clone https://github.com/rantala/string-sorting.git upstream" >&2
    exit 1
fi

mkdir -p "$BUILD_DIR"
cmake -S "$SRC_DIR" -B "$BUILD_DIR" -DCMAKE_BUILD_TYPE=Release
cmake --build "$BUILD_DIR" -j"$(nproc)"

echo
echo "Binário: $BUILD_DIR/sortstring"
echo "Para listar algoritmos disponíveis: $BUILD_DIR/sortstring -L"

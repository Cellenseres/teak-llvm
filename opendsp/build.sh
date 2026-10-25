#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")/.." && pwd)
cmake -S "$ROOT/llvm" -B "$ROOT/build" -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLVM_TARGETS_TO_BUILD="" -DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=Teak \
    -DLLVM_ENABLE_PROJECTS="clang;lld" \
    -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
    -DCMAKE_CXX_FLAGS="-include cstdint -include limits -Wno-everything" \
    -DLLVM_INCLUDE_TESTS=OFF -DLLVM_INCLUDE_BENCHMARKS=OFF \
    -DLLVM_INCLUDE_EXAMPLES=OFF -DLLVM_PARALLEL_LINK_JOBS=1
ninja -C "$ROOT/build" -j "${BUILD_JOBS:-2}" clang lld llc llvm-readelf FileCheck

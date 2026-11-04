#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
TOOLS=${TEAK_TOOLS:-"$ROOT/build/bin"}
OUTPUT=${TEAK_RUNTIME_OUTPUT:-"$ROOT/build/lib/teak"}
mkdir -p "$OUTPUT"
"$TOOLS/clang" --target=teak -O2 -ffreestanding -ffunction-sections \
    -integrated-as -c "$ROOT/opendsp/runtime/divide.ll" -o "$OUTPUT/divide.o"
"$TOOLS/clang" --target=teak -integrated-as \
    -c "$ROOT/opendsp/runtime/quotient.s" -o "$OUTPUT/quotient.o"
"$TOOLS/clang" --target=teak -integrated-as \
    -c "$ROOT/opendsp/runtime/indirect.s" -o "$OUTPUT/indirect.o"
"$TOOLS/clang" --target=teak -O2 -ffreestanding -ffunction-sections \
    -integrated-as -c "$ROOT/opendsp/runtime/multiply.ll" -o "$OUTPUT/multiply.o"
"$TOOLS/clang" --target=teak -integrated-as \
    -c "$ROOT/opendsp/runtime/products.s" -o "$OUTPUT/products.o"
"$TOOLS/clang" --target=teak -integrated-as \
    -c "$ROOT/opendsp/runtime/program.s" -o "$OUTPUT/program.o"
"$TOOLS/llvm-ar" rcs "$OUTPUT/libteak_rt.a" "$OUTPUT/divide.o" "$OUTPUT/quotient.o" "$OUTPUT/indirect.o" \
    "$OUTPUT/multiply.o" "$OUTPUT/products.o" "$OUTPUT/program.o"

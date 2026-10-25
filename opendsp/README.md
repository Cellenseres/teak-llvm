# OpenDSP compiler branch

This branch starts at Gericom's `bda74e1c0e3e6f04ae08fc5356fb4208aebb0f9e`.
OpenDSP's former build-time patches are ordinary commits here:

| Commit | Existing change |
| --- | --- |
| `5786a258b7a` | Word offsets in constant GEPs and SCEV struct indexing |
| `9fa01a503d8` | Word offsets for inline memory operations |
| `3c86b20fb93` | 16-bit Clang data pointers |
| `f9afa50c4b3` | R7 offset addressing hazard |

New fixes follow those commits. This is still an experimental Teak compiler,
not a claim of complete C support or working Vorbis/Opus DSP playback.

## Incorrect condition reuse

The old backend can emit `cmp; clr a0, lt; ret lt`. CLR changes ICC, so the RET
tests the flags from CLR. For example, a comparison can return true for both
`a < b` and `a >= b`. The new predicate callback reports flag definitions to
LLVM. A conservative profitability check also rejects if-conversion of blocks
that modify ICC, including the duplicated-tail cases that still pass LLVM 11's
predicate analysis. Ordinary branches preserve the comparison's meaning.

The executable regressions cover signed/unsigned boundary comparisons, min/max,
register pressure, unmodified Opus insertion sort and eight upstream SILK NLSF
vectors. The references use Python arithmetic or the same upstream C compiled
for the host. Teak instructions execute in the pinned Teakra emulator. ELF data
is loaded explicitly; host arithmetic does not supply intermediate DSP results.

Locally the fixed backend passes 495 simple comparison results, 333 combined
results, and all 128 NLSF coefficients. The previous backend fails 144 simple
results, 30 combined results, and 59 NLSF coefficients in the original OpenDSP
harness. Passing these tests does not prove full compiler correctness or a
hardware playback deadline.

## Build and test

On Ubuntu 24.04, install git, clang, lld, cmake, ninja-build, Python 3 and g++:

```sh
sh opendsp/build.sh
build/bin/llc -mtriple=teak -O2 -asm-verbose=false llvm/test/CodeGen/Teak/predicate-flags.ll -o - |
  build/bin/FileCheck llvm/test/CodeGen/Teak/predicate-flags.ll
```

The build uses LLVM 11's existing C++ include compatibility flags on modern
hosts. No patch is applied during configuration. OpenDSP must pin a full commit
SHA, rather than build the moving branch head.

For executable tests, build Teakra commit
`3d697a18df504f4677b65129d9ab14c7c597e3eb` into its `b/` directory and check out
Opus `22244de5a79bd1d6d623c32e72bf1954b56235be`. Set `TEAKRA`, `OPUS_SOURCE`,
`TEAK_CC` and `TEAK_LD` to their absolute paths, then run:

```sh
python3 opendsp/tests/run.py --case simple
python3 opendsp/tests/run.py --case comparisons
python3 opendsp/tests/run.py --case sort
python3 opendsp/tests/run.py --case nlsf
```

Test declaration shims are not a DSP C runtime. Generated files remain under
`opendsp/tests/build/`. The CI workflow builds from a clean checkout and executes
these checks with pinned source dependencies. Physical 3DS validation remains
necessary for firmware changes.

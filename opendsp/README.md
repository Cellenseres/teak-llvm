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

Leading-zero counts now use bounded binary search for 16-bit and 40-bit
registers. Promoted 32-bit values use the same lowering. The native `clz` test
covers zero, powers of two, nearby values and deterministic random inputs.
No runtime helper or multiplier state is required.

Wide multiplication uses six signed 15-bit partial products. The native test
checks 1,752 result words across 16-, 32- and 40-bit boundary/random inputs.
Accumulator spills now preserve all 40 bits, including the extension byte.
Keeping the old spills produces 160 wrong words with the same unsaturated
startup. Narrowed loads are disabled because their byte offsets address the
wrong DSP word. The upstream energy, bandwidth-expansion and linear-log tests
then match all 293 host-reference words; previously seven shift values differed.

The standalone C tests disable both arithmetic and move saturation in MOD0.
With move saturation enabled, intermediate values above signed 32-bit range
are clamped during transfers. This is a required execution mode for these wide
integer tests, not a change to OpenDSP's firmware startup. Multiplier tests run
with interrupts masked. A production decoder must protect P0/Y0 and restore
the caller's arithmetic mode while sharing the DSP with the renderer.

Local addresses now reference the lowest word of each frame object. Ordinary
memory instructions access locals in the same word order as globals; compiler
spills retain their private format. Frame-index analysis no longer treats byte
alignment as word alignment. The `stack` regression checks 747 words covering
scalar addresses, arrays, full 32-bit updates and neighboring volatile guards.
Bulk initialization and byte-memory intrinsics remain separate compiler gaps.
`--case bulk` reproduces the failing automatic array initializer and is
excluded from the passing CI suite.

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
python3 opendsp/tests/run.py --case clz
python3 opendsp/tests/run.py --case multiply
python3 opendsp/tests/run.py --case silk_math
python3 opendsp/tests/run.py --case stack
```

Test declaration shims are not a DSP C runtime. Generated files remain under
`opendsp/tests/build/`. The CI workflow builds from a clean checkout and executes
these checks with pinned source dependencies. Physical 3DS validation remains
necessary for firmware changes.

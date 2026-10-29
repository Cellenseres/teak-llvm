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

The general wide-multiplication fallback uses six signed 15-bit partial
products. The native test checks 2,628 result words across 16-, 32- and 40-bit
boundary/random inputs, including signed 16-by-40-bit products.
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
Aligned, even-sized memory intrinsics use native words. The `bulk` regression
checks 163 words covering automatic initialization, copying, filling, overlap
in both directions and neighboring guards. Unaligned 32-bit accesses and
64-bit memory transfers also use explicit word addresses. General 64-bit
arithmetic and packed byte-memory operations remain separate requirements.

The missing `i40` to IR-type conversion is repaired. A clean Clang build exposed
this when its SLP cost analysis visited the native CLZ IR test; the split local
frontend/llc path did not run that optimizer. CI continues testing the full
Clang path, and retains compiler binaries after a successful build even when
a later regression fails.

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
python3 opendsp/tests/run.py --case bulk
```

Test declaration shims are not a DSP C runtime. Generated files remain under
`opendsp/tests/build/`. The CI workflow builds from a clean checkout and executes
these checks with pinned source dependencies. Physical 3DS validation remains
necessary for firmware changes.


Constant data pointers now use `R_TEAK_16` relocations with word-addressed
addends. The `table_words` regression checks 23 words, including array and
structure offsets, writes, negative alias offsets and internal symbols. The
Clang constant emitter also accounts for the allocation stride when applying byte offsets;
the `pointers` C regression checks that path in a complete frontend build.
Its clean CI result remains pending. The split local frontend predates this
constant-emission fix and fails that C case as expected.

The `fft_math` regression checks 780 words from the unchanged Opus Q15/Q16
multiplication macros against integer references. Those checks pass locally;
they do not establish correctness of the complete decoder.


Data-pointer relocations also normalize expression offsets before combining
them with section-relative symbol offsets. The previous assembler fix divided
internal offsets twice, making the FFT state point inside its bit-reversal
table. The original 60-point FFT then differed in 503 of 1,200 result words.

The unmodified upstream forward FFT is checked at 60, 120, 240 and 480 points,
with five deterministic real/complex input patterns per size. The test uses
Opus's original mode tables and compares every 32-bit component to the host.
All 20 local cases pass 18,000 result words. Including the earlier groups,
23,520 words pass. See `opendsp/validation/fft-20261025.json`. The clean Clang
CI result remains pending. Emulator Run(1) counts
are instruction-step observations, not physical cycle or real-time guarantees.


Proven signed 16-bit operands use one native multiply when both factors fit,
two partial products for an unsigned 16-bit partner, or three for a wider
partner. Other operands retain the full fallback. The same 480-point complex
FFT drops from 1,849,963 to 764,698 emulator steps with identical output.
The Q15/Q16 macro group drops from 77,371 to 13,996 steps.

All groups, including the enlarged multiplication vectors and 20 FFT cases,
pass 24,396 words. `opendsp/validation/narrow-products-20261025.json` records
the results. The existing firmware rebuild remains byte-identical and both
multiplier scans pass. These measurements do not change the production
requirements for interrupt-safe multiplier use and arithmetic-mode handling.


Clean Linux Clang commit `d1d5da89fe3bb62285bcfce9d628e5183f80edd7` passes
all nine original groups after the IR fixture command explicitly selects the
Teak integrated assembler. The enlarged multiplication vectors bring that run
to 5,593 words. Its initial CI failure was a host-assembler invocation after
successful IR optimization, not another i40 crash. This baseline predates the
later pointer and multiplication changes; their clean CI results are separate.
See `opendsp/validation/clean-clang-20261025.json`.

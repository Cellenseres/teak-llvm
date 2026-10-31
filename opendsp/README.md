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
The clean c8fa267 compiler passes that C case locally. The older split
frontend predates this constant-emission fix and fails it as expected.

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


Arguments beyond the four scalar registers now use the stack. A 16-bit value
uses one word; a promoted 32-bit or native 40-bit value uses three, with the
most significant word first. The DSP pre-decrements SP. Outgoing arguments
start at SP, followed below by two return-address words and the saved frame
pointer. Outgoing stack space is released after each call. Fixed incoming slots
also establish a frame pointer in functions without local variables.

The `calls` regression checks 639 words across mixed scalar types, nested
calls, local guards and complete 40-bit arguments/results. It passes at O1
and O2. The unchanged SILK interpolation unit adds 335 host comparisons across
all Q2 factors and LPC lengths up to 16, including neighboring guards. All
current groups pass 25,387 words, excluding duplicate O1 checks. See
`opendsp/validation/stack-arguments-20261025.json`. Variadic calls and aggregate
argument rules are not covered. `TEAK_TEST_BUILD` selects a separate output
directory for compiler comparisons.

The clean Linux compiler at c8fa267 also passes all 20 forward-FFT cases and
both pointer groups directly: 18,040 words. This verifies the original FFT and
frontend fixes outside the split build. See `opendsp/validation/clean-fft-20261025.json`.
The workflow at that revision failed on its old assembler command; the local
rerun explicitly selects the integrated assembler. Newer arithmetic and stack
changes retain separate validation.

The complete clean build at `4c485020ce03583ce30be47461508c6ea45850fc`
also passes its CI regression suite: 32 cases and 24,413 result words.
See `opendsp/validation/clean-ci-20261025.json`.

Indexed word accesses now require an actual i16 result or stored value.
Extending loads use ordinary addressing, since the indexed instruction patterns
do not implement them. This allows the complete upstream Opus MDCT unit to
compile. Fifteen standalone groups and two backward-MDCT cases pass 9,943
words locally. See `opendsp/validation/indexed-words-20261025.json`.

The MDCT harness compares original Opus code and mode tables against a host
reference. It covers windowing, retained overlap, input strides, buffer guards,
silence and scaling boundaries. Separate cases run one or two blocks. The full
matrix has its own evidence; successful compilation alone is insufficient.

All 100 MDCT cases pass 80,720 result words. They cover every original Opus
block size from 120 to 960 samples, valid strides through eight, eight input
patterns over two blocks, and separate single-block checks. Silence, near-zero
values and large coefficients exercise scaling. See
`opendsp/validation/mdct-20261025.json`. This validates the inverse transform,
not packet decoding or physical playback.

High products now support both signed and unsigned 40-bit operands. Ten-bit
digits keep each native multiplier input positive and preserve the full carry.
Constants beyond 32 bits retain their upper byte; previously the immediate
patterns silently dropped it. That affected signed division and comparisons.

The new group passes 3,834 words, including 110 complete constants, boundary
products and division by five. All current standalone groups, 20 FFT cases
and four additional MDCT cases pass 33,473 words. See
`opendsp/validation/high-products-20261025.json`. General i80 arithmetic is not
supported; the product tests use LLVM fixed-point intrinsics.

Function pointers use program address space one, with a 32-bit representation
and alignment. `R_TEAK_32` stores program addresses as two words. Program
constants use a data constant pool, retaining addresses above 64K words.

Indirect calls pass the destination in R0/R1 and call `__teak_indirect_call`.
Link `opendsp/runtime/indirect.s` and use CPC zero. The entry pushes the target
and returns into it, preserving all four argument registers and stack slots.

The callback group passes 216 words at O1 and O2. It covers two far functions,
including an internal symbol with a section offset, tables, records, returned
pointers, six arguments and nested calls. The complete locally rebuilt frontend
and backend pass 33,689 words across 41 O2 cases. The existing firmware builds
to 246,672 bytes, including the call entry; both multiplier scans pass. This is
an isolated candidate, not a replacement for the production prebuilt. See
`opendsp/validation/program-pointers-20261025.json`. A clean complete compiler
rebuild and physical playback validation remain separate requirements.

Published main stops at `f9afa50c4b359aba51be2750fcd605a857535759`, containing
only the four compiler patches shipped with OpenDSP v1.2.2. Newer compiler
work remains local until publication is approved.

Byte loads and stores use complete words, with explicit eight-bit masking and
sign extension. Constant byte arrays retain their allocated stride. String
sections use physical element widths, so the linker preserves padded strings.
Pointer scaling now precedes truncation, including offsets beyond 32 KiB.

All 42 compiler cases pass 35,517 result words. The existing firmware remains
byte-identical to the 246,672-byte candidate above; both multiplier scans pass.
See `opendsp/validation/byte-storage-20261025.json`.

The original full-accuracy Tremor inverse transform passes 40 cases and 163,360
words. Every supported size from 64 to 8192 is checked with silence, impulses,
alternating coefficients, mixed coefficients and small values. Buffer guards
also match. Scalar word order is big-endian; the host uses its native order.
The largest observed run takes 25,489,586 emulator steps. These are neither
physical cycle counts nor a playback benchmark. See
`opendsp/validation/vorbis-mdct-20261025.json`.

Full packet decoding remains incomplete. Byte-containing C records still
require a consistent layout. Dynamic scratch, general division and decoder
scheduling remain separate work. The locally rebuilt compiler is not a clean
complete build, and no physical New 3DS validation is claimed.

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

## Stack loads with live flags

Signed 16-bit stack loads into A0 or A1 now restore saved STT0. Previously,
the status word stayed on the stack, and RET consumed an invalid address.
The native MIR regression covers all four accumulators, short and long frame
offsets, both branch outcomes, arithmetic modes and dead-flag controls.
All 768 cases and 6,144 words match; the same MIR aborts with the old backend.
Run `python3 opendsp/tests/stack_flags.py` with the usual toolchain environment.
Set `TEAK_LLC` to the matching llc binary. Physical behavior remains untested.

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

General signed and unsigned division use the 40-bit runtime. Normalization
aligns the divisor and skips unnecessary iterations. Link
`build/lib/teak/libteak_rt.a` after application objects. `opendsp/build.sh`
builds that library; `opendsp/runtime/build.sh` also runs separately.
The library includes the indirect-call entry.

Full-width comparisons split the high byte and lower 32 bits. This avoids
overflow in the DSP's signed subtraction flags. Division checks cover 16,
32 and 40 bits, including negative operands and boundary values. All 3,588
words match; normalization reduces the same run from 43,464,836 to 8,705,034
emulator steps. Archive linking produces identical results.

The original Opus range decoder passes 6,664 reference words across 32 packet
contexts. Checks cover front and reverse byte reads, interval updates, inverse
CDF tables, raw bits, bounded integers, bit counts, internal state and guards.
This is entropy-decoder validation, not full Opus packet reconstruction.

The complete division candidate passes 44 cases and 45,769 words. Existing
firmware stays byte-identical, with both multiplier scans passing. See
`opendsp/validation/division-20261025.json`. A subsequent byte-swap promotion
fix avoids invalid 40-bit BSWAP nodes and passes another 202 words, recorded
separately in `opendsp/validation/byte-order-20261025.json`.

Variable stack allocations preserve word addressing and requested alignment.
Stack save and restore use SP, and the epilogue restores the fixed frame before
popping saved registers. Instruction selection also preserves machine nodes
already emitted during lowering.

Dynamic-buffer tests pass 140 words at O1 and O2. They cover multiple
allocations, eight-byte alignment, scoped VLAs, guards and six-argument calls.
The related O2 call, stack and memory checks bring this run to 1,905 words.
See `opendsp/validation/dynamic-stack-20261025.json`. Allocation limits for a
production decoder remain separate from compiler support.

Teak reports a maximum pointer width of 32 bits while retaining 16-bit data
pointers. This keeps Clang's cached size types consistent with size_t and
program pointers. VLA pointer arithmetic casts the element count to the index
type before scaling. The dedicated group checks 180 words, including large
variable sizes, indexing, pointer advancement and both pointer representations.

The locally rebuilt frontend and backend pass 47 cases and 46,291 words, plus
the 16,388-word largest Vorbis-transform case. Seventeen of 23 decoder units
compile, including Vorbis sharedbook. The firmware builds to 246,696 bytes,
with 194,942 text bytes; both multiplier scans pass. Its SHA-256 is
`6bf212400f345d7b51d0fe95cf2469124330d47bc46e42855bf085cc95f8660a`.
See `opendsp/validation/size-types-20261025.json`. The production prebuilt and
compiler publication baseline remain unchanged.

Expanded integers retain their actual upper-bit width when shifting, comparing
and extending. An 80-bit intermediate splits into two native 40-bit values.
Extending loads preserve the original memory access before extension, avoiding
five-byte fragments on word-addressed memory. The granule group checks 1,716
words at O1 and O2, including signed loads and returns. All 48 O2 groups pass
48,007 words. Vorbis block processing now compiles. See
`opendsp/validation/granules-20261025.json`.

Variadic functions pass every argument on the stack, including fixed arguments.
Native 16-bit arguments occupy one word; 40-bit parts occupy three words.
Argument lists support copying and independent traversal. Tests cover direct
and indirect calls, mixed pointers and integers, and 64-bit values. Both
optimization levels pass 272 words; related checks bring this run to 4,165
words. Opus main and CELT decoder units now compile, bringing the probe to
20 of 23 units. Byte-containing records still block SILK and Ogg framing.
See `opendsp/validation/varargs-20261025.json`. Full packet decoding and physical
playback remain unverified.

The optional `silk_core` group requires an Opus source tree supporting
`OPUS_WORD_STORAGE`. Native signed-byte fields use 16-bit storage; the host
reference retains ordinary eight-bit fields. The original SILK synthesis and
LPC filter units pass 1,888 output, guard and state words across eight frames.
Cases cover 8, 12 and 16 kHz, voiced and unvoiced excitation, and both LPC
orders. Dynamic scratch uses VLAs. This validates synthesis rather than full
packet reconstruction. See `opendsp/validation/silk-core-20261025.json`.

High products now use three 15-bit digits and nine native partial products,
replacing sixteen ten-bit products. Seven related groups pass 31,382 words.
The full-width product group drops from 1,294,334 to 929,960 emulator steps.
The largest mixed Vorbis transform drops from 25,597,722 to 16,632,881 steps;
its object shrinks from 247,964 to 161,456 bytes. SILK synthesis increases
slightly from 10,359,579 to 10,395,563 steps, so this is not a uniform speedup.
These figures measure emulator work and object size, not physical deadlines
or complete firmware fit. See `opendsp/validation/wide-digits-20261025.json`.

`-mllvm -teak-outline-products` enables shared wide-product functions. It is
disabled by default. Link the rebuilt runtime archive when using the option.
The native functions preserve MOD0, MOD3 and their saved registers, masking
interrupts while product registers are live. The standard calling environment
still applies to compiled code around those functions.

The boundary group passes 3,060 words, including 360 calls with both interrupt
states and altered product modes. Values and restored modes match. Interrupt
injection has not been tested. Archive linking passes another 3,834 words.
The default high-product code remains byte-identical to the preceding compiler.
See `opendsp/validation/product-runtime-20261025.json`. This option remains an
experiment; it does not yet make the full Opus decoder fit program RAM.

## Program memory reads

Address-space 1 loads now use full program addresses. The runtime provides
`__teak_program_read16` and `__teak_program_read32`; padded eight-bit loads
use the word helper with the required mask or sign extension. MOVP reads
through A0, independently of PCMHI. The opcodes 0x0d40 and 0x0d41 target
R0 and R1. No interrupt mask or product register is needed.

Place constant tables in a program section and link the rebuilt runtime:

```c
typedef const long __attribute__((address_space(1))) program_value;
static program_value coefficients[]
    __attribute__((section(".teak_program_data"))) = {0x12345678L};
```

Include `.teak_program_data` in a program-memory PT_LOAD segment, before
switching the location counter to X data. Program addresses are word-based,
as function addresses are. Mutable program globals and atomic accesses are
outside this interface; program-memory stores are rejected.

`python3 opendsp/tests/program_memory.py` checks constants, variable indices,
structure fields, signed and unsigned conversions, and addresses crossing
64 Kiwords. All four PCMHI settings produce the same 138 expected words;
the register is also retained. Runtime archive linking and rejection of a
program-memory store are checked. Set `TEAK_AR` when llvm-ar is not on PATH.
These are emulator checks with locally rebuilt components, not hardware
timing or a clean toolchain build.

The recorded run passes 552 program-table words and the existing 48 groups,
48,007 words. The full banked Opus decoder object is byte-identical with
this backend. See `opendsp/validation/program-memory-20261026.json`.

## Byte-array constants

Teak stores each eight-bit array element in a separate 16-bit word. Clang
now emits aggregate initializers with that storage width. Previously,
optimizing `{255, 255}` into one 32-bit store produced `0xff00ff00`.
Byte loads then read two zeroes. The corrected store is `0x00ff00ff`.
This fixes the silence packet used during an Opus Hybrid-to-SILK transition.

The native `byte_constants` test covers local and global arrays, signed
payloads, nested arrays, zero initialization and trailing zero fillers.
It checks 136 words at both `-O2` and `-Oz`. See
`opendsp/validation/byte-constants-20261026.json`.

String constants now use the same word storage. Previously, initializing
an automatic string array could copy only half its physical storage or
leave characters zeroed. `byte_strings` checks 107 words at both `-O2`
and `-Oz`, covering empty strings, odd lengths, embedded zeroes, high
bytes, padding and direct literals. The byte-memory and aggregate tests
also pass. See `opendsp/validation/byte-strings-20261026.json`.

## Division runtime

Signed and unsigned division retain their existing entry points. Their
shared `__teak_divmod40` helper now uses a native shift/subtract loop in
`opendsp/runtime/quotient.s`. It handles all 40 bits, returns early for a
smaller numerator and preserves MOD0, R0 and R1. It leaves interrupts enabled
when they were enabled on entry. Rebuild the runtime archive when updating.

`division_vectors` checks 975 pairs against independent integer results.
All 11,700 quotient/remainder words match, including signed extrema and
divisors near powers of two. The same inputs decrease from 12,654,981 to
3,325,551 emulator instructions, about 74 percent. `division` also passes
3,588 words at `-Oz`; the existing 48 groups pass 48,007 words at their
recorded settings.

`python3 opendsp/tests/quotient_modes.py` checks return bits and preserved
registers across 16 arithmetic modes, including saturation and logical
shifts. All 112 words match. MOD0 bits 2..4 are read-only in Teakra; their
observed reset value is included in the reference. These tests use local
compiler components and do not establish physical timing. See
`opendsp/validation/quotient-20261026.json`.

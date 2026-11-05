#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
"""Check full accumulator spill state."""
import argparse
import json
import os
from pathlib import Path
import struct

from stack_flags import digest, invoke

HERE = Path(__file__).resolve().parent
VALUES = [0, 1, -1, 0x7fffffff, -0x80000000, 0x7fffffffff, -0x8000000000,
          0x123456789a, -0x123456789a]
MODES = [3, 0x83]


def machine_source(cases):
    lines = ['--- |', '  target triple = "teak"']
    lines += ['  define void @wide_spill_' + str(index) + '() { ret void }' for index in range(len(cases))]
    lines += ['...']
    for index, (register, offset, flags_live, shift_live) in enumerate(cases):
        fallback = 'a1' if register == 'a0' else 'a0'
        lines += ['---', 'name: wide_spill_' + str(index), 'tracksRegLiveness: true', 'body: |',
            '  bb.0:', '    liveins: $r7, $icc, $stt0, $sp, $r0, $sv, $' + register + ', $' + fallback,
            '    STORE_REG_TO_STACK_PSEUDO_32 $' + register + ', $r7, ' + str(offset) + ' :: (store 5, align 2)']
        if flags_live:
            lines += ['    PUSH_ararpsttmod $stt0, implicit-def $sp, implicit $sp, implicit $icc',
                      '    $r1 = POP_regnob16 implicit-def $sp, implicit-def $icc, implicit $sp']
        else:
            lines += ['    $r1 = MOV_imm16_regnob16 0, implicit-def $icc']
        lines += ['    $r2 = COPY $sv'] if shift_live else [
            '    $r2 = MOV_imm16_regnob16 0, implicit-def $icc',
            '    $sv = MOV_imm16_regnob16 13124, implicit-def $icc']
        lines += ['    $' + register + ' = COPY $' + fallback,
            '    CMPV_imm16_RegNoBRegs16 0, $r0, implicit-def $icc',
            '    $' + register + ' = LOAD_REG_FROM_STACK_PSEUDO_32_SEXT40 $r7, ' + str(offset) + ' :: (load 5, align 2)']
        if flags_live:
            lines += ['    PUSH_ararpsttmod $stt0, implicit-def $sp, implicit $sp, implicit $icc']
        if not shift_live:
            lines += ['    $sv = MOV_imm16_regnob16 4660, implicit-def $icc']
        if flags_live:
            lines += ['    $stt0 = POP_ararpsttmod implicit-def $sp, implicit-def $icc, implicit $sp',
                '    RET 1, $icc, implicit-def $sp, implicit $sp, implicit $' + register + ', implicit $r1, implicit $r2, implicit $sv']
        lines += ['    RET 0, $noreg, implicit-def $sp, implicit $sp, implicit $' + register +
                  ', implicit $r1, implicit $r2, implicit $sv', '...']
    return '\n'.join(lines) + '\n'


def assembly_source(cases):
    lines = ['// SPDX-License-Identifier: BSD-2-Clause', '.text']
    saved = ['mod0', *['r' + str(index) for index in range(8)], 'sv', 'stt0']
    for index, (register, offset, flags_live, shift_live) in enumerate(cases):
        name = 'check_wide_spill_' + str(index)
        lines += ['.global ' + name, name + ':', '    push mod3', '    dint']
        lines += ['    push ' + item for item in saved]
        lines += ['    mov a0l, r1', '    mov a1l, r0', '    mov b1l, r6', '    push b0l', '    pop mod0',
            '    mov 0x1357, sv', '    mov ' + hex(0x5000 + offset + 1) + ', r7', '    mov sv, [r7]',
            '    mov 0x2468, sv', '    mov ' + hex(0x5000 + offset - 3) + ', r7', '    mov sv, [r7]',
            '    mov 0x5000, r7', '    mov [r1++], a0', '    and 0xffff, a0', '    mov [r1++], a1',
            '    shfi a1, a1, +16', '    or a1, a0', '    mov [r1], sv', '    push sv', '    pop a0e']
        if register != 'a0':
            lines += ['    mov a0, ' + register, '    clr a0, always']
        if register != 'a1':
            lines += ['    clr a1, always']
        lines += ['    mov 0x5aa5, sv', '    mov sp, r4', '    push mod0', '    pop r5',
            '    cmpv 0, r0', '    push stt0', '    pop r3', '    call wide_spill_' + str(index) + ', always',
            '    push stt0', '    pop r0', '    addv 5, r6', '    mov sv, [r6]', '    addv 0xfffb, r6']
        if register != 'a0':
            lines += ['    mov ' + register + ', a0']
        lines += ['    mov a0l, [r6++]', '    mov a0h, [r6++]', '    push a0e', '    pop sv', '    mov sv, [r6++]',
            '    mov sp, a0', '    mov r4, a1', '    sub a1, a0', '    mov a0l, [r6++]', '    mov r7, [r6++]',
            '    addv 1, r6', '    push mod0', '    pop sv', '    mov sv, a0', '    mov r5, a1',
            '    xor a1, a0', '    mov a0l, [r6++]']
        for flag_register in ['r1', 'r0']:
            lines += ['    mov ' + flag_register + ', a0', '    mov r3, a1', '    xor a1, a0'] if flags_live else [
                '    clr a0, always']
            lines += ['    mov a0l, [r6++]']
        lines += ['    mov r2, [r6++]', '    mov ' + hex(0x5000 + offset + 1) + ', r7', '    mov [r7], sv',
            '    mov sv, [r6++]', '    mov ' + hex(0x5000 + offset - 3) + ', r7', '    mov [r7], sv', '    mov sv, [r6]']
        lines += ['    pop ' + item for item in reversed(saved)]
        lines += ['    pop mod3', '    ret always']
    return '\n'.join(lines) + '\n'


def set_input(image, value):
    data = bytearray(image)
    header = struct.unpack_from('<16sHHIIIIIHHHHHH', data)
    sections = [struct.unpack_from('<10I', data, header[6] + index * header[11]) for index in range(header[12])]
    for section in sections:
        if section[1] != 2:
            continue
        strings = sections[section[6]]
        names = data[strings[4]:strings[4] + strings[5]]
        for position in range(section[4], section[4] + section[5], section[9]):
            name, address, size, _, _, index = struct.unpack_from('<IIIBBH', data, position)
            if names[name:].split(b'\0', 1)[0] != b'input':
                continue
            target = sections[index]
            assert target[1] == 1 and size == 6
            offset = target[4] + address - target[3]
            struct.pack_into('<3H', data, offset, value & 65535, (value >> 16) & 65535, (value >> 32) & 255)
            return data
    raise AssertionError('Missing input symbol')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=HERE / 'build/wide-spills')
    parser.add_argument('--baseline-llc', type=Path)
    args = parser.parse_args()
    build = args.output.resolve()
    build.mkdir(parents=True, exist_ok=True)
    cc, ld, llc = [os.environ.get(name, default) for name, default in
                   [('TEAK_CC', 'clang'), ('TEAK_LD', 'ld.lld'), ('TEAK_LLC', 'llc')]]
    teakra = Path(os.environ['TEAKRA'])
    cases = [(register, offset, flags, shift) for register in ['a0', 'a1', 'b0', 'b1']
             for offset in [-65, 0, 129] for flags in [False, True] for shift in [False, True]]
    count = len(cases) * len(MODES) * 2 * 12
    lines = ['typedef unsigned short u16;', 'volatile u16 input[3]={1,2,3};', 'u16 out[' + str(count) + '];']
    lines += ['void check_wide_spill_' + str(index) + '(volatile u16 *,u16,u16,u16 *);' for index in range(len(cases))]
    lines += ['int main(void) { u16 condition, mode, next=0;', 'for(condition=0;condition<2;++condition) {']
    for mode in MODES:
        for index in range(len(cases)):
            lines += ['check_wide_spill_' + str(index) + '(input,condition,' + str(mode) + ',out+next); next+=12;']
    lines += ['}', '((volatile u16 *)0x7000)[2]=(u16)out;', '((volatile u16 *)0x7000)[3]=' + str(count) + ';',
              '((volatile u16 *)0x7000)[0]=0x600d;', 'return 0; }']
    (build / 'main.c').write_text('\n'.join(lines) + '\n')
    (build / 'spills.mir').write_text(machine_source(cases))
    (build / 'wrappers.s').write_text(assembly_source(cases))
    objects = []
    for source in [build / 'main.c', build / 'wrappers.s', HERE / 'crt0.s']:
        target = build / (source.stem + '.o')
        invoke([cc, '--target=teak', '-O2', '-ffreestanding', '-fno-builtin', '-fwrapv', '-integrated-as',
                '-c', source, '-o', target], target.with_suffix('.log'))
        objects.append(target)
    invoke(['c++', '-O2', '-std=c++17', '-I' + str(teakra / 'include'), HERE / 'runner.cpp',
            teakra / 'b/src/libteakra.a', '-o', build / 'runner'], build / 'runner.log')
    outputs = {}
    for name, backend in [('current', llc)] + ([('baseline', str(args.baseline_llc))] if args.baseline_llc else []):
        target = build / (name + '.o')
        invoke([backend, '-mtriple=teak', '-start-before=postrapseudos', '-filetype=obj', build / 'spills.mir',
                '-o', target], build / (name + '-codegen.log'))
        original = build / (name + '.elf')
        invoke([ld, '--gc-sections', '-T', HERE / 'link.ld', *objects, target, '-o', original], build / (name + '-link.log'))
        results = []
        for index, value in enumerate(VALUES):
            expected = []
            extension = (value >> 32) & 255
            extension |= 0xff00 if extension & 128 else 0
            for condition in range(2):
                for mode in MODES:
                    for _, _, _, shift_live in cases:
                        expected += [value & 65535, (value >> 16) & 65535, extension, 0, 0x5000,
                            0x5aa5 if shift_live else 0x1234, 0, 0, 0, 0x5aa5 if shift_live else 0, 0x1357, 0x2468]
            image = build / (name + str(index) + '.elf')
            image.write_bytes(set_input(original.read_bytes(), value))
            reference = build / ('expected' + str(index) + '.pcm')
            reference.write_bytes(struct.pack('<' + str(count) + 'H', *expected))
            result = invoke([build / 'runner', image, reference, build / (name + str(index) + '.pcm'),
                             '500000', '0x7000'], build / (name + str(index) + '-execute.log'), check=False)
            assert result.returncode == 0, (name, index, result.stdout, result.stderr[:1000])
            output = json.loads(result.stdout)
            assert output['completed'] and not output['errors'] and output['comparisons'] == count
            results.append(output)
        outputs[name] = dict(comparisons=sum(item['comparisons'] for item in results),
                             steps=sum(item['steps'] for item in results), results=results, object_sha256=digest(target))
    sources = [Path(__file__), HERE / 'stack_flags.py', HERE / 'runner.cpp', HERE / 'crt0.s', HERE / 'link.ld',
               HERE.parents[1] / 'llvm/lib/Target/Teak/TeakInstrInfo.cpp']
    report = dict(passed=True, physical_hardware=False, interrupts_masked=True, result=outputs,
                  cases=len(cases) * len(MODES) * 2 * len(VALUES),
                  sources={path.resolve().relative_to(HERE.parents[1]).as_posix(): digest(path) for path in sources})
    (build / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=True, cases=report['cases'], result={name: {key: value for key, value in result.items()
        if key != 'results'} for name, result in outputs.items()})), flush=True)


if __name__ == '__main__':
    main()

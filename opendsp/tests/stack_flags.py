#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
"""Check stack loads with live flags."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
VALUES = [-32768, -12345, -1024, -1, 0, 1, 1024, 32767]
MODES = [3, 0x83]
OFFSETS = [-65, 0, 129]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(command, log, check=True):
    command = list(map(str, command))
    if os.name != 'nt' and command[0].endswith('.exe'):
        command = [command[0], *[argument[5].upper() + ':/' + argument[7:]
            if argument.startswith('/mnt/') and argument[6:7] == '/' else argument for argument in command[1:]]]
    result = subprocess.run(command, capture_output=True, text=True, timeout=120)
    log.write_text(json.dumps(command) + '\n' + result.stdout + result.stderr)
    if check and result.returncode:
        raise RuntimeError(str(log) + ': exit ' + str(result.returncode))
    return result


def machine_source(cases):
    lines = ['--- |', '  target triple = "teak"']
    lines += ['  define void @stack_flags_' + str(index) + '() { ret void }' for index in range(len(cases))]
    lines += ['...']
    for index, (register, offset, live) in enumerate(cases):
        fallback = 'a1' if register == 'a0' else 'a0'
        lines += ['---', 'name: stack_flags_' + str(index), 'tracksRegLiveness: true', 'body: |',
            '  bb.0:', '    liveins: $r7, $icc, $sp, $' + fallback,
            '    $' + register + ' = LOAD_REG_FROM_STACK_PSEUDO_16_SEXT40 $r7, ' + str(offset)]
        if live:
            lines += ['    RET 1, $icc, implicit-def $sp, implicit $sp, implicit $' + register,
                      '    $' + register + ' = COPY $' + fallback]
        lines += ['    RET 0, $noreg, implicit-def $sp, implicit $sp, implicit $' + register, '...']
    return '\n'.join(lines) + '\n'


def assembly_source(cases):
    lines = ['// SPDX-License-Identifier: BSD-2-Clause', '.text']
    saved = ['mod0', *['r' + str(index) for index in range(8)], 'sv', 'stt0']
    for index, (register, offset, live) in enumerate(cases):
        name = 'check_stack_flags_' + str(index)
        lines += ['.global ' + name, name + ':', '    push mod3', '    dint']
        lines += ['    push ' + item for item in saved]
        lines += ['    mov a0l, r1', '    mov a1l, r0', '    mov b1l, r6',
            '    push b0l', '    pop mod0', '    mov 0x5000, r7', '    addv ' + hex(offset & 65535) + ', r7',
            '    mov r1, [r7]', '    mov 0x5000, r7', '    mov 0x5aa5, sv', '    mov sp, r4',
            '    push mod0', '    pop r5']
        lines += ['    clr ' + item + ', always' for item in ['a0', 'a1', 'b0', 'b1']]
        lines += ['    cmpv 0, r0', '    push stt0', '    pop r3',
            '    call stack_flags_' + str(index) + ', always', '    push stt0', '    pop r2']
        if register != 'a0':
            lines += ['    mov ' + register + ', a0']
        lines += ['    mov a0l, [r6++]', '    mov a0h, [r6++]', '    push a0e', '    pop r1',
            '    mov r1, [r6++]', '    mov sp, a0', '    mov r4, a1', '    sub a1, a0',
            '    mov a0l, [r6++]', '    mov r7, [r6++]', '    push sv', '    pop r1',
            '    mov r1, [r6++]', '    push mod0', '    pop r1', '    mov r1, a0',
            '    mov r5, a1', '    xor a1, a0', '    mov a0l, [r6++]']
        if live:
            lines += ['    mov r2, a0', '    mov r3, a1', '    xor a1, a0', '    cmpv 0, r0',
                      '    br .Lflags_' + str(index) + ', eq']
        lines += ['    clr a0, always', '.Lflags_' + str(index) + ':', '    mov a0l, [r6]']
        lines += ['    pop ' + item for item in reversed(saved)]
        lines += ['    pop mod3', '    ret always']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=HERE / 'build/stack-flags')
    parser.add_argument('--baseline-llc', type=Path)
    args = parser.parse_args()
    build = args.output.resolve()
    build.mkdir(parents=True, exist_ok=True)
    cc, ld, llc = [os.environ.get(name, default) for name, default in
                   [('TEAK_CC', 'clang'), ('TEAK_LD', 'ld.lld'), ('TEAK_LLC', 'llc')]]
    teakra = Path(os.environ['TEAKRA'])
    cases = [(register, offset, False) for register in ['a0', 'a1', 'b0', 'b1'] for offset in OFFSETS]
    cases += [(register, offset, True) for register in ['b0', 'b1', 'a0', 'a1'] for offset in OFFSETS]
    expected = []
    for value in VALUES:
        for condition in range(2):
            for mode in MODES:
                for _, _, live in cases:
                    result = value if not live or not condition else 0
                    expected += [result & 65535, 65535 if result < 0 else 0,
                                 65535 if result < 0 else 0, 0, 0x5000, 0x5aa5, 0, 0]
    count = len(expected)
    source = ['typedef unsigned short u16;', 'typedef signed short s16;', 'u16 out[' + str(count) + '];',
              'static const s16 values[] = {' + ','.join(map(str, VALUES)) + '};',
              'static const u16 modes[] = {' + ','.join(map(str, MODES)) + '};']
    source += ['void check_stack_flags_' + str(index) + '(u16,u16,u16,u16 *);' for index in range(len(cases))]
    source += ['int main(void) { u16 value, condition, mode, next = 0;',
              'for(value=0;value<8;++value) for(condition=0;condition<2;++condition) for(mode=0;mode<2;++mode) {']
    for index in range(len(cases)):
        source += ['check_stack_flags_' + str(index) + '(values[value],condition,modes[mode],out+next); next+=8;']
    source += ['}', '((volatile u16 *)0x7000)[2]=(u16)out;',
               '((volatile u16 *)0x7000)[3]=' + str(count) + ';',
               '((volatile u16 *)0x7000)[0]=0x600d;', 'return 0; }']
    (build / 'main.c').write_text('\n'.join(source) + '\n')
    (build / 'loads.mir').write_text(machine_source(cases))
    (build / 'wrappers.s').write_text(assembly_source(cases))
    flags = ['--target=teak', '-O2', '-ffreestanding', '-fno-builtin', '-fwrapv', '-integrated-as']
    objects = []
    for path in [build / 'main.c', build / 'wrappers.s', HERE / 'crt0.s']:
        target = build / (path.stem + '.o')
        invoke([cc, *flags, '-c', path, '-o', target], target.with_suffix('.log'))
        objects.append(target)
    invoke(['c++', '-O2', '-std=c++17', '-I' + str(teakra / 'include'), HERE / 'runner.cpp',
            teakra / 'b/src/libteakra.a', '-o', build / 'runner'], build / 'runner.log')
    reference = build / 'expected.pcm'
    reference.write_bytes(struct.pack('<' + str(count) + 'H', *expected))
    outputs = {}
    compilers = [('current', llc)] + ([('baseline', str(args.baseline_llc))] if args.baseline_llc else [])
    for name, backend in compilers:
        target = build / (name + '.o')
        invoke([backend, '-mtriple=teak', '-start-before=postrapseudos', '-filetype=obj', build / 'loads.mir',
                '-o', target], build / (name + '-codegen.log'))
        image = build / (name + '.elf')
        invoke([ld, '--gc-sections', '-T', HERE / 'link.ld', *objects, target, '-o', image], build / (name + '-link.log'))
        result = invoke([build / 'runner', image, reference, build / (name + '.pcm'), '500000', '0x7000'],
                        build / (name + '-execute.log'), check=False)
        records = [json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
        output = records[-1] if records else dict(completed=False)
        output.update(exit_code=result.returncode, image_sha256=digest(image), object_sha256=digest(target))
        outputs[name] = output
    sources = [Path(__file__), HERE / 'runner.cpp', HERE / 'crt0.s', HERE / 'link.ld',
               HERE.parents[1] / 'llvm/lib/Target/Teak/TeakInstrInfo.cpp']
    report = dict(passed=outputs['current']['exit_code'] == 0, physical_hardware=False,
                  cases=len(cases) * len(VALUES) * 2 * len(MODES), comparisons=count, result=outputs,
                  arithmetic_modes=MODES, frame_offsets=OFFSETS, interrupts_masked=True,
                  sources={path.resolve().relative_to(HERE.parents[1]).as_posix(): digest(path) for path in sources},
                  generated={path.name: digest(path) for path in [build / 'main.c', build / 'loads.mir', build / 'wrappers.s']})
    (build / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(dict(passed=report['passed'], cases=report['cases'], comparisons=count, result=outputs)), flush=True)
    assert report['passed'], outputs['current']
    if args.baseline_llc:
        assert outputs['baseline']['exit_code'] != 0, outputs['baseline']


if __name__ == '__main__':
    main()

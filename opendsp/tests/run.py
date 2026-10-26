#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
"""Run native compiler regressions."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
CC = os.environ.get('TEAK_CC', 'clang')
LD = os.environ.get('TEAK_LD', 'ld.lld')
TEAKRA = Path(os.environ.get('TEAKRA', 'teakra')).resolve()
OPUS = Path(os.environ.get('OPUS_SOURCE', 'opus')).resolve()

BUILD = HERE / 'build'
VALUES = [-32768, -32767, -1024, -1, 0, 1, 1024, 32766, 32767]


def command(args, name, cwd=None):
    result = subprocess.run(list(map(str, args)), capture_output=True, text=True, cwd=cwd)
    (BUILD / name).write_text('COMMAND: ' + ' '.join(map(str, args)) + '\n' + result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'{name}: exit {result.returncode}; see {BUILD / name}')
    return result.stdout


def comparisons(simple=False):
    source = '''
__attribute__((noinline)) u16 compare(s16 a, s16 b) {
    return (a < b) | ((a <= b) << 1) | ((a > b) << 2) |
           ((a >= b) << 3) | ((a == b) << 4) | ((a != b) << 5);
}
__attribute__((noinline)) u16 compare_unsigned(u16 a, u16 b) {
    return (a < b) | ((a <= b) << 1) | ((a > b) << 2) |
           ((a >= b) << 3) | ((a == b) << 4) | ((a != b) << 5);
}
__attribute__((noinline)) s16 minimum(s16 a, s16 b) { return a < b ? a : b; }
__attribute__((noinline)) s16 maximum(s16 a, s16 b) { return a > b ? a : b; }
__attribute__((noinline)) s16 sign(s16 a) { return a < 0 ? -1 : a > 0; }
'''
    if simple:
        source = '\n'.join(f'__attribute__((noinline)) u16 cmp_{i}(s16 a,s16 b) {{ return a {op} b; }}' for i, op in enumerate(['<','<=','>','>=','==','!=']))
    body, expected = [], []
    def cmp(a, b):
        return sum(int(value) << bit for bit, value in enumerate([a < b, a <= b, a > b, a >= b, a == b, a != b]))
    for a in VALUES:
        body.append(f'out[n++] = sign(input[{VALUES.index(a)}]);')
        expected.append(-1 if a < 0 else int(a > 0))
        for b in VALUES:
            args = f'input[{VALUES.index(a)}], input[{VALUES.index(b)}]'
            if simple:
                body.extend(f'out[n++] = cmp_{i}({args});' for i in range(6))
                expected.extend([a < b, a <= b, a > b, a >= b, a == b, a != b])
                continue
            body += [f'out[n++] = compare({args});', f'out[n++] = compare_unsigned({args});',
                     f'out[n++] = minimum({args});', f'out[n++] = maximum({args});']
            expected += [cmp(a, b), cmp(a & 65535, b & 65535), min(a, b), max(a, b)]
    if simple:
        source += '\n__attribute__((noinline)) s16 sign(s16 a) { return a < 0 ? -1 : a > 0; }\n'
    return source, body, expected


def sort_case():
    source = '''
void silk_insertion_sort_increasing_all_values_int16(s16 *, int);
'''
    body, expected = [], []
    for values in [VALUES, list(reversed(VALUES)), [1000]*9, [30000-i*1900 for i in range(9)]]:
        offset = len(expected)
        body.extend(f'out[{offset+i}] = {v};' for i, v in enumerate(values))
        body.append(f'silk_insertion_sort_increasing_all_values_int16((s16 *)out+{offset}, 9);')
        expected += sorted(values)
    return source, body, expected


def nlsf_case():
    source = 'void silk_NLSF_stabilize(s16 *, const s16 *, int);\ns16 nlsf[16], delta[17];\n'
    body, expected = [], []
    body.extend(f'delta[{i}]={32+(i & 3)};' for i in range(17))
    for c in range(8):
        values=[]
        for i in range(16):
            v = 200+i*1900 if c==0 else 30000-i*1900 if c==1 else 1000 if c==2 else 32760-i*4 if c==3 else -100+i*8 if c==4 else (i*3779+c*791)&32767
            values.append(v)
        body.extend(f'nlsf[{i}]={v}; out[n++] = nlsf[{i}];' for i,v in enumerate(values))
        body.append('silk_NLSF_stabilize(nlsf, delta, 16);')
        body.extend(f'out[n++] = nlsf[{i}];' for i in range(16))
        expected.extend([0]*32)
    return source, body, expected


def clz_case():
    values16 = {0, 0xffff}
    values32 = {0, 0xffffffff}
    values40 = {0, 0xffffffffff}
    for width, values in [(16, values16), (32, values32), (40, values40)]:
        mask = (1 << width)-1
        for bit in range(width):
            values.update([(1 << bit)-1, 1 << bit, ((1 << bit)+1) & mask])
        state = 0x1f123bb5
        for _ in range(128):
            state = (state*6364136223846793005+1442695040888963407) & mask
            values.add(state)
    source = '''
__attribute__((noinline)) u16 leading_zeroes(u16 low_word, u16 high_word) {
    u32 value = ((u32)high_word << 16) | low_word;
    return value ? __builtin_clz(value) : 32;
}
u16 leading_zeroes40(u16, u16, u16);
u16 leading_zeroes16(u16);
'''
    inputs, body, expected = [], [], []
    for width, values in [(16, values16), (32, values32), (40, values40)]:
        for value in sorted(values):
            index = len(inputs)
            inputs.extend([(value >> shift) & 65535 for shift in [0, 16, 32]])
            argument_count = 1 if width == 16 else 2 if width == 32 else 3
            arguments = ','.join(f'bit_inputs[{index+i}]' for i in range(argument_count))
            function = 'leading_zeroes' if width == 32 else f'leading_zeroes{width}'
            body.append(f'out[n++] = {function}({arguments});')
            expected.append(width-value.bit_length())
    source += '\nvolatile u16 bit_inputs[] = {' + ','.join(map(str, inputs)) + '};\n'
    return source, body, expected


def stack_case():
    source = '''
__attribute__((noinline)) void change_short(s16 *value) { *value += 5; }
__attribute__((noinline)) void change_word(u32 *value) { *value ^= 0x13579bdfu; }
__attribute__((noinline)) s16 local_short(s16 value) {
    s16 local_value = value;
    change_short(&local_value);
    return local_value;
}
__attribute__((noinline)) s16 local_array(s16 value) {
    s16 local_values[7];
    u16 index;
    for (index=0; index<7; ++index) local_values[index] = value+index;
    change_short(&local_values[3]);
    return local_values[0]+local_values[3]+local_values[6];
}
__attribute__((noinline)) u16 local_word(u16 low_word, u16 high_word) {
    u32 local_value = ((u32)high_word << 16) | low_word;
    change_word(&local_value);
    return local_value >> 16;
}
'''
    body, expected = [], []
    for index, value in enumerate(VALUES):
        body.extend([f'out[n++] = local_short(input[{index}]);',
                     f'out[n++] = local_array(input[{index}]);'])
        expected.extend([value+5, 3*value+14])
        for high_index, high_word in enumerate(VALUES):
            body.append(f'out[n++] = local_word(input[{index}],input[{high_index}]);')
            value32 = (((high_word & 65535) << 16) | (value & 65535)) ^ 0x13579bdf
            expected.append(value32 >> 16)
    return source, body, expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--opt', default='-O2')
    parser.add_argument('--label')
    parser.add_argument('--case', choices=['comparisons', 'simple', 'sort', 'nlsf', 'clz', 'stack'], default='comparisons')
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    factories = {'nlsf': nlsf_case, 'sort': sort_case, 'clz': clz_case, 'stack': stack_case}
    functions, body, expected = factories[args.case]() if args.case in factories else comparisons(args.case == 'simple')
    stem = args.case + args.opt.replace('-', '')
    source = BUILD / (stem + '.c')
    source.write_text('#include "kernels.h"\n#ifdef HOST_REFERENCE\n#include <stdio.h>\n#endif\n' + functions + '\nvolatile s16 input[] = {' + ','.join(map(str, VALUES)) + '};\n' +
                      f'u16 out[{len(expected)}];\nint main(void) {{ u16 n=0;\n' + '\n'.join(body) +
                      f'\n#ifdef HOST_REFERENCE\nfwrite(out,2,{len(expected)},stdout);\n#else\n((volatile u16 *)0x3000)[2]=(u16)(unsigned)out;\n((volatile u16 *)0x3000)[3]={len(expected)};\n((volatile u16 *)0x3000)[0]=0x600d;\n#endif\nreturn 0; }}\n')
    flags = ['--target=teak', '-march=teak', args.opt, '-ffreestanding', '-fno-builtin', '-fno-strict-aliasing',
             '-ffunction-sections', '-fdata-sections', '-nostdlib', '-integrated-as', '-I'+str(HERE)]
    objects = []
    for path in [HERE / 'crt0.s', source]:
        obj = BUILD / (path.stem+'.o')
        command([CC, *flags, '-c', path, '-o', obj], path.stem+'.log')
        objects.append(obj)
    command([CC, *flags, '-S', source, '-o', BUILD / (stem+'.s')], stem+'-asm.log')
    if args.case == 'clz':
        ir_source = HERE/'clz40.ll'
        obj = BUILD/'clz40.o'
        command([CC, '--target=teak', '-O2', '-c', ir_source, '-o', obj], 'clz40.log')
        objects.append(obj)
    if args.case in ['sort', 'nlsf']:
        units = ['sort'] + (['NLSF_stabilize'] if args.case == 'nlsf' else [])
        upstream_flags = ['-DFIXED_POINT', '-DOPUS_BUILD', '-DHAVE_STDINT_H', '-DHAVE_INTTYPES_H']
        includes = ['-I'+str(HERE/'include'), *['-I'+str(OPUS/p) for p in ['include','celt','silk','.']]]
        for name in units:
            obj = BUILD / (name+'.o')
            command([CC, *flags, *upstream_flags, *includes, '-c', OPUS/'silk'/(name+'.c'), '-o', obj], name+'.log')
            objects.append(obj)
        if args.case == 'nlsf':
            host = BUILD/'host-reference'
            command(['cc', '-O2', '-fwrapv', '-DHOST_REFERENCE', '-I'+str(HERE), *upstream_flags,
                     *['-I'+str(OPUS/p) for p in ['include','celt','silk','.']], source,
                     *[OPUS/'silk'/(name+'.c') for name in units], '-o', host], 'host.log')
            reference_bytes = subprocess.check_output([host])
    elf, cdc = BUILD/(stem+'.elf'), BUILD/(stem+'.cdc')
    command([LD, '--gc-sections', '-T', HERE/'link.ld', *objects, '-o', elf], 'link.log')
    runner = BUILD/'runner'
    if not runner.exists():
        command(['g++', '-O2', '-std=c++17', '-I'+str(TEAKRA/'include'), HERE/'runner.cpp',
                 TEAKRA/'b/src/libteakra.a', '-o', runner], 'runner.log')
    reference = BUILD/(stem+'.pcm')
    reference.write_bytes(reference_bytes if args.case == 'nlsf' else struct.pack('<'+'H'*len(expected), *[v & 65535 for v in expected]))
    result = subprocess.run([str(runner), str(elf), str(reference)], capture_output=True, text=True)
    (BUILD/(stem+'-emulate.log')).write_text(result.stdout+result.stderr)
    if not result.stdout.strip():
        raise RuntimeError(f'Emulation failed; see {BUILD / (stem+"-emulate.log")}')
    if args.label:
        if not args.label.replace('-', '').replace('_', '').isalnum():
            raise SystemExit('Invalid label')
        evidence = json.loads(result.stdout)
        evidence.update(case=args.case, optimization=args.opt, diagnostics=result.stderr.splitlines(),
                        compiler=CC, physical_hardware=False)
        (BUILD/(args.label+'-'+stem+'.json')).write_text(json.dumps(evidence, indent=2)+'\n')
    print(result.stdout+result.stderr, end='')
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()

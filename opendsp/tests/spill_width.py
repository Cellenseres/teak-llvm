#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
"""Check that -teak-spill40 selects the accumulator spill format."""
import argparse
import os
from pathlib import Path
import re

from stack_flags import invoke

HERE = Path(__file__).resolve().parent
SOURCE = '''target triple = "teak"

declare void @clobber()

define i32 @narrow(i32 %a, i32 %b) {
  %sum = add i32 %a, %b
  call void @clobber()
  %result = xor i32 %sum, %a
  ret i32 %result
}

define i32 @extended(i32 %a, i32 %b) {
  %wide_a = sext i32 %a to i40
  %wide_b = sext i32 %b to i40
  %product = mul i40 %wide_a, %wide_b
  call void @clobber()
  %high = ashr i40 %product, 8
  %result = trunc i40 %high to i32
  ret i32 %result
}
'''
# Whether spills save the extension byte, for each -teak-spill40 setting.
EXPECTED = {None: True, 'true': True, 'false': False}


def wide_functions(assembly):
    result, function = {}, None
    for line in assembly.splitlines():
        label = re.match(r'([A-Za-z_]\w*):', line)
        if label:
            function = label.group(1)
            result.setdefault(function, False)
        elif function and re.search(r'\bpush [ab][01]e\b', line):
            result[function] = True
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=HERE / 'build/spill-width')
    args = parser.parse_args()
    build = args.output.resolve()
    build.mkdir(parents=True, exist_ok=True)
    llc = os.environ.get('TEAK_LLC', 'llc')
    source = build / 'spill_width.ll'
    source.write_text(SOURCE)
    failures = []
    for setting, wide in EXPECTED.items():
        name = 'default' if setting is None else setting
        output = build / (name + '.s')
        flags = [] if setting is None else ['-teak-spill40=' + setting]
        invoke([llc, *flags, '-mtriple=teak', '-O2', source, '-o', output], build / (name + '.log'))
        actual = wide_functions(output.read_text())
        for function in ['narrow', 'extended']:
            if actual.get(function) != wide:
                failures.append(f'{name}: {function} wide={actual.get(function)}, expected {wide}')
    print('\n'.join(failures) if failures else 'Spill widths match')
    raise SystemExit(1 if failures else 0)


if __name__ == '__main__':
    main()

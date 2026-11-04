#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
"""Check division across arithmetic modes."""
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    build = HERE / "build/quotient-modes"
    build.mkdir(exist_ok=True)
    modes = [base | low for base in [0, 0x80, 0xc00, 0xc80] for low in range(4)]
    expected = [value for mode in modes for value in [mode | 4, 65535, 65535, mode | 4, 0x1357, 0x2468, 255]]
    source = build / "modes.c"
    source.write_text('#include "kernels.h"\nvoid quotient_mode(u16,u16 *);\n'
        'volatile u16 modes[]={' + ','.join(map(str, modes)) + '};\n'
        'u16 result[7], out[112];\nint main(void) {\n'
        'u16 i,j,n=0; for(i=0;i<16;++i) { quotient_mode(modes[i],result); '
        'for(j=0;j<7;++j) out[n++]=result[j]; }\n'
        '((volatile u16 *)0x3000)[2]=(u16)(unsigned)out;\n'
        '((volatile u16 *)0x3000)[3]=112; ((volatile u16 *)0x3000)[0]=0x600d; return 0; }\n')
    inputs = [HERE / "crt0.s", HERE / "quotient_state.s", ROOT / "opendsp/runtime/quotient.s", source]
    recorded = [*inputs, HERE / "kernels.h", HERE / "link.ld", HERE / "runner.cpp", Path(__file__)]
    hashes = {str(path.relative_to(ROOT)): digest(path) for path in recorded}
    objects = []
    for path in inputs:
        target = build / (path.stem + ".o")
        command = [os.environ["TEAK_CC"], "--target=teak", "-O2", "-ffreestanding", "-fno-builtin",
                   "-integrated-as", "-I" + str(HERE), "-c", str(path), "-o", str(target)]
        result = subprocess.run(command, capture_output=True, text=True)
        (build / (path.stem + ".log")).write_text(result.stdout + result.stderr)
        assert not result.returncode, result.stderr
        objects.append(target)
    image = build / "modes.elf"
    subprocess.run([os.environ["TEAK_LD"], "--gc-sections", "-T", str(HERE / "link.ld"),
                    *map(str, objects), "-o", str(image)], check=True)
    teakra = Path(os.environ["TEAKRA"])
    runner = build / "runner"
    subprocess.run(["g++", "-O2", "-std=c++17", "-I" + str(teakra / "include"), str(HERE / "runner.cpp"),
                    str(teakra / "b/src/libteakra.a"), "-o", str(runner)], check=True)
    reference = build / "expected.pcm"
    reference.write_bytes(struct.pack("<112H", *expected))
    result = subprocess.run([str(runner), str(image), str(reference), str(build / "actual.pcm")],
                            capture_output=True, text=True)
    (build / "execute.log").write_text(result.stdout + result.stderr)
    assert result.returncode == 0 and not result.stderr, result.stdout + result.stderr
    record = json.loads(result.stdout)
    assert record["completed"] and not record["errors"] and record["comparisons"] == 112
    assert hashes == {str(path.relative_to(ROOT)): digest(path) for path in recorded}
    record.update(passed=True, physical_hardware=False, modes=modes, sources=hashes,
                  image_sha256=digest(image), reference_sha256=digest(reference))
    (build / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps(record), flush=True)


if __name__ == "__main__":
    main()

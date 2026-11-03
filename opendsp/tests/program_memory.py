#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
"""Check program tables across address pages."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess

HERE = Path(__file__).resolve().parent
BUILD = Path(os.environ.get("TEAK_TEST_BUILD", str(HERE / "build/program-memory")))


def execute(arguments, label):
    arguments = list(map(str, arguments))
    if os.name != "nt" and arguments[0].lower().endswith(".exe"):
        arguments = [arguments[0], *[argument[5].upper() + ":/" + argument[7:]
                     if argument.startswith("/mnt/") and argument[6:7] == "/" else argument
                     for argument in arguments[1:]]]
    result = subprocess.run(arguments, capture_output=True, text=True)
    (BUILD / (label + ".log")).write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(label + ":\n" + (result.stdout + result.stderr)[-2500:])
    return result


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    (BUILD / "result.json").write_text(json.dumps(dict(passed=False)) + "\n")
    values = [0, 1, -1, -(1 << 31), (1 << 31) - 1, 0x12345678, -65537, 65535, 65536]
    words = [0, 1, 32767, 32768, 65535]
    bytes_values = [0, 1, 127, 128, 255]
    source = r'''
typedef unsigned char uint8_t;
typedef signed char int8_t;
typedef unsigned short uint16_t;
typedef unsigned long uint32_t;
typedef long int32_t;
typedef unsigned long long uint64_t;
typedef long long int64_t;
#define PROGRAM __attribute__((address_space(1)))
#define LOW __attribute__((section(".program_low")))
#define HIGH __attribute__((section(".program_high")))
static volatile const int32_t PROGRAM low[] LOW = {VALUES};
static volatile const int32_t PROGRAM high[] HIGH = {VALUES};
static volatile const uint16_t PROGRAM word_values[] HIGH = {WORDS};
static volatile const uint8_t PROGRAM byte_values[] HIGH = {OCTETS};
struct Record { uint16_t tag; int32_t value; uint16_t tail; };
static volatile const struct Record PROGRAM records[] HIGH = {
    {0x1234, -2147483647-1, 0x5678}, {0xabcd, 0x12345678, 0xef01}
};
static volatile int32_t data_values[] = {VALUES};
static volatile uint16_t indices[] = {0,1,2,3,4,5,6,7,8};
static uint16_t output[512];
static void append(uint16_t *count, uint32_t value) {
    output[(*count)++] = value;
    output[(*count)++] = value >> 16;
}
int main(void) {
    volatile uint16_t *mailbox = (void *)0x3000;
    uint16_t count = 0;
    mailbox[0] = 0x1111;
    while (mailbox[0] != 0x2222) {}
    for (unsigned iteration = 0; iteration < 9; ++iteration) {
        unsigned index = indices[iteration];
        append(&count, low[index]);
        append(&count, high[index]);
        append(&count, data_values[index]);
        uint32_t value = high[index];
        output[count++] = value > 0x7fffffffUL;
        output[count++] = (int32_t)value < 0;
        int64_t signed_value = high[index];
        uint64_t unsigned_value = (uint32_t)high[index];
        append(&count, signed_value >> 32);
        append(&count, unsigned_value >> 32);
    }
    for (unsigned iteration = 0; iteration < 5; ++iteration) {
        unsigned index = indices[iteration];
        output[count++] = word_values[index];
        output[count++] = byte_values[index];
        output[count++] = (int8_t)byte_values[index];
    }
    for (unsigned iteration = 0; iteration < 2; ++iteration) {
        unsigned index = indices[iteration];
        output[count++] = records[index].tag;
        append(&count, records[index].value);
        output[count++] = records[index].tail;
    }
    append(&count, low[3]);
    append(&count, high[5]);
    append(&count, records[1].value);
    output[count++] = records[1].tail;
    mailbox[2] = (unsigned)output;
    mailbox[3] = count;
    mailbox[0] = 0x600d;
    return 0;
}
'''.replace("VALUES", ",".join(str(value) + "L" for value in values)).replace(
        "WORDS", ",".join(map(str, words))).replace("OCTETS", ",".join(map(str, bytes_values)))
    (BUILD / "program.c").write_text(source)
    expected = []
    def append(value):
        expected.extend([value & 65535, (value >> 16) & 65535])
    for value in values:
        for _ in range(3):
            append(value)
        expected.extend([int(value < 0), int(value < 0)])
        append(-1 if value < 0 else 0)
        append(0)
    for word, octet in zip(words, bytes_values):
        expected.extend([word, octet, (octet if octet < 128 else octet - 256) & 65535])
    for tag, value, tail in [(0x1234, -(1 << 31), 0x5678), (0xabcd, 0x12345678, 0xef01)]:
        expected.append(tag)
        append(value)
        expected.append(tail)
    append(values[3])
    append(values[5])
    append(0x12345678)
    expected.append(0xef01)
    (BUILD / "expected.pcm").write_bytes(struct.pack("<" + "H" * len(expected), *expected))
    layout = (HERE / "link.ld").read_text().replace(
        "    . = 0x10002000;", "    . = 0x1fff0;\n    .program_low : { *(.program_low) } :prog\n"
        "    . = 0x3f000;\n    .program_high : { *(.program_high) } :prog\n    . = 0x10002000;")
    (BUILD / "link.ld").write_text(layout)
    cc = os.environ.get("TEAK_CC", "clang")
    flags = ["--target=teak", "-march=teak", "-O2", "-ffreestanding", "-fno-builtin",
             "-fwrapv", "-fno-strict-aliasing"]
    objects = []
    for path in [BUILD / "program.c", HERE / "crt0.s", HERE.parent / "runtime/program.s"]:
        target = BUILD / (path.stem + ("_runtime" if path.suffix == ".s" and path.stem == "program" else "") + ".o")
        execute([cc, *flags, "-integrated-as", "-c", path, "-o", target], target.stem)
        objects.append(target)
    archive = BUILD / "libprogram.a"
    execute([os.environ.get("TEAK_AR", "llvm-ar"), "rcs", archive, objects.pop()], "archive")
    objects.append(archive)
    execute([os.environ.get("TEAK_LD", "ld.lld"), "--gc-sections", "-T", BUILD / "link.ld", *objects,
             "-o", BUILD / "program.elf"], "link")
    teakra = Path(os.environ["TEAKRA"])
    execute(["g++", "-O2", "-std=c++17", "-I" + str(teakra / "include"), HERE / "runner.cpp",
             teakra / "b/src/libteakra.a", "-o", BUILD / "runner"], "runner")
    results = []
    for page in range(4):
        result = execute([BUILD / "runner", BUILD / "program.elf", BUILD / "expected.pcm",
                          BUILD / ("actual" + str(page) + ".pcm"), "1000000", "0x3000", page], "page" + str(page))
        record = json.loads(result.stdout)
        record["program_page"] = page
        results.append(record)
    invalid = BUILD / "invalid_store.c"
    invalid.write_text("void invalid_store(short __attribute__((address_space(1))) *pointer) { *pointer = 1; }\n")
    rejected = subprocess.run([cc, *flags, "-c", str(invalid), "-o", str(BUILD / "invalid_store.o")],
                              capture_output=True, text=True)
    (BUILD / "invalid-store.log").write_text(rejected.stdout + rejected.stderr)
    store_rejected = rejected.returncode != 0 and "Program memory stores are unsupported" in rejected.stderr
    report = dict(passed=all(record["completed"] and record["errors"] == 0 and
                             record["comparisons"] == len(expected) for record in results) and store_rejected,
                  program_store_rejected=store_rejected, archive_linked=True,
                  physical_hardware=False, cases=results,
                  image_sha256=hashlib.sha256((BUILD / "program.elf").read_bytes()).hexdigest(),
                  expected_sha256=hashlib.sha256((BUILD / "expected.pcm").read_bytes()).hexdigest())
    root = HERE.parent.parent
    report["sources"] = {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                         for path in [Path(__file__), HERE / "runner.cpp", HERE.parent / "runtime/program.s",
                                      root / "llvm/lib/Target/Teak/TeakISelLowering.cpp",
                                      root / "llvm/lib/Target/Teak/TeakISelLowering.h"]}
    report["toolchain"] = {}
    for name in ["TEAK_CC", "TEAK_CC1", "TEAK_LLC", "TEAK_LD", "TEAK_AR"]:
        if name in os.environ:
            path = Path(shutil.which(os.environ[name]) or os.environ[name])
            if path.is_file():
                report["toolchain"][name] = hashlib.sha256(path.read_bytes()).hexdigest()
    (BUILD / "result.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

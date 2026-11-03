// SPDX-License-Identifier: BSD-2-Clause
.section .text.__teak_program_read16
.global __teak_program_read16
.type __teak_program_read16,@function
__teak_program_read16:
    push r0
    .short 0x0d40
    mov r0, a0l
    pop r0
    ret always
.size __teak_program_read16, .-__teak_program_read16

.section .text.__teak_program_read32
.global __teak_program_read32
.type __teak_program_read32,@function
__teak_program_read32:
    push r0
    push r1
    .short 0x0d40
    add 0x1, a0
    .short 0x0d41
    mov r0, a0
    shfi a0, a0, +16
    mov r1, a1l
    add a1, a0
    pop r1
    pop r0
    ret always
.size __teak_program_read32, .-__teak_program_read32

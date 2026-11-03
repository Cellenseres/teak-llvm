// SPDX-License-Identifier: BSD-2-Clause
// Preserve interrupt and product modes.
.section .text.__teak_mulword40
.global __teak_mulword40
__teak_mulword40:
    push mod3
    dint
    push mod0
    set 0x0003, mod0
    rst 0x0c00, mod0
    push y0
    push r0
    push r1
    push r2
    mov a0l, r0
    mov a0h, r1
    shfi a0, a0, -32
    and 0x00ff, a0
    mov a0l, r2
    mov a1l, y0
    mpysu y0, r0, a0
    clr a0, always
    add p*, a0
    mov a0, b1
    mpysu y0, r1, a0
    clr a0, always
    add p*, a0
    shfi a0, a0, +16
    add a0, b1
    mpysu y0, r2, a0
    clr a0, always
    add p*, a0
    shfi a0, a0, +31
    shfi a0, a0, +1
    add b1, a0
    pop r2
    pop r1
    pop r0
    pop y0
    pop mod0
    pop mod3
    ret always

.section .text.__teak_mul40
.global __teak_mul40
__teak_mul40:
    push mod3
    dint
    push mod0
    set 0x0003, mod0
    rst 0x0c00, mod0
    push y0
    push r0
    push r1
    push r2
    push r3
    push r4
    push r5
    mov a0, b0
    and 0x7fff, a0
    mov a0l, r0
    shfi b0, a0, -15
    and 0x7fff, a0
    mov a0l, r1
    shfi b0, a0, -30
    and 0x03ff, a0
    mov a0l, r2
    mov a1, b0
    and 0x7fff, a1
    mov a1l, r3
    shfi b0, a1, -15
    and 0x7fff, a1
    mov a1l, r4
    shfi b0, a1, -30
    and 0x03ff, a1
    mov a1l, r5
    clr a0, always
    mov r0, y0
    mpy y0, r3, a1
    clr a1, always
    add p*, a1
    add a1, a0
    mov a0, b1
    clr a0, always
    mov r0, y0
    mpy y0, r4, a1
    clr a1, always
    add p*, a1
    add a1, a0
    mov r1, y0
    mpy y0, r3, a1
    clr a1, always
    add p*, a1
    add a1, a0
    shfi a0, a0, +15
    add a0, b1
    clr a0, always
    mov r0, y0
    mpy y0, r5, a1
    clr a1, always
    add p*, a1
    add a1, a0
    mov r1, y0
    mpy y0, r4, a1
    clr a1, always
    add p*, a1
    add a1, a0
    mov r2, y0
    mpy y0, r3, a1
    clr a1, always
    add p*, a1
    add a1, a0
    shfi a0, a0, +30
    add b1, a0
    pop r5
    pop r4
    pop r3
    pop r2
    pop r1
    pop r0
    pop y0
    pop mod0
    pop mod3
    ret always

.section .text.__teak_umulh40
.global __teak_umulh40
__teak_umulh40:
    push mod3
    dint
    push mod0
    set 0x0003, mod0
    rst 0x0c00, mod0
    push y0
    push r0
    push r1
    push r2
    push r3
    push r4
    push r5
    mov a0, b0
    and 0x7fff, a0
    mov a0l, r0
    shfi b0, a0, -15
    and 0x7fff, a0
    mov a0l, r1
    shfi b0, a0, -30
    and 0x03ff, a0
    mov a0l, r2
    mov a1, b0
    and 0x7fff, a1
    mov a1l, r3
    shfi b0, a1, -15
    and 0x7fff, a1
    mov a1l, r4
    shfi b0, a1, -30
    and 0x03ff, a1
    mov a1l, r5
    clr a0, always
    mov r0, y0
    mpy y0, r3, a1
    clr a1, always
    add p*, a1
    add a1, a0
    shfi a0, a0, -15
    mov r0, y0
    mpy y0, r4, a1
    clr a1, always
    add p*, a1
    add a1, a0
    mov r1, y0
    mpy y0, r3, a1
    clr a1, always
    add p*, a1
    add a1, a0
    shfi a0, a0, -15
    mov r0, y0
    mpy y0, r5, a1
    clr a1, always
    add p*, a1
    add a1, a0
    mov r1, y0
    mpy y0, r4, a1
    clr a1, always
    add p*, a1
    add a1, a0
    mov r2, y0
    mpy y0, r3, a1
    clr a1, always
    add p*, a1
    add a1, a0
    mov a0, a1
    shfi a1, a1, -10
    and 0x001f, a1
    mov a1, b1
    shfi a0, a0, -15
    mov r1, y0
    mpy y0, r5, a1
    clr a1, always
    add p*, a1
    add a1, a0
    mov r2, y0
    mpy y0, r4, a1
    clr a1, always
    add p*, a1
    add a1, a0
    mov a0, a1
    and 0x7fff, a1
    shfi a1, a1, +5
    add a1, b1
    shfi a0, a0, -15
    mov r2, y0
    mpy y0, r5, a1
    clr a1, always
    add p*, a1
    add a1, a0
    mov a0, a1
    and 0x7fff, a1
    shfi a1, a1, +20
    add a1, b1
    shfi a0, a0, -15
    shfi a0, a0, +20
    shfi a0, a0, +15
    add b1, a0
    pop r5
    pop r4
    pop r3
    pop r2
    pop r1
    pop r0
    pop y0
    pop mod0
    pop mod3
    ret always


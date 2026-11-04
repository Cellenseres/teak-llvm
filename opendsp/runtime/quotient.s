// SPDX-License-Identifier: BSD-2-Clause
.section .text.__teak_divmod40
.global __teak_divmod40
.type __teak_divmod40,@function
__teak_divmod40:
    push r0
    push r1
    push mod0
    set 0x0003, mod0
    mov b0l, r0
    cmp a1, a0
    br .Ldivide_small, c
    clr b0, always
    mov 0x28, r1
.Ldivide_bit:
    shfi a0, a0, +1
    // ROL b0, always
    .short 0x6f50
    br .Ldivide_subtract, c
    cmp a1, b0
    br .Ldivide_next, c
.Ldivide_subtract:
    sub a1, b0
    or 0x1, a0
.Ldivide_next:
    addv 0xffff, r1
    br .Ldivide_bit, neq
    cmpv 0x0, r0
    br .Ldivide_return, eq
    mov b0, a0
    br .Ldivide_return, always
.Ldivide_small:
    cmpv 0x0, r0
    br .Ldivide_return, neq
    clr a0, always
.Ldivide_return:
    pop mod0
    pop r1
    pop r0
    ret always
.size __teak_divmod40, .-__teak_divmod40

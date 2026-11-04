// SPDX-License-Identifier: BSD-2-Clause
.text
.global quotient_mode
quotient_mode:
    push mod0
    push r0
    push r1
    push r2
    push r3
    push r6
    mov a1l, r6
    push a0l
    pop mod0
    push mod0
    pop r2
    mov r2, [r6++]
    mov 0x1357, r0
    mov 0x2468, r1
    clr a0, always
    not a0, always
    mov 0x1, a1
    clr b0, always
    call __teak_divmod40, always
    mov a0l, [r6++]
    mov a0h, [r6++]
    push mod0
    pop r2
    mov r2, [r6++]
    mov r0, [r6++]
    mov r1, [r6++]
    set 0x0083, mod0
    shfi a0, a0, -32
    and 0x00ff, a0
    mov a0l, [r6]
    pop r6
    pop r3
    pop r2
    pop r1
    pop r0
    pop mod0
    ret always

// SPDX-License-Identifier: BSD-2-Clause
.text
.global state_word_product
state_word_product:
    push mod0
    push mod3
    push r0
    push r3
    push r6
    mov b0l, r6
    mov b1l, r0
    mov 0x0c00, mod0
    push r0
    pop mod3
    push mod0
    pop r3
    mov r3, [r6++]
    push mod3
    pop r3
    mov r3, [r6++]
    call __teak_mulword40, always
    push mod0
    pop r3
    mov r3, [r6++]
    push mod3
    pop r3
    mov r3, [r6]
    pop r6
    pop r3
    pop r0
    pop mod3
    pop mod0
    ret always

.global state_low_product
state_low_product:
    push mod0
    push mod3
    push r0
    push r3
    push r6
    mov b0l, r6
    mov b1l, r0
    mov 0x0c00, mod0
    push r0
    pop mod3
    push mod0
    pop r3
    mov r3, [r6++]
    push mod3
    pop r3
    mov r3, [r6++]
    call __teak_mul40, always
    push mod0
    pop r3
    mov r3, [r6++]
    push mod3
    pop r3
    mov r3, [r6]
    pop r6
    pop r3
    pop r0
    pop mod3
    pop mod0
    ret always

.global state_high_product
state_high_product:
    push mod0
    push mod3
    push r0
    push r3
    push r6
    mov b0l, r6
    mov b1l, r0
    mov 0x0c00, mod0
    push r0
    pop mod3
    push mod0
    pop r3
    mov r3, [r6++]
    push mod3
    pop r3
    mov r3, [r6++]
    call __teak_umulh40, always
    push mod0
    pop r3
    mov r3, [r6++]
    push mod3
    pop r3
    mov r3, [r6]
    pop r6
    pop r3
    pop r0
    pop mod3
    pop mod0
    ret always


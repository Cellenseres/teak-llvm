// SPDX-License-Identifier: BSD-2-Clause
.section .text.start
.global _start
_start:
    dint
    mov 0x0000, mod3
    rst 0x6ce1, mod0
    set 0x0003, mod0
    rst 0xd0ff, mod1
    set 0x2000, mod1
    mov 0x0000, mod2
    mov 0x0000, cfgi
    mov 0x0000, cfgj
    mov 0x0000, stepi0
    mov 0x0000, stepj0
    mov 0x0021, arp0
    mov 0x258c, arp1
    mov 0x4ab5, arp2
    mov 0x6c63, arp3
    mov 0, sp
    addv 0x07ff, sp
    mov 0x110c, ar0
    mov 0x56a3, ar1
    call main, always
.Lhalt:
    br .Lhalt, always

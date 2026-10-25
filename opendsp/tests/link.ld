OUTPUT_FORMAT("elf32-teak", "elf32-teak", "elf32-teak")
OUTPUT_ARCH(teak)
ENTRY(_start)
PHDRS { prog PT_LOAD; data PT_LOAD; }
SECTIONS {
    . = 0;
    .text : { KEEP(*(.text.start)) *(.text*) } :prog
    . = 0x10002000;
    .rodata : ALIGN(4) { *(.rodata*) } :data
    .data : ALIGN(4) { *(.data*) } :data
    .bss : ALIGN(4) { *(.bss* COMMON) } :data
    ASSERT(. < 0x10006000, "Probe globals overlap result mailbox")
    /DISCARD/ : { *(.comment) *(.note*) }
}

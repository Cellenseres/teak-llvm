; RUN: llc -mtriple=teak -O2 %s \
; RUN: -o - | FileCheck %s

target datalayout = "E-m:e-P1-p0:16:16:16-p1:32:32:32-i1:16:16-i8:16:16-i16:16:16-i32:32:32-a:0:32-n16:40"
target triple = "teak"

@large_array = external global [8194 x i32], align 4

; CHECK-LABEL: large_offset:
; CHECK: mov large_array+16386, a0l
define i32* @large_offset() addrspace(1) {
  %address = getelementptr [8194 x i32], [8194 x i32]* @large_array, i16 1, i16 -1
  ret i32* %address
}

; CHECK-LABEL: large_element:
; CHECK: mov large_array+32766, a0l
define i32* @large_element() addrspace(1) {
  %address = getelementptr [8194 x i32], [8194 x i32]* @large_array, i16 0, i16 16383
  ret i32* %address
}

; CHECK-LABEL: negative_offset:
; CHECK: mov large_array-2, a0l
define i32* @negative_offset() addrspace(1) {
  %address = getelementptr [8194 x i32], [8194 x i32]* @large_array, i16 0, i16 -1
  ret i32* %address
}

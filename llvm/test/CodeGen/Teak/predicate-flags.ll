; RUN: llc -mtriple=teak -O2 -asm-verbose=false < %s | FileCheck %s
;
; CLR overwrites the comparison flags.

; CHECK-LABEL: less_than:
; CHECK: cmp a1l, a0
; CHECK-NEXT: br {{.*}}, lt
; CHECK: clr a0, always
; CHECK-NEXT: ret always
define i16 @less_than(i16 %a, i16 %b) {
  %condition = icmp slt i16 %a, %b
  %value = zext i1 %condition to i16
  ret i16 %value
}

; CHECK-LABEL: greater_equal:
; CHECK: cmp a1l, a0
; CHECK-NEXT: br {{.*}}, ge
; CHECK: clr a0, always
; CHECK-NEXT: ret always
define i16 @greater_equal(i16 %a, i16 %b) {
  %condition = icmp sge i16 %a, %b
  %value = zext i1 %condition to i16
  ret i16 %value
}

; CHECK-LABEL: equal:
; CHECK: cmp a1l, a0
; CHECK-NEXT: br {{.*}}, eq
; CHECK: clr a0, always
; CHECK-NEXT: ret always
define i16 @equal(i16 %a, i16 %b) {
  %condition = icmp eq i16 %a, %b
  %value = zext i1 %condition to i16
  ret i16 %value
}

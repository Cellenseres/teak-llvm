; SPDX-License-Identifier: BSD-2-Clause
target datalayout = "E-m:e-P1-p0:16:16:16-p1:32:32:32-i1:16:16-i8:16:16-i16:16:16-i32:32:32-a:0:32-n16:40"
target triple = "teak"

declare i40 @__teak_umulh40(i40, i40) addrspace(1) nounwind readnone

define i40 @__teak_smulh40(i40 %left, i40 %right) addrspace(1) #0 {
  %unsigned_high = call addrspace(1) i40 @__teak_umulh40(i40 %left, i40 %right)
  %left_sign = ashr i40 %left, 39
  %right_sign = ashr i40 %right, 39
  %left_correction = and i40 %left_sign, %right
  %right_correction = and i40 %right_sign, %left
  %first = sub i40 %unsigned_high, %left_correction
  %result = sub i40 %first, %right_correction
  ret i40 %result
}

attributes #0 = { noinline nounwind readnone }
